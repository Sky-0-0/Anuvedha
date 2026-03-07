import os, datetime, time, numpy, orjson
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv
from threading import Thread, Event, Lock
from queue import Queue
from Utility import Configuration, Logger

# -------- ETL Pipeline -------- #
class ETL:
    def __init__(self):
        load_dotenv()
        self._Log = Logger.Proxy("ETL")
        self._RNG = numpy.random.default_rng(555)
        self._Client = MongoClient(os.getenv("MongoUri"), w = 0)
        self._History = self._Client["Stratum"]["History"]
        self._Trains = self._Client["Stratum"]["Trains"]

        # -------- Indexes -------- #
        for Name, File in Configuration["Files"].items():
            if Name not in ["Models", "History"] and "PK" in File and File["PK"] not in self._Client["Stratum"][Name].index_information():
                self._Client["Stratum"][Name].create_index(File["PK"], unique = True)

        # (TrainNumber, Year) is the new document identity — one doc per train per year
        if "TrainNumber_1_Year_1" not in self._History.index_information(): self._History.create_index([("TrainNumber", 1), ("Year", 1)], unique = True)
        if "Category_1" not in self._History.index_information(): self._History.create_index("Category")
        if "Zone_1" not in self._History.index_information(): self._History.create_index("Zone")

        # -------- Static Data -------- #
        StaticData = {Name: orjson.loads(open(File["Path"], "rb").read()) for Name, File in Configuration["Files"].items() if "Path" in File and "PK" in File}
        ZoneLookup = {St["Code"]: Z["ZoneCode"] for Z in StaticData["Zones"] for D in Z["Divisions"] for St in D["Stations"]}

        # -------- Station Validation -------- #
        if Unmapped := {S for Train in StaticData["Trains"] for S in Train["Route"]["Path"] if S not in ZoneLookup}:
            self._Log.Event("Station Validation Failed | [%s] stations unmapped: %s", len(Unmapped), Unmapped)
            raise SystemExit(1)
        self._Log.Event("Station Validation Passed | All stations mapped")

        # -------- Precompute Train Features -------- #
        self._TrainFeatures = [{
            "TrainNumber": Train["TrainNumber"], "Category": Train["Category"], "Type": Train["Type"], "Priority": Train["Priority"],
            "Zone": ZoneLookup[Train["Route"]["Path"][0]], "Frequency": 7 if Train["Frequency"] == ["Daily"] else len(Train["Frequency"]),
            "Rake": [numpy.array(Rake[W], dtype = numpy.int32) for W in ValidWagons], "SegmentCount": len(Train["Route"]["Segments"]),
            "Wagons": numpy.array([C if (C := Train["Rake"][W].get("Capacity")) else 0 for W in ValidWagons], dtype = numpy.float64)}
            for Train in StaticData["Trains"]
            for Rake in [Configuration["ETL"]["Trains"]["RakeCompositions"][Train["Type"]]]
            for ValidWagons in [[W for W in Rake if W in Train["Rake"]]]]

        # -------- Vectorised Generation Arrays -------- #
        self._TrainCount = len(self._TrainFeatures)
        self._Frequencies = numpy.array([T["Frequency"] for T in self._TrainFeatures], dtype = numpy.int32)
        self._SegmentCounts = numpy.array([T["SegmentCount"] for T in self._TrainFeatures], dtype = numpy.int32)
        self._MaxSegments = int(self._SegmentCounts.max())

        # -------- Precompute Year Variation Curves -------- #
        self._YearCurves = {
            Year: {
                "DemandScale": {
                    "PAX": (1 + Configuration["ETL"]["YearVariation"]["DemandGrowth"]["PAX"]) ** (Year - Configuration["ETL"]["YearVariation"]["BaseYear"]),
                    "FGT": (1 + Configuration["ETL"]["YearVariation"]["DemandGrowth"]["FGT"]) ** (Year - Configuration["ETL"]["YearVariation"]["BaseYear"]),
                },
                "DelayMean":  next(P for P in Configuration["ETL"]["YearVariation"]["DelayProfile"] if Year < P["Until"])["Mean"],
                "DelaySigma": next(P for P in Configuration["ETL"]["YearVariation"]["DelayProfile"] if Year < P["Until"])["Sigma"],
                "EventScale": next(S["Scale"] for S in Configuration["ETL"]["YearVariation"]["EventScale"] if Year < S["Until"]),
            }
            for Year in range(2006, 2026)
        }

        self._Log.Metrics("Loaded [%s] Zones | [%s] Trains", len(StaticData["Zones"]), self._TrainCount)

    # -------- Purge: drop all collections for a fresh run -------- #
    def Purge(self):
        Dropped = ["History"] + [f"{N}" for N, M in Configuration["Files"].items() if "PK" in M and N not in ["Models", "History"]]
        self._History.drop()
        [self._Client["Stratum"][N].drop() for N, M in Configuration["Files"].items() if "PK" in M and N not in ["Models", "History"]]
        self._Log.Event("Purged %s", Dropped)

    # -------- Writer (Consumer) -------- #
    def _Writer(self, WriteQueue, Results, WriteLoader, WriteDone, Mutex, Counter):
        Batch, BatchStart = 1, time.time()
        while (Buffer := WriteQueue.get()) is not None:
            self._History.bulk_write([UpdateOne({"TrainNumber": Doc["TrainNumber"], "Year": Doc["Year"]}, {"$set": Doc}, upsert = True) for Doc in Buffer], ordered = False)
            Results.append((Batch, len(Buffer), round(time.time() - BatchStart, 2)))
            WriteLoader.Advance(len(Buffer))
            Batch += 1; BatchStart = time.time()
        with Mutex:
            Counter[0] -= 1
            if Counter[0] == 0: WriteDone.set()

    # -------- Run (Producer) -------- #
    def Run(self):
        self.Purge()
        self._Log.Event("Generating + Writing Train Histories...")
        StartTime = time.time()
        TotalRecords = self._TrainCount * 20
        WriteQueue = Queue(maxsize = Configuration["ETL"].get("WriterThreads", 6) * 2)
        Results = []
        WriteDone = Event()
        Mutex = Lock()
        Counter = [Configuration["ETL"].get("WriterThreads", 6)]

        Inserted = [N for N, M in Configuration["Files"].items() if "Path" in M and "PK" in M and self._Client["Stratum"][N].count_documents({}) == 0 and not self._Client["Stratum"][N].insert_many(orjson.loads(open(M["Path"], "rb").read()))]
        if Inserted: self._Log.Event("Inserted %s", Inserted)

        with Logger.Loader(TotalRecords, "[gold]Generating...") as GenLoader, Logger.Loader(TotalRecords, "[cyan]Writing...  ") as WriteLoader:
            for _ in range(Configuration["ETL"].get("WriterThreads", 6)):
                Thread(target = self._Writer, args=(WriteQueue, Results, WriteLoader, WriteDone, Mutex, Counter), daemon = True).start()
            Buffer = []

            try:
                for Year in range(2006, 2026):
                    Curve = self._YearCurves[Year]
                    WeekCount = datetime.date(Year, 12, 28).isocalendar()[1]

                    # ---- Vectorised RNG: all weeks for this year at once ---- #
                    DemandNoise = self._RNG.uniform(0.85, 1.1, size=(WeekCount, self._TrainCount))
                    CancelProbs = self._RNG.binomial(numpy.tile(self._Frequencies, (WeekCount, 1)), 0.18)
                    AllDelays = self._RNG.lognormal(Curve["DelayMean"], Curve["DelaySigma"], size=(WeekCount, int(self._SegmentCounts.sum())))
                    PAXLoadIn = self._RNG.uniform(0.05, 0.25, size=(WeekCount, self._TrainCount, self._MaxSegments))
                    PAXLoadOut = self._RNG.uniform(0.05, 0.20, size=(WeekCount, self._TrainCount, self._MaxSegments))
                    FRTLoadIn = self._RNG.uniform(0.02, 0.15, size=(WeekCount, self._TrainCount, self._MaxSegments))
                    FRTLoadOut = self._RNG.uniform(0.02, 0.10, size=(WeekCount, self._TrainCount, self._MaxSegments))

                    for Index, Train in enumerate(self._TrainFeatures):
                        Weeks = []
                        for W in range(WeekCount):
                            Capacity = int(numpy.dot([int(self._RNG.choice(Opts)) for Opts, Cap in zip(Train["Rake"], Train["Wagons"]) if Cap], [Cap for Cap in Train["Wagons"] if Cap]))
                            EventImpact = numpy.prod([
                                self._RNG.uniform(E["Impact"][Train["Category"]][0] * Curve["EventScale"], E["Impact"][Train["Category"]][1] * Curve["EventScale"]) for E in Configuration["ETL"]["Events"] if (W + 1) in E["Weeks"] and E["Zone"] in ("ALL", Train["Zone"])
                            ]) if any((W + 1) in E["Weeks"] and E["Zone"] in ("ALL", Train["Zone"]) for E in Configuration["ETL"]["Events"]) else 1.0

                            CurrentLoad = min(Capacity, int(Capacity * Configuration["ETL"]["Trains"]["DemandFactor"][Train["Type"]] / 1000 * Curve["DemandScale"][Train["Category"]] * EventImpact * DemandNoise[W, Index]))

                            SegOffset = int(self._SegmentCounts[:Index].sum())
                            AccumDelays = numpy.minimum(numpy.cumsum(AllDelays[W, SegOffset:SegOffset + Train["SegmentCount"]].clip(0, 120) * 0.15) + AllDelays[W, SegOffset:SegOffset + Train["SegmentCount"]].clip(0, 120), 180.0)

                            Segments = []
                            for SegIdx in range(Train["SegmentCount"]):
                                TotalLoad = round(min(CurrentLoad - (PAXLoadIn if Train["Category"] == "PAX" else FRTLoadIn)[W, Index, SegIdx] * CurrentLoad + (PAXLoadOut if Train["Category"] == "PAX" else FRTLoadOut)[W, Index, SegIdx] * (Capacity - CurrentLoad), Capacity))
                                CurrentLoad = TotalLoad - (int(self._RNG.binomial(int(TotalLoad), 0.05)) if Train["Category"] == "PAX" else round(TotalLoad * 0.05))
                                Segments.append({"EffectiveLoad": CurrentLoad, "Delay": round(float(AccumDelays[SegIdx]), 2)})

                            Weeks.append({"Week": W + 1, "Capacity": Capacity, "Reliability": round(1 - (CancelProbs[W, Index] / Train["Frequency"]), 4), "Segments": Segments})

                        Buffer.append({"TrainNumber": Train["TrainNumber"], "Year": Year, "Category": Train["Category"], "Type": Train["Type"], "Zone": Train["Zone"], "Priority": Train["Priority"], "Weeks": Weeks})
                        GenLoader.Advance()

                        if len(Buffer) >= 1000:
                            WriteQueue.put(Buffer)
                            Buffer = []

            except KeyboardInterrupt: self._Log.Event("ETL Interrupted — flushing [%s] remaining records...", len(Buffer))

            finally:
                if Buffer: WriteQueue.put(Buffer)
                for _ in range(Configuration["ETL"].get("WriterThreads", 6)): WriteQueue.put(None)
                WriteDone.wait()

        for Batch, Count, Elapsed in Results: self._Log.Metrics("Batch [%s] → [%s] records | [%s s]", Batch, Count, Elapsed)
        self._Log.Event("Completed [%s] records in [%s s]", TotalRecords, round(time.time() - StartTime, 2))

if __name__ == "__main__": ETL().Run()