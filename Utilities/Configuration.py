Configuration = {
    "Simulation": {
        "Seed": 555, "SimulationWindow": (2021, 2026),

        # Sorted: Engines [Alphabetical by Class] [WAG12B, WAG7, WAG9, WAP5, WAP7, WDG4G] | Elements: [RoadSeries]
        "Engines": (60001, 27001, 31001, 30001, 45001, 12001),

        # Sorted: Segments [Alphabetical by Group] [A, B, C, D-Spl, D, E] | Elements: [SpeedLimit]
        "Segments": (160, 130, 100, 110, 100, 80),

        # Sorted: Stations [Alphabetical by Category] [HG-1, HG-2, HG-3, NSG-1, NSG-2, NSG-3, NSG-4, NSG-5, NSG-6, SG-1, SG-2, SG-3] | | Elements: [LoopLines]
        "Stations": (0, 0, 0, 8, 6, 5, 4, 3, 2, 4, 3, 2),

        # Sorted: Wagons [Alphabetical by Design] [BCACBM, BCN, BLC, BOXN, BOXNHL, BRN, BTPN, BVM, EMU, ICF, LHB, VB16] | Elements: [Length, MPS, Axles, MaxAxleLoad, TareWeightAC, TareWeightNAC, HotelLoadAC, HotelLoadCC, HotelLoadNAC]
        "Wagons": ((23.55, 95, 4, 12.80, 35.70, 35.70, 0, 0, 0), (15.10, 100, 4, 20.32, 25.54, 25.54, 0, 0, 0), (13.62, 100, 4, 20.32, 19.10, 19.10, 0, 0, 0), (10.71, 100, 4, 20.32, 22.50, 22.50, 0, 0, 0), (10.96, 100, 4, 22.90, 20.60, 20.60, 0, 0, 0), (14.64, 100, 4, 20.32, 23.50, 23.50, 0, 0, 0),
            (12.42, 80, 4, 20.32, 23.40, 23.40, 0, 0, 0), (14.00, 100, 4, 16.00, 23.90, 23.90, 0, 0, 0), (20.92, 105, 4, 16.00, 60.00, 33.60, 0, 0, 0), (22.28, 110, 4, 16.25, 45.00, 43.00, -50, -15, 0), (24.00, 160, 4, 16.25, 42.00, 39.00, -50, -50, 0), (23.00, 160, 4, 17.00, 45.00, 45.00, -50, -45, -80)),

        # Sorted: TrainTypes [Alphabetically by Train Type] # ["AC EXPRESS", "AC SUPERFAST", "AMRIT BHARAT", "ANTYODAYA", "AUTO CARRIER", "CEMENT COVERED RAKE", "COAL OPEN RAKE", "DEMU", "DOUBLE DECKER", "DOUBLE STACK CONTAINER", "DURONTO", "EMU", "FERTILIZER COVERED RAKE", "FOOD GRAIN COVERED RAKE", "GARIB RATH", "HOPPER RAKE", "HUMSAFAR", "HYDERABAD SUBURBAN", "IRON ORE RAKE", "JAN SHATABDI", "MAIL", "MEMU", "PARCEL VAN", "PASSENGER", "PETROLEUM TANKER", "RAJDHANI", "SAMPARK KRANTI", "SHATABDI", "STANDARD CONTAINER", "STEEL COIL FLATBED", "SUPERFAST", "TEJAS", "TIME TABLED PARCEL EXPRESS", "VANDE BHARAT"]
        "EngineMappings": {
            "NominatedPower": ("WAP7", "WAP7", "WAP7", "WAP7", "WDG4G", "WAG7", "WAG12B", "", "WAP7", "WAG12B", "WAP7", "", "WAG9", "WAG7", "WAP7", "WAG12B", "WAP7", "", "WAG12B", "WAP7", "WAP7", "", "WAP7", "WAP7", "WAG9", "WAP7", "WAP7", "WAP5", "WAG9", "WAG9", "WAP7", "WAP5", "WAP7", ""),
            "TractionCount": (1, 1, 2, 1, 1, 1, 2, 0, 1, 2, 1, 0, 1, 1, 1, 2, 1, 0, 2, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0)},

        "Services": {
            # Sorted: ServiceNames [Alphabetically by Service Name]
            "Names": ("FreightAgriculturalBulk", "FreightAutomobile", "FreightDepartmental", "FreightIndustrialBulk", "FreightIndustrialMetals", "FreightIntermodal", "FreightMineralBulk", "FreightParcelSpecial", "FreightPetroleumTanker", "FreightRollOnRollOff", "HillRailway", "LocalPassenger", "MailExpress", "PremiumExpress", "StrategicMilitary", "Suburban"),
            # Sorted: Priorites [Alphabetically by Service-nName] [FreightAgriculturalBulk, FreightAutomobile, FreightDepartmental, FreightIndustrialBulk, FreightIndustrialMetals, FreightIntermodal, FreightMineralBulk, FreightParcelSpecial, FreightPetroleumTanker, FreightRollOnRollOff, HillRailway, LocalPassenger, MailExpress, PremiumExpress, StrategicMilitary, Suburban]
            "Priorites": (5, 4, 7, 5, 5, 3, 5, 3, 6, 6, 6, 5, 1, 0, 6, 4),
            # Sorted: EngineLoad [Alphabetically by ServicemName] [FreightAgriculturalBulk, FreightAutomobile, FreightDepartmental, FreightIndustrialBulk, FreightIndustrialMetals, FreightIntermodal, FreightMineralBulk, FreightParcelSpecial, FreightPetroleumTanker, FreightRollOnRollOff, HillRailway, LocalPassenger, MailExpress, PremiumExpress, StrategicMilitary, Suburban]
            "EngineServices": ("F", "F", "M", "F", "F", "F", "F", "M", "F", "F", "M", "P", "P", "P", "M", "M"),
            # Sorted: TrainTypes [Alphabetically by Train Type] # ["AC EXPRESS", "AC SUPERFAST", "AMRIT BHARAT", "ANTYODAYA", "AUTO CARRIER", "CEMENT COVERED RAKE", "COAL OPEN RAKE", "DEMU", "DOUBLE DECKER", "DOUBLE STACK CONTAINER", "DURONTO", "EMU", "FERTILIZER COVERED RAKE", "FOOD GRAIN COVERED RAKE", "GARIB RATH", "HOPPER RAKE", "HUMSAFAR", "HYDERABAD SUBURBAN", "IRON ORE RAKE", "JAN SHATABDI", "MAIL", "MEMU", "PARCEL VAN", "PASSENGER", "PETROLEUM TANKER", "RAJDHANI", "SAMPARK KRANTI", "SHATABDI", "STANDARD CONTAINER", "STEEL COIL FLATBED", "SUPERFAST", "TEJAS", "TIME TABLED PARCEL EXPRESS", "VANDE BHARAT"]
            "TrainServices": ("MailExpress", "MailExpress", "MailExpress", "LocalPassenger", "FreightAutomobile", "FreightIndustrialBulk", "FreightMineralBulk", "LocalPassenger", "MailExpress", "FreightIntermodal", "PremiumExpress", "Suburban", "FreightIndustrialBulk", "FreightAgriculturalBulk", "MailExpress", "FreightMineralBulk", "MailExpress", "Suburban", "FreightMineralBulk", "MailExpress", "MailExpress", "Suburban", "FreightParcelSpecial", "LocalPassenger", "FreightPetroleumTanker", "PremiumExpress", "MailExpress", "PremiumExpress", "FreightIntermodal", "FreightIndustrialMetals", "MailExpress", "PremiumExpress", "FreightParcelSpecial", "PremiumExpress"),
            # Sorted: TrainTypes [Alphabetically by Train Type]
            "TrainTypes": ("AC EXPRESS", "AC SUPERFAST", "AMRIT BHARAT", "ANTYODAYA", "AUTO CARRIER", "CEMENT COVERED RAKE", "COAL OPEN RAKE", "DEMU", "DOUBLE DECKER", "DOUBLE STACK CONTAINER", "DURONTO", "EMU", "FERTILIZER COVERED RAKE", "FOOD GRAIN COVERED RAKE", "GARIB RATH", "HOPPER RAKE", "HUMSAFAR", "HYDERABAD SUBURBAN", "IRON ORE RAKE", "JAN SHATABDI", "MAIL", "MEMU", "PARCEL VAN", "PASSENGER", "PETROLEUM TANKER", "RAJDHANI", "SAMPARK KRANTI", "SHATABDI", "STANDARD CONTAINER", "STEEL COIL FLATBED", "SUPERFAST", "TEJAS", "TIME TABLED PARCEL EXPRESS", "VANDE BHARAT")},

        "Market": {
            "Traffic": {
                # Sorted: Stations [Alphabetical by Category] [HG-1, HG-2, HG-3, NSG-1, NSG-2, NSG-3, NSG-4, NSG-5, NSG-6, SG-1, SG-2, SG-3] | Elements: [Min Multiplier, Max Multiplier]
                "Stations": ((0.35, 0.65), (0.20, 0.40), (0.08, 0.22), (2.10, 2.90), (1.70, 2.30), (1.35, 1.85), (1.10, 1.50), (0.80, 1.20), (0.60, 0.90), (1.50, 2.10), (1.15, 1.65), (0.70, 1.10)),
                # Sorted: TrainTypes [Alphabetically by Train Type] [AC EXPRESS, AC SUPERFAST, AMRIT BHARAT, ANTYODAYA, AUTO CARRIER, CEMENT COVERED RAKE, COAL OPEN RAKE, DEMU, DOUBLE DECKER, DOUBLE STACK CONTAINER, DURONTO, EMU, FERTILIZER COVERED RAKE, Food Grain Covered Rake, GARIB RATH, Hopper Rake, HUMSAFAR, HYDERABAD SUBURBAN, Iron Ore Rake, Jan Shatabdi, Mail, MEMU, Parcel Van, Passenger, Petroleum Tanker, Rajdhani, Sampark Kranti, Shatabdi, Standard Container, Steel Coil Flatbed, SuperFast, Tejas, Time Tabled Parcel Express, Vande Bharat]
                "Trains": ((0.65, 0.90), (0.68, 0.92), (0.72, 0.95), (0.75, 0.98), (0.70, 0.95), (0.88, 1.00), (0.90, 1.00), (0.55, 0.80), (0.70, 0.92), (0.88, 1.00), (0.72, 0.95), (0.60, 0.85), (0.88, 1.00), (0.88, 1.00), (0.72, 0.95), (0.88, 1.00), (0.72, 0.95), (0.60, 0.85), (0.92, 1.00), (0.68, 0.90), (0.65, 0.88), (0.58, 0.82), (0.70, 0.95), (0.62, 0.85), (0.90, 1.00), (0.75, 0.95), (0.70, 0.92), (0.72, 0.95), (0.85, 1.00), (0.88, 1.00), (0.68, 0.90), (0.75, 0.95), (0.72, 0.95), (0.75, 0.95)),
                # Sorted: Wagons [Alphabetical by Class] [BAFRDR, BCACBM, BCNAHS, BCNHL, BFNS, BLC, BOBRN, BOBYN, BOXNHL, BOXNS, BRNA, BTFLN, BVZI, DPC, DTC, DPTC, GS, GSLR, LFCZAC, LGS, LVPH, LWACCN, LWACCNE, LWACCW, LWCBAC, LWCTZAC, LWCZDAC, LWFAC, LWFCWAC, LWFCZAC, LWLRRM, LWSCN, LWSCZA, LWSCZAC, LWSLRD, NMGHS, TC, TCC, TECC, VPH, VPU, WGACCN, WGACCW, WGCBAC, WGFAC, WGFCWAC, WGSCN, WGSCZ, WGSCZAC, WLLRM] | Elements: [Occupancy Rate]
                "Wagons": (1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 0.00, 1.20, 1.20, 0.85, 1.20, 0.00, 0.65, 1.20, 0.00, 0.88, 0.90, 0.82, 0.00, 0.65, 0.85, 0.70, 0.76, 0.85, 0.00, 0.95, 0.88, 0.85, 0.00, 1.00, 1.20, 0.85, 0.85, 0.00, 0.00, 0.88, 0.82, 0.00, 0.70, 0.76, 0.95, 0.88, 0.85, 0.00)},

            "Haulage": {
                # Engines [Alphabetical by Class] [WAG12B, WAG7, WAG9, WAP5, WAP7, WDG4G] | Elements: [Stabling Rate, SEKC, Turnaround IDX, Holding Share]
                "Engines": ((0.5, 283.36, 8.0, 0.22), (0.3, 197.8, 7.0, 0.12), (0.2, 241.96, 9.0, 0.38), (0.6, 520.2, 16.0, 0.03), (0.6, 530.4, 14.0, 0.21), (0.4, 271.4, 8.0, 0.04)),
                # Wagons [Alphabetical by Class] [BAFRDR, BCACBM, BCNAHS, BCNHL, BFNS, BLC, BOBRN, BOBYN, BOXNHL, BOXNS, BRNA, BTFLN, BVZI, DPC, DTC, DPTC, GS, GSLR, LFCZAC, LGS, LVPH, LWACCN, LWACCNE, LWACCW, LWCBAC, LWCTZAC, LWCZDAC, LWFAC, LWFCWAC, LWFCZAC, LWLRRM, LWSCN, LWSCZA, LWSCZAC, LWSLRD, NMGHS, TC, TCC, TECC, VPH, VPU, WGACCN, WGACCW, WGCBAC, WGFAC, WGFCWAC, WGSCN, WGSCZ, WGSCZAC, WLLRM] | Elements: [Detention Rate, SWKC, Turnaround IDX, Holding Share]
                "Wagons": ((3.5,1.5,1.2,0.045),(3.5,1.5,1.2,0.025),(3.8,1.4,1.2,0.037),(3.8,1.5,1.2,0.037),(3.5,1.5,1.2,0.033),(4.0,2.0,1.6,0.045),(3.2,1.2,1.4,0.045),(3.6,1.6,1.4,0.045),(4.0,2.0,1.3,0.209),(4.5,2.2,1.3,0.209), (3.5,1.2,1.2,0.033),(2.8,1.2,0.9,0.066),(0.6,0.15,1.0,0.033),(1.0,0.3,1.0,0.002),(1.0,0.3,1.0,0.002),(1.0,0.3,1.0,0.002),(0.6,0.15,1.0,0.008),(0.6,0.15,1.0,0.004),(1.4,0.5,1.0,0.002),(0.6,0.15,1.0,0.002), (1.2,0.4,1.0,0.004),(1.5,0.5,1.0,0.014),(1.5,0.5,1.0,0.003),(1.8,0.6,1.0,0.006),(1.2,0.4,1.0,0.003),(1.4,0.5,1.0,0.002),(2.2,0.8,1.0,0.002),(2.5,0.9,1.0,0.005),(2.2,0.8,1.0,0.005),(2.5,0.9,1.0,0.002),
                    (1.2,0.4,1.0,0.004),(1.5,0.5,1.0,0.022),(1.2,0.4,1.0,0.002),(1.4,0.5,1.0,0.005),(1.2,0.4,1.0,0.003),(1.0,0.3,1.0,0.002),(1.0,0.3,1.0,0.002),(1.0,0.3,1.0,0.002),(1.0,0.3,1.0,0.002),(0.6,0.15,1.0,0.003), (0.6,0.15,1.0,0.002),(1.5,0.5,1.0,0.003),(1.8,0.6,1.0,0.002),(1.2,0.4,1.0,0.002),(2.5,0.9,1.0,0.003),(2.2,0.8,1.0,0.002),(1.5,0.5,1.0,0.003),(1.2,0.4,1.0,0.002),(1.4,0.5,1.0,0.002),(1.2,0.4,1.0,0.002))},

            # Sorted: Macro Economic Factors [Alphabetical] [EnergyTariff, FreightTariffYield, OpexInflation, PassengerFareYield] | Elements: [Mean Annual Drift, Weekly Volatility]
            "Escalation": ((0.040, 0.012), (0.045, 0.008), (0.055, 0.010), (0.035, 0.005))},

        "Maintenance": {
            # Sorted: Wagons [Alphabetical by Design] [] | Elements: [SchA, SchB, IOH, POH, SchAMD, SchBMD, IOHMD, POHMD, FOR]
            "Wagons": ((4, 13, 36, 96, 25000, 50000, 100000, 140000, 0.009), (4, 13, 36, 96, 25000, 50000, 100000, 140000, 0.009), (4,13,36,96,25000,50000,100000,127500,0.010),(4,13,36,96,25000,50000,100000,142500,0.013),(4,13,36,96,25000,50000,100000,142500,0.012),(4,13,36,96,25000,50000,100000,112500,0.010),
                (4, 13, 36, 96, 25000, 50000, 100000, 120000, 0.009), (4, 13, 36, 78, 25000, 50000, 80000, 102000, 0.015), (4,13,36,156,25000,50000,80000,360000,0.018),(4,13,78,234,25000,50000,80000,360000,0.008),(4,13,78,234,30000,60000,100000,415000,0.006),(12,24,52,156,40000,80000,600000,395000,0.016)),
            # Sorted: Segments [Alphabetical by Group] [A, B, C, D, D-Spl, E] | Elements: [Segment Capacity]
            "Segments": (520, 650, 780, 1040, 910, 1300)},

        # Zones [Alphabetical]: CR, ECR, ECoR, ER, KR, NCR, NER, NFR, NR, NWR, SCR, SECR, SER, SCoR, SR, SWR, WCR, WR | Elements per zone: (MinRain,MaxRain), (TMin,TMax), (HumMin,HumMax), (WindMin,WindMax)
        "Environment": (
            ((0.0, 48.0),(12.0, 40.0),(38.0, 82.0),(4.0, 22.0)), ((0.0,38.0),(8.0,42.0),(42.0,86.0),(3.0,18.0)), ((0.0,58.0),(14.0,40.0),(60.0,92.0),(4.0, 24.0)), ((0.0,62.0),(10.0,40.0),(52.0,90.0),(4.0,20.0)), ((0.0,115.0),(18.0,36.0),(68.0,96.0),(6.0,28.0)), ((0.0,32.0),(5.0,45.0),(24.0,72.0),(2.0,16.0)),
            ((0.0,68.0),(8.0,36.0),(58.0,92.0),(3.0,16.0)), ((0.0,96.0),(5.0,34.0),(62.0,95.0),(4.0,18.0)), ((0.0,28.0),(2.0,45.0),(22.0,78.0),(4.0,24.0)), ((0.0,14.0),(5.0,48.0),(14.0,55.0),(5.0, 24.0)), ((0.0,34.0),(12.0,44.0),(32.0,76.0),(4.0,20.0)), ((0.0,46.0),(10.0,44.0),(30.0,80.0),(3.0,16.0)),  ((0.0,54.0),(10.0,42.0),(44.0,88.0),(3.0,18.0)),
            ((0.0,38.0),(16.0,42.0),(46.0,84.0),(4.0, 22.0)), ((0.0,46.0),(18.0,40.0),(54.0,88.0),(4.0,22.0)), ((0.0,54.0),(15.0,38.0),(48.0,90.0),(4.0,20.0)), ((0.0,30.0),(6.0,46.0),(22.0,74.0),(3.0,20.0)), ((0.0,24.0),(8.0,44.0),(24.0,78.0),(4.0,24.0))),

        # Sorted: Services [Alphabetical by Zone] [CR, ECR, ECoR, ER, KR, NCR, NER, NFR, NR, NWR, SCR, SECR, SER, SCoR, SR, SWR, WCR, WR] | Elements: [A₀, A₁, φ₁, A₂, φ₂]
        "Seasonality": (
            (1.00, 0.18, -4.20, 0.09, -1.80), (1.00, 0.10, -2.66, 0.05, -0.80), (1.00, 0.14, -3.60, 0.07, -1.80), (1.00, 0.12, -1.20, 0.06, -0.60), (1.00, 0.42, -5.50, 0.21, -2.80), (1.00, 0.08, -1.00, 0.04, -0.50), (1.00, 0.20, -2.66, 0.10, -1.20), (1.00, 0.28, -3.60, 0.14, -1.80), (1.00, 0.15, -4.50, 0.08, -2.20),
            (1.00, 0.12, -0.60, 0.06, -0.30), (1.00, 0.09, -2.66, 0.04, -1.20), (1.00, 0.08, -1.80, 0.04, -0.90), (1.00, 0.16, -4.20, 0.10, -2.10), (1.00, 0.28, -5.07, 0.14, -2.66), (1.00, 0.14, -3.60, 0.10, -4.20), (1.00, 0.35, -5.07, 0.18, -2.66), (1.00, 0.08, 0.00, 0.04, 0.00), (1.00, 0.22, -4.20, 0.11, -2.10)),
    },

    "Analytics": {
        "Backends": {("onnx", "tensorrt"): "TensorRTExecutionProvider", ("torch", "cuda"): "CUDAExecutionProvider", ("onnx", "cuda"): "CUDAExecutionProvider", ("torch", "hip"): "MIGraphXExecutionProvider", ("onnx", "rocm"): "MIGraphXExecutionProvider", ("qnn", "npu"): "QnnExecutionProvider", ("onnx", "directml"): "DmlExecutionProvider", ("torch", "mps"): "MpsExecutionProvider",
        ("onnx", "coreml"): "CoreMLExecutionProvider", ("openvino", "gpu"): "OpenVINOExecutionProvider", ("openvino", "npu"): "OpenVINOExecutionProvider", ("openvino", "cpu"): "OpenVINOExecutionProvider", ("onnx", "cpu"): "CPUExecutionProvider", ("cpu", "cpu"): "CPUExecutionProvider"},
        "Targets": ("AssetAttrition", "NetworkStress", "ScheduleVolatility", "YieldElasticity"), "Paths": {"Database": "./.Cache/Database"}, "Lookback": 8, "Horizon": 4, "Chunk": 52, "SessionChunk": 1024, "TCN": {"Batch": 8192, "Epochs": 30, "lr": 0.0006, "weight_decay": 0.0001, "beta": 1.5, "Patience": 5, "MinDelta": 0.0001, "Clip": 1.0}
    },

    "Adjudicator": {
        "Assets": (("Engines", "L", "RoadNumber", "Shed"), ("Wagons",  "W", "WagonNumber", "Depot")),
        "Actions": ("ScheduledWithdrawal", "ImmediateWithdrawal", "LocoLink", "SpeedRestriction", "SectionBlock", "Diversion", "CrossingPriority", "RakeAugmentation")
    },

    "Dashboard": {
        "Zones": {
            "CR": "Central Railway", "ECR": "East Central Railway", "ECoR": "East Coast Railway", "ER": "Eastern Railway", "KR": "Konkan Railway", "NCR": "North Central Railway",
            "NER": "North Eastern Railway", "NFR": "Northeast Frontier Railway", "NR": "Northern Railway", "NWR": "North Western Railway", "SCR": "South Central Railway", "SCoR": "South Coast Railway",
            "SECR": "South East Central Railway", "SER": "South Eastern Railway", "SR": "Southern Railway", "SWR": "South Western Railway", "WCR": "West Central Railway", "WR": "Western Railway"
        },

        "Divisions": {
            "AGC": "Agra", "ADI": "Ahmedabad", "ADRA": "Adra", "AII": "Ajmer", "ALP": "Alipurduar", "AMB": "Ambala", "ASN": "Asansol", "BKN": "Bikaner", "BPL": "Bhopal", "BSB": "Varanasi", "BSL": "Bhusawal", "BSP": "Bilaspur", "BVP": "Bhavnagar", "BRC": "Vadodara", "BZA": "Vijayawada", "CKP": "Chakradharpur", "CSMT": "Mumbai CSMT", "DLI": "Delhi", "DNR": "Danapur", "DDU": "Pt. Deen Dayal Upadhyaya",
            "DHN": "Dhanbad", "FZR": "Firozpur", "GNT": "Guntur", "GTL": "Guntakal", "HWH": "Howrah", "HYB": "Hyderabad", "IZZ": "Izzatnagar", "JAT": "Jammu Tawi", "JBP": "Jabalpur", "JHS": "Jhansi", "JP": "Jaipur", "JU": "Jodhpur", "KIR": "Katihar", "KOTA": "Kota", "KUR": "Khurda Road", "KTA": "Kota", "KAWR": "Karwar", "KGP": "Kharagpur", "LKO": "Lucknow", "LJN": "Lucknow NER", "LDM": "Lumding", "MAS": "Chennai",
            "MDU": "Madurai", "MLDT": "Malda", "MB": "Moradabad", "MMCT": "Mumbai Central", "MYS": "Mysuru", "BLR": "Bengaluru", "NGP": "Nagpur", "NED": "Nanded", "PRYJ": "Prayagraj", "PAL": "Palakkad", "PUNE": "Pune", "R": "Raipur", "RN": "Ratnagiri", "RTM": "Ratlam", "RGDA": "Rayagada", "RJT": "Rajkot", "RNC": "Ranchi", "RNY": "Rangiya", "SA": "Salem", "SBP": "Sambalpur",
            "SC": "Secunderabad", "SDAH": "Sealdah", "SPJ": "Samastipur", "SEE": "Sonpur", "SBC": "Bengaluru City", "SUR": "Solapur", "TPJ": "Tiruchchirappalli", "TSK": "Tinsukia", "TVC": "Thiruvananthapuram", "UBL": "Hubballi", "UMB": "Ambala", "VGLJ": "VGL Jhansi Junction", "VSKP": "Visakhapatnam"
        },

        # Sorted: Thresholds [Alphabetical] | Elements: (Excellent, Marginal, Degraded, HigherIsBetter)
        "Thresholds": ((0.92, 0.85, 0.75, True), (0.35, 0.55, 0.75, False), (1.20, 1.80, 2.50, False), (0.28, 0.48, 0.68, False), (0.92, 0.85, 0.75, True)),

        "HTML": """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agradrishti</title><style>{{ CSS | safe }}</style></head><body><div id="App">
            <header id="HDR"><b>Agradrishti</b><div style="display:flex;gap:6px;align-items:center;flex:1"><button class="FTab Active" data-f="All">All</button><button class="FTab" data-f="A">Asset</button><button class="FTab" data-f="N">Network</button><button class="FTab" data-f="S">Schedule</button><button class="BtnExport" id="XBTN">↓ Export</button></div></header>
            <div id="SkeletonScreen"><div style="display:grid;grid-template-columns:repeat({{ MC }},1fr);gap:10px">{% for _ in range(MC) %}<div class="Skeleton" style="height:88px"></div>{% endfor %}</div><div style="display:grid;grid-template-columns:repeat({{ TC }},1fr);gap:10px">{% for _ in range(TC) %}<div class="Skeleton" style="height:80px"></div>{% endfor %}</div>


            <div class="Skeleton" style="height:220px"></div></div>
            <main id="AppMain" style="display:none"><section id="Health"><div class="SHdr"><span>Model Health</span><hr></div><div class="Grid" id="KPIGrid"></div></section><section id="Targets"><div class="SHdr"><span>Target Confidence</span><hr></div><div class="Strip" id="TargetStrip"></div></section><section id="Manifest"><div class="SHdr"><span>Decision Manifest</span><hr></div><table class="MTable"><thead><tr><th>ID</th><th>Affected Entity</th><th>Action</th><th>Recommendation</th></tr></thead><tbody id="MB"></tbody></table><div class="PG" id="MPG"><span class="PGINF">Showing <b id="MST">0</b>–<b id="MED">0</b> of <b id="MTotal">0</b></span><div class="PGCTL"><button class="PGBTN" id="MPV" disabled>← Prev</button><div class="PGS" id="MNums"></div><button class="PGBTN" id="MNext">Next →</button></div></div><section id="Detail"><div class="SHdr"><span>Inspection & Trace</span><hr></div><div id="DP"><p class="NoSel">Select a row to inspect</p></div></section></section></main></div>
            <script>{{ JS | safe }}</script></body></html>""",

        "CSS": """@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');
            :root{--Bg:#0a0c0f;--Sur:#111318;--Bdr:#1e2229;--ACC:#e8ff47;--INF:#47c5ff;--WARN:#ffaa47;--ALT:#ff6b47;--MUTE:#4a5260;--Txt:#d4dae6;--Dim:#6b7585}
            *,::before,::after{box-sizing:border-box;margin:0;padding:0}
            body{background:var(--Bg);color:var(--Txt);font-family:'DM Mono',monospace;font-size:13px;line-height:1.4}
            body::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent 0 2px,rgba(255,255,255,.012) 2px 4px);pointer-events:none;z-IDX:9999}
            ::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:var(--Bg)}::-webkit-scrollbar-thumb{background:var(--Bdr);border-radius:2px}
            header{position:sticky;top:0;z-IDX:100;background:color-mix(in srgb,var(--Bg) 95%,transparent);backdrop-filter:blur(12px);border-bottom:1px solid var(--Bdr);padding:0 28px;display:flex;align-items:center;gap:16px;height:56px}
            header b{font-family:'Syne',sans-serif;font-weight:800;font-size:15px;letter-spacing:.08em;color:var(--ACC);text-transform:uppercase;flex-shrink:0}
            #App main,#SkeletonScreen{padding:24px 28px;display:flex;flex-direction:column;gap:28px}
            .SHdr{display:flex;align-items:center;gap:12px}
            .SHdr span{font-family:'Syne',sans-serif;font-weight:700;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--Dim)}
            .SHdr hr{flex:1;height:1px;border:0;background:var(--Bdr)}
            .Label{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--Dim)}
            .PGBTN,.FTab,.BtnExport,.PagNum{font-family:'DM Mono',monospace;font-size:10px;border-radius:2px;cursor:pointer;transition:all .15s ease}
            .BtnExport{background:transparent;border:1px solid var(--ACC);color:var(--ACC);font-size:11px;letter-spacing:.08em;padding:5px 14px;text-transform:uppercase;margin-left:auto}
            .FTab,.PagNum{background:transparent;border:1px solid var(--Bdr);color:var(--Dim);letter-spacing:.1em;text-transform:uppercase;padding:5px 14px}
            .PagNum{min-width:24px;height:24px;padding:0 4px;display:inline-flex;align-items:center;justify-content:center}
            .FTab:hover,.FTab.Active,.PagNum:hover,.PagNum.Active,.PGBTN:hover:not(:disabled){border-color:var(--ACC);color:var(--ACC);background:color-mix(in srgb,var(--ACC) 8%,transparent)}
            #Health .Grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
            .KPI,.TCard,.DPanel{background:var(--Sur);border:1px solid var(--Bdr);border-radius:4px;position:relative;overflow:hidden}
            .KPI{padding:16px 18px}
            .KPI::after,.TCard::after{content:'';position:absolute;bottom:0;inset-x:0;height:2px}
            .KPI::after{background:var(--Ka,var(--MUTE))}
            .TCard::after{background:var(--INF)}
            .KPI b{font-family:'Syne',sans-serif;font-weight:700;font-size:28px;color:var(--Txt);line-height:1;display:block;margin:4px 0}
            .Badge,.DTag,.DActions{display:inline-block;border-radius:2px;letter-spacing:.06em}
            .Badge{font-size:9px;padding:2px 6px;margin-top:6px;background:color-mix(in srgb,var(--Ba,var(--MUTE)) 15%,transparent);color:var(--Ba,var(--MUTE))}
            #Targets .Strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
            .TCard{padding:14px 16px}
            .TName{font-family:'Syne',sans-serif;font-weight:700;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--Dim);margin-bottom:10px}
            .TMetrics{display:flex;gap:14px}
            .TMetric,.DField{display:flex;flex-direction:column;gap:2px}
            .TMetric span:first-child,.DField span:first-child{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--Dim)}
            .TMetric span:last-child,.DField span:last-child{font-family:'Syne',sans-serif;font-weight:700;font-size:14px;color:var(--Txt)}
            .MTable{width:100%;border-collapse:collapse}
            .MTable th{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--Dim);text-align:left;padding:8px 12px;border-bottom:1px solid var(--Bdr);font-weight:400}
            .MTable td{padding:9px 12px;border-bottom:1px solid color-mix(in srgb,var(--Bdr) 60%,transparent);font-size:12px;color:var(--Txt);cursor:pointer}
            .MTable tr:hover td{background:rgba(255,255,255,.02)}
            .MTable tr.Selected td{background:color-mix(in srgb,var(--ACC) 5%,transparent);border-bottom-color:color-mix(in srgb,var(--ACC) 20%,transparent)}
            .DTag{padding:2px 7px;font-size:10px;font-weight:500}
            .DTag-A{background:color-mix(in srgb,var(--ACC) 15%,transparent);color:var(--ACC);border:1px solid color-mix(in srgb,var(--ACC) 30%,transparent)}
            .DTag-N{background:color-mix(in srgb,var(--INF) 15%,transparent);color:var(--INF);border:1px solid color-mix(in srgb,var(--INF) 30%,transparent)}
            .DTag-S{background:color-mix(in srgb,#c084fc 15%,transparent);color:#c084fc;border:1px solid color-mix(in srgb,#c084fc 30%,transparent)}
            .DPanel{padding:20px}
            .DHeader{display:flex;align-items:center;gap:12px;margin-bottom:16px}
            .DGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
            .DActions{font-size:10px;padding:3px 8px;background:color-mix(in srgb,var(--ALT) 12%,transparent);color:var(--ALT);border:1px solid color-mix(in srgb,var(--ALT) 25%,transparent)}
            .NoSel{color:var(--MUTE);font-size:12px;padding:24px;text-align:center}
            @keyframes Shimmer{to{background-position:200% 0}}
            .Skeleton{background:linear-gradient(90deg,var(--Sur) 25%,var(--Bdr) 50%,var(--Sur) 75%) 0 0/200% 100%;animation:Shimmer 1.5s infinite;border-radius:4px}
            .PG{display:flex;align-items:center;justify-content:space-between;padding-top:10px;margin-top:8px;border-top:1px solid color-mix(in srgb,var(--Bdr) 60%,transparent);font-size:11px;color:var(--Dim)}
            .PGINF b{color:var(--Txt);font-weight:500}
            .PGCTL{display:flex;align-items:center;gap:6px}
            .PGBTN{background:var(--Sur);border:1px solid var(--Bdr);color:var(--Txt);padding:4px 10px}
            .PGBTN:disabled{color:var(--MUTE);border-color:var(--Bdr);cursor:not-allowed;opacity:.4}
            .PGS{display:flex;gap:4px}""",

        "JS": """const MNF={{ MANIFEST | safe }}, EVL={{ EVALUATIONS | safe }}, THS={{ THRESHOLDS | safe }}, ACT={{ ACTIONS | safe }}, SNP={{ SNAPSHOT | safe }};
            const CLR=['#e8ff47','#ffaa47','#ff6b47'], MTR=['DA','MAE','MaxE','RMSE','TEX'], BND=['Excellent','Marginal','Degraded'];
            const FMT = (K, V) => (K === 'DA' || K === 'TEX') ? (V * 100).toFixed(1) + '%' : Number(V).toFixed(4);
            const BNDF = (V, [E, M, D, H]) => H ? (V >= E ? 0 : V >= M ? 1 : 2) : (V <= E ? 0 : V <= M ? 1 : 2);
            const $ = ID => document.getElementById(ID);
            $('KPIGrid').innerHTML = MTR.map((K, I) => { const B = BNDF(EVL.General[K], THS[I]), C = CLR[B]; return `<div class="KPI" style="--Ka:${C}"><span class="Label">${K}</span><b>${FMT(K, EVL.General[K])}</b><span class="Badge" style="--Ba:${C}">${BND[B]}</span></div>`; }).join('');
            $('TargetStrip').innerHTML = Object.entries(EVL.Targets).map(([N, T]) => `<div class="TCard"><div class="TName">${N}</div><div class="TMetrics">${['DA','RMSE','MaxE'].map(K => `<div class="TMetric"><span>${K}</span><span>${FMT(K, T[K])}</span></div>`).join('')}</div></div>`).join('');

             const Decoder = (ID, RW, REC) => {
                if (RW == null || RW === '—') return '—';
                if (Array.isArray(RW)) return RW.map(V => Decoder(ID, V, REC));
                switch (ID?.[0]) {

                    case 'A': { const K = ID.startsWith('A2') ? (typeof REC !== 'undefined' && REC ? 'L' : 'T') : ID[3]; return (K === 'T' ? SNP?.Encodings?.Trains?.TrainNo?.Reverse?.[RW] ?? RW : K === 'W' ? SNP?.Encodings?.Wagons?.WagonNumber?.Reverse?.[RW] ?? RW : SNP?.Encodings?.Engines?.RoadNumber?.Reverse?.[RW] ?? RW); }
                    case 'N': return ID.startsWith('N3') ? (SNP?.Encodings?.Stations?.Code?.Reverse?.[RW] ?? RW) : (SNP?.Encodings?.Trains?.TrainNo?.Reverse?.[RW] ?? RW);
                    case 'S': return SNP?.Encodings?.Trains?.TrainNo?.Reverse?.[RW] ?? RW;
                    default:  return RW;
                }
            };

            const TraceDetails = (ID, RV) => {
                if (RV == null || RV === '—') return null;
                const T = ID.startsWith('A2') ? 'L' : ID.charAt(3); const P = T === 'L' ? SNP?.Encodings?.Engines?.RoadNumber?.Position?.[RV] : T === 'W' ? SNP?.Encodings?.Wagons?.WagonNumber?.Position?.[RV] : SNP?.Encodings?.Trains?.TrainNo?.Position?.[RV] ?? RV;
                const E = SNP?.Instances?.Engines, W = SNP?.Instances?.Wagons, TR = SNP?.Instances?.Trains, ST = SNP?.Instances?.Stations; const EE = SNP?.Encodings?.Engines, WE = SNP?.Encodings?.Wagons, TE = SNP?.Encodings?.Trains, SE = SNP?.Encodings?.Stations, CE = SNP?.Encodings?.Configuration;

                switch (ID?.[0]) {
                    case 'A': return T === 'L' ? {
                            Class: EE?.Class?.Reverse?.[E?.Class?.[P]] ?? '—', Service: EE?.Service?.Reverse?.[E?.Service?.[P]] ?? '—',
                            Traction: EE?.Traction?.Reverse?.[E?.Traction?.[P]] ?? '—', Shed: SE?.Code?.Reverse?.[E?.Shed?.[P]] ?? '—', CommissioningYear: E?.CommissioningYear?.[P] ?? '—'
                        } : {
                            Class: WE?.Class?.Reverse?.[W?.Class?.[P]] ?? '—', Design: WE?.Design?.Reverse?.[W?.Design?.[P]] ?? '—',
                            Stock: WE?.Stock?.Reverse?.[W?.Stock?.[P]] ?? '—', Depot: SE?.Code?.Reverse?.[W?.Depot?.[P]] ?? '—', CommissioningYear: W?.CommissioningYear?.[P] ?? '—'
                        };
                    case 'N': return ID.startsWith('N3') ? {
                            Name: SE?.Name?.Reverse?.[RV] ?? '—', Category: SE?.Category?.Reverse?.[ST?.Category?.[RV]] ?? '—',
                            Zone: SE?.Zone?.Reverse?.[ST?.Zone?.[RV]] ?? '—', Division: SE?.Division?.Reverse?.[ST?.Division?.[RV]] ?? '—',
                            Location: ST?.Location?.[RV] ?? '—', Platforms: ST?.Platforms?.[RV] ?? '—', EPL: ST?.EPL?.[RV] ?? '—'
                        } : { Type: TE?.Type?.Reverse?.[TR?.Type?.[P]] ?? '—', Service: CE?.TrainServices?.Reverse?.[TR?.Service?.[P]] ?? '—', Priority: TR?.Priority?.[P] ?? '—' };
                    case 'S': return ID.startsWith('S2') ? {
                            Design: WE?.Design?.Reverse?.[W?.Design?.[RV]] ?? '—', Stock: WE?.Stock?.Reverse?.[W?.Stock?.[RV]] ?? '—',
                            Accommodation: WE?.Accommodation?.Reverse?.[W?.Accommodation?.[RV]] ?? '—', Capacity: W?.Capacity?.[RV] ?? '—'
                        } : { Type: TE?.Type?.Reverse?.[TR?.Type?.[P]] ?? '—', Service: CE?.TrainServices?.Reverse?.[TR?.Service?.[P]] ?? '—', Priority: TR?.Priority?.[P] ?? '—' };
                    default: return null;
                }
            };

            const FMN = Object.values(MNF).flatMap(Data => Data?.ID?.map((ID, IDX) => {const A = Data.Affected?.[IDX], R = Data.Recommendations?.[IDX], N3 = ID.startsWith('N3'), S2 = ID.startsWith('S2'); return {ID, UNT: N3 ? Decoder(ID, A?.slice(0, 2)).join(' ↔ ') : Decoder(ID, A), ACT: ACT[R?.[0]] ?? R?.[0] ?? '—', TRG: N3 ? `${Decoder(ID, A?.[0])} ↔ ${Decoder(ID, R?.[1])} ↔ ${Decoder(ID, A?.[1])}` : S2 ? `${(R?.[1] ?? 0) > 0 ? '+' : ''}${R?.[1] ?? ''} × ${Decoder(ID, R?.[2])}` : Decoder(ID, R?.[1]), ...TraceDetails(ID, N3 ? A?.[0] : S2 ? R?.[2] : ID[0] === 'A' ? R?.[1] : A)};}) ?? []);
            let ROW = null, CTG = 'All', PAG = 1, PSZ = 20, FLT = [];
            const PBTS = (P, M) => {if (M <= 7) return Array.from({length: M}, (_, I) => `<button class="PagNum ${P === I + 1 ? 'Active' : ''}" data-p="${I + 1}">${I + 1}</button>`).join(''); let S = Math.max(2, P - 1), E = Math.min(M - 1, P + 1); if (P <= 3) { S = 2; E = 4; } else if (P >= M - 2) { S = M - 3; E = M - 1; } return `<button class="PagNum ${P === 1 ? 'Active' : ''}" data-p="1">1</button>` + (S > 2 ? '<span class="PagEllipsis">…</span>' : '') + Array.from({length: E - S + 1}, (_, I) => `<button class="PagNum ${P === S + I ? 'Active' : ''}" data-p="${S + I}">${S + I}</button>`).join('') + (E < M - 1 ? '<span class="PagEllipsis">…</span>' : '') + `<button class="PagNum ${P === M ? 'Active' : ''}" data-p="${M}">${M}</button>`;};

            const Render = () => {
                FLT = CTG === 'All' ? FMN : FMN.filter(R => R.ID[0] === CTG); const TOT = FLT.length;
                if (!TOT) { $('MB').innerHTML = '<tr><td colspan="4" class="NoSel">No Decisions Made</td></tr>'; $('MPG').style.display = 'none'; return; }
                $('MPG').style.display = 'flex'; const MAX = Math.ceil(TOT / PSZ) || 1; if (PAG > MAX) PAG = MAX; const IDX = (PAG - 1) * PSZ, SLC = FLT.slice(IDX, IDX + PSZ);$('MB').innerHTML = SLC.map((R, I) => `<tr data-i="${IDX + I}" class="${ROW === (IDX + I) ? 'Selected' : ''}"><td><span class="DTag DTag-${R.ID[0]}">${R.ID}</span></td><td>${R.UNT}</td><td>${R.ACT}</td><td>${R.TRG}</td></tr>`).join('');
                $('MNums').innerHTML = PBTS(PAG, MAX);$('MST').innerText = IDX + 1; $('MED').innerText = Math.min(IDX + PSZ, TOT);$('MTotal').innerText = TOT; $('MPV').disabled = PAG === 1; $('MNext').disabled = PAG === MAX;
            };

            $('MB').addEventListener('click', EVT => {
                const TRG = EVT.target.closest('tr'); if (!TRG?.dataset.i) return; ROW = +TRG.dataset.i; const R = FLT[ROW]; if (!R) return;
                $('DP').innerHTML = `<div class="DPanel"><div class="DHeader"><span class="DTag DTag-${R.ID[0]}">${R.ID}</span></div><div class="DGrid"><div class="DField"><span>Decision ID</span><span>${R.ID}</span></div><div class="DField"><span>Affected Entity</span><span>${R.UNT}</span></div><div class="DField"><span>Action</span><span>${R.ACT}</span></div><div class="DField"><span>Recommendation</span><span>${R.TRG}</span></div>${Object.entries(R).map(([K, V]) => ['ID','UNT','ACT','TRG'].includes(K) ? '' : `<div class="DField"><span>${K}</span><span>${V}</span></div>`).join('')}</div></div>`;
                Render();
            });

            $('MPV').onclick = () => { if (PAG > 1) { PAG--; Render(); } };
            $('MNext').onclick = () => { PAG++; Render(); };$('MPG').addEventListener('click', EVT => { if (EVT.target.classList.contains('PagNum')) { PAG = +EVT.target.dataset.p; Render(); } });
            if ($('HDR')) {$('HDR').addEventListener('click', EVT => {if (!EVT.target.classList.contains('FTab')) return; CTG = EVT.target.dataset.f; ROW = null; PAG = 1; document.querySelectorAll('.FTab').forEach(T => T.classList.toggle('Active', T === EVT.target)); Render();}); }

            $('XBTN').onclick = async () => {
                const DAT = JSON.stringify({ Manifest: MNF, Evaluations: EVL }, null, 2), NAM = `Agradrishti_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
                if (window.showSaveFilePicker) { try { const HND = await showSaveFilePicker({ suggestedName: NAM, types: [{ accept: { 'application/json': ['.json'] } }] }); const WRT = await HND.createWritable(); await WRT.write(DAT); await WRT.close(); return; } catch {} }
                const URL_ = URL.createObjectURL(new Blob([DAT], { type: 'application/json' })); Object.assign(document.createElement('a'), { href: URL_, download: NAM }).click(); URL.revokeObjectURL(URL_);
            };

            Render(); $('SkeletonScreen').style.display = 'none';$('AppMain').style.display = 'flex';"""
    },

    "Schema": {
        "Engines": {"Class": str, "Service": str, "Traction": str, "Power": int, "MPS": int, "TareWeight": int, "CL": int, "IA": int, "IB": int, "IC": int, "M12": int, "IOH": int, "POH": int, "IOHMD": int, "POHMD": int, "REKM": int, "FOR": int},
        "Events": {"Name": str, "Window": (list, int), "Zones": (list, str), "Services": (list, str), "Scale": (list, float), "Probability": (list, float)},
        "Rakes": {"RakeNo": str, "Trains": (list, str), "Design": str, "CDOs": (list, str), "Composition": (dict, int)},
        "Schedules": {"TrainNo": str, "Stops": (list, {"Station": str, "Day": int, "Arrival": int, "Departure": int})},
        "Segments": {"Key": str, "Group": str, "Distance": float, "Line": int},
        "Stations": {"Code": str, "Name": str, "Category": str, "Zone": str, "Division": str, "Location": (list, float), "Platforms": int, "EPL": int},
        "Trains": {"TrainNo": str, "Name": str, "Type": str, "Frequency": (list, str)},
        "Wagons": {"Class": str, "Stock": str, "Design": str, "Accommodation": int | None, "AC": bool, "Capacity": float, "Length": float | None, "MPS": int | None, "TareWeight": float | None, "HotelLoad": float | None, "CL": int, "REKM": int}
    },

    "FS": {"Engines": ("Data/Engines.json", "Class", None), "Events": ("Data/Events.json", "Name", None), "Rakes": ("Data/Rakes.json", "RakeNo", None), "Schedules": ("Data/Schedules.json", "TrainNo", None), "Segments": ("Data/Segments.json", "Key", None), "Stations": ("Data/Stations.json", "Code", {"Schedules": "Stops|Station", "Segments": ["Key|0", "Key|1"] }), "Trains": ("Data/Trains.json", "TrainNo", {"Schedules": "TrainNo"}),"Wagons": ("Data/Wagons.json", "Class", None)}
}
