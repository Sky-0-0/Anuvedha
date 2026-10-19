import os, sys, atexit, contextlib, types, traceback, warnings, pathlib, time, datetime, itertools, collections, threading, queue, math, logging, sqlite3, orjson, zstandard, numpy, scipy, torch, onnxruntime
from rich.progress import Progress, ProgressColumn, BarColumn, TextColumn, SpinnerColumn, MofNCompleteColumn, TaskProgressColumn
from rich.text import Text
from rich.table import Column
from rich.console import Console
from .Configuration import Configuration
warnings.filterwarnings("ignore")

# -------- Logger -------- #
class Logger:
    type LogValue = int | float | str | bool | torch.Tensor | numpy.generic | numpy.ndarray | dict | list | tuple | set
    __slots__ = ("M", "F")
    _Console, _Queue, _FileHandlers, _WorkerThread = Console(force_terminal=True, legacy_windows=False), queue.SimpleQueue(), {}, None

    def __init__(self, M: str, F: str | None = None):
        self.M, self.F = M, (Target := F or M)
        if Target not in Logger._FileHandlers:
            os.makedirs("Logs", exist_ok=True)
            (FH := logging.FileHandler(f"Logs/{Target}.log", mode="w", encoding="utf-8")).setFormatter(logging.Formatter("%(message)s"))
            Logger._FileHandlers[Target] = FH
            if not Logger._WorkerThread:
                Logger._WorkerThread = threading.Thread(target=Logger._ProcessQueue, daemon=True)
                Logger._WorkerThread.start(); atexit.register(lambda: (Logger._Queue.put_nowait(None), Logger._WorkerThread.join())) # type: ignore[reportOptionalMemberAccess]

    def Trace(self, M: str, *A): Logger._Queue.put_nowait((self.M, self.F, "Trace", M, A, None))
    def Step(self, M: str, *A): Logger._Queue.put_nowait((self.M, self.F, "Step", M, A, None))
    def Metrics(self, M: str, *A): Logger._Queue.put_nowait((self.M, self.F, "Metrics", M, A, None))
    def Warn(self, M: str, *A): Logger._Queue.put_nowait((self.M, self.F, "Warn", M, A, sys.exc_info()))
    def Exception(self, M: str, *A): Logger._Queue.put_nowait((self.M, self.F, "Exception", M, A, sys.exc_info()))

    @staticmethod
    def _ProcessQueue():
        while (Item := Logger._Queue.get()) is not None:
            try:
                M, F, L, MSG, Args, EXC = Item
                FM = MSG if not Args else (MSG % tuple(A if isinstance(A, (int, str, bool)) else Logger._Stringify(A) for A in Args))
                Logger._Console.out(Line := f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - [{L}] [{M}] {FM}", highlight=True)
                if FH := Logger._FileHandlers.get(F): FH.emit(logging.LogRecord(M, logging.INFO, "", 0, Line, (), None))

                if L in ("Warn", "Exception") and EXC and EXC[2]:
                    S = [FS for FS in traceback.extract_tb(EXC[2]) if not any(X in FS.filename.lower() for X in ('site-packages', '\\lib\\', 'utilities.py'))] or traceback.extract_tb(EXC[2])[:1]
                    Logger._Console.out(ELine := f"{''.join(traceback.format_list(S[:2] + S[-2:] if len(S) > 4 else S))}{EXC[0].__name__}: {str(EXC[1]).split(chr(10), 1)[0]}", highlight=True)
                    if FH: FH.emit(logging.LogRecord(M, logging.INFO, "", 0, ELine, (), None))
            except Exception as E: print(f"[Exception] {type(E).__name__}: {E}", flush=True)

    @staticmethod
    def _Stringify(V: LogValue, D: int = 0, M: int = 10, S: set | None = None) -> str:
        if D > M: return "<MaxDepth>"
        match V:
            case float() | numpy.floating(): return "NaN" if math.isnan(V) else ("-Inf" if V < 0 else "Inf") if math.isinf(V) else f"{V:.5f}"
            case int() | str() | bool(): return str(V)

            case torch.Tensor(): return f"{V.item():.5f}" if V.numel() == 1 else (f"[Shape: {tuple(V.shape)} | Type: {str(V.dtype).split('.')[-1]} ({V.element_size()}B)]" if V.ndim > 2 or V.numel() > 16 else numpy.array2string(V.detach().cpu().numpy(), max_line_width=sys.maxsize, separator=", ", formatter={"float_kind": lambda X: f"{X:.5f}"}))
            case numpy.generic() as V: return str(X) if isinstance(X := V.item(), (int, str, bool)) else f"{float(X):.5f}"
            case numpy.ndarray(): return f"[Shape: {V.shape} | Type: {'T' if V.dtype.kind == 'T' else f'{V.dtype.str} ({V.itemsize}B)'}{f' | Distribution: ({V.min():.5f}, {V.mean():.5f}, {V.max():.5f})' if V.dtype.kind in 'biuf' and V.size > 0 else ''}]" if V.ndim > 2 or V.size > 64 else numpy.array2string(V, max_line_width=sys.maxsize, separator=", ", formatter={"float_kind": lambda X: f"{X:.5f}"})

            case dict() | list() | tuple() | set() if S is not None and id(V) in S: return f"<Cycle:{type(V).__name__}>"
            case list() | tuple():
                if len(V) > 32: return f"[{type(V).__name__.capitalize()} | Elements: {', '.join(Logger._Stringify(X, D + 1, M, S) for X in itertools.islice(V, 5))}, ..., {', '.join(Logger._Stringify(X, D + 1, M, S) for X in collections.deque(V, maxlen = 3))} | Size: {len(V)}]"
                (C := S or set()).add(id(V)); return "[" + ", ".join(Logger._Stringify(X, D + 1, M, C) for X in V) + "]"
            case dict():
                if len(V) > 16: return f"[Dictionary | Keys: {', '.join(str(K) for K in itertools.islice(V.keys(), 5))}, ..., {', '.join(str(K) for K in collections.deque(V.keys(), maxlen = 3))} | Size: {len(V)}]"
                (C := S or set()).add(id(V)); return "{" + ", ".join(f"{Logger._Stringify(K, D + 1, M, C)}: {Logger._Stringify(V1, D + 1, M, C)}" for K, V1 in V.items()) + "}"
            case set():
                if len(V) > 16: return f"[Set | Keys: {', '.join(str(X) for X in itertools.islice(V, 5))}, ..., {', '.join(str(X) for X in collections.deque(V, maxlen = 3))} | Size: {len(V)}]"
                (C := S or set()).add(id(V)); return "[" + ", ".join(Logger._Stringify(X, D + 1, M, C) for X in V) + "]"

            case scipy.sparse.sparray(): return f"[Shape: {V.shape} | NNZ: {V.nnz} | Format: {V.format.upper()} | Type: {V.dtype.str} ({V.dtype.itemsize}B)]"
            case types.FunctionType() | types.MethodType(): return f"<Function {V.__name__}>"
            case _: return str(V)

# -------- Timer -------- #
class Timer:
    __slots__ = ("_T0", "_TS")
    def __init__(self): self._T0 = self._TS = time.perf_counter_ns()
    def __enter__(self): self._T0 = self._TS = time.perf_counter_ns(); return self
    def __exit__(self, *A): pass
    def Start(self): self._T0 = self._TS = time.perf_counter_ns()
    def Split(self) -> str: D = (N := time.perf_counter_ns()) - self._TS; self._TS = N; return self._F(D)
    def Elapsed(self) -> str: D = (time.perf_counter_ns()) - self._T0; return self._F(D)
    def _F(self, Ns: int) -> str:
        if (D := Ns / 1_000_000_000.0) >= 3600.0: return f"{int(D // 3600)}H {int(D % 3600 // 60)}M"
        if D >= 60.0: return f"{int(D // 60)}M {int(D % 60)}s"
        if D >= 1.0: return f"{D:.2f}s"
        return f"{D * 1000.0:.2f}ms" if D >= 0.001 else f"{Ns / 1000.0:.2f}μs"

# -------- Loader -------- #
class Loader:
    __slots__ = ("_P", "_T", "_L", "_E")
    class _Speed(ProgressColumn):
        def render(self, T): return Text(f"{T.speed:.0f}/s" if T.speed is not None else "—/s", style="#b0b0b0") # type: ignore[reportIncompatibleMethodOverride]

    class _Time(ProgressColumn):
        __slots__ = ("_F",)
        def __init__(self): super().__init__(); self._F = lambda S: (f"{int(S)//3600:02d}:{int(S)%3600//60:02d}:{int(S)%60:02d}" if S and int(S) >= 3600 else f"{int(S)//60:02d}:{int(S)%60:02d}") if S else "--:--"
        def render(self, T): return Text.from_markup(f"[pale_green3]{self._F(T.elapsed)}[/] [grey30]•[/] [light_coral]{self._F(T.time_remaining)}[/]") # type: ignore[reportIncompatibleMethodOverride]

    def __init__(self, Total, Description):
        self._L = self._E = 0
        self._P = Progress(TextColumn(f"[#b0b0b0]{Description}[/]"), SpinnerColumn("dots", style="#50e3c2"), BarColumn(bar_width=40, style="grey19", complete_style="#4a90e2", finished_style="pale_green3"), MofNCompleteColumn(table_column=Column(style="#b0b0b0")), TaskProgressColumn(style="#b0b0b0"), Loader._Speed(), TextColumn("[grey23]│[/] [#e0a030]L: {task.fields[L]}[/] [grey23]│[/] [#50e3c2]E: {task.fields[E]}[/] [grey23]│[/]"), Loader._Time(), console=Logger._Console, transient=True, speed_estimate_period=120.0)
        self._T = self._P.add_task("", total=Total, L="—", E="—")

    def __enter__(self): self._P.__enter__(); return self
    def __exit__(self, *A): return self._P.__exit__(*A)

    def Advance(self, N = 1, L = None, E = None):
        self._L = L if L is not None else self._L; self._E = E if E is not None else self._E
        self._P.update(self._T, advance=N, L=f"{self._L:.5f}" if isinstance(self._L, float) else self._L, E=self._E)

# -------- Database Context Handler -------- #
class Database:
    __slots__ = ("Connection", "_Compressor", "_Decompressor", "_Path")

    def __enter__(self):
        self._Path = pathlib.Path(Configuration["Analytics"]["Paths"]["Database"])
        self._Path.parent.mkdir(parents=True, exist_ok=True)
        self.Connection = sqlite3.connect(self._Path, timeout=30.0)
        self.Connection.executescript("PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF; PRAGMA cache_size=-128000; PRAGMA temp_store=MEMORY; PRAGMA mmap_size=1073741824;")
        self._Compressor, self._Decompressor = zstandard.ZstdCompressor(), zstandard.ZstdDecompressor()
        return self

    def __exit__(self, Type, Value, Traceback):
        if self.Connection:
            try: self.Connection.commit() if Type is None else self.Connection.rollback()
            finally: self.Connection.close(); self.Connection = self._Compressor = self._Decompressor = self._Path = None

    @property
    def Size(self) -> str:
        if (B := self._Path.stat().st_size) >= (1 << 30): return f"{B / (1 << 30):.2f} GB" # type: ignore[reportOptionalMemberAccess]
        if B >= (1 << 20): return f"{B / (1 << 20):.2f} MB"
        if B >= (1 << 10): return f"{B / (1 << 10):.2f} KB"
        return f"{B} B"

    # -------- Nest -------- #
    @staticmethod
    def _Nest(I):
        R, S = {}, []
        for K, V in I:
            if type(V) is numpy.ndarray and V.size == 1: V = V.item()
            CR = R
            while "/" in K: P, K = K.split("/", 1); CR = CR.setdefault(P, {})
            CR[K] = V
        S = [R]
        while S:
            C = S.pop()
            for K, V in C.items():
                match V:
                    case dict():
                        match V:
                            case {"Data": D, "Indices": I, "Indptr": P, "Shape": SH}: C[K] = scipy.sparse.csr_array((D, I, P), shape=tuple(SH))
                            case _ if V and all(K0.isdigit() for K0 in V): C[K] = tuple(V[str(IX)] for IX in range(len(V)))
                            case {"__state_dict__": _, **SD}: C[K] = {SK: torch.from_numpy(SV) for SK, SV in SD.items()}
                            case _: S.append(V)
        return R

    # -------- Denest -------- #
    @staticmethod
    def _Denest(D):
        R, S = {}, [(D, "")]
        while S:
            C, P = S.pop()
            for K, V in C.items():
                Q = f"{P}/{K}" if P else K
                match V:
                    case torch.nn.Module() as M: S.append(({"__state_dict__": True, **Transforms.Quantize(M)}, Q))
                    case dict() as D0 if any(type(VV) is torch.Tensor for VV in D0.values()): S.append(({"__state_dict__": True, **Transforms.Quantize(D0)}, Q))
                    case dict(): S.append((V, Q))
                    case scipy.sparse.sparray() as M: R[f"{Q}/Data"], R[f"{Q}/Indices"], R[f"{Q}/Indptr"], R[f"{Q}/Shape"] = *Transforms.Quantize(M.data, M.indices, M.indptr), numpy.asarray(M.shape)
                    case tuple():
                        for I, A in enumerate(V): R[f"{Q}/{I}"] = A if type(A) is numpy.ndarray else Transforms.Quantize(A)
                    case _: R[Q] = V if type(V) is numpy.ndarray else Transforms.Quantize(V)
        return R

    # -------- Reader -------- #
    def Reader(self, Table):
        try: return Database._Nest((R[0], numpy.frombuffer(self._Decompressor.decompress(R[4]), dtype=R[1]).reshape(orjson.loads(R[2]))) for R in self.Connection.execute(f"SELECT KEY, DTYPE, SHAPE, BYTES, BLOB FROM [{Table}]")) # type: ignore[reportOptionalMemberAccess]
        except sqlite3.OperationalError: return None
        except Exception as E: raise RuntimeError(f"Reader failed on [{Table}]: {type(E).__name__}: {E}") from E

    # -------- Writer -------- #
    def Writer(self, Table, Data):
        try:
            F = Database._Denest(Data) if any(not isinstance(V, numpy.ndarray) for V in Data.values()) else Data
            self.Connection.execute(f"CREATE TABLE IF NOT EXISTS [{Table}] (KEY TEXT PRIMARY KEY, DTYPE TEXT, SHAPE TEXT, BYTES INT, BLOB BLOB)") # type: ignore[reportOptionalMemberAccess]
            self.Connection.executemany(f"INSERT OR REPLACE INTO [{Table}] VALUES (?,?,?,?,?)", [(K, (A := numpy.ascontiguousarray(V)).dtype.str, str(list(A.shape)), A.nbytes, self._Compressor.compress(A)) for K, V in F.items()]) # type: ignore[reportOptionalMemberAccess]
            self.Connection.commit(); return (N := len(F)), N # type: ignore[reportOptionalMemberAccess]
        except Exception as E: raise RuntimeError(f"Writer failed on [{Table}]: {type(E).__name__}: {E}") from E

# -------- Transforms ------- #
class Transforms:
    __slots__ = ("_Encodings", "_Device")
    def __init__(self, Encodings = None, Device = None): self._Encodings, self._Device = Encodings or {}, Device

    @property
    def Encodings(self): return self._Encodings

    # -------- Quantization ------- #
    @staticmethod
    def Quantize(*Args):
        match Args:
            case (D,): Data = D
            case _: return tuple(Transforms.Quantize(A) for A in Args)
        match Data:
            # -------- Core NumPy Quantization -------- #
            case numpy.ndarray() as A:
                if isinstance(A, numpy.matrix): A = A.A.squeeze() if 1 in A.shape else A.A
                if not A.size or A.dtype.kind in ("S", "U", "b"): return A
                if A.dtype.kind == "O": raise TypeError(f"[OBJECT LEAK]: {A}")
                if A.dtype.kind in ("i", "u"):
                    MN, MX = (None, A.max()) if A.dtype.kind == "u" else (A.min(), A.max())
                    DT = (numpy.uint8 if MX < 256 else numpy.uint16 if MX < 65536 else numpy.uint32 if MX < 4294967296 else numpy.uint64) if MN is None or MN >= 0 else (numpy.int8 if MN >= -128 and MX <= 127 else numpy.int16 if MN >= -32768 and MX <= 32767 else numpy.int32 if MN >= -2147483648 and MX <= 2147483647 else A.dtype)
                    return A if A.dtype == DT else A.astype(DT, copy = False)
                if A.dtype.kind in ("f", "c"):
                    if A.dtype == numpy.float16: return A
                    return A if A.dtype == (DT := numpy.float16 if (AMX := abs(A).max()) < 65504.0 else numpy.float32 if AMX < 3.4e38 else A.dtype) else A.astype(DT, copy=False)
                return A

            # -------- ML Models -------- #
            case torch.Tensor() as T: return (D := T.detach()).to(device = "cpu", dtype = (torch.float16 if torch.amax(torch.abs(D)).item() < 65504.0 else torch.float32), non_blocking=True).numpy() if D.dtype in (torch.float32, torch.float64) else D.cpu().numpy()
            case torch.nn.Module() as M: return Transforms.Quantize(M.state_dict())

            # -------- Sparse / Containers -------- #
            case scipy.sparse.sparray() as M:
                if M.format != "csr": M = M.tocsr()
                M.data, M.indices, M.indptr = Transforms.Quantize(M.data), Transforms.Quantize(M.indices), Transforms.Quantize(M.indptr)
                return M
            case V if type(V) in (int, float, bool, str, bytes, type(None)): return V
            case dict() as D: return {K: Transforms.Quantize(V) for K, V in D.items()}
            case (Data, tuple() as Shape) if Shape and isinstance(Shape[0], (int, numpy.integer)): return Transforms.Quantize(Data).reshape(Shape)
            case tuple() | list() as G:
                if not G: return ()
                if (T := type(G[0])) is tuple or T is list:
                    try: return Transforms.Quantize(numpy.asarray(G))
                    except ValueError: return Transforms.Quantize(numpy.asarray(tuple(itertools.chain.from_iterable(G))))
                return Transforms.Quantize(numpy.asarray(G))
            case _: raise TypeError(f"[UNSUPPORTED QUANTIZABLE TYPE] Type: {type(Data)} | Value: {Data}")

    # -------- Encoding ------- #
    def Encode(self, *Args):
        for Data in Args:
            match Data:
                case str() as TK, str() as C, V: Target = ((TK, C, V.keys() if type(V) is dict else V),)
                case dict() as D: Target = tuple((TK, C, V.keys() if type(V) is dict else V) for TK, CL in D.items() for C, V in CL.items() if type(V) not in (scipy.sparse.coo_array, numpy.ndarray))
                case _: Target = ()

            for TK, C, V in Target:
                if (Q := Transforms.Quantize(V)).dtype.kind in ("S", "U"):
                    RV, FW = numpy.unique(Q, return_inverse=True)
                    self._Encodings.setdefault(TK, {})[C] = {"Forward": Transforms.Quantize(FW), "Reverse": RV}

        # -------- Foreign Key Mappings -------- #
        for TK, (_, PK, FK) in Configuration["FS"].items():
            if PK and FK and (E1 := self._Encodings.get(TK)) and (MR := E1.get(PK, {}).get("Reverse")) is not None:
                for DT, DCs in FK.items():
                    if ED := self._Encodings.get(DT):
                        for C in ([DCs] if type(DCs) is str else DCs):
                            if (E := ED.get(C)) and "Reverse" in E: E["Forward"] = Transforms.Quantize(numpy.searchsorted(MR, E.pop("Reverse"))[E["Forward"]])

    # -------- Window ------- #
    def Window(self, *Data):
        L, H, CS = (C := Configuration["Analytics"])["Lookback"], C["Horizon"], C["Chunk"]
        for W in range(0, Data[0].shape[0] - L - H, CS): yield tuple(torch.from_numpy(A[(W if not IX else W + L):(W if not IX else W + L) + min(CS, Data[0].shape[0] - W - L - H) + (S := L if not IX else H) - 1, :, :]).unfold(0, S, 1).permute(1, 0, 2, 3).reshape(-1, S * A.shape[-1]) for IX, A in enumerate(Data))

    # -------- Session -------- #
    @staticmethod
    def Session(Payload, Framework, Device, Provider):
        SO = onnxruntime.SessionOptions(); SO.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL; SO.enable_cpu_mem_arena = SO.enable_mem_pattern = True; SO.log_severity_level = 3
        match Framework, Device:
            case ("openvino", D): return onnxruntime.InferenceSession(Payload, sess_options=SO, providers=[Provider], provider_options=[{"device_type": str(D).upper()}])
            case ("onnx", "directml"): return onnxruntime.InferenceSession(Payload, sess_options=SO, providers=[Provider], provider_options=[{"device_id": "0"}])
            case ("torch", "cuda") | ("onnx", "cuda"): return onnxruntime.InferenceSession(Payload, sess_options=SO, providers=[Provider], provider_options=[{"device_id": "0", "arena_extend_strategy": "kNextPowerOfTwo"}])
            case ("onnx", "tensorrt"): return onnxruntime.InferenceSession(Payload, sess_options=SO, providers=[Provider], provider_options=[{"trt_engine_cache_enable": "1"}])
            case ("qnn", "npu"): return onnxruntime.InferenceSession(Payload, sess_options=SO, providers=[Provider], provider_options=[{"backend_path": "QnnHtp.dll" if os.name == "nt" else "libQnnHtp.so"}])
            case _: return onnxruntime.InferenceSession(Payload, sess_options=SO, providers=[Provider])

    # -------- Nullify -------- #
    @staticmethod
    @contextlib.contextmanager
    def Nullify():
        FD = E = 0
        try: sys.stderr.flush(); FD = os.dup(E := sys.stderr.fileno()); os.dup2(DN := os.open(os.devnull, os.O_WRONLY), E); os.close(DN); yield
        finally: sys.stderr.flush(); os.dup2(FD, E); os.close(FD)

# -------- Summary -------- #
class Summary:
    __slots__ = ("Data",)
    def __init__(self, Data: dict): self.Data = Data
    def __str__(self): return f"[{' | '.join(f'{K} [{V[0]}R ⨯ {V[1]}C]' if type(V) is tuple else f'{K} [{(S := V.shape)[0]}R ⨯ {S[1] if len(S) > 1 else 1}C]' if hasattr(V, 'shape') else f'{K} [{len(V)}R ⨯ 1C]' for K, V in self.Data.items())}]"
    def __repr__(self): return self.__str__()
