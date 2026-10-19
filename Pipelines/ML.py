import io, logging, numpy, torch, scipy, orjson, uvicorn, jinja2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from Utilities import Configuration, Logger, Timer, Loader, Database, Transforms, Summary

# -------- TCNN -------- #
class TCNN(torch.nn.Sequential):
    __slots__ = ("_Log", "_T", "_D", "_TF", "_O", "_C", "_R")
    def __init__(self, Device, _TF, I, O):
        F, L = I // (AN := Configuration["Analytics"])["Lookback"], AN["Lookback"]
        torch.manual_seed(Configuration["Simulation"]["Seed"])
        super().__init__(
            torch.nn.Conv1d(F, 16, kernel_size=3, padding=1), torch.nn.SiLU(),
            torch.nn.Conv1d(16, 16, kernel_size=3, padding=1, dilation=1), torch.nn.SiLU(),
            torch.nn.Flatten(), torch.nn.Linear(16 * L, O))
        self._Log, self._T, self._R, self._D, self._TF, self._C = Logger("TCNN", "ML"), Timer(), (F, L), Device, _TF, Configuration["Analytics"]["TCN"]; self.to(Device)
        self._O = torch.optim.AdamW(self.parameters(), lr=self._C["lr"], weight_decay=self._C["weight_decay"]) # type: ignore[reportPrivateImportUsage]

    def forward(self, X): return super().forward(X.view(-1, self._R[1], self._R[0]).transpose(1, 2)) # type: ignore[reportIncompatibleMethodOverride]

    # -------- Fit -------- #
    def Fit(self, A, B):
        BH, E, AN = self._C["Batch"], self._C["Epochs"], Configuration["Analytics"]
        NC, NB, PT, MD, Best, Wait, BS = -(-(A.shape[0] - AN["Lookback"] - AN["Horizon"]) // AN["Chunk"]), -(-(AN["Chunk"] * A.shape[1]) // BH), self._C["Patience"], self._C["MinDelta"], float("inf"), 0, None
        S = torch.optim.lr_scheduler.CosineAnnealingLR(self._O, T_max=E * NC * NB, eta_min=self._C["lr"] / 100); self.train()
        with Loader(E * NC * NB, "Training TCNN") as LD:
            for EP in range(E):
                EL, ST = 0.0, 0
                for XC, YC in self._TF.Window(A, B):
                    for I in range(0, XC.shape[0], BH): self._O.zero_grad(set_to_none=True); ST += 1; EL += (Loss := torch.nn.functional.smooth_l1_loss(self(XC[I:I+BH].to(self._D, dtype = torch.float32, non_blocking=True)), YC[I:I+BH].to(self._D, dtype = torch.float32, non_blocking=True), beta=self._C["beta"])).item(); Loss.backward(); torch.nn.utils.clip_grad_norm_(self.parameters(), self._C["Clip"]); self._O.step(); S.step(); LD.Advance(L=EL / ST, E=f"{EP+1}/{E}")
                    del XC, YC
                EL /= max(ST, 1); Best, Wait, BS = (EL, 0, {K: V.clone() for K, V in self.state_dict().items()}) if Best - EL > MD else (Best, Wait + 1, BS)
                self._Log.Step("E: [%d] | L: [%s] | LR: [%s] | G: [%s] | W: [%d/%d] | T: [%s]", EP + 1, EL, self._O.param_groups[0]["lr"], max((P.grad.abs().max().item() if P.grad is not None else 0.0) for P in self.parameters()), Wait, PT, self._T.Elapsed())
                if Wait >= PT: break
        if BS: self.load_state_dict(BS)

    # -------- Predict -------- #
    @torch.no_grad()
    def Predict(self, A, B, Session):
        self.eval(); BH, AN = (C := Configuration["Analytics"])["SessionChunk"], C
        NI, IS, NT = Session.get_inputs()[0].name, tuple(Session.get_inputs()[0].shape[1:]), A.shape[1]
        N, L = (A.shape[0] - AN["Lookback"] - AN["Horizon"]) * NT, len(AN["Targets"])
        SE, AE, DA, TX, MX, NDA, NTX, TP  = torch.zeros(L), torch.zeros(L), torch.zeros(L), torch.zeros(L), torch.zeros(L), 0, 0, torch.zeros(NT, L)
        with Loader(-(-(A.shape[0] - AN["Lookback"] - AN["Horizon"]) // AN["Chunk"]) * -(-(AN["Chunk"] * NT) // BH), "Evaluating TCNN") as LD:
            for XC, YC in self._TF.Window(A, B):
                XC, CN = XC.numpy().astype(numpy.float32), XC.shape[0]
                if (R := CN % BH): XC = numpy.pad(XC, ((0, BH - R), (0, 0)), mode="edge")
                PC = numpy.empty((XC.shape[0], self[-1].out_features), dtype = numpy.float32)
                for I in range(0, XC.shape[0], BH): BC = Session.run(None, {NI: XC[I:I+BH].reshape(-1, *IS)})[0]; PC[I:I+BC.shape[0]] = BC; LD.Advance()
                PC, D = torch.from_numpy(PC[:CN]), torch.from_numpy(PC[:CN]) - YC
                AEB = D.abs_().reshape(-1, L); SE += D.pow(2).reshape(-1, L).sum(dim=0); AE += AEB.sum(dim=0); MX = torch.max(MX, AEB.amax(dim=0))
                PT, YT = PC.reshape(NT, -1, L), YC.reshape(NT, -1, L)
                DA += ((PT[:, 1:] - PT[:, :-1]).sign_() == (YT[:, 1:] - YT[:, :-1]).sign_()).float().sum(dim=(0, 1))
                TX += ((PT > 1.0) == (YT > 1.0)).float().sum(dim=(0, 1)); NDA += NT * (PT.shape[1] - 1); NTX += NT * PT.shape[1]
                TP += PC.reshape(NT, -1, L).mean(dim=1)
                del XC, YC, PC, D, AEB, PT, YT
        return SE / N, AE / N, MX, DA / NDA, TX / NTX, TP / -(-(A.shape[0] - AN["Lookback"] - AN["Horizon"]) // AN["Chunk"])

# -------- Simulation Engine -------- #
class SimulationEngine:
    __slots__ = ("_Log", "_RNG", "_T", "_TF", "_Snapshot", "_NWeeks", "_ANWeeks")

    @property
    def Snapshot(self): return self._Snapshot

    def __init__(self, Encodings, Graph, Engines, Events, Rakes, Schedules, Segments, Stations, Trains, Wagons):
        self._Log = Logger("Simulation", "ML")
        self._Snapshot = {"Encodings": Encodings, "Instances": {"Engines": Engines, "Events": Events, "Rakes": Rakes, "Schedules": Schedules, "Segments": Segments, "Stations": Stations, "Trains": Trains, "Wagons": Wagons, "Graph": Graph}, "Tensors": {}}
        self._RNG, self._T, self._TF = numpy.random.default_rng(Configuration["Simulation"]["Seed"]), Timer(), Transforms(self._Snapshot["Encodings"])
        self._NWeeks, self._ANWeeks = (NW := ((W := Configuration["Simulation"]["SimulationWindow"])[1] - W[0] + 1) * 52), (numpy.arange(NW) % 52) + 1
        self._BuildInstances()
        self._BuildTensors()

    # -------- Build Instances -------- #
    def _BuildInstances(self):
        NPT, NST, NEV, MKC, SRV, EMP, ENGC = ((INS := self.Snapshot["Instances"])["Trains"]["Frequency"].sum(), INS["Stations"]["Code"].size, INS["Events"]["Name"].size) + self._TF.Quantize((C := Configuration["Simulation"])["Market"], C["Services"], C["EngineMappings"], C["Engines"])
        FTT = self._RNG.choice(numpy.flatnonzero(numpy.isin((TS := (ENC := self._Snapshot["Encodings"])["Configuration"]["TrainServices"]["Forward"]), (FRS := numpy.flatnonzero(numpy.char.startswith(ENC["Configuration"]["ServiceNames"]["Reverse"], "Freight"))))), size = (NFTB := int(NST * 0.75)), p=(D := (MKCT := MKC["Traffic"]["Trains"])[numpy.isin(TS, FRS).nonzero()[0]][:, 1]) / numpy.maximum(D.sum(), 1e-8)); FFREQ = numpy.minimum(7, numpy.maximum(1, numpy.round(2.8 * self._RNG.uniform((MI := MKCT[FTT])[:, 0], MI[:, 1])))).astype(numpy.intp)
        NE, NW = int(((NPT + (NFT := int(FFREQ.sum()))) / ((MKE := MKC["Haulage"]["Engines"])[..., 2] @ MKE[..., 3])) / numpy.maximum(1.0 - MKE[..., 0] @ MKE[..., 3] - 0.08, 0.1) / 1.057), int(((IT := INS["Trains"])["WagonComposition"].sum() + NFTB * 45) * 1.146)
        EY, WY, EV = ((SW := C["SimulationWindow"])[1] - (self._RNG.beta(4, 5, size = NE) * 35).astype(int)).clip(SW[1] - 35, SW[1]), (SW[1] - (self._RNG.beta(3, 3, size = NW) * 35).astype(int)).clip(SW[1] - 35, SW[1]), (numpy.where((W := INS["Events"]["Window"])[:, 0:1] > W[:, 1:], (self._ANWeeks >= W[:, 0:1]) | (self._ANWeeks <= W[:, 1:]), (self._ANWeeks >= W[:, 0:1]) & (self._ANWeeks <= W[:, 1:])) & (self._RNG.random((NEV, self._NWeeks)) <= self._RNG.uniform((P := INS["Events"]["Probability"])[:, 0:1], P[:, 1:]))).nonzero()
        TRFW, TRFT, TRFS = (MKW := MKC["Haulage"]["Wagons"])[self._RNG.integers(0, MKW.shape[0], size = NW)], (MKCT := MKC["Traffic"]["Trains"])[INS["Trains"]["Type"]], MKC["Traffic"]["Stations"][INS["Stations"]["Category"]]

        (EC := self._RNG.choice(BEC := INS["Engines"]["Class"].shape[0], size = NE, p=MKE[..., 3])).sort(); WC = self._RNG.integers(0, (IW := INS["Wagons"])["Class"].shape[0], size = NW); EY = EY.clip(SW[1] - INS["Engines"]["CL"][EC] // 52, SW[1]); WY = WY.clip(SW[1] - IW["CL"][WC] // 52, SW[1])
        self._TF.Encode(("Engines", "RoadNumber", (ENGC[EC] + (numpy.arange(NE) - numpy.pad(numpy.cumsum(numpy.bincount(EC, minlength=BEC)), (1, 0))[EC])).astype(str)), ("Wagons", "WagonNumber", ((B := (WC + 10) * 10**9 + (WC * 0 + INS["Stations"]["Zone"][DPT := self._RNG.integers(0, NST, size = NW)] + 1) * 10**7 + (WY % 100) * 10**5 + (numpy.arange(NW) % 1000) * 10) + (10 - ((sum((B // (10 ** I) % 10) * W_WT for I, W_WT in enumerate([1, 3, 1, 3, 1, 3, 1, 3, 1, 3]))) % 10)) % 10).astype(str)))

        INS["Engines"] = self._TF.Quantize({**(E := {K: V[EC] for K, V in INS["Engines"].items()}), "Class": EC, "RoadNumber": ENC["Engines"]["RoadNumber"]["Forward"], "Shed": (SHD := numpy.flatnonzero(((CAT := INS["Stations"]["Category"]) >= 3) & (CAT <= 4)))[self._RNG.integers(0, numpy.maximum(SHD.size, 1), size = NE)], "CommissioningYear": EY, "Kilometrage": (SW[1] - EY) * E["REKM"] * self._RNG.uniform(0.85, 1.15, size = NE), "PLC": (LR := (SW[1] - EY) * 52 / E["CL"]), "FOR": self._RNG.poisson((SW[1] - EY) * E["FOR"]), "HaulageTariff": E["Haulage"], "State": numpy.where(LR > 0.75, 2, 0)})

        INS["Wagons"] = self._TF.Quantize({**(W := {K: V[WC] for K, V in IW.items()}), "WagonNumber": ENC["Wagons"]["WagonNumber"]["Forward"], "Depot": DPT, "CommissioningYear": WY, "Kilometrage": (SW[1] - WY) * W["REKM"] * self._RNG.uniform(0.85, 1.15, size = NW), "PLC": (WLR := (SW[1] - WY) * 52 / W["CL"]), "FOR": self._RNG.poisson((SW[1] - WY) * W["FOR"]), "HaulageTariff": TRFW, "State": numpy.where(WLR > 0.88, 2, 0)})

        INS["Stations"] |= self._TF.Quantize({"Traffic": ((TR := self._RNG.uniform(TRFS[:, 0, None], TRFS[:, 1, None], size = (NST, self._NWeeks))) * 0.3 + numpy.concatenate([TR[:, :1], TR[:, :-1]], axis = 1) * 0.7, (NST, self._NWeeks))})

        INS["Events"] = self._TF.Quantize({**(E := {K: V[EV[0]] for K, V in INS["Events"].items()}), "Window": (EV[1] + 1)[:, None], "Probability": self._RNG.uniform(E["Probability"][:, 0], E["Probability"][:, 1]), "Scale": self._RNG.uniform(E["Scale"][:, 0], E["Scale"][:, 1])})

        (PE := numpy.empty(NE, dtype=numpy.intp))[ENC["Engines"]["RoadNumber"]["Forward"]] = numpy.arange(NE)
        ENC["Engines"]["RoadNumber"]["Position"] = PE

        (PW := numpy.empty(NW, dtype=numpy.intp))[ENC["Wagons"]["WagonNumber"]["Forward"]] = numpy.arange(NW)
        ENC["Wagons"]["WagonNumber"]["Position"] = PW

        FWP = numpy.bincount(WC, weights=INS["Wagons"]["HaulageTariff"][:, 3], minlength=50) / numpy.maximum(numpy.bincount(WC, minlength=50), 1.0); FWP /= FWP.sum()
        FRK, FNC = self._RNG.choice([22, 42, 45, 58], size = NFTB, p = [0.10, 0.25, 0.20, 0.45]), numpy.arange(4) < self._RNG.integers(2, 5, size = (NFTB, 1))

        FWCS, FWCMASK, FPC = numpy.argsort(self._RNG.gumbel(size = (NFTB, 50)) + numpy.log(FWP), axis = 1)[:, :4], FNC.ravel(), numpy.maximum(1, FRK[:, None] // FNC.sum(axis = 1, keepdims = True)) * FNC
        (FSTA := numpy.zeros((NFTB, 8), dtype = numpy.intp))[:, 0] = self._RNG.integers(0, NST, size = NFTB)

        ENC["Trains"]["Name"] = self._TF.Quantize({"Forward": IT["Name"] + 1, "Reverse": numpy.concatenate([[""], ENC["Trains"]["Name"]["Reverse"]])})
        ENC["Trains"]["Type"] = self._TF.Quantize({"Forward": numpy.concatenate([numpy.searchsorted((TTN := ENC["Configuration"]["TrainTypes"]["Reverse"]), ENC["Trains"]["Type"]["Reverse"])[IT["Type"]], FTT]), "Reverse": TTN})
        self._TF.Encode(("Trains", "TrainNo", numpy.concatenate([ENC["Trains"]["TrainNo"]["Reverse"], numpy.arange(70001, 70001 + NFTB).astype(str)])))
        INS["Trains"] |= self._TF.Quantize({"TrainNo": ENC["Trains"]["TrainNo"]["Forward"], "Name": numpy.concatenate([ENC["Trains"]["Name"]["Forward"], numpy.zeros(NFTB, dtype = ENC["Trains"]["Name"]["Forward"].dtype)]), "Type": ENC["Trains"]["Type"]["Forward"], "Service": numpy.concatenate([IT["Service"], (FSVC := TS[FTT])]), "Priority": numpy.concatenate([IT["Priority"], SRV["Priorites"][FSVC]]),
            "Demand": numpy.concatenate([IT["Demand"], ((FWC := scipy.sparse.csc_array((FPC.ravel()[FWCMASK], (numpy.repeat(numpy.arange(NFTB), 4)[FWCMASK], FWCS.ravel()[FWCMASK])), shape=(NFTB, 50))) @ (TW := IW["TareWeight"]))[:, None] + (FWC @ (IW["Axles"] * IW["MaxAxleLoad"] - TW))[:, None] * MKC["Traffic"]["Trains"][FTT][:, :2]]), "Frequency": numpy.concatenate([IT["Frequency"], FFREQ]), "WagonComposition": scipy.sparse.vstack([IT["WagonComposition"], FWC])})

        for I in range(1, 8): FSTA[:, I] = numpy.where(self._RNG.random(NFTB) < 0.8, (G := INS["Graph"]["Adjacency"]).indices[G.indptr[FSTA[:, I-1]] + self._RNG.integers(0, G.indptr[FSTA[:, I-1] + 1] - G.indptr[FSTA[:, I-1]])], self._RNG.integers(0, NST, size = NFTB))
        INS["Schedules"] = self._TF.Quantize({"Station": numpy.concatenate([(IS := INS["Schedules"])["Station"], FSTA[(FM := numpy.arange(8) < (FS := self._RNG.integers(4, 9, size = NFTB))[:, None])]]), "Arrival": numpy.concatenate([IS["Arrival"], ((ST := self._RNG.uniform(0.0, 10080.0, size = NFTB))[:, None] + (MTT := INS["Segments"]["TravelTime"].mean() * 10.0) * numpy.arange(8) / 7.0)[FM]]), "Departure": numpy.concatenate([IS["Departure"], (ST[:, None] + MTT * numpy.arange(8) / 7.0 + self._RNG.uniform(0.5, 2.0, (NFTB, 8)))[FM]]), "Day": numpy.concatenate([IS["Day"], numpy.zeros(FM.sum())]), "Offsets": numpy.concatenate([IS["Offsets"], IS["Offsets"][-1] + numpy.cumsum(FS)])})

        INS["Trains"] = self._TF.Quantize({**({K: V[(TI := numpy.repeat(numpy.arange((TT := INS["Trains"]["Type"]).size), INS["Trains"]["Frequency"]))] for K, V in INS["Trains"].items()}), "Delay": (DEL := numpy.where((RM := self._RNG.random(TI.size)) < 0.80, 0.0, numpy.where(RM < 0.92, self._RNG.uniform(1.0, 30.0, size = TI.size), self._RNG.exponential(size = TI.size) * (5.0 + 115.0 * (1.0 - SRV["Priorites"][TS[TT[TI]]] / numpy.maximum(SRV["Priorites"].max(), 1.0)))))), "Arrival": INS["Schedules"]["Arrival"][INS["Schedules"]["Offsets"][1:] - 1][TI] + DEL, "Departure": INS["Schedules"]["Departure"][INS["Schedules"]["Offsets"][:-1]][TI] + DEL, "Traffic": (TRFT := MKC["Traffic"]["Trains"][TT[TI]])[:, 0] + self._RNG.random(TI.size) * (TRFT[:, 1] - TRFT[:, 0]),
            "Engines": (TEN := (AE := numpy.nonzero(INS["Engines"]["State"] < 2)[0])[(AECO := numpy.pad(numpy.cumsum(numpy.bincount(EC[AE], minlength=BEC)), (1, 0)))[ECL := numpy.searchsorted(ENC["Engines"]["Class"]["Reverse"], (NP := ENC["Configuration"]["NominatedPower"])["Reverse"][NP["Forward"][TT[TI]]])][:, None] + self._RNG.integers(0, numpy.maximum(1, AECO[ECL + 1] - AECO[ECL])[:, None], size = (TI.size, 2))] * (EMP["TractionCount"][TT[TI]][:, None] > numpy.arange(2))), "Wagons": (TWA := (AW := numpy.nonzero(INS["Wagons"]["State"] < 2)[0])[(AWCO := numpy.pad(numpy.cumsum(numpy.bincount(WC[AW], minlength=IW["Class"].shape[0] + 1)), (1, 0)))[WC_CLS := numpy.repeat((WCP := INS["Trains"]["WagonComposition"][numpy.unique(TI)]).indices, WCP.data)] + self._RNG.integers(0, numpy.maximum(1, AWCO[WC_CLS + 1] - AWCO[WC_CLS]))])})

        EB = numpy.bincount(TEN[:, 0][M := TEN[:, 0] > 0], weights=(INS["Schedules"]["Arrival"][INS["Schedules"]["Offsets"][1:] - 1] - INS["Schedules"]["Departure"][INS["Schedules"]["Offsets"][:-1]])[TI][M], minlength=NE)
        if (OT := numpy.flatnonzero(numpy.isin(TEN[:, 0], numpy.flatnonzero(EB > (WPM := 7 * 24 * 60) * 0.80)))).size and (UDA := numpy.flatnonzero(UDM := (EB < WPM * 0.40) & (INS["Engines"]["State"] < 2))).size:
            UDCO = numpy.pad(numpy.cumsum(numpy.bincount(EC[UDM], minlength=BEC)), (1, 0)); AVI = numpy.flatnonzero(INS["Engines"]["State"] < 2); CP = numpy.array([INS["Engines"]["Power"][M].mean() if (M := AVI[EC[AVI] == C]).size else 0 for C in range(BEC)])
            for Slot, SI in ((0, OT), (1, OT[EMP["TractionCount"][TT[TI[OT]]] > 1])):
                OC = EC[TEN[SI, Slot]]; OP = UDCO[OC]; OS = UDCO[OC + 1] - OP; HU = OS > 0; TEN[SI[HU], Slot] = UDA[OP[HU] + self._RNG.integers(0, OS[HU], size = HU.sum())]
                if (FB := SI[~HU]).size: D = INS["Engines"]["Power"][AVI] - CP[EC[TEN[FB, Slot]]][:, None]; D[D < 0] *= -1.1; TEN[FB, Slot] = AVI[numpy.argmin(D, axis = 1)]

        INS["Trains"]["Engines"], INS["Trains"]["Wagons"] = self._TF.Quantize(TEN), self._TF.Quantize(INS["Wagons"]["WagonNumber"][TWA])
        ME, MW = numpy.unique(TEN[TEN > 0]), numpy.unique(TWA); INS["Engines"]["State"][ME[INS["Engines"]["State"][ME] == 0]] = 1; INS["Wagons"]["State"][MW[INS["Wagons"]["State"][MW] == 0]] = 1

        (PT := numpy.empty(INS["Trains"]["Type"].size, dtype=numpy.intp))[INS["Trains"]["TrainNo"]] = numpy.arange(INS["Trains"]["Type"].size)
        ENC["Trains"]["TrainNo"]["Position"] = PT

        self._Log.Metrics("Instances: Engine: %s | Wagon: %s | Train: [P: %s | F: %s] | Station: %s | Schedules: %s | Event: %s | Time: [%s]", NE, NW, NPT, NFT, NST, INS["Schedules"]["Offsets"].size - 1, EV[0].size, self._T.Split())

    # -------- Build Tensors -------- #
    def _BuildTensors(self ):
        ENV, SZN, EVT, MKP, MNC = self._TF.Quantize((C := Configuration["Simulation"])["Environment"], C["Seasonality"], (INS := self._Snapshot["Instances"])["Events"], C["Market"], C["Maintenance"]["Segments"])
        FRQ, PR = numpy.sqrt((FRQ0 := (IT := INS["Trains"])["Frequency"][:(NTrains := IT["Type"].shape[0])]) / FRQ0.max()), IT["Priority"][:NTrains]
        WL, GTW0 = (WC := IT["WagonComposition"][:NTrains]) @ (IW := INS["Wagons"])["Length"][(WI := numpy.unique(IW["Class"], return_index=True)[1])], ((INS["Engines"]["TareWeight"][EI := IT["Engines"][:NTrains]] * (EI > 0)).sum(axis = 1)) + (WC @ IW["TareWeight"][WI]); GTW = GTW0 / GTW0.mean()
        BC = scipy.sparse.csr_array((numpy.ones((SIPT := (SI := INS["Segments"])["PT"]).size), (SIPT, numpy.arange(SIPT.size))), shape=(NTrains, SIPT.size))
        ENGW = numpy.where((M := EI > 0), INS["Engines"]["PLC"][EI], 0.0).sum(axis = 1) / numpy.maximum(M.sum(axis = 1), 1.0)
        TZ = (BC @ INS["Stations"]["Zone"][(STN := (INS["Schedules"])["Station"][SIPT])] / numpy.maximum((BCS := BC.sum(axis = 1)).ravel(), 1.0))[:NTrains].clip(0, INS["Stations"]["Zone"].max()).astype(numpy.intp)

        # -------- Simulation Tensors: Weather -------- #
        Weather = numpy.empty((NW := self._NWeeks, ENV.shape[0], 4), dtype = ENV.dtype)
        Weather[..., 0] = numpy.log1p(self._RNG.uniform(ENV[:, 0, 0], ENV[:, 0, 1], (NW, ENV.shape[0])) * (SN := numpy.sin(2.0 * numpy.pi * (AW := (self._ANWeeks % 52))[:, None] / 52.0)).clip(0.0) ** 2)
        Weather[..., 1] = numpy.clip(self._RNG.uniform(ENV[:, 1, 0], ENV[:, 1, 1], (NW, ENV.shape[0])) + SN * self._RNG.uniform(0.0, ENV[:, 1, 1] - ENV[:, 1, 0], (NW, ENV.shape[0])), ENV[:, 1, 0], ENV[:, 1, 1])
        Weather[..., 2] = self._RNG.uniform(ENV[:, 2, 0], ENV[:, 2, 1], (NW, ENV.shape[0]))
        Weather[..., 3] = self._RNG.uniform(ENV[:, 3, 0], ENV[:, 3, 1], (NW, ENV.shape[0]))
        Weather /= numpy.maximum(Weather.max(axis = 0, keepdims = True), 1e-8)

        # -------- Simulation Tensors: Seasonality -------- #
        Seasonality = numpy.empty((NW, SZN.shape[0]), dtype = SZN.dtype)
        Seasonality[:] = SZN[:, 0] + SZN[:, 1] * numpy.cos((T := (2.0 * numpy.pi * AW[:, None] / 52.0)) + SZN[:, 2]) + SZN[:, 3] * numpy.cos(2.0 * T + SZN[:, 4])
        Seasonality -= Seasonality.min(axis = 0, keepdims = True)
        Seasonality /= numpy.maximum(Seasonality.max(axis = 0, keepdims = True), 1e-8)

        # -------- Simulation Tensors: Events -------- #
        Events = numpy.empty((NW, (NEI := EVT["Window"].shape[0]), 3), dtype = EVT["Probability"].dtype)
        Events[..., 0] = numpy.where((self._ANWeeks[:, None] == EVT["Window"].reshape(1, -1)) & (self._RNG.uniform(0.0, 1.0, (NW, NEI)) < EVT["Probability"].reshape(1, -1)), EVT["Scale"].reshape(1, -1), 0.0)
        Events[..., 1] = EVT["Zones"].reshape(1, -1)
        Events[..., 2] = EVT["Services"].reshape(1, -1)

        # -------- Simulation Tensors: Escalation -------- #
        Escalation = numpy.empty((NW, MKP["Escalation"].shape[0], 2), dtype = MKP["Escalation"].dtype)
        Escalation[..., 0] = MKP["Escalation"][:, 0] * (ANW := (self._ANWeeks / 52.0)[:, None])
        Escalation[..., 1] = self._RNG.normal(MKP["Escalation"][:, 0], MKP["Escalation"][:, 1], (NW, MKP["Escalation"].shape[0]))

        # -------- Simulation Tensors: Features -------- #
        TZ, EMSK = self._TF.Quantize(TZ, (((EVT["Zones"][:, None] & (numpy.uint32(1) << TZ[None, :])) != 0) & ((EVT["Services"][:, None] & (numpy.uint16(1) << IT["Service"][:NTrains][None, :])) != 0)))
        TRF = self._TF.Quantize((self._RNG.uniform(IT["Demand"][:NTrains, 0], IT["Demand"][:NTrains, 1], (NW, NTrains)) * (1.0 + (SZNS := Seasonality[:, IT["Service"][:NTrains]])) * (1.0 + scipy.sparse.csr_matrix(Events[:, :, 0], dtype = numpy.float32) @ EMSK.astype(numpy.float32))).clip(0.0))
        INS["Segments"] |= self._TF.Quantize({"SMGT": (SMGT := BC.T @ (GTW0 * TRF.mean(axis = 0) * FRQ0) * 1e-6), "SOH": (SOH := numpy.maximum(0.0, 1.0 - (CMGT := SMGT * self._NWeeks) / (MNCE := MNC[(SI := INS["Segments"])["Group"][SIPI := SI["PI"]]])))[SIPI], "Screening": CMGT / 350.0, "CTR": CMGT / MNCE, "USFD": SMGT * 52.0 / 40.0, "THP": (THP := SMGT / MNCE)})
        INS["Segments"]["BC"], INS["Segments"]["TF"] = self._TF.Quantize(BC, (BC @ numpy.column_stack([SI["Distance"][SIPI], SI["SpeedLimit"][SIPI], SI["Line"][SIPI], INS["Stations"]["LoopLines"][STN], SOH, WL[SIPT] > INS["Stations"]["EPL"][STN], THP])) / numpy.maximum(BCS[:, None], 1.0))
        ENGWD = numpy.minimum(ENGW * (1.0 + 0.3 * INS["Segments"]["TF"][:, 6]), 1.0)
        TRF, PR, ENGW, TZ = self._TF.Quantize(TRF / numpy.maximum(TRF.max(), 1e-8), PR / numpy.maximum(PR.max(), 1e-8), ENGW / numpy.maximum(ENGW.max(), 1e-8), TZ)
        Features = numpy.empty((NW, NTrains, 13), dtype = numpy.float32)
        Features[..., 0]  = Weather[:, TZ, 0]
        Features[..., 1]  = Weather[:, TZ, 1]
        Features[..., 2]  = Weather[:, TZ, 2]
        Features[..., 3]  = Weather[:, TZ, 3]
        Features[..., 4]  = (ESC0 := Escalation[:, 0, 0][:, None])
        Features[..., 5]  = (ESC1 := Escalation[:, 0, 1][:, None])
        Features[..., 6]  = SZNS
        Features[..., 7]  = ANW
        Features[..., 8]  = TRF
        Features[..., 9]  = FRQ
        Features[..., 10] = GTW
        Features[..., 11] = ENGWD
        Features[..., 12] = PR

        # -------- Simulation Tensors: Targets -------- #
        Targets = numpy.empty((NW, NTrains, 4), dtype = numpy.float32)
        Targets[..., 0] = ENGWD * (1.0 + 0.3 * Weather[:, TZ, 1] + 0.2 * Weather[:, TZ, 2])
        Targets[..., 1] = GTW * TRF * (1.0 + 0.4 * FRQ + 0.3 * Weather[:, TZ, 0])
        Targets[..., 2] = (1.0 - PR) * (1.0 + 0.3 * ENGWD + 0.1 * Weather[:, TZ, 1] + 0.15 * Weather[:, TZ, 0] + 0.15 * Weather[:, TZ, 3] + 0.1 * INS["Segments"]["TF"][:, 6])
        Targets[..., 3] = (GTW * TRF * FRQ) * (1.0 + ESC0) * (1.0 + 0.3 * SZNS) * (1.0 - 0.2 * ESC1)
        numpy.minimum(Targets, Targets.mean(axis = (0, 1), keepdims = True) + 3.0 * Targets.std(axis = (0, 1), keepdims = True), out = Targets)

        # -------- Feature & Target Standardization -------- #
        TM, TS = Targets.mean(axis = (0, 1), keepdims = True), numpy.maximum(Targets.std(axis = (0, 1), keepdims = True), 1e-8)
        FM, FS = Features.mean(axis = (0, 1), keepdims = True), numpy.maximum(Features.std(axis = (0, 1), keepdims = True), 1e-8)
        Targets -= TM; Targets /= TS; Features -= FM; Features /= FS
        self._Snapshot["Tensors"] = {"Features": self._TF.Quantize(Features), "Targets": self._TF.Quantize(Targets), "Normalizations": {"Targets": (self._TF.Quantize(TM), self._TF.Quantize(TS)), "Features": (self._TF.Quantize(FM), self._TF.Quantize(FS))}}

        self._Log.Metrics("Tensors: Features: %s | Targets: %s | Tensor Time: [%s] | Total Time: [%s]", Features.shape, Targets.shape, self._T.Split(), self._T.Elapsed())

# -------- Analytics Engine -------- #
class AnalyticsEngine:
    __slots__ = ("_Log", "_T", "_TF", "_Snapshot", "_Framework", "_Device", "_Provider", "_TDevice", "_Models", "_Targets", "_Features", "_Evaluations", "_Weights", "_Predictions", "_Encodings")
    def __init__(self, Snapshot, Framework, Device, Provider, TorchDevice):
        self._Log, self._T, self._Snapshot, self._Framework, self._Models, self._Evaluations, self._Weights, self._Predictions = Logger("Analytics", "ML"), Timer(), Snapshot, Framework, {}, {}, {}, {}
        self._Device, self._Provider, self._TDevice, self._Targets, self._Features, self._Encodings  = Device, Provider, TorchDevice, (TNS := self._Snapshot["Tensors"])["Targets"], TNS["Features"], self._Snapshot["Encodings"]; self._TF = Transforms(Device = self._TDevice)
        logging.getLogger("torch").setLevel(logging.ERROR); logging.getLogger("torch.onnx").setLevel(logging.ERROR)

    # -------- Train -------- #
    def Train(self):
        self._Models["TCNN"] = TCNN(self._TDevice, self._TF, (C := Configuration["Analytics"])["Lookback"] * self._Features.shape[-1], C["Horizon"] * self._Targets.shape[-1])
        self._Log.Metrics("Training Started: Features: %s | Targets: %s", self._Features.shape, self._Targets.shape)

        self._Models["TCNN"].Fit(self._Features, self._Targets); self._Weights["TCNN"] = self._Models["TCNN"].state_dict()
        self._Log.Metrics("TCNN Trained: %s", self._T.Split())

        # -------- Hardware ONNX Compilation -------- #
        torch.onnx.export((M := self._Models["TCNN"]).cpu().eval(), torch.randn(C["SessionChunk"], M._R[0], M._R[1]), (BFR := io.BytesIO()), opset_version=17, dynamic_axes={})
        self._Weights["ONNX"] = BFR.getvalue(); M.to(self._TDevice)
        self._Log.Metrics("Inference Compiled: %s", self._T.Split())
        return {"Weights": self._Weights}

    # -------- Load -------- #
    def Load(self, CSnapshot):
        self._Models, self._Weights, self._Evaluations, self._Predictions = {"TCNN": TCNN(self._TDevice, self._TF, (C := Configuration["Analytics"])["Lookback"] * self._Features.shape[-1], C["Horizon"] * self._Targets.shape[-1])}, CSnapshot["Weights"], CSnapshot.get("Evaluations", {}), CSnapshot.get("Predictions", {})
        self._Models["ONNX"] = self._TF.Session(self._Weights["ONNX"], self._Framework, self._Device, self._Provider) # type: ignore[reportArgumentType]
        self._Log.Metrics("Session Established: %s", self._T.Split())

        # -------- Model Evaluation -------- #
        if not self._Evaluations:
            TSE, TAE, TMX, TDA, TTX, TP = self._Models["TCNN"].Predict(self._Features, self._Targets, self._Models["ONNX"])
            TM, TS = self._Snapshot["Tensors"]["Normalizations"]["Targets"]; TS2 = TS.squeeze(); self._Predictions = TP.numpy() * TS2 + TM.squeeze(); self._Snapshot["Predictions"] = self._TF.Quantize(self._Predictions)
            self._Evaluations = {"General": {"RMSE": (TSE.sqrt() * TS2).mean().item(), "MAE": (TAE * TS2).mean().item(), "MaxE": (TMX * TS2).mean().item(), "DA": TDA.mean().item(), "TEX": TTX.mean().item()}, "Targets": {N: {"RMSE": (TSE[I].sqrt() * TS2[I]).item(), "MAE": (TAE[I] * TS2[I]).item(), "MaxE": (TMX[I] * TS2[I]).item(), "DA": TDA[I].item(), "TEX": TTX[I].item()} for I, N in enumerate(Configuration["Analytics"]["Targets"])}}
        self._Log.Metrics("Loaded Model Metrics | RMSE: %s | MAE: %s | MaxE: %s | DA: %s | TEX: %s", (G := self._Evaluations["General"])["RMSE"], G["MAE"], G["MaxE"], G["DA"], G["TEX"])
        for N, M in self._Evaluations["Targets"].items(): self._Log.Metrics("%s | RMSE: %s | MAE: %s | MaxE: %s | DA: %s | TEX: %s", N, M["RMSE"], M["MAE"], M["MaxE"], M["DA"], M["TEX"])
        return {"Evaluations": self._Evaluations, "Predictions": self._Predictions, "Weights": self._Weights}

# -------- Adjudicator -------- #
class Adjudicator:
    __slots__ = ("_Log", "_T", "_TF", "_Snapshot", "_Evaluations", "_Predictions", "_Manifest",)
    def __init__(self, Snapshot, Evaluations, Predictions):
        self._Log, self._T, self._TF, self._Snapshot, self._Evaluations, self._Predictions, self._Manifest = Logger("Adjudicator", "ML"), Timer(), Transforms(), Snapshot, Evaluations, Predictions, {}
        self.Adjudicate()

    # -------- Adjudicatef -------- #
    def Adjudicate(self):
        self._Log.Metrics("Instances: Engines: %s | Wagons: %s | Trains: %s | Segments: %s | Stations: %s | Schedules: %s | Events: %s | Graph Nodes: %s", (E := (INS := self._Snapshot["Instances"])["Engines"])["Class"].size, (W := INS["Wagons"])["Class"].size, (TRN := INS["Trains"])["Type"].size, (SI := INS["Segments"])["Source"].size, (STN := INS["Stations"])["Code"].size, (SCH := INS["Schedules"])["Offsets"].size - 1, INS["Events"]["Name"].size, (ADJ := INS["Graph"]["Adjacency"]).shape[0])
        # -------- A1 [Scheduled Withdrawal] -------- #
        PLC, FOR, CLS = numpy.concatenate([E["PLC"], W["PLC"]]), numpy.concatenate([E["FOR"], W["FOR"]]), numpy.concatenate([E["Class"], W["Class"] + E["Class"].max() + 1])
        if (Q := numpy.flatnonzero((PLC >= 0.95) | ((PLC >= 0.75) & (FOR > numpy.where(numpy.arange(PLC.size) < E["PLC"].size, E["FOR"].mean(), W["FOR"].mean()))))).size:
            POOL = numpy.flatnonzero(~numpy.isin(numpy.arange(PLC.size), Q)); PSRT = POOL[numpy.lexsort((PLC[POOL], CLS[POOL]))]
            self._Manifest["A1"] = {"ID": numpy.char.add("A1-", numpy.char.add(numpy.where(IE := Q < E["PLC"].size, "L", "W"), numpy.char.zfill(numpy.where(IE, IE.cumsum(), (~IE).cumsum()).astype(str), 4))), "Affected": (IDS := numpy.concatenate([E["RoadNumber"], W["WagonNumber"]]))[Q], "Recommendations": self._TF.Quantize(numpy.column_stack([(PLC[Q] >= 0.95).view(numpy.uint8), IDS[PSRT[numpy.searchsorted(CLS[PSRT], CLS[Q])]].astype(numpy.float32)]))}
        self._Log.Metrics("A1: ScheduledWithdrawal: [E: %s | W: %s] | ImmediateWithdrawal: [E: %s | W: %s]", ((SW := PLC[Q] < 0.95) & (IE := Q < E["PLC"].size)).sum(), (SW & ~IE).sum(), (~SW & IE).sum(), (~SW & ~IE).sum())

        # -------- A2 [Loco Link] -------- #
        if (Q := numpy.flatnonzero(((AA := self._Predictions[:, 0]) > numpy.percentile(AA, 95)) & ((TEN := TRN["Engines"][:, 0]) > 0))).size:
            self._Manifest["A2"] = {"ID": numpy.char.add("A2-T", numpy.char.zfill(numpy.arange(1, Q.size + 1).astype(str), 4)), "Affected": TRN["TrainNo"][Q], "Recommendations": self._TF.Quantize(numpy.column_stack([numpy.broadcast_to(2, Q.size), E["RoadNumber"][(ESRT := (AE := numpy.flatnonzero(E["PLC"] < E["PLC"].mean()))[numpy.lexsort((E["PLC"][AE], E["Class"][AE]))])[numpy.searchsorted(E["Class"][ESRT], E["Class"][TEN[Q]])] ]]))}
        self._Log.Metrics("A2: LocoLink: %s", Q.size)

        # -------- N1 [Infrastructure Stress] -------- #
        LPCUM = numpy.maximum.accumulate(numpy.where(numpy.isin(SCH["Station"], numpy.flatnonzero(STN["LoopLines"] > 0)), numpy.arange(SCH["Station"].size), 0))
        Q = numpy.flatnonzero(((TTHP := SI["TF"][:, 6]) > numpy.percentile(TTHP, 95)) | ((NS := self._Predictions[:, 1]) > numpy.percentile(NS, 95))); Q = Q[numpy.unique(TRN["TrainNo"][Q], return_index=True)[1]]
        if Q.size: self._Manifest["N1"] = {"ID": numpy.char.add("N1-T", numpy.char.zfill(numpy.arange(1, Q.size + 1).astype(str), 4)), "Affected": TRN["TrainNo"][Q], "Recommendations": self._TF.Quantize(numpy.column_stack([numpy.broadcast_to(3, Q.size), numpy.maximum(30.0, SI["TF"][Q, 1] * (1.0 - TTHP[Q]))]))}
        self._Log.Metrics("N1: SpeedRestriction: %s", Q.size)

        # -------- N2 [Section Block] -------- #
        Q = numpy.flatnonzero((PTHP := SI["BC"] @ SI["THP"]) > numpy.percentile(PTHP, 95)); Q = Q[numpy.unique(TRN["TrainNo"][Q], return_index=True)[1]]
        if Q.size and (VM := (HOLD := SCH["Station"][LPCUM[SCH["Offsets"][1:][Q] - 1]]) > 0).any(): self._Manifest["N2"] = {"ID": numpy.char.add("N2-T", numpy.char.zfill(numpy.arange(1, VM.sum() + 1).astype(str), 4)), "Affected": TRN["TrainNo"][Q[VM]], "Recommendations": self._TF.Quantize(numpy.column_stack([numpy.broadcast_to(4, VM.sum()), HOLD[VM]]))}
        self._Log.Metrics("N2: SectionBlock: %s", len(self._Manifest.get("N2", {}).get("Affected", ())))

        # -------- N3 [Diversion] -------- #
        if (Q := numpy.flatnonzero(SI["USFD"] > numpy.percentile(SI["USFD"], 95))).size and (Q := Q[numpy.unique(numpy.column_stack([numpy.minimum(SI["Source"][SI["PI"][Q]], SI["Destination"][SI["PI"][Q]]), numpy.maximum(SI["Source"][SI["PI"][Q]], SI["Destination"][SI["PI"][Q]])]), axis=0, return_index=True)[1]]).size:
            self._Manifest["N3"] = {"ID": numpy.char.add("N3-S", numpy.char.zfill(numpy.arange(1, Q.size + 1).astype(str), 4)), "Affected": self._TF.Quantize(numpy.column_stack([SI["Source"][SI["PI"][Q]], SI["Destination"][SI["PI"][Q]]])), "Recommendations": self._TF.Quantize(numpy.column_stack([
                    numpy.broadcast_to(5, Q.size), numpy.fromiter((ADJ.indices[ADJ.indptr[S] + numpy.argmax(SI["SOH"][numpy.searchsorted(SI["SK"], numpy.minimum(S, (NBRS := ADJ.indices[ADJ.indptr[S]:ADJ.indptr[S+1]])) * numpy.uint32(STN["Code"].size) + numpy.maximum(S, NBRS))])] for S in SI["Source"][SI["PI"][Q]]), dtype=int, count=Q.size)]))}
        self._Log.Metrics("N3: Diversion: %s", Q.size)

        # -------- S1 [Crossing Priority] -------- #
        PTIDX = numpy.searchsorted(SCH["Offsets"][1:], (SIDX := numpy.lexsort((SCH["Arrival"], SCH["Station"]))), side="right")
        if (CM := (numpy.diff(SCH["Station"][SIDX]) == 0) & (SCH["Arrival"][SIDX][1:] < SCH["Departure"][SIDX][:-1])).any():
            PA, PB = PTIDX[:-1][CM], PTIDX[1:][CM]; LO = numpy.where(TRN["Priority"][PA] < TRN["Priority"][PB], PA, PB)
            HOLD = numpy.where(STN["LoopLines"][SCH["Station"][SIDX][1:][CM]] > 0, SCH["Station"][SIDX][1:][CM], SCH["Station"][LPCUM[SCH["Offsets"][1:][LO] - 1]]); LSRT = numpy.argsort(LO); LO, HOLD = LO[LSRT], HOLD[LSRT]
            if (Q := numpy.unique(LO)).size: self._Manifest["S1"] = {"ID": numpy.char.add("S1-T", numpy.char.zfill(numpy.arange(1, Q.size + 1).astype(str), 4)), "Affected": TRN["TrainNo"][Q], "Recommendations": self._TF.Quantize(numpy.column_stack([numpy.broadcast_to(6, Q.size), HOLD[numpy.searchsorted(LO, Q)]]))}
        self._Log.Metrics("S1: CrossingPriority: %s", Q.size)

        # -------- S2 [Rake Augmentation] -------- #
        Q = numpy.flatnonzero((DELTA := numpy.round((TRN["Demand"][:, 0] + TRN["Demand"][:, 1]) * 0.5 / ((W["MaxAxleLoad"] * W["Axles"]).mean()) - TRN["WagonComposition"][:TRN["Type"].size].sum(axis=1).ravel()).astype(int)) != 0)
        Q = Q[numpy.unique(TRN["TrainNo"][Q], return_index=True)[1]]
        if Q.size: WCS = TRN["WagonComposition"][Q].tocsr(); self._Manifest["S2"] = {"ID": numpy.char.add("S2-T", numpy.char.zfill(numpy.arange(1, Q.size + 1).astype(str), 4)), "Affected": TRN["TrainNo"][Q], "Recommendations": self._TF.Quantize(numpy.column_stack([numpy.broadcast_to(7, Q.size), DELTA[Q], numpy.fromiter((WCS.indices[WCS.indptr[I]:WCS.indptr[I+1]][WCS.data[WCS.indptr[I]:WCS.indptr[I+1]].argmax()] for I in range(Q.size)), dtype=int, count=Q.size)]))}
        self._Log.Metrics("S2: RakeAugmentation: %s | Attach: %s | Detach: %s", Q.size, (DELTA[Q] > 0).sum(), (DELTA[Q] < 0).sum())

        self._Log.Metrics("Decisions: %s | Total: %s | Time: [%s]", len(self._Manifest), sum(len(V["Affected"]) for V in self._Manifest.values()), self._T.Elapsed())

        return self._Manifest

# -------- Dashboard -------- #
class Dashboard:
    __slots__ = ("_Log", "_T", "_Snapshot", "_Evaluations", "_Manifest", "_Application")
    def __init__(self, Evaluations, Snapshot, Manifest):
        self._Log, self._Manifest, self._Snapshot, self._Evaluations = Logger("Dashboard", "ML"), orjson.dumps({K: {FK: FV.tolist() for FK, FV in V.items()} for K, V in Manifest.items()}), orjson.dumps({K: V for K, V in Snapshot.items() if K != 'Tensors'}, option=orjson.OPT_SERIALIZE_NUMPY, default=lambda x: {"data": x.data, "indices": x.indices, "indptr": x.indptr, "shape": list(x.shape)} if hasattr(x, "tocsr") else x.tolist() if hasattr(x, "tolist") else None), orjson.dumps(Evaluations)
        self._Application = self._Build()

    def _Build(self):
        Application = FastAPI()
        HTML = jinja2.Environment(loader = jinja2.BaseLoader()).from_string(Configuration["Dashboard"]["HTML"]).render(CSS=Configuration["Dashboard"]["CSS"], JS=jinja2.Environment(loader = jinja2.BaseLoader()).from_string(Configuration["Dashboard"]["JS"]).render(MANIFEST=self._Manifest.decode(), EVALUATIONS=self._Evaluations.decode(),
            THRESHOLDS=orjson.dumps(Configuration["Dashboard"]["Thresholds"]).decode(), ACTIONS=orjson.dumps(Configuration["Adjudicator"]["Actions"]).decode(), SNAPSHOT=self._Snapshot.decode()), MC=len(Configuration["Dashboard"]["Thresholds"]), TC=len(Configuration["Analytics"]["Targets"]))
        Application.get("/")(lambda: HTMLResponse(HTML))
        Application.get("/Manifest")(lambda: Response(self._Manifest, media_type="application/json"))
        Application.get("/Evaluations")(lambda: Response(self._Evaluations, media_type="application/json"))
        return Application

    def Run(self, Host="127.0.0.1", Port=8080): self._Log.Metrics("Dashboard → http://%s:%d", Host, Port); uvicorn.run(self._Application, host=Host, port=Port, log_level="error")

# -------- Orchestrator -------- #
class ML:
    __slots__ = ("_Log", "_Framework", "_Device", "_Provider", "_TDevice", "_Snapshot", "_Analytics", "_Adjudicator")
    def __init__(self):
        self._Log = Logger("ML")

        # -------- Framework Resolution -------- #
        F = D = "cpu"
        for F0, D0 in Configuration["Analytics"]["Backends"]:
            try:
                match F0:
                    case "torch" if (M := __import__("torch")) and (M.backends.mps.is_available() if D0 == "mps" else M.cuda.is_available() if D0 in ("cuda", "hip", "rocm") else False): F, D = F0, D0; break
                    case "qnn" | "onnx" if Configuration["Analytics"]["Backends"][(F0, D0)] in __import__("onnxruntime").get_available_providers(): F, D = F0, D0; break
                    case "openvino" if any(D0.upper() in D1 for D1 in __import__("openvino").Core().available_devices): F, D = F0, D0; break
            except (ImportError, AttributeError, KeyError): continue

        # -------- Device Resolution -------- #
        try: TD = __import__("torch_directml").device()
        except ImportError: TD = M.device(D) if (F == "torch" and D in ("cuda", "hip", "rocm", "mps") and (M := __import__("torch"))) else (M.device("cuda") if (M := __import__("torch")).cuda.is_available() else M.device("cpu"))

        self._Framework, self._Device, self._Provider, self._TDevice = F, D, Configuration["Analytics"]["Backends"].get((F, D), F), TD
        self._Log.Metrics("Framework: [%s] | Device: [%s] | Provider: [%s] | Torch Device: [%s]", F, D, self._Provider, self._TDevice)

    # -------- Run -------- #
    def Run(self):
        with Database() as DB, Timer() as T:
            match DB.Reader("SimulationSnapshot"):
                case None: self._Snapshot = SimulationEngine(Encodings = DB.Reader("Encodings"), Graph=DB.Reader("Graph"), **{TAB: DB.Reader(TAB) for TAB in Configuration["FS"]}).Snapshot; DB.Writer("SimulationSnapshot", self._Snapshot)
                case Data: self._Snapshot = Data
            self._Log.Metrics("Snapshot Dimensions: [%s] | DB Size: [%s] | Time: [%s]", Summary(self._Snapshot), DB.Size, T.Elapsed())

            # -------- Analytics & Models -------- #
            self._Analytics = AnalyticsEngine(self._Snapshot, self._Framework, self._Device, self._Provider, self._TDevice)
            match DB.Reader("Model"):
                case None: self._Analytics.Train(); DB.Writer("Model", self._Analytics.Load({"Weights": self._Analytics._Weights}))
                case Data: DB.Writer("Model", self._Analytics.Load(Data))

            # -------- Adjudication & Dashboard -------- #
            self._Adjudicator = Adjudicator(self._Snapshot, self._Analytics._Evaluations, self._Analytics._Predictions)
            _Dashboard = Dashboard(self._Analytics._Evaluations, self._Snapshot, self._Adjudicator._Manifest).Run()

if __name__ == "__main__": ML().Run()
