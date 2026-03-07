import os, logging, numpy, pandas, shap, joblib, orjson, time, pyarrow, pyarrow.parquet, torch, torch.nn as NN, dash_bootstrap_components as dbc, plotly.graph_objects as GO
from concurrent.futures import ThreadPoolExecutor, as_completed
from torch.utils.data import DataLoader, TensorDataset
from dash import Dash, dcc, html, Input, Output, State
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from Utility import Configuration, Logger

Lookback = 26
torch.set_num_threads(4)

# -------- Analytics Pipeline -------- #
class Analytics:
    def __init__(self, Log, Frame, Statics):
        self._Log = Log
        self._Frame = Frame.to_pandas()
        self.Statics = Statics
        self._NNDir = Path(Configuration["Files"]["NN"]["Directory"])
        self._ParquetDir = Path(Configuration["Files"]["Parquets"]["Directory"])
        self._ParquetDir.mkdir(parents = True, exist_ok = True)
        self._Frame.sort_values(["SegmentKey", "TimeIndex"], inplace = True)
        for Col in self._Frame.select_dtypes(include=[numpy.number]).columns.difference({"Year", "TimeIndex"}): self._Frame[f"{Col}Trend"] = self._Frame.groupby("SegmentKey")[Col].diff().fillna(0)

        # -------- Derived Features -------- #
        self._Frame["TrainIndex"] = self._Frame["TrainNumber"].astype("category").cat.codes
        self._Frame["LoadUtilization"] = self._Frame["EffectiveLoad"] / self._Frame["Capacity"].replace(0, numpy.nan)
        self._Frame["GradientLoad"] = self._Frame["Gradient"] * self._Frame["Distance"]
        self._Frame["WeekSin"] = numpy.sin(2 * numpy.pi * self._Frame["Week"] / 52)
        self._Frame["WeekCos"] = numpy.cos(2 * numpy.pi * self._Frame["Week"] / 52)
        self._Frame.fillna(0, inplace = True)

        # -------- Targets / Features -------- #
        self._Targets = Configuration["ML"]["Targets"]
        self._Features = Configuration["ML"]["Features"] + [f"{T}Trend" for T in self._Targets]
        self._FullCols = self._Targets + [F for F in self._Features if F not in self._Targets]
        self._Models, self._Scalers, self._Drift, self._Importance, self._Metrics, self._Version = {}, {}, {}, None, {}, None
        self._Log.Event("Analytics ready | %s rows | %s targets | %s features", len(self._Frame), len(self._Targets), len(self._Features))

    # -------- GRU Architecture -------- #
    def _GRU(self, InputSize, OutputSize):
        class _Net(NN.Module):
            def __init__(self): super().__init__(); self.GRU = NN.GRU(InputSize, 64, 2, batch_first = True, dropout = 0.2); self.Head = NN.Linear(64, OutputSize)
            def forward(self, X): Out, _ = self.GRU(X); return self.Head(Out[:, -1, :])
        return _Net()

    # -------- Sliding Window -------- #
    def _Windows(self, Values): return numpy.lib.stride_tricks.sliding_window_view(Values[:-1], (Lookback, Values.shape[1])).squeeze(1).astype(numpy.float32), Values[Lookback:, :len(self._Targets)].astype(numpy.float32)

    # -------- Per-Segment Normalisation -------- #
    def _Fit(self, Key, Arr): M, S = Arr.mean(0), Arr.std(0) + 1e-8; self._Scalers[Key] = (M, S); return (Arr - M) / S
    def _Scale(self, Key, Arr): M, S = self._Scalers[Key]; return (Arr - M) / S
    def _Unscale(self, Key, Pred): M, S = self._Scalers[Key]; return Pred * S[:len(self._Targets)] + M[:len(self._Targets)]

    # -------- Train One Segment (Thread Pool) -------- #
    def _TrainSegment(self, Key, Arr, Epochs = 50, Patience = 10):
        torch.set_num_threads(2)
        if len(Arr) <= Lookback + 4: return Key, None, numpy.inf
        X, Y = self._Windows(Arr)
        Ti, Vi = int(0.8 * len(X)), int(0.9 * len(X))
        Loader = DataLoader(TensorDataset(torch.from_numpy(X[:Ti]), torch.from_numpy(Y[:Ti])), batch_size = 32, shuffle = True)
        Model, Loss = self._GRU(len(self._FullCols), len(self._Targets)), NN.MSELoss()
        Opt = torch.optim.Adam(Model.parameters(), lr = 1e-3, weight_decay = 1e-4)
        Sched = torch.optim.lr_scheduler.ReduceLROnPlateau(Opt, patience = 5, factor = 0.5)
        BestLoss, BestState, Wait = numpy.inf, None, 0
        XVal, YVal = torch.from_numpy(X[Ti:Vi]), torch.from_numpy(Y[Ti:Vi])
        for _ in range(Epochs):
            Model.train()
            for Xb, Yb in Loader: Opt.zero_grad(); L = Loss(Model(Xb), Yb); L.backward(); NN.utils.clip_grad_norm_(Model.parameters(), 1.0); Opt.step()
            Model.eval()
            ValLoss = Loss(Model(XVal), YVal).item() if len(XVal) else numpy.inf
            Sched.step(ValLoss)
            if ValLoss < BestLoss - 1e-4: BestLoss, BestState, Wait = ValLoss, {K: V.clone() for K, V in Model.state_dict().items()}, 0
            else:
                Wait += 1
                if Wait >= Patience: break
        if BestState: Model.load_state_dict(BestState)
        return Key, Model, BestLoss

    # -------- Train -------- #
    def Train(self):
            self._Models, self._Scalers = {}, {}
            SegmentKeys = self._Frame["SegmentKey"].unique()
            SegArrays = {Key: self._Fit(Key, Group[self._FullCols].values.astype(numpy.float32)) for Key, Group in self._Frame.groupby("SegmentKey")}
            AllPreds = {}

            with Logger.Loader(len(SegmentKeys), "Training segments") as Progress:
                with ThreadPoolExecutor(max_workers = 3) as Pool:
                    for Future in as_completed({Pool.submit(self._TrainSegment, Key, SegArrays[Key]): Key for Key in SegmentKeys}):
                        Key, Model, _ = Future.result()
                        if Model:
                            self._Models[Key] = Model
                            Q = max(len(SegArrays[Key]) // 8, 1)
                            self._Drift[Key] = float(numpy.abs(SegArrays[Key][-Q * 2: - Q].mean(0) - SegArrays[Key][-Q:].mean(0)).mean())
                            X, Y = self._Windows(SegArrays[Key])
                            Model.eval()
                            with torch.no_grad(): AllPreds[Key] = (self._Unscale(Key, Y), self._Unscale(Key, Model(torch.from_numpy(X)).numpy()))
                        Progress.Advance()

            YAll, PAll = numpy.vstack([V[0] for V in AllPreds.values()]), numpy.vstack([V[1] for V in AllPreds.values()])
            self._Metrics = {"R2": round(float(1 - ((YAll - PAll) ** 2).sum() / ((YAll - YAll.mean(0)) ** 2).sum()), 3), "MAE": round(float(numpy.abs(YAll - PAll).mean()), 3), "SMAPE": round(float((2 * numpy.abs(YAll - PAll) / (numpy.abs(YAll) + numpy.abs(PAll) + 1e-8)).mean()), 3), "LoadUnder": float((YAll > PAll).sum() / YAll.size)}
            for I, T in enumerate(self._Targets): self._Metrics[f"{T}MAE"] = round(float(numpy.abs(YAll[:, I] - PAll[:, I]).mean()), 3)

            # -------- Feature Importance -------- #
            ImportScores = numpy.zeros(len(self._FullCols))
            Sample = list(self._Models.keys())[::5]
            for Key in Sample:
                Xt = torch.from_numpy(self._Windows(SegArrays[Key])[0]).requires_grad_(True)
                self._Models[Key](Xt).sum().backward()
                ImportScores += Xt.grad.abs().mean((0, 1)).detach().numpy()
            self._Importance = pandas.DataFrame({"Feature": self._FullCols, "Importance": ImportScores / len(Sample)}).sort_values("Importance", ascending = False)

            self._Version = f"V{len(list(self._NNDir.glob('V*.pt'))) + 1}"
            torch.save({"Models": {K: M.state_dict() for K, M in self._Models.items()}, "Scalers": self._Scalers}, self._NNDir / f"{self._Version}.pt")
            pyarrow.parquet.write_table(pyarrow.Table.from_pandas(self._Frame).replace_schema_metadata({b"Metrics": orjson.dumps(self._Metrics), b"Importance": orjson.dumps(self._Importance.to_dict("records"))}), self._ParquetDir / f"{self._Version}.parquet")
            self._Drift = {Key: 0.0 for Key in self._Models}
            self._Log.Event("%s | R2 %s | MAE %s | SMAPE %s | DelayMAE %s | %s segments", self._Version, self._Metrics["R2"], self._Metrics["MAE"], self._Metrics["SMAPE"] * 100, self._Metrics["DelayMAE"], len(self._Models))
        
    # -------- Load -------- #
    def Load(self, Version):
        Stem = (max((F.name for F in self._NNDir.glob("V*.pt")), default="V1.pt") if Version is None else f"{Version}.pt")[:-3]
        Snapshot = torch.load(self._NNDir / f"{Stem}.pt", map_location="cpu", weights_only = False)
        self._Scalers = Snapshot["Scalers"]
        self._Models = {}
        for Key, State in Snapshot["Models"].items():
            M = self._GRU(len(self._FullCols), len(self._Targets))
            M.load_state_dict(State)
            M.eval()
            self._Models[Key] = M
        self._Drift = {Key: 0.0 for Key in self._Models}
        self._Version = Stem
        Meta = pyarrow.parquet.read_schema(self._ParquetDir / f"{Stem}.parquet").metadata
        self._Metrics, self._Importance = orjson.loads(Meta[b"Metrics"]), pandas.DataFrame(orjson.loads(Meta[b"Importance"]))
        self._Log.Event("Loaded %s | %s segments | Ready", self._Version, len(self._Models))

    # -------- Serve -------- #
    def Serve(self, Frame: pandas.DataFrame, DriftThreshold: float = 0.05) -> pandas.DataFrame:
        if max(self._Drift.values(), default = 0) > DriftThreshold: self._Log.Event("Drift %s — Retraining.", DriftThreshold * 100); self.Train()
        Results = []
        for Key, Group in Frame.groupby("SegmentKey"):
            if Key not in self._Models: continue
            Scaled = self._Scale(Key, Group[self._FullCols].fillna(0).values.astype(numpy.float32))
            if len(Scaled) < Lookback: Scaled = numpy.pad(Scaled, ((Lookback - len(Scaled), 0), (0, 0)))
            self._Models[Key].eval()
            with torch.no_grad(): Pred = self._Unscale(Key, self._Models[Key](torch.from_numpy(Scaled[-Lookback:]).unsqueeze(0)).numpy()[0])
            Row = Group.iloc[[-1]].copy()
            for I, T in enumerate(self._Targets): Row[f"Predicted{T}"] = Pred[I]
            Results.append(Row)
        return pandas.concat(Results, ignore_index = True) if Results else Frame.head(0)

    # -------- Explain -------- #
    def Explain(self, SegmentKey):
        X, _ = self._Windows(self._Scale(SegmentKey, self._Frame[self._Frame["SegmentKey"] == SegmentKey][self._FullCols].fillna(0).values.astype(numpy.float32)))
        return shap.GradientExplainer(self._Models[SegmentKey], torch.from_numpy(X[:32])).shap_values(torch.from_numpy(X))

    # -------- Forecast -------- #
    def Forecast(self, TrainNumber: str, Year: int, Week: int) -> pandas.DataFrame:
        Rows = []
        Groups = list(self._Frame[self._Frame["TrainNumber"] == TrainNumber].groupby("SegmentKey"))
        with Logger.Loader(len(Groups), f"Forecasting {TrainNumber}") as Progress:
            for Key, Group in Groups:
                if Key not in self._Models: Progress.Advance(); continue
                Recent, Last = Group.sort_values("TimeIndex").tail(Lookback), Group.sort_values("TimeIndex").iloc[-1]
                Cap, Dist, Grad = float(Last["Capacity"]), float(Last["Distance"]), float(Last["Gradient"])
                NextRow = {C: float(Last[C]) if C in Last else 0.0 for C in self._FullCols}
                NextRow.update({"LoadUtilization": float(Last.get("EffectiveLoad", 0)) / Cap if Cap > 0 else 0, "GradientLoad": Grad * Dist, "WeekSin": float(numpy.sin(2 * numpy.pi * Week / 52)), "WeekCos": float(numpy.cos(2 * numpy.pi * Week / 52)), "TimeIndex": Year * 52 + Week, "Week": Week})
                for T in self._Targets:
                    if f"{T}Trend" in self._FullCols: NextRow[f"{T}Trend"] = float(numpy.polyfit(numpy.arange(min(12, len(Recent))), Recent[T].tail(12).values, 1)[0])
                Scaled = self._Scale(Key, numpy.vstack([Recent[self._FullCols].fillna(0).values.astype(numpy.float32), numpy.array([[NextRow[C] for C in self._FullCols]], dtype = numpy.float32)]))
                self._Models[Key].eval()
                with torch.no_grad(): Pred = self._Unscale(Key, self._Models[Key](torch.from_numpy(Scaled[-Lookback:]).unsqueeze(0)).numpy()[0])
                Rows.append({"TrainNumber": TrainNumber, "SegmentKey": Key, "Source": Last["Source"], "Destination": Last["Destination"], "Year": Year, "Week": Week, "Capacity": Cap, "Distance": Dist, "Gradient": Grad, **{f"Predicted{T}": float(Pred[I]) for I, T in enumerate(self._Targets)}})
                Progress.Advance()
        Frame = pandas.DataFrame(Rows)
        Frame["UtilisationPercent"] = (Frame["PredictedEffectiveLoad"] / Frame["Capacity"] * 100).round(1)
        Frame["RiskLevel"] = Frame["UtilisationPercent"].apply(lambda U: "Critical" if U > 95 else "High" if U > 85 else "Medium" if U > 70 else "Low")
        self._Log.Event("Forecast | %s | %sY W%s | %s segments", TrainNumber, Year, Week, len(Frame))
        return Frame.reset_index(drop = True)


# -------- Dashboard -------- #
class Dashboard:
    # -------- Theme -------- #
    _C = {"BG": "#0a0c0f", "Surface": "#111318", "Border": "#1e2229", "Accent": "#e8ff47", "Accent2": "#47c5ff", "Accent3": "#ff6b47", "Warn": "#ffaa47", "Muted": "#4a5260", "Dim": "#6b7585"}
    _T = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font = dict(family="DM Mono, monospace", color="#6b7585", size = 11), margin = dict(l = 8, r = 8, t = 28, b = 8), legend = dict(bgcolor="rgba(0,0,0,0)", font = dict(color="#6b7585", size = 10)),
        xaxis = dict(gridcolor="#1e2229", showgrid = True, zeroline = False, linecolor="#1e2229"), yaxis = dict(gridcolor="#1e2229", showgrid = True, zeroline = False, linecolor="#1e2229"))

    # -------- CSS -------- #
    _CSS = """@import url('https://fonts.googleapis.com/css2?family = DM+Mono:wght@300;400;500&family = Syne:wght@400;600;700;800&display = swap');
        body,.dash-app{background:#0a0c0f!important;color:#d4dae6;font-family:'DM Mono',monospace;font-size:13px}
        body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(255,255,255,.012) 2px,rgba(255,255,255,.012) 4px);pointer-events:none;z-index:9999}
        ::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:#0a0c0f}::-webkit-scrollbar-thumb{background:#1e2229;border-radius:2px}
        .rail-header{position:sticky;top:0;z-index:100;background:rgba(10,12,15,.95);backdrop-filter:blur(12px);border-bottom:1px solid #1e2229;padding:0 28px;display:flex;align-items:center;gap:24px;height:56px}
        .rail-logo{font-family:'Syne',sans-serif;font-weight:800;font-size:15px;letter-spacing:.08em;color:#e8ff47;text-transform:uppercase;white-space:nowrap;flex-shrink:0}
        .filter-label{font-size:10px;color:#6b7585;letter-spacing:.1em;text-transform:uppercase;white-space:nowrap}
        .filter-group{display:flex;align-items:center;gap:6px}
        .rail-main{padding:24px 28px;display:flex;flex-direction:column;gap:28px}
        .section-hdr{display:flex;align-items:center;gap:12px;margin-bottom:14px}
        .section-title{font-family:'Syne',sans-serif;font-weight:700;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#6b7585;white-space:nowrap}
        .section-line{flex:1;height:1px;background:#1e2229}
        .kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:10px}
        .kpi-card{background:#111318;border:1px solid #1e2229;border-radius:4px;padding:16px 18px;position:relative;overflow:hidden}
        .kpi-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px}
        .kpi-good::after{background:#e8ff47}.kpi-info::after{background:#47c5ff}.kpi-warn::after{background:#ffaa47}.kpi-alert::after{background:#ff6b47}.kpi-neu::after{background:#4a5260}
        .kpi-label{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#6b7585;margin-bottom:8px}
        .kpi-value{font-family:'Syne',sans-serif;font-weight:700;font-size:28px;color:#d4dae6;line-height:1;margin-bottom:4px}
        .kpi-sub{font-size:10px;color:#6b7585}
        .kpi-badge{display:inline-block;font-size:9px;padding:2px 6px;border-radius:2px;margin-top:6px;letter-spacing:.06em}
        .badge-good{background:rgba(232,255,71,.12);color:#e8ff47}.badge-warn{background:rgba(255,170,71,.12);color:#ffaa47}.badge-alert{background:rgba(255,107,71,.12);color:#ff6b47}.badge-muted{background:rgba(74,82,96,.2);color:#4a5260}
        .cols-3{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px}.cols-32{display:grid;grid-template-columns:3fr 2fr;gap:10px}.cols-2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
        .rail-card{background:#111318;border:1px solid #1e2229;border-radius:4px;padding:18px 20px}
        .card-title{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#6b7585;margin-bottom:12px}
        .forecast-controls{display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:4px}
        .forecast-input-group{display:flex;flex-direction:column;gap:4px}
        .forecast-input-label{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#6b7585}
        .route-strip{display:flex;align-items:stretch;gap:2px;border-radius:3px;overflow:hidden;margin-bottom:6px;height:90px}
        .route-segment{display:flex;align-items:center;justify-content:center;flex-direction:column;font-size:9px;letter-spacing:.06em;text-transform:uppercase;font-weight:500;cursor:pointer;transition:filter .15s;padding:2px 4px;text-align:center;min-width:0}
        .route-segment:hover{filter:brightness(1.2)}
        .route-labels{display:flex;gap:2px;margin-bottom:12px}
        .route-segment-label{font-size:9px;color:#6b7585;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
        .risk-table{width:100%;border-collapse:collapse}
        .risk-table th{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#6b7585;text-align:left;padding:8px 12px;border-bottom:1px solid #1e2229;font-weight:400}
        .risk-table td{padding:9px 12px;border-bottom:1px solid rgba(30,34,41,.6);font-size:12px;color:#d4dae6}
        .risk-table tr:hover td{background:rgba(255,255,255,.02)}
        .pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:10px;letter-spacing:.05em}
        .pill-red{background:rgba(255,107,71,.15);color:#ff6b47;border:1px solid rgba(255,107,71,.25)}.pill-yellow{background:rgba(255,170,71,.15);color:#ffaa47;border:1px solid rgba(255,170,71,.25)}
        .Select-control,.Select-menu-outer{background:#111318!important;border-color:#1e2229!important;color:#d4dae6!important;font-family:'DM Mono',monospace!important;font-size:12px!important}
        .Select-control input,.Select input[type = text]{color:#d4dae6!important;background:transparent!important;font-family:'DM Mono',monospace!important}
        .Select-value-label,.Select-placeholder{color:#d4dae6!important}.Select-option{background:#111318!important;color:#d4dae6!important}.Select-option:hover,.Select-option.is-focused{background:#1e2229!important}
        input[type = number]{background:#111318;border:1px solid #1e2229;color:#d4dae6;font-family:'DM Mono',monospace;font-size:12px;padding:6px 10px;border-radius:3px;outline:none;width:90px}
        input[type = number]:focus{border-color:#e8ff47}
        .btn-forecast{background:transparent;border:1px solid #e8ff47;color:#e8ff47;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;padding:7px 18px;cursor:pointer;text-transform:uppercase;border-radius:2px}
        .btn-export{background:transparent;border:1px solid #e8ff47;color:#e8ff47;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;padding:5px 14px;cursor:pointer;text-transform:uppercase;border-radius:2px;margin-left:auto}
        .no-data{color:#4a5260;font-size:12px;padding:24px;text-align:center}"""

    @staticmethod
    def _RGBA(Hex, Alpha): return f"rgba({int(Hex[1:3],16)},{int(Hex[3:5],16)},{int(Hex[5:7],16)},{Alpha})"

    # -------- Init -------- #
    def __init__(self, DataFrame, Analytics, Metrics, Importance, Years):
        self._DataFrame = DataFrame.reset_index(drop = True)
        self._Analytics = Analytics
        self._Metrics = Metrics or {}
        self._Importance = Importance
        self._Zones = sorted(self._DataFrame["Zone"].unique()) if "Zone" in self._DataFrame.columns else []
        self._Types = sorted(self._DataFrame["Type"].unique()) if "Type" in self._DataFrame.columns else []
        self._Years = Years if Years else (sorted(self._DataFrame["Year"].unique()) if "Year" in self._DataFrame.columns else [])
        self._Categories = sorted(self._DataFrame["Category"].unique()) if "Category" in self._DataFrame.columns else []
        self._Trains = sorted([{"label": f"{Row['TrainNumber']} — {Row['Name']}", "value": Row["TrainNumber"]} for _, Row in self._DataFrame[["TrainNumber", "Name"]].drop_duplicates().iterrows()], key = lambda X: X["value"]) if {"TrainNumber", "Name"} <= set(self._DataFrame.columns) else [{"label": V, "value": V} for V in sorted(self._DataFrame["TrainNumber"].unique())]
        self._App = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
        self._App.title = "Halcyon"
        self._App.index_string = self._App.index_string.replace("</head>", f"<style>{self._CSS}</style></head>")
        self._App.layout = self._Layout()
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        self._RegisterCallbacks()

    # -------- Layout -------- #
    def _Layout(self):
        DropStyle = {"backgroundColor": self._C["Surface"], "border": f"1px solid {self._C['Border']}", "color": "#d4dae6", "fontFamily": "DM Mono, monospace", "fontSize": "12px", "minWidth": "120px"}
        HasLoad = {"EffectiveLoad", "PredictedEffectiveLoad"} <= set(self._DataFrame.columns)
        R2 = self._Metrics.get("R2", 0)

        ScatterFigure = GO.Figure(layout = self._T)
        for Category, Column in [("PAX", self._C["Accent"]), ("FGT", self._C["Accent2"])]:
            Sub = self._DataFrame[self._DataFrame["Category"] == Category] if "Category" in self._DataFrame.columns else self._DataFrame
            ScatterFigure.add_trace(GO.Scatter(x = Sub.get("EffectiveLoad", []), y = Sub.get("PredictedEffectiveLoad", []), mode="markers", name = Category, marker = dict(color = Column, size = 4)))
        if HasLoad:
            MaxLoad = max(self._DataFrame["EffectiveLoad"].max(), self._DataFrame["PredictedEffectiveLoad"].max())
            ScatterFigure.add_trace(GO.Scatter(x=[0, MaxLoad], y=[0, MaxLoad], mode="lines", name="Perfect fit", line = dict(color = self._C["Muted"], dash="dash", width = 1)))
        ScatterFigure.update_layout(xaxis_title="Actual", yaxis_title="Predicted")

        ImportFigure = GO.Figure(layout = self._T)
        if self._Importance is not None and not self._Importance.empty:
            TopFeat = self._Importance.head(10)
            ImportFigure.add_trace(GO.Bar(x = TopFeat["Importance"], y = TopFeat["Feature"], orientation="h", marker = dict(line = dict(width = 0), color=[self._C["Accent"], self._RGBA(self._C["Accent"],0.8), self._RGBA(self._C["Accent"],0.67), self._RGBA(self._C["Accent2"],0.8), self._RGBA(self._C["Accent2"],0.53), self._RGBA(self._C["Muted"],0.8), self._RGBA(self._C["Muted"],0.53), self._RGBA(self._C["Muted"],0.4), self._RGBA(self._C["Muted"],0.27), self._RGBA(self._C["Muted"],0.13)][:len(TopFeat)])))
            ImportFigure.update_layout(yaxis = dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"))

        ErrorFigure = GO.Figure(layout = self._T)
        if HasLoad:
            ErrorFigure.add_trace(GO.Histogram(x = self._DataFrame["EffectiveLoad"] - self._DataFrame["PredictedEffectiveLoad"], nbinsx = 30, marker={"color": self._C["Accent"]}, opacity = 0.4, marker_line_width = 0))
            ErrorFigure.update_layout(xaxis_title="Residual (Actual − Predicted)", bargap = 0.05)

        def SHdr(Title): return html.Div([html.Span(Title, className="section-title"), html.Div(className="section-line")], className="section-hdr")
        def Card(Title, *Body): return html.Div([html.Div(Title, className="card-title"), *Body], className="rail-card")
        def Figure(Id, F = None, H="200px"): return dcc.Graph(id = Id, figure = F or GO.Figure(layout = self._T), config={"displayModeBar": False}, style={"height": H})

        return html.Div([
            dcc.Interval(id="InitTrigger", interval = 1, max_intervals = 1),
            dcc.Store(id="FilterStore", data={"Zone": None, "Type": None, "Year": None, "Category": None}),
            dcc.Store(id="ForecastStore", data=[]),
            dcc.Download(id="DownloadJSON"),

            html.Div([
                html.Div("Halcyon", className="rail-logo"),
                html.Div([
                    html.Div([html.Span("Zone", className="filter-label"), dcc.Dropdown(id="ZoneFilter", options=[{"label": V, "value": V} for V in self._Zones], placeholder="All Zones", clearable = True, style = DropStyle)], className="filter-group"),
                    html.Div([html.Span("Type", className="filter-label"), dcc.Dropdown(id="TypeFilter", options=[{"label": V, "value": V} for V in self._Types], placeholder="All Types", clearable = True, style = DropStyle)], className="filter-group"),
                    html.Div([html.Span("Year", className="filter-label"), dcc.Dropdown(id="YearFilter", options=[{"label": str(V), "value": V} for V in self._Years], placeholder="All Years", clearable = True, style = DropStyle, optionHeight = 28, maxHeight = 200)], className="filter-group"),
                    html.Div([html.Span("Category", className="filter-label"), dcc.Dropdown(id="CategoryFilter", options=[{"label": V, "value": V} for V in self._Categories], placeholder="All", clearable = True, style = DropStyle)], className="filter-group"),
                ], style={"display": "flex", "gap": "12px", "alignItems": "center", "flex": "1"}),
                html.Button("↓ Export", id="ExportBtn", className="btn-export"),
            ], className="rail-header"),

            html.Div([
                html.Section([
                    SHdr("Model Health"),
                    html.Div([html.Div([html.Div(Label, className="kpi-label"), html.Div(Value, className="kpi-value"), html.Div(Sub, className="kpi-sub"), html.Span(Badge, className = f"kpi-badge {BC}")], className = f"kpi-card {KC}") for Label, Value, Sub, Badge, BC, KC in [
                        ("R²", f"{R2:.3f}", "Overall fit", "Strong" if R2 > 0.85 else "Moderate", "badge-good" if R2 > 0.85 else "badge-warn", "kpi-good" if R2 > 0.85 else "kpi-warn"),
                        ("MAE", f"{self._Metrics.get('MAE', 0):.1f}", "Mean abs. error", f"{'↓ Good' if self._Metrics.get('MAE', 0) < 50 else '↑ High'}", "badge-good" if self._Metrics.get('MAE', 0) < 50 else "badge-warn", "kpi-info"),
                        ("SMAPE", f"{self._Metrics.get('SMAPE', 0)*100:.1f}%", "Sym. abs. % error", f"{'Good' if self._Metrics.get('SMAPE', 0) < 0.2 else 'Watch'}", "badge-good" if self._Metrics.get('SMAPE', 0) < 0.2 else "badge-warn", "kpi-warn"),
                        ("Delay MAE", f"{self._Metrics.get('DelayMAE', 0):.0f}min", "Per segment", f"{'↓ Good' if self._Metrics.get('DelayMAE', 0) < 15 else '↑ Watch'}", "badge-good" if self._Metrics.get('DelayMAE', 0) < 15 else "badge-alert", "kpi-alert"),
                        ("Segments", str(len(self._Analytics._Models)), "Models trained", self._Analytics._Version or "—", "badge-muted", "kpi-neu"),
                    ]], className="kpi-grid"),
                    html.Div([Card("Actual vs Predicted — Effective Load", Figure("ScatterChart", ScatterFigure)), Card("Feature Importance", Figure("ImportanceChart", ImportFigure)), Card("Prediction Error Distribution", Figure("ErrorDistChart", ErrorFigure))], className="cols-3"),
                ]),

                html.Section([
                    SHdr("Demand & Traffic"),
                    html.Div([Card("Load Utilisation % over Time — by Zone", Figure("UtilChart")), Card("Delay Trend — by Category", Figure("DelayTrendChart"))], className="cols-32", style={"marginBottom": "10px"}),
                    html.Div([Card("Top 10 Congested Segments", Figure("CongestionChart", H="300px")), Card("Predicted Load Distribution — Next Period", Figure("LoadDistChart", H="300px"))], className="cols-2"),
                ]),

                html.Section([SHdr("Operations"), html.Div([Card("Reliability vs Delay — per Train", Figure("ReliabilityChart", H="400px")), Card("High-Risk Segments — Predicted Overload", html.Div(id="RiskTable"))], className="cols-2")]),

                html.Section([
                    SHdr("Forecast"),
                    html.Div([
                        Card("Controls",
                            html.Div([
                                html.Div([html.Div("Train", className="forecast-input-label"), dcc.Dropdown(id="ForecastTrain", options = self._Trains, placeholder="Select or type train...", clearable = False, searchable = True, style={**DropStyle, "minWidth": "220px"})], className="forecast-input-group"),
                                html.Div([html.Div("Year", className="forecast-input-label"), dcc.Input(id="ForecastYear", type="number", value = 2027, min = 2006, max = 2099, step = 1)], className="forecast-input-group"),
                                html.Div([html.Div("Week", className="forecast-input-label"), dcc.Input(id="ForecastWeek", type="number", value = 1, min = 1, max = 52, step = 1)], className="forecast-input-group"),
                                html.Button("Run Forecast", id="ForecastBtn", className="btn-forecast"),
                            ], className="forecast-controls"),
                            html.Div(id="ForecastStatus", style={"fontSize": "11px", "color": self._C["Dim"]}),
                        ),
                        Card("Segment Forecast Detail", Figure("ForecastChart", H="160px")),
                    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px", "marginBottom": "10px", "gridTemplateRows": "220px"}),
                    html.Div([html.Div("Route Strip — Utilisation by Segment", className="card-title"), html.Div(id="RouteStrip")], className="rail-card", style={"minHeight": "175px"}),
                ]),
            ], className="rail-main"),
        ], style={"backgroundColor": self._C["BG"], "minHeight": "100vh"})

    # -------- Callbacks -------- #
    def _RegisterCallbacks(self):
        self._App.callback(Output("FilterStore", "data"), Input("ZoneFilter", "value"), Input("TypeFilter", "value"), Input("YearFilter", "value"), Input("CategoryFilter", "value"), Input("InitTrigger", "n_intervals"))(lambda Zone, Type, Year, Category, _: {"Zone": Zone, "Type": Type, "Year": Year, "Category": Category})
        self._App.callback(Output("UtilChart", "figure"), Output("DelayTrendChart", "figure"), Output("CongestionChart", "figure"), Output("LoadDistChart", "figure"), Output("ReliabilityChart", "figure"), Output("RiskTable", "children"), Input("FilterStore", "data"))(self._RenderCharts)
        self._App.callback(Output("ForecastStore", "data"), Output("ForecastStatus", "children"), Input("ForecastBtn", "n_clicks"), State("ForecastTrain", "value"), State("ForecastYear", "value"), State("ForecastWeek", "value"), prevent_initial_call = True)(self._RunForecast)
        self._App.callback(Output("RouteStrip", "children"), Output("ForecastChart", "figure"), Input("ForecastStore", "data"))(self._RenderForecast)
        self._App.callback(Output("DownloadJSON", "data"), Input("ExportBtn", "n_clicks"), State("FilterStore", "data"), prevent_initial_call = True)(
            lambda _, Params: dict(content = orjson.dumps(self._DataFrame[numpy.logical_and.reduce([(self._DataFrame[C] == V) for C, V in Params.items() if V] or [numpy.ones(len(self._DataFrame), bool)])].to_dict("records"), option = orjson.OPT_INDENT_2).decode(), filename = f"Halcyon_{pandas.Timestamp.now():%Y%m%d_%H%M%S}.json") if Params else None)

    # -------- Chart Rendering -------- #
    def _RenderCharts(self, Params):
        Frame = self._DataFrame[numpy.logical_and.reduce([(self._DataFrame[C] == V) for C, V in Params.items() if V] or [numpy.ones(len(self._DataFrame), bool)])]
        if Frame.empty: return GO.Figure(layout = self._T), GO.Figure(layout = self._T), GO.Figure(layout = self._T), GO.Figure(layout = self._T), GO.Figure(layout = self._T), html.Div("No data", className="no-data")
        Frame = Frame.assign(UtilPct=(Frame["PredictedEffectiveLoad"] / Frame["Capacity"].replace(0, numpy.nan) * 100).fillna(0).clip(0, 150) if {"PredictedEffectiveLoad", "Capacity"} <= set(Frame.columns) else 0)

        UtilFigure = GO.Figure(layout = self._T)
        for Zone, Column in zip(sorted(Frame["Zone"].unique()), [self._C["Accent"], self._C["Accent2"], self._C["Accent3"], self._C["Warn"], self._C["Muted"]]):
            Sub = Frame[Frame["Zone"] == Zone].groupby("Week")["UtilPct"].mean().reset_index()
            UtilFigure.add_trace(GO.Scatter(x = Sub["Week"], y = Sub["UtilPct"], name = Zone, mode="lines", line = dict(color = Column, width = 2), fill="tozeroy", fillcolor = self._RGBA(Column, 0.09)))
        UtilFigure.update_layout(yaxis_title="Utilisation %", xaxis_title="Week", yaxis = dict(**self._T["yaxis"], range=[0, 150]))

        DelayFigure = GO.Figure(layout = self._T)
        if {"Category", "Delay"} <= set(Frame.columns):
            for Category, Column, Dash in [("PAX", self._C["Accent2"], "solid"), ("FGT", self._C["Muted"], "dash")]:
                Sub = Frame[Frame["Category"] == Category].groupby("Week")["Delay"].mean().reset_index()
                if not Sub.empty: DelayFigure.add_trace(GO.Scatter(x = Sub["Week"], y = Sub["Delay"], name = Category, mode="lines", line = dict(color = Column, width = 2, dash = Dash)))
        DelayFigure.update_layout(yaxis_title="Avg Delay (min)", xaxis_title="Week", yaxis = dict(**self._T["yaxis"], range=[0, float(Frame["Delay"].max() * 1.1) if "Delay" in Frame.columns and not Frame["Delay"].empty else 100]))

        CongFigure = GO.Figure(layout = self._T)
        if {"PredictedEffectiveLoad", "Capacity", "SegmentKey"} <= set(Frame.columns):
            SegUtil = Frame.assign(Util = Frame["PredictedEffectiveLoad"] / Frame["Capacity"].replace(0, numpy.nan) * 100).fillna(0).groupby("SegmentKey")["Util"].mean().nlargest(10).reset_index()
            SegUtil.columns = ["Segment", "Utilisation"]
            CongFigure.add_trace(GO.Bar(x = SegUtil["Utilisation"], y = SegUtil["Segment"], orientation="h", marker = dict(color=[self._C["Accent3"] if U > 85 else self._C["Warn"] if U > 75 else self._RGBA(self._C["Accent"], 0.53) for U in SegUtil["Utilisation"]], line = dict(width = 0))))
            CongFigure.update_layout(yaxis = dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"), xaxis_title="Avg Utilisation %", xaxis = dict(**self._T["xaxis"], range=[0, 150]), height = 300)

        DistFigure = GO.Figure(GO.Pie(labels=["< 60%", "60–80%", "80–95%", "> 95% Risk"], values=[(Frame["UtilPct"] < 60).sum(), ((Frame["UtilPct"] >= 60) & (Frame["UtilPct"] < 80)).sum(), ((Frame["UtilPct"] >= 80) & (Frame["UtilPct"] < 95)).sum(), (Frame["UtilPct"] >= 95).sum()],
            hole = 0.68, marker = dict(colors=[self._RGBA(self._C["Muted"],0.53), self._RGBA(self._C["Accent"],0.4), self._RGBA(self._C["Warn"],0.53), self._RGBA(self._C["Accent3"],0.8)], line = dict(width = 0))), layout = self._T)

        RelFigure = GO.Figure(layout = self._T)
        if {"Reliability", "Delay", "Type"} <= set(Frame.columns):
            for TrainType, Column in [("Express", self._C["Accent"]), ("Superfast", self._C["Accent2"]), ("BOXN", self._C["Muted"])]:
                Sub = Frame[Frame["Type"] == TrainType].groupby("TrainNumber").agg(AvgDelay=("Delay", "mean"), AvgRel=("Reliability", "mean"), Count=("Delay", "count")).reset_index()
                if not Sub.empty: RelFigure.add_trace(GO.Scatter(x = Sub["AvgDelay"], y = Sub["AvgRel"], mode="markers", name = TrainType, marker = dict(color = self._RGBA(Column, 0.4), size = numpy.sqrt(Sub["Count"]).clip(4, 16), line = dict(width = 0))))
        RelFigure.update_layout(xaxis_title="Avg Delay (min)", yaxis = dict(**self._T["yaxis"], tickformat=".0%", title="Reliability", range=[0, 1]))

        RiskTable = html.Div("No risk data", className="no-data")
        if {"PredictedEffectiveLoad", "Capacity", "SegmentKey"} <= set(Frame.columns):
            Risk = Frame.assign(Util = Frame["PredictedEffectiveLoad"] / Frame["Capacity"].replace(0, numpy.nan) * 100).fillna(0)
            Risk = Risk[Risk["Util"] > 70].nlargest(8, "Util").drop_duplicates("SegmentKey")
            RiskTable = html.Table([
                html.Thead(html.Tr([html.Th(H) for H in ["Segment", "Train", "Zone", "Pred. Load", "Capacity", "Utilisation", "Risk"]])),
                html.Tbody([html.Tr([
                    html.Td(str(Row["SegmentKey"]).replace("_", " ").replace("-", " → "), style={"fontSize": "11px"}),
                    html.Td(Row["TrainNumber"], style={"color": self._C["Dim"]}),
                    html.Td(Row["Zone"], style={"color": self._C["Dim"]}),
                    html.Td(f"{Row['PredictedEffectiveLoad']:.0f}"),
                    html.Td(f"{Row['Capacity']:.0f}", style={"color": self._C["Dim"]}),
                    html.Td(html.Div([html.Div(html.Div(style={"width": f"{min(Row['Util'], 100):.1f}%", "height": "100%", "borderRadius": "2px", "background": self._C["Accent3"] if Row["Util"] > 95 else self._C["Warn"] if Row["Util"] > 80 else self._C["Accent"]}), style={"flex": "1", "height": "4px", "background": self._C["Border"], "borderRadius": "2px", "overflow": "hidden"}), html.Span(f"{Row['Util']:.1f}%", style={"color": self._C["Accent3"] if Row["Util"] > 95 else self._C["Warn"] if Row["Util"] > 80 else self._C["Accent"], "fontSize": "11px", "minWidth": "38px"})], style={"display": "flex", "alignItems": "center", "gap": "8px"})),
                    html.Td(html.Span("Critical" if Row["Util"] > 95 else "High" if Row["Util"] > 85 else "Medium", className="pill " + ("pill-red" if Row["Util"] > 95 else "pill-yellow"))),
                ]) for _, Row in Risk.iterrows()])
            ], className="risk-table")
        return UtilFigure, DelayFigure, CongFigure, DistFigure, RelFigure, RiskTable

    # -------- Forecast Rendering -------- #
    def _RunForecast(self, _, TrainNumber, Year, Week):
        if not TrainNumber or not Year or not Week: return [], "Select a train, year and week first."
        try: return self._Analytics.Forecast(str(TrainNumber), int(Year), int(Week)).to_dict("records"), f"Forecast Completed — {TrainNumber} | {Year} W{Week}"
        except Exception as E: return [], f"Error: {E}"

    def _RenderForecast(self, Records):
        if not Records: return html.Div("Run a forecast to see the route strip.", className="no-data"), GO.Figure(layout = self._T)
        Frame = pandas.DataFrame(Records)
        TotalDist = Frame["Distance"].sum()
        RiskBG = {"Critical": self._C["Accent3"], "High": self._C["Warn"], "Medium": self._C["Accent"], "Low": self._C["Muted"]}
        Labels = Frame["Source"] + "→" + Frame["Destination"]
        Figure = GO.Figure(layout = self._T)
        Figure.add_trace(GO.Bar(name="Pred. Load", x = Labels, y = Frame["PredictedEffectiveLoad"], marker = dict(color=[RiskBG.get(R, self._C["Muted"]) for R in Frame["RiskLevel"]], line = dict(width = 0))))
        Figure.add_trace(GO.Scatter(name="Capacity", x = Labels, y = Frame["Capacity"], mode="lines+markers", line = dict(color = self._C["Accent2"], dash="dash", width = 1), marker = dict(size = 4)))
        if "PredictedDelay" in Frame.columns: Figure.add_trace(GO.Scatter(name="Pred. Delay (min)", x = Labels, y = Frame["PredictedDelay"], mode="lines+markers", line = dict(color = self._C["Accent3"], width = 1), marker = dict(size = 4), yaxis="y2"))
        Figure.update_layout(yaxis2 = dict(overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", title="Delay (min)", color = self._C["Dim"]), barmode="group", xaxis = dict(**self._T["xaxis"], tickangle=-30))
        return html.Div([
            html.Div([html.Div([html.Div(f"{Row['UtilisationPercent']:.0f}%", style={"fontSize": "9px", "fontWeight": "600", "color": self._C["BG"] if Row["RiskLevel"] != "Low" else self._C["Dim"]}), html.Div(Row["RiskLevel"][:3].upper(), style={"fontSize": "8px", "color": (self._C["BG"] + "aa") if Row["RiskLevel"] != "Low" else self._C["Dim"]})], className="route-segment", style={"width": f"{max(Row['Distance'] / TotalDist * 100, 3):.1f}%", "background": RiskBG.get(Row["RiskLevel"], self._C["Muted"])}) for _, Row in Frame.iterrows()], className="route-strip"),
            html.Div([html.Div(f"{Row['Source']}→{Row['Destination']}", className="route-segment-label", style={"width": f"{max(Row['Distance'] / TotalDist * 100, 3):.1f}%"}) for _, Row in Frame.iterrows()], className="route-labels"),
        ]), Figure

    # -------- Run -------- #
    def Run(self, Host="127.0.0.1", Port = 8050, Debug = False): self._App.run(host = Host, port = Port, debug = Debug)


# -------- ML Orchestrator -------- #
class ML:
    def __init__(self):
        load_dotenv()
        self._Log = Logger.Proxy("ML")
        self._Client = MongoClient(os.getenv("MongoURI"))
        self._Log.Event("ML Started")
        Static = {K: {str(D[C["PK"]]): D for D in self._Client["Stratum"][K].find({}, {"_id": 0})} for K, C in Configuration["Files"].items() if "PK" in C}
        _NNDir = Path(Configuration["Files"]["NN"]["Directory"])
        _NNDir.mkdir(parents = True, exist_ok = True)
        if Versions := sorted(_NNDir.glob("V*.pt")):
            Table = pyarrow.parquet.read_table(Path(Configuration["Files"]["Parquets"]["Directory"]) / f"{Versions[-1].stem}.parquet")
        else:
            Start = time.time()
            with Logger.Loader(1, "MongoDB aggregation") as Progress:
                Table = pyarrow.Table.from_pylist(list(self._Client["Stratum"]["History"].aggregate([
                    {"$match": {"Year": {"$gte": 2006}}},
                    {"$lookup": {"from": "Trains", "localField": "TrainNumber", "foreignField": "TrainNumber", "pipeline": [{"$project": {"_id": 0, "Segments": "$Route.Segments", "Name": 1}}], "as": "Static"}},
                    {"$set": {"TrainName": {"$first": "$Static.Name"}, "Static": {"$first": "$Static.Segments"}}},
                    {"$unwind": {"path": "$Weeks", "includeArrayIndex": "WeekIdx"}},
                    {"$unwind": {"path": "$Weeks.Segments", "includeArrayIndex": "SegIdx"}},
                    {"$set": {"Geometry": {"$arrayElemAt": ["$Static", "$SegIdx"]}}},
                    {"$project": {"_id": 0, "TrainNumber": 1, "Year": 1, "Category": 1, "Type": 1, "Zone": 1, "Priority": 1, "Week": "$Weeks.Week", "Capacity": "$Weeks.Capacity", "Reliability": "$Weeks.Reliability", "EffectiveLoad": "$Weeks.Segments.EffectiveLoad", "Delay": "$Weeks.Segments.Delay", "Source": "$Geometry.Source", "Destination": "$Geometry.Destination", "Distance": "$Geometry.Distance", "Gradient": "$Geometry.Gradient", "Name": "$TrainName", "SegmentKey": {"$concat": ["$Geometry.Source", "-", "$Geometry.Destination"]}, "TimeIndex": {"$add": [{"$multiply": [{"$subtract": ["$Year", 2006]}, 52]}, "$Weeks.Week"]}}}
                ], allowDiskUse = True)))
                Progress.Advance()
            self._Log.Event("Fetched [%s] rows | [%s] MB | [%ss]", Table.num_rows, Table.nbytes / 1024**2, time.time() - Start)
        self._Analytics = Analytics(self._Log, Table.sort_by([("SegmentKey", "ascending"), ("TimeIndex", "ascending")]), Static)

    # -------- Run -------- #
    def Run(self):
        self._Analytics.Load(None) if list(self._Analytics._NNDir.glob("V*.pt")) else self._Analytics.Train()
        Dashboard(self._Analytics.Serve(self._Analytics._Frame.groupby("SegmentKey").tail(104)).reset_index(drop = True), Analytics = self._Analytics, Metrics = self._Analytics._Metrics, Importance = self._Analytics._Importance, Years = sorted(self._Analytics._Frame["Year"].unique().tolist())).Run()

ML().Run()