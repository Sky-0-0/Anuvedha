import os, sys, types, math, pandas, numpy, logging
from rich.progress import Progress, BarColumn, ProgressColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from rich.text import Text
from rich.traceback import install

install(show_locals = False)

# ---- Level Map ---- #
_Levels = {"Trace": logging.DEBUG, "Event": logging.INFO, "Metrics": logging.INFO, "Warn": logging.WARNING, "Exception": logging.ERROR,}

# ---- Logger ---- #
class Logger:
    os.makedirs("Logs", exist_ok = True)
    _Console = None

    # ---------- Stringify ---------- #
    @staticmethod
    def Stringify(Value, MaxDepth = 10, _CD = 0, _V = None):
        # ---- Recursion State ----
        if _V is None: _V = frozenset()
        if _CD > MaxDepth: return "<MaxDepthReached>"

        # ---- Circular Detection ----
        if isinstance(Value, (dict, list, tuple, set, pandas.Series)):
            if id(Value) in _V: return "<CircularReference>"
            _V = _V | {id(Value)}

        # ---- Primitive Types ----
        if isinstance(Value, (types.FunctionType, types.MethodType)): return f"<Function {Value.__name__}>"
        if isinstance(Value, pandas.DataFrame): return f"<DataFrame Shape = {Value.shape}>"
        if isinstance(Value, (int, numpy.integer)): return str(int(Value))

        if isinstance(Value, pandas.Series): return ("[" + ", ".join(Logger.Stringify(V, MaxDepth, _CD + 1, _V) for V in Value) + "]")
        if isinstance(Value, dict): return ("{" + ", ".join(f"{Logger.Stringify(K, MaxDepth, _CD + 1, _V)}: {Logger.Stringify(V, MaxDepth, _CD + 1, _V)}" for K, V in sorted(Value.items(), key = lambda Item: str(Item[0]))) + "}")
        if isinstance(Value, set): return ("[" + ", ".join(Logger.Stringify(V, MaxDepth, _CD + 1, _V) for V in sorted(Value, key = str)) + "]")
        if isinstance(Value, (list, tuple)): return ("[" + ", ".join(Logger.Stringify(V, MaxDepth, _CD + 1, _V) for V in Value) + "]")
        if isinstance(Value, (float, numpy.floating)):
            if math.isnan(Value) or math.isinf(Value): return "NaN"
            return f"{Value:.2f}"

        return str(Value)

    # ---------- Loader ---------- #
    class _SpeedColumn(ProgressColumn):
        def render(self, Task) -> Text: return Text(f"{Task.speed:.0f} E/s" if Task.speed else "-- E/s", style = "cyan")

    @staticmethod
    def Loader(Total: int, Description: str):
        if Logger._Console is None: Logger._Console = Console()
        ProgressI = Progress(TextColumn("{task.description}"), BarColumn(), TextColumn("{task.completed}/{task.total}"), TextColumn("{task.percentage:>3.0f}%"), Logger._SpeedColumn(), TimeRemainingColumn(), console = Logger._Console)

        class Context:
            def __init__(self, PI): self._PI = PI
            def __enter__(self):
                self._PI.__enter__()
                self._Task = self._PI.add_task(Description, total = Total)
                return self
            def __exit__(self, ExcType, ExcVal, ExcTb): return self._PI.__exit__(ExcType, ExcVal, ExcTb)
            def Advance(self, Amount = 1): self._PI.update(self._Task, advance = Amount)
            def Update(self, **Kwargs): self._PI.update(self._Task, **Kwargs)

        return Context(ProgressI)

    # ---------- Proxy ---------- #
    class Proxy:
        def __init__(self, Module: str):
            self.Module = Module
            self._Cache = {}
            LogPath = os.path.join("Logs", f"{Module}.log")

            with open(LogPath, "w", encoding = "utf-8"): pass

            if Logger._Console is None: Logger._Console = Console()

            self.Logger = logging.getLogger(Module)
            self.Logger.handlers.clear()
            self.Logger.setLevel(logging.DEBUG)
            self.Logger.propagate = False

            Formatter = logging.Formatter("%(asctime)s - [%(levelname)s] [%(name)s] %(message)s", datefmt = "%d/%m/%Y %H:%M:%S")

            FH = logging.FileHandler(LogPath, mode="a", encoding="utf-8")
            FH.setFormatter(Formatter)
            self.Logger.addHandler(FH)

            CH = logging.StreamHandler(sys.stdout)
            CH.setFormatter(Formatter)
            self.Logger.addHandler(CH)

        def __getattr__(self, Level: str):
            if Level not in _Levels: raise AttributeError(Level)
            if Level in self._Cache: return self._Cache[Level]

            def LogMethod(Message, *Args):
                try: FormattedMessage = Message % tuple(Logger.Stringify(A) for A in Args) if Args else str(Message)
                except Exception: FormattedMessage = str(Message)
                Record = self.Logger.makeRecord(self.Logger.name, _Levels[Level], "[Unknown]", 0, FormattedMessage, [], None)
                Record._CustomLevel = Level
                self.Logger.handle(Record)

            self._Cache[Level] = LogMethod
            return LogMethod

    @classmethod
    def RegisterModule(cls, Module: str): return cls.Proxy(Module)