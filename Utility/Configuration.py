Configuration = {
    "ETL": {
        "Events": [
            {"Name": "Republic Day", "Zone": "NR", "Weeks": [5], "Impact": { "PAX": [1.05, 1.15], "FGT": [0.98, 1.02]}},
            {"Name": "Pongal", "Zone": "SR", "Weeks": [3, 4], "Impact": { "PAX": [1.05, 1.15], "FGT": [1.02, 1.08]}},
            {"Name": "Eid", "Zone": "NR", "Weeks": [15], "Impact": { "PAX": [1.10, 1.25], "FGT": [0.98, 1.02]}},
            {"Name": "Rath Yatra", "Zone": "ER", "Weeks": [27, 28], "Impact": { "PAX": [1.10, 1.25], "FGT": [0.98, 1.02]}},
            {"Name": "Ganesh Chaturthi", "Zone": "CR", "Weeks": [36, 37], "Impact": { "PAX": [1.10, 1.30], "FGT": [1.00, 1.05]}},
            {"Name": "Navratri", "Zone": "NR", "Weeks": [39, 40, 41], "Impact": { "PAX": [1.05, 1.25], "FGT": [0.98, 1.02]}},
            {"Name": "Durga Puja", "Zone": "ER", "Weeks": [40, 41], "Impact": { "PAX": [1.20, 1.35], "FGT": [1.00, 1.05]}},
            {"Name": "Diwali", "Zone": "NR", "Weeks": [44, 45], "Impact": { "PAX": [1.30, 1.45], "FGT": [1.05, 1.15]}},
            {"Name": "Chhath Puja", "Zone": "ER", "Weeks": [45, 46], "Impact": { "PAX": [1.15, 1.30], "FGT": [1.00, 1.05]}},
            {"Name": "Christmas", "Zone": "ALL", "Weeks": [51, 52], "Impact": { "PAX": [1.15, 1.25], "FGT": [1.00, 1.05]}},
            {"Name": "New Year", "Zone": "ALL", "Weeks": [52], "Impact": { "PAX": [1.20, 1.35], "FGT": [1.00, 1.05]}},
            {"Name": "Summer Travel Peak", "Zone": "ALL", "Weeks": [18, 19, 20, 21, 22], "Impact": { "PAX": [1.15, 1.25], "FGT": [1.00, 1.03]}},
            {"Name": "Monsoon Travel Dip", "Zone": "ALL", "Weeks": [27, 28, 29, 30], "Impact": { "PAX": [0.90, 0.98], "FGT": [0.95, 1.00]}}
        ],

        "Trains": {
            "RakeCompositions": {
                "Rajdhani": {"1A":[2], "2A":[4, 6], "3A":[8, 10], "EOG":[2], "PC":[2]},
                "Duronto": {"1A":[1, 2], "2A":[3, 4], "3A":[6, 8], "EOG":[2], "GEN":[1], "SL":[12, 14]},
                "Shatabdi": {"CC":[12, 14, 16], "EC":[2, 4], "EOG":[1], "GS":[2]},
                "Jan Shatabdi": {"CC":[10, 12, 14], "EC":[1, 2], "EOG":[1], "PC":[1], "2S":[4, 6]},
                "Garib Rath": {"CC":[12, 14, 16], "EOG":[1], "3E":[8, 10]},
                "Intercity": {"2S":[4, 6], "CC":[6, 8, 10], "EOG":[1], "GS":[4, 6, 8]},
                "Mail": {"2A":[1], "3A":[1, 2], "EOG":[1, 2], "GEN":[4, 6], "SL":[6, 8, 10]},
                "Express": {"2A":[1, 2], "3A":[2, 3], "EOG":[1, 2], "GEN":[2, 3, 4], "SL":[8, 10, 12]},
                "Superfast": {"2A":[2, 3], "3A":[4, 6], "EOG":[2], "GEN":[1, 2], "SL":[10, 12, 14]},
                "MEMU": {"EOG":[1], "GS":[12, 14, 16]},

                "BCAL": {"BCAL":[20, 25, 30], "BOBE-AL":[8, 10], "BOXN-25":[10, 12], "BOSTH":[12, 15]},
                "BCN": {"BCACNHL":[10, 12], "BCN":[25, 30, 35], "BOXN-25":[8, 10], "BOSTH":[10, 12]},
                "BCNA": {"BCACN":[12, 15], "BCNA":[20, 25], "BOXN-25":[10, 12], "BOSTH":[8, 10]},
                "BCNHL": {"BCNHL":[15, 20], "BOXNAL":[12, 15], "BOXNCR":[10, 12], "BOY-25":[10, 12]},
                "BOBSN": {"BOBE-AL":[10, 12], "BOBSN-25":[20, 25, 30], "BOXN-25":[8, 10], "BOXNCR":[12, 15]},
                "BOBYN": {"BCACN":[10, 12], "BCNAG":[12, 15], "BOXNAL":[10, 12], "BOBYN":[25, 30, 35]},
                "BOXN": {"BOXN":[40, 50, 60], "BOXNAL":[10, 15], "BOXNLW":[10, 15], "BOXNCR":[10, 15]},
                "BOXNAL": {"BCAL":[15, 20], "BOXNAL":[25, 30], "BOXNCR":[12, 15], "BOY-25":[10, 12]},
                "BOXNCR": {"BCAL":[12, 15], "BOX":[15, 20], "BOBE-AL":[10, 12], "BOXNCR":[25, 30, 35]}
            },

            "DemandFactor": {
                "Shatabdi": 600, "Intercity": 700, "Rajdhani": 800, "Jan Shatabdi": 900, "Garib Rath": 1000, "Mail": 1000, "Duronto": 1100, "Express": 1200, "Superfast": 1400, "MEMU": 500, 
                "BCAL": 2000, "BCN": 2000, "BCNA": 2000, "BCNHL": 2000, "BOBSN": 2000, "BOBYN": 2000, "BOXN": 2200, "BOXNAL": 2100, "BOXNCR": 2100
            }
        },
        "StationCategory": {"A1": { "DCM": 1.55 }, "A":  { "DCM": 1.35 }, "B":  { "DCM": 1.15 }, "C":  { "DCM": 0.95 }, "D":  { "DCM": 0.75 }, "E":  { "DCM": 0.55 }},
        "WriterThreads": 6,

        "YearVariation": {
            "BaseYear": 2006, "DemandGrowth": {"PAX": 0.04, "FGT": 0.03},
            "DelayProfile": [{"Until": 2010, "Mean": 4.4, "Sigma": 1.1}, {"Until": 2015, "Mean": 4.2, "Sigma": 1.0}, {"Until": 2020, "Mean": 4.0, "Sigma": 0.9}, {"Until": 2026, "Mean": 3.7, "Sigma": 0.7}],
            "EventScale": [{"Until": 2010, "Scale": 1.00}, {"Until": 2018, "Scale": 1.10}, {"Until": 2026, "Scale": 1.20}]
        },
    },

    "ML": {
        "Targets": ["EffectiveLoad", "Delay"],
        "Features": ["TrainIndex", "TimeIndex", "Week", "Distance", "Gradient", "Priority", "LoadUtilization", "GradientLoad", "WeekSin", "WeekCos"]
    },

    "Files": {
        "Trains": {"Path": "Data/Statics/Trains.json", "PK": "TrainNumber"},
        "Zones": {"Path": "Data/Statics/Zones.json", "PK": "ZoneCode"},
        "Models": {"Directory": "./.Cache/Models"},
        "Parquets": {"Directory": "./.Cache/Parquets"},
        "NN": {"Directory": "./.Cache/NN"}
    }
}
