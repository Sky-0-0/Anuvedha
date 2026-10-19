import builtins, itertools, types, numpy, orjson, scipy, scipy.sparse
from Utilities import Configuration, Database, Logger, Summary, Timer, Transforms


# -------- ETL Pipeline -------- #
class ETL:
    def __init__(self):
        self._Log, self._T, self._TF = Logger("ETL"), Timer(), Transforms()

    # -------- Ravel -------- #
    def _Ravel(self, D, N):
        if not D: return {}
        C = {}
        for K, T in Configuration["Schema"][N].items():
            if not (V := tuple(R[K] for R in D if K in R)): continue
            C1, I1 = (T[0], T[1]) if isinstance(T, tuple) else (T, None)
            match (C1.__args__[0] if (N1 := isinstance(C1, types.UnionType)) else C1):
                case builtins.list:
                    C[f"{K}|Offsets"] = (0, *itertools.accumulate(len(X) for X in V))
                    if isinstance(I1, dict):
                        for K1 in I1: C[f"{K}|{K1}"] = tuple(D1[K1] for X in V for D1 in X if D1)
                    else: C[K] = tuple(itertools.chain.from_iterable(V))
                case builtins.dict:
                    if VD := [(I, X) for I, X in enumerate(V) if X]:
                        M = {K1: I1 for I1, K1 in enumerate({K2 for _, X in VD for K2 in X})}
                        C[K] = scipy.sparse.coo_array(([V1 for _, X in VD for V1 in X.values()], ([I for I, X in VD for _ in X], [M[K1] for _, X in VD for K1 in X])), shape=(len(V), len(M)))
                        C[f"{K}|Keys"] = tuple(M.keys())
                case builtins.float: C[K] = tuple(numpy.nan if X is None else X for X in V) if N1 else V
                case builtins.int: C[K] = tuple(0 if X is None else X for X in V) if N1 else V
                case builtins.bool: C[K] = tuple(False if X is None else X for X in V) if N1 else V
                case _: C[K] = tuple("" if X is None else X for X in V) if N1 else V
        return C

    # -------- Materialize -------- #
    def _Materialize(self):
        WC, SC, STNC, MKC, MNC = self._TF.Quantize((C := Configuration["Simulation"])["Wagons"], C["Segments"], C["Stations"], C["Market"], C["Maintenance"])
        ENG, EVT, RK, SCH, SEG, STN, TRN, WCF, CNFG = ((ENC := (S := self._Statics)["Encodings"])["Engines"]), ENC["Events"], ENC["Rakes"], ENC["Schedules"], ENC["Segments"], ENC["Stations"], ENC["Trains"], ENC["Wagons"], ENC["Configuration"]
        Engines, Events, Rakes, Schedules, Segments, Stations, Trains, Wagons = S["Engines"], S["Events"], S["Rakes"], S["Schedules"], S["Segments"], S["Stations"], S["Trains"], S["Wagons"]

        # ---- Infrastructure: Stations ----
        S["Stations"] = self._TF.Quantize({"Code": STN["Code"]["Forward"], "Name": STN["Name"]["Forward"], "Category": (STC := STN["Category"]["Forward"]), "Zone": STN["Zone"]["Forward"], "Division": STN["Division"]["Forward"], "Location": (Stations["Location"], (-1, 2)), "Platforms": Stations["Platforms"], "LoopLines": STNC[STC], "EPL": Stations["EPL"], "Traffic": MKC["Traffic"]["Stations"][STC]})

        # ---- Rolling Stock: Engines ----
        S["Engines"] = self._TF.Quantize({"Class": (ECF := ENG["Class"]["Forward"]), "Service": ENG["Service"]["Forward"], "Traction": ENG["Traction"]["Forward"], "Power": Engines["Power"], "MPS": Engines["MPS"], "TareWeight": Engines["TareWeight"], "CL": Engines["CL"], "IA": Engines["IA"], "IB": Engines["IB"], "IC": Engines["IC"], "M12": Engines["M12"], "IOH": Engines["IOH"], "POH": Engines["POH"], "IOHMD": Engines["IOHMD"], "POHMD": Engines["POHMD"], "REKM": Engines["REKM"], "FOR": Engines["FOR"], "Haulage": MKC["Haulage"]["Engines"][ECF]})

        # ---- Rolling Stock: Wagons ----
        WM, WCD = MNC["Wagons"][WDF := WCF["Design"]["Forward"]], WC[WDF]
        S["Wagons"] = self._TF.Quantize({"Class": (WCI := WCF["Class"]["Forward"]), "Accommodation": WCF["Accommodation"]["Forward"], "Design": WDF, "Stock": WCF["Stock"]["Forward"], "AC": (WAC := Wagons["AC"]), "Length": numpy.where(numpy.isnan(WL := Wagons["Length"]), WCD[:, 0], WL), "MPS": numpy.where(numpy.isnan(WS := Wagons["MPS"]), WCD[:, 1], WS), "Axles": WCD[:, 2], "MaxAxleLoad": WCD[:, 3], "TareWeight": numpy.where(numpy.isnan(WT := Wagons["TareWeight"]), numpy.where(WAC, WCD[:, 4], WCD[:, 5]), WT), "Capacity": Wagons["Capacity"], "HotelLoad": numpy.where(numpy.isnan(WH := Wagons["HotelLoad"]), numpy.where(WAC, WCD[:, 6], WCD[:, 8]), WH), "SchA": WM[:, 0], "SchB": WM[:, 1], "IOH": WM[:, 2], "POH": WM[:, 3], "CL": Wagons["CL"], "SchAMD": WM[:, 4], "SchBMD": WM[:, 5], "IOHMD": WM[:, 6], "POHMD": WM[:, 7], "FOR": WM[:, 8], "REKM": Wagons["REKM"], "Traffic": MKC["Traffic"]["Wagons"][WCI], "Haulage": MKC["Haulage"]["Wagons"][WCI]})

        # ---- Rolling Stock: Schedules ----
        S["Schedules"] = self._TF.Quantize({"TrainNo": SCH["TrainNo"]["Forward"], "Station": SCH["Stops|Station"]["Forward"], "Offsets": Schedules["Stops|Offsets"], "Day": Schedules["Stops|Day"], "Arrival": Schedules["Stops|Arrival"], "Departure": Schedules["Stops|Departure"]}); Rakes["Composition"]._shape = (Rakes["Composition"].shape[0], WCI.size)

        # ---- Rolling Stock: Rakes ----
        Rakes["Composition"] = scipy.sparse.csr_array((Rakes["Composition"].data, (numpy.repeat(numpy.arange(NRK := Rakes["Composition"].shape[0]), numpy.diff(Rakes["Composition"].indptr.astype(numpy.intp))), numpy.searchsorted(WCF["Class"]["Reverse"], RK["Composition|Keys"]["Reverse"])[RK["Composition|Keys"]["Forward"]][Rakes["Composition"].indices])), shape=(NRK, WCI.size))
        S["Rakes"] = self._TF.Quantize({"RakeNo": RK["RakeNo"]["Forward"], "Design": RK["Design"]["Forward"], "CDOs": RK["CDOs"]["Forward"], "CDOs|Offsets": Rakes["CDOs|Offsets"], "Trains": RK["Trains"]["Forward"], "Trains|Offsets": Rakes["Trains|Offsets"], "Composition": Rakes["Composition"], "Composition|Keys": RK["Composition|Keys"]["Forward"]})

        # ---- Rolling Stock: Trains ----
        S["Trains"] = self._TF.Quantize({"TrainNo": SCH["TrainNo"]["Forward"], "Name": TRN["Name"]["Forward"], "Type": (T := TRN["Type"]["Forward"]), "Service": (SSVC := CNFG["TrainServices"]["Forward"][T]), "Priority": self._TF.Quantize(C["Services"]["Priorites"])[SSVC], "Frequency": numpy.diff(Trains["Frequency|Offsets"]), "WagonComposition": (WRC := scipy.sparse.csc_array((numpy.ones(RK["Trains"]["Forward"].size, dtype=bool), RK["Trains"]["Forward"], Rakes["Trains|Offsets"]), shape=(TRN["TrainNo"]["Reverse"].size, RK["RakeNo"]["Reverse"].size)) @ Rakes["Composition"]),
            "Demand": (WRC @ (TW := S["Wagons"]["TareWeight"]))[:, None] + (WRC @ (S["Wagons"]["Axles"] * S["Wagons"]["MaxAxleLoad"] - TW))[:, None] * MKC["Traffic"]["Trains"][T][:, :2]})

        # ---- Infrastructure: Segments ----
        (SM := numpy.ones((STP := SCH["Stops|Station"]["Forward"]).size - 1, dtype = bool))[(OFF := S["Schedules"]["Offsets"])[1:-1] - 1] = False
        S["Segments"] = self._TF.Quantize({"Source": (SA := SEG["Key|0"]["Forward"]), "Destination": (SB := SEG["Key|1"]["Forward"]), "Line": Segments["Line"], "Group": (G := SEG["Group"]["Forward"]), "Distance": (SD := Segments["Distance"]), "SpeedLimit": (SPD := SC[G]), "TravelTime": SD / SPD,
            "PI": (SI := numpy.argsort(SK := numpy.minimum(SA, SB) * (NSTN := numpy.uint32(STN["Code"]["Reverse"].size)) + numpy.maximum(SA, SB)))[numpy.searchsorted(SK[SI], numpy.minimum(A := STP[:-1][SM], B := STP[1:][SM]) * NSTN + numpy.maximum(A, B))], "PT": numpy.searchsorted(OFF[1:], numpy.flatnonzero(SM), side='right'), "SK": SK[SI]})

        # ---- Infrastructure: Graph ----
        S["Graph"] = self._TF.Quantize({"Adjacency": scipy.sparse.coo_array((numpy.ones(SA.size * 2, dtype = bool), (numpy.concatenate([SA, SB]), numpy.concatenate([SB, SA]))), shape = (NSTN, NSTN))})

        # ---- Environment: Events ----
        S["Events"] = self._TF.Quantize({"Name": EVT["Name"]["Forward"], "Window": (Events["Window"], (-1, 2)), "Zones": Events["Zones"], "Services": Events["Services"], "Scale": (Events["Scale"], (-1, 2)), "Probability": (Events["Probability"], (-1, 2))})

        self._Log.Step("Initialized: Engines: %s | Events: %s | Rakes: %s | Schedules: %s | Segments: %s | Stations: %s | Trains: %s | Wagons: %s | Encodings: [%s] | Time: [%s]", ENG["Class"]["Reverse"].size, EVT["Name"]["Reverse"].size, RK["RakeNo"]["Reverse"].size, S["Schedules"]["Offsets"].size - 1, len(S["Segments"]["Source"]), STN["Code"]["Reverse"].size, TRN["TrainNo"]["Reverse"].size, WCF["Class"]["Reverse"].size, sum(map(len, ENC.values())), self._T.Split())

    # -------- Run -------- #
    def Run(self):
        self._T.Start(); self._Statics = {}; UPK = set()

        # -------- File Read & Ravel -------- #
        for N, (P, PK, *_) in Configuration["FS"].items():
            if PK is None: continue
            with open(P, "rb") as F: self._Statics[N] = (D := self._Ravel(orjson.loads(F.read()), N))
            UPK.update(D[PK])
        self._Log.Step("Schema Ingestion and Ravel: %s", self._T.Split())

        # -------- Tokenization -------- #
        for C in self._Statics.values():
            for K, V in tuple(C.items()):
                if isinstance(V, tuple) and V and isinstance(V[0], str) and "-" in V[0] and set(V[0].split("-")).issubset(UPK):
                    C[f"{K}|0"], C[f"{K}|1"] = (C0 := [None] * (N := len(V))), (C1 := [None] * N)
                    for I, S in enumerate(V): C0[I], C1[I] = S.split("-", 1)
                    del C[K]

        # -------- Encodings -------- #
        (TF := Transforms()).Encode(self._Statics, ("Configuration", "NominatedPower", (C := Configuration["Simulation"])["EngineMappings"]["NominatedPower"]),("Configuration", "ServiceNames", C["Services"]["Names"]), ("Configuration", "TrainServices", C["Services"]["TrainServices"]), ("Configuration", "EngineServices", C["Services"]["EngineServices"]),("Configuration", "TrainTypes", C["Services"]["TrainTypes"]) )
        self._Statics["Encodings"] = TF.Encodings

        # -------- Event Expansion & Bitmask Encoding -------- #
        STN, CNFG = ((ENC := self._Statics["Encodings"])["Stations"], ENC["Configuration"])
        CNFG["TrainServices"] = {"Forward": TF.Quantize(numpy.searchsorted((SN := CNFG["ServiceNames"]["Reverse"]), (TS := CNFG["TrainServices"])["Reverse"])[TS["Forward"]]), "Reverse": SN}
        EV, SM, ZM = self._Statics["Events"], {R: 1 << I for I, R in enumerate(CNFG["ServiceNames"]["Reverse"])}, {R: 1 << I for I, R in enumerate(STN["Zone"]["Reverse"])}
        ZM["*"], SM["*"] = (1 << len(ZM)) - 1, (1 << len(SM)) - 1

        ZO, SO = EV.pop("Zones|Offsets"), EV.pop("Services|Offsets")
        EV["Zones"] = [sum(ZM[X] for X in itertools.islice(EV["Zones"], I, J)) for I, J in itertools.pairwise(ZO)]
        EV["Services"] = [sum(SM[X] for X in itertools.islice(EV["Services"], I, J)) for I, J in itertools.pairwise(SO)]
        self._Log.Step("Tokenization | Encodings | Bitmasks: %s", self._T.Split())

        # -------- Statics Materialization -------- #
        for N, T in self._Statics.items(): self._Statics[N] = self._TF.Quantize(T)
        self._Materialize()

        # -------- Database Write -------- #
        with Database() as DB:
            DB.Connection.executescript("".join(f"DROP TABLE IF EXISTS [{N}];" for N in self._Statics)) # type: ignore[reportOptionalMemberAccess]
            self._Log.Step("Purged: %s", list(self._Statics.keys()))
            self._Log.Step("Tables: %s | DB Size: [%s] | Write Time: [%s] | Total ETL: [%s]", Summary({N: DB.Writer(N, self._Statics[N]) for N in self._Statics}), DB.Size, self._T.Split(), self._T.Elapsed())

if __name__ == "__main__": ETL().Run()
