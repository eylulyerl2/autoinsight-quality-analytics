"""
AutoInsight - synthetic data generation.

Step 1: suppliers and parts.
Step 2: vehicles.
Step 3: quality incidents.

Run from the project root:
    python src/generate_data.py

All data is synthetic. All costs are in TRY (Turkish Lira).
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

SEED = 42  # same seed -> same data every time you run the script
N_VEHICLES = 2000
N_INCIDENTS = 5000

# Incidents are generated between these dates.
# DATA_END is also the "snapshot date" of the dataset (used for incident status).
DATA_START = "2023-01-01"
DATA_END = "2025-12-31"

# ---------------------------------------------------------------------------
# Suppliers (10)
# ---------------------------------------------------------------------------
SUPPLIERS = [
    # (supplier_name, country, supplier_category)
    ("Supplier A", "Turkey", "Mechanical"),
    ("Supplier B", "Germany", "Electronics"),
    ("Supplier C", "China", "Electronics"),
    ("Supplier D", "Turkey", "Plastics"),
    ("Supplier E", "Japan", "Mechanical"),
    ("Supplier F", "South Korea", "Electronics"),
    ("Supplier G", "Poland", "Mechanical"),
    ("Supplier H", "Romania", "Plastics"),
    ("Supplier I", "India", "Mechanical"),
    ("Supplier J", "Mexico", "Rubber"),
]

# ---------------------------------------------------------------------------
# Parts (30)
# ---------------------------------------------------------------------------
PARTS = [
    # (part_name, category, supplier_name, unit_cost in TRY)
    # Engine
    ("Timing Belt", "Engine", "Supplier J", 1200),
    ("Spark Plug Set", "Engine", "Supplier I", 650),
    ("Turbocharger", "Engine", "Supplier E", 18500),
    ("Oil Pump", "Engine", "Supplier A", 2800),
    # Fuel system
    ("Fuel Pump", "Fuel System", "Supplier G", 3200),
    ("Fuel Injector", "Fuel System", "Supplier E", 2400),
    # Brake
    ("Brake Pad", "Brake", "Supplier A", 900),
    ("Brake Disc", "Brake", "Supplier I", 1800),
    ("ABS Sensor", "Brake", "Supplier C", 1500),
    ("Brake Caliper", "Brake", "Supplier G", 3500),
    # Cooling
    ("Water Pump", "Cooling", "Supplier A", 2200),
    ("Radiator", "Cooling", "Supplier I", 4200),
    ("Radiator Hose", "Cooling", "Supplier J", 450),
    ("Thermostat", "Cooling", "Supplier G", 700),
    # Electronics
    ("Electronic Control Unit", "Electronics", "Supplier B", 14500),
    ("Oxygen Sensor", "Electronics", "Supplier B", 1900),
    ("Airbag Control Module", "Electronics", "Supplier B", 6800),
    ("Infotainment Display", "Electronics", "Supplier C", 9500),
    # Electrical
    ("Battery Module", "Electrical", "Supplier F", 22000),
    ("Alternator", "Electrical", "Supplier F", 5200),
    ("Starter Motor", "Electrical", "Supplier C", 3900),
    # Suspension
    ("Shock Absorber", "Suspension", "Supplier E", 2600),
    ("Control Arm", "Suspension", "Supplier I", 2100),
    ("Wheel Bearing", "Suspension", "Supplier A", 1100),
    # Transmission
    ("Clutch Kit", "Transmission", "Supplier G", 5400),
    ("Gearbox Sensor", "Transmission", "Supplier F", 1700),
    # HVAC
    ("Air Conditioning Compressor", "HVAC", "Supplier E", 8500),
    ("Cabin Air Filter", "HVAC", "Supplier D", 350),
    # Steering and body
    ("Power Steering Pump", "Steering", "Supplier I", 4800),
    ("Door Handle Assembly", "Body & Interior", "Supplier H", 850),
]

# ---------------------------------------------------------------------------
# Vehicle models
# ---------------------------------------------------------------------------
# share       : share of all vehicles that are this model
# fuel        : probability of each fuel type for this model
# lines       : production lines that build this model (and how often)
# first_year  : first production year of the model
VEHICLE_MODELS = {
    "City Hatchback": {
        "share": 0.22,
        "fuel": {"Petrol": 0.70, "Diesel": 0.15, "Hybrid": 0.15},
        "lines": {"F1-L1": 0.5, "F1-L2": 0.5},
        "first_year": 2021,
    },
    "Compact Sedan": {
        "share": 0.20,
        "fuel": {"Petrol": 0.50, "Diesel": 0.35, "Hybrid": 0.15},
        "lines": {"F2-L1": 0.6, "F2-L2": 0.4},
        "first_year": 2021,
    },
    "Compact SUV": {
        "share": 0.25,
        "fuel": {"Petrol": 0.40, "Diesel": 0.35, "Hybrid": 0.25},
        "lines": {"F2-L2": 0.5, "F3-L1": 0.5},
        "first_year": 2021,
    },
    "Family SUV": {
        "share": 0.15,
        "fuel": {"Diesel": 0.45, "Petrol": 0.30, "Hybrid": 0.25},
        "lines": {"F3-L1": 0.5, "F3-L2": 0.5},
        "first_year": 2021,
    },
    "Pickup Truck": {
        "share": 0.08,
        "fuel": {"Diesel": 0.85, "Petrol": 0.15},
        "lines": {"F3-L2": 1.0},
        "first_year": 2021,
    },
    "Electric Crossover": {
        "share": 0.10,
        "fuel": {"Electric": 1.0},
        "lines": {"F1-L2": 1.0},
        "first_year": 2022,  # launched later than the other models
    },
}

# How many vehicles were produced in each year (relative weights)
YEAR_WEIGHTS = {2021: 0.10, 2022: 0.15, 2023: 0.20, 2024: 0.27, 2025: 0.28}

# ---------------------------------------------------------------------------
# Quality incident settings
# ---------------------------------------------------------------------------
# --- Which vehicles have incidents? -----------------------------------------
# Relative incident risk of each model (1.0 = average)
MODEL_RISK = {
    "City Hatchback": 1.0,
    "Compact Sedan": 0.9,
    "Compact SUV": 1.1,
    "Family SUV": 1.0,
    "Pickup Truck": 0.9,
    "Electric Crossover": 1.6,  # newer technology, more problems
}
# Vehicles are assumed to enter service on April 1 of their production year
IN_SERVICE_MONTH = 4
# Each extra year of age adds this much to a vehicle's incident risk
AGE_RISK_PER_YEAR = 0.12

# --- Which parts fail? -------------------------------------------------------
# Relative failure weight of each part (bigger = fails more often)
PART_FAILURE_WEIGHT = {
    "Timing Belt": 3,
    "Spark Plug Set": 4,
    "Turbocharger": 2,
    "Oil Pump": 3,
    "Fuel Pump": 4,
    "Fuel Injector": 4,
    "Brake Pad": 9,
    "Brake Disc": 5,
    "ABS Sensor": 6,
    "Brake Caliper": 3,
    "Water Pump": 7,
    "Radiator": 4,
    "Radiator Hose": 5,
    "Thermostat": 4,
    "Electronic Control Unit": 5,
    "Oxygen Sensor": 7,
    "Airbag Control Module": 2,
    "Infotainment Display": 6,
    "Battery Module": 3,
    "Alternator": 3,
    "Starter Motor": 4,
    "Shock Absorber": 6,
    "Control Arm": 3,
    "Wheel Bearing": 6,
    "Clutch Kit": 3,
    "Gearbox Sensor": 3,
    "Air Conditioning Compressor": 6,
    "Cabin Air Filter": 2,
    "Power Steering Pump": 3,
    "Door Handle Assembly": 4,
}

# Parts that do not exist on some vehicle types
ELECTRIC_EXCLUDED_PARTS = {
    "Timing Belt", "Spark Plug Set", "Turbocharger", "Oil Pump", "Fuel Pump",
    "Fuel Injector", "Oxygen Sensor", "Clutch Kit", "Gearbox Sensor",
    "Alternator", "Starter Motor",
}
DIESEL_EXCLUDED_PARTS = {"Spark Plug Set"}
BATTERY_FUEL_TYPES = {"Electric", "Hybrid"}  # only these have a Battery Module
# Electric vehicles rely more on these parts
ELECTRIC_PART_BOOST = {"Battery Module": 3.0, "Infotainment Display": 1.3}

# Seasonal effects: (part category, months, multiplier)
SEASONAL_EFFECTS = [
    ("Cooling", {6, 7, 8}, 1.8),         # summer heat
    ("HVAC", {6, 7, 8}, 2.0),            # air conditioning in summer
    ("Electrical", {12, 1, 2}, 1.8),     # battery, starter in winter
    ("Brake", {11, 12, 1, 2}, 1.2),      # wet and icy roads
]

# --- Overall incident trend --------------------------------------------------
# Incidents per month grow by this much each month (fleet grows and ages)
MONTHLY_TREND = 0.02

# --- Planted pattern 1: faulty batch from Supplier B -------------------------
# Vehicles produced in SPIKE_VEHICLE_YEAR had faulty Supplier B electronics.
# The failures show up between SPIKE_START and SPIKE_END.
N_SPIKE_INCIDENTS = 320
SPIKE_START = "2024-03-01"
SPIKE_END = "2024-06-30"
SPIKE_VEHICLE_YEAR = 2023
SPIKE_PART_WEIGHT = {
    "Electronic Control Unit": 0.45,
    "Oxygen Sensor": 0.35,
    "Airbag Control Module": 0.20,
}
SPIKE_SOURCE_WEIGHTS = {"Supplier Defect": 0.85, "Material Failure": 0.05, "Unknown": 0.10}
SPIKE_TYPE_WEIGHTS = {"Electrical Failure": 0.55, "Software Error": 0.25, "Performance Issue": 0.20}

# --- Planted pattern 2: production line problem -------------------------------
# From PROBLEM_LINE_START, line F2-L1 produces more assembly and manufacturing errors
PROBLEM_LINE = "F2-L1"
PROBLEM_LINE_START = "2025-01-01"
PROBLEM_LINE_MULTIPLIERS = {"Assembly Error": 2.5, "Manufacturing Error": 1.5}

# --- Defect source -----------------------------------------------------------
BASE_SOURCE_WEIGHTS = {
    "Manufacturing Error": 0.18,
    "Supplier Defect": 0.30,
    "Assembly Error": 0.15,
    "Material Failure": 0.15,
    "Design Issue": 0.10,
    "Customer Misuse": 0.07,
    "Unknown": 0.05,
}
# Some part categories are more likely to have certain defect sources
CATEGORY_SOURCE_MULTIPLIERS = {
    "Electronics": {"Supplier Defect": 1.5, "Design Issue": 1.5, "Assembly Error": 0.5},
    "Electrical": {"Supplier Defect": 1.5, "Design Issue": 1.2, "Assembly Error": 0.5},
    "Engine": {"Manufacturing Error": 1.5, "Material Failure": 1.3},
    "Transmission": {"Manufacturing Error": 1.5, "Material Failure": 1.3},
    "Brake": {"Material Failure": 1.5},
    "Suspension": {"Material Failure": 1.5},
    "Body & Interior": {"Assembly Error": 1.6},
    "Steering": {"Assembly Error": 1.6},
    "Cooling": {"Supplier Defect": 1.2, "Assembly Error": 1.2},
    "HVAC": {"Supplier Defect": 1.2, "Assembly Error": 1.2},
    "Fuel System": {"Supplier Defect": 1.2, "Assembly Error": 1.2},
}

# --- Defect type -------------------------------------------------------------
# (When the source is "Assembly Error", half of the defects become
#  "Incorrect Installation" - see draw_defect_type)
CATEGORY_DEFECT_TYPES = {
    "Engine": {"Breakage": 0.25, "Noise": 0.15, "Overheating": 0.20, "Leakage": 0.15, "Performance Issue": 0.25},
    "Fuel System": {"Leakage": 0.30, "Performance Issue": 0.35, "Breakage": 0.15, "Noise": 0.20},
    "Brake": {"Noise": 0.35, "Breakage": 0.20, "Performance Issue": 0.30, "Leakage": 0.15},
    "Cooling": {"Leakage": 0.40, "Overheating": 0.40, "Breakage": 0.10, "Noise": 0.10},
    "Electronics": {"Electrical Failure": 0.45, "Software Error": 0.35, "Performance Issue": 0.20},
    "Electrical": {"Electrical Failure": 0.70, "Overheating": 0.15, "Performance Issue": 0.15},
    "Suspension": {"Noise": 0.40, "Breakage": 0.30, "Leakage": 0.10, "Performance Issue": 0.20},
    "Transmission": {"Noise": 0.25, "Performance Issue": 0.40, "Breakage": 0.20, "Leakage": 0.15},
    "HVAC": {"Performance Issue": 0.40, "Leakage": 0.30, "Noise": 0.20, "Electrical Failure": 0.10},
    "Steering": {"Noise": 0.35, "Leakage": 0.25, "Performance Issue": 0.30, "Breakage": 0.10},
    "Body & Interior": {"Breakage": 0.50, "Noise": 0.50},
}

# --- Severity ----------------------------------------------------------------
SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
SEVERITY_BY_DEFECT_TYPE = {
    "Noise": [0.55, 0.35, 0.09, 0.01],
    "Leakage": [0.25, 0.45, 0.25, 0.05],
    "Performance Issue": [0.35, 0.45, 0.17, 0.03],
    "Electrical Failure": [0.15, 0.40, 0.35, 0.10],
    "Software Error": [0.35, 0.45, 0.17, 0.03],
    "Breakage": [0.10, 0.35, 0.40, 0.15],
    "Overheating": [0.05, 0.30, 0.45, 0.20],
    "Incorrect Installation": [0.30, 0.45, 0.20, 0.05],
}
# Brakes and airbags are safety critical, so severe cases are more likely
SAFETY_CRITICAL_BOOST = 1.5

# --- Customer complaint ------------------------------------------------------
# Probability that the customer complained, by severity
COMPLAINT_PROBABILITY = {"Low": 0.25, "Medium": 0.45, "High": 0.70, "Critical": 0.85}

# --- Status (depends on how old the incident is at the snapshot date) --------
STATUS_LEVELS = ["Closed", "Under Investigation", "Open"]
STATUS_OLD = [0.97, 0.02, 0.01]      # older than 90 days
STATUS_MIDDLE = [0.80, 0.12, 0.08]   # 30 to 90 days
STATUS_RECENT = [0.25, 0.35, 0.40]   # 30 days or less


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def weighted_choice(rng: np.random.Generator, weights: dict, size: int) -> np.ndarray:
    """Pick `size` random keys from a {key: weight} dictionary."""
    keys = list(weights.keys())
    probabilities = np.array(list(weights.values()), dtype=float)
    probabilities = probabilities / probabilities.sum()
    return rng.choice(keys, size=size, p=probabilities)


def factory_from_line(production_line: str) -> str:
    """'F2-L1' -> 'Factory 2'"""
    return "Factory " + production_line.split("-")[0][1:]


# ---------------------------------------------------------------------------
# Generators: suppliers, parts, vehicles
# ---------------------------------------------------------------------------
def generate_suppliers() -> pd.DataFrame:
    """Build the suppliers table."""
    suppliers = pd.DataFrame(
        SUPPLIERS, columns=["supplier_name", "country", "supplier_category"]
    )
    suppliers.insert(0, "supplier_id", range(1, len(suppliers) + 1))
    return suppliers


def generate_parts(suppliers: pd.DataFrame) -> pd.DataFrame:
    """Build the parts table. Supplier names are converted to supplier_id."""
    supplier_ids = dict(zip(suppliers["supplier_name"], suppliers["supplier_id"]))

    parts = pd.DataFrame(
        PARTS, columns=["part_name", "category", "supplier_name", "unit_cost"]
    )
    parts["supplier_id"] = parts["supplier_name"].map(supplier_ids)
    parts = parts.drop(columns=["supplier_name"])
    parts.insert(0, "part_id", range(1, len(parts) + 1))

    # Keep the same column order as the ER diagram
    return parts[["part_id", "part_name", "category", "supplier_id", "unit_cost"]]


def generate_vehicles(rng: np.random.Generator) -> pd.DataFrame:
    """Build the vehicles table (N_VEHICLES rows)."""
    frames = []

    for model, config in VEHICLE_MODELS.items():
        n = round(config["share"] * N_VEHICLES)

        # A model cannot be produced before its launch year
        year_weights = {
            year: weight
            for year, weight in YEAR_WEIGHTS.items()
            if year >= config["first_year"]
        }

        production_line = weighted_choice(rng, config["lines"], n)
        frames.append(
            pd.DataFrame(
                {
                    "model": model,
                    "production_year": weighted_choice(rng, year_weights, n).astype(int),
                    "production_line": production_line,
                    "factory": [factory_from_line(line) for line in production_line],
                    "fuel_type": weighted_choice(rng, config["fuel"], n),
                }
            )
        )

    vehicles = pd.concat(frames, ignore_index=True)

    # Shuffle, then sort by year so older vehicles get smaller IDs
    vehicles = vehicles.sample(frac=1, random_state=SEED)
    vehicles = vehicles.sort_values("production_year", kind="stable")
    vehicles = vehicles.reset_index(drop=True)
    vehicles.insert(0, "vehicle_id", range(1, len(vehicles) + 1))

    return vehicles[
        [
            "vehicle_id",
            "model",
            "production_year",
            "production_line",
            "factory",
            "fuel_type",
        ]
    ]


# ---------------------------------------------------------------------------
# Generators: quality incidents
# ---------------------------------------------------------------------------
def generate_base_dates(rng: np.random.Generator, n: int) -> pd.DatetimeIndex:
    """Random incident dates. Later months get more incidents (growing trend)."""
    months = pd.date_range(DATA_START, DATA_END, freq="MS")  # first day of each month

    trend = 1 + MONTHLY_TREND * np.arange(len(months))
    noise = rng.uniform(0.9, 1.1, size=len(months))
    weights = trend * noise
    probabilities = weights / weights.sum()

    month_index = rng.choice(len(months), size=n, p=probabilities)
    day_offset = rng.integers(0, months.days_in_month.values[month_index])
    return months[month_index] + pd.to_timedelta(day_offset, unit="D")


def assign_vehicles(
    rng: np.random.Generator, dates: pd.DatetimeIndex, vehicles: pd.DataFrame
) -> np.ndarray:
    """
    Pick a vehicle for every incident date.
    A vehicle can only have incidents after it entered service, risky models
    are picked more often, and older vehicles are picked more often.
    """
    vehicle_ids = np.empty(len(dates), dtype=int)
    periods = dates.to_period("M")

    for period in periods.unique():
        positions = np.where(periods == period)[0]
        year, month = period.year, period.month

        in_service = (vehicles["production_year"] < year) | (
            (vehicles["production_year"] == year) & (month >= IN_SERVICE_MONTH)
        )
        pool = vehicles[in_service]

        age = year - pool["production_year"]
        weights = pool["model"].map(MODEL_RISK) * (1 + AGE_RISK_PER_YEAR * age)
        probabilities = (weights / weights.sum()).to_numpy()

        vehicle_ids[positions] = rng.choice(
            pool["vehicle_id"].to_numpy(), size=len(positions), p=probabilities
        )

    return vehicle_ids


def part_probabilities(parts: pd.DataFrame, fuel_type: str, month: int) -> np.ndarray:
    """Probability of each part failing, for one fuel type in one month."""
    weights = []
    for part_name, category in zip(parts["part_name"], parts["category"]):
        weight = float(PART_FAILURE_WEIGHT[part_name])

        # Parts that do not exist on this vehicle type
        if fuel_type == "Electric" and part_name in ELECTRIC_EXCLUDED_PARTS:
            weight = 0.0
        if fuel_type == "Diesel" and part_name in DIESEL_EXCLUDED_PARTS:
            weight = 0.0
        if part_name == "Battery Module" and fuel_type not in BATTERY_FUEL_TYPES:
            weight = 0.0

        # Electric vehicles rely more on some parts
        if fuel_type == "Electric":
            weight *= ELECTRIC_PART_BOOST.get(part_name, 1.0)

        # Seasonal effects
        for season_category, season_months, multiplier in SEASONAL_EFFECTS:
            if category == season_category and month in season_months:
                weight *= multiplier

        weights.append(weight)

    weights = np.array(weights)
    return weights / weights.sum()


def assign_parts(
    rng: np.random.Generator,
    dates: pd.DatetimeIndex,
    vehicle_ids: np.ndarray,
    vehicles: pd.DataFrame,
    parts: pd.DataFrame,
) -> np.ndarray:
    """Pick the failed part for every incident (depends on fuel type and season)."""
    fuel_of_vehicle = vehicles.set_index("vehicle_id")["fuel_type"]
    fuel_types = fuel_of_vehicle.loc[vehicle_ids].to_numpy()
    months = np.asarray(dates.month)

    part_ids = np.empty(len(dates), dtype=int)
    part_id_values = parts["part_id"].to_numpy()

    combinations = set(zip(fuel_types, months))
    for fuel_type, month in combinations:
        positions = np.where((fuel_types == fuel_type) & (months == month))[0]
        probabilities = part_probabilities(parts, fuel_type, month)
        part_ids[positions] = rng.choice(
            part_id_values, size=len(positions), p=probabilities
        )

    return part_ids


def generate_spike_incidents(
    rng: np.random.Generator, vehicles: pd.DataFrame, parts: pd.DataFrame
) -> pd.DataFrame:
    """
    Planted pattern 1: a faulty batch of Supplier B electronics.
    Vehicles produced in SPIKE_VEHICLE_YEAR fail between SPIKE_START and SPIKE_END.
    """
    start = pd.Timestamp(SPIKE_START)
    n_days = (pd.Timestamp(SPIKE_END) - start).days + 1
    dates = start + pd.to_timedelta(
        rng.integers(0, n_days, size=N_SPIKE_INCIDENTS), unit="D"
    )

    pool = vehicles[
        (vehicles["production_year"] == SPIKE_VEHICLE_YEAR)
        & (vehicles["fuel_type"] != "Electric")
    ]
    vehicle_ids = rng.choice(pool["vehicle_id"].to_numpy(), size=N_SPIKE_INCIDENTS)

    part_ids_by_name = dict(zip(parts["part_name"], parts["part_id"]))
    spike_part_names = weighted_choice(rng, SPIKE_PART_WEIGHT, N_SPIKE_INCIDENTS)
    part_ids = [part_ids_by_name[name] for name in spike_part_names]

    return pd.DataFrame(
        {
            "incident_date": dates,
            "vehicle_id": vehicle_ids,
            "part_id": part_ids,
            "is_spike": True,
        }
    )


# ---------------------------------------------------------------------------
# Generators: defect details (source, type, severity, complaint, status)
# ---------------------------------------------------------------------------
def draw_defect_source(
    rng: np.random.Generator,
    category: str,
    production_line: str,
    incident_date: pd.Timestamp,
    is_spike: bool,
) -> str:
    if is_spike:
        return weighted_choice(rng, SPIKE_SOURCE_WEIGHTS, 1)[0]

    weights = dict(BASE_SOURCE_WEIGHTS)
    for source, multiplier in CATEGORY_SOURCE_MULTIPLIERS.get(category, {}).items():
        weights[source] *= multiplier

    # Planted pattern 2: production line problem
    if production_line == PROBLEM_LINE and incident_date >= pd.Timestamp(PROBLEM_LINE_START):
        for source, multiplier in PROBLEM_LINE_MULTIPLIERS.items():
            weights[source] *= multiplier

    return weighted_choice(rng, weights, 1)[0]


def draw_defect_type(
    rng: np.random.Generator, category: str, source: str, is_spike: bool
) -> str:
    if is_spike:
        return weighted_choice(rng, SPIKE_TYPE_WEIGHTS, 1)[0]

    weights = dict(CATEGORY_DEFECT_TYPES[category])

    # Assembly errors often show up as incorrect installation
    if source == "Assembly Error":
        total = sum(weights.values())
        weights = {defect: weight / total * 0.5 for defect, weight in weights.items()}
        weights["Incorrect Installation"] = 0.5

    return weighted_choice(rng, weights, 1)[0]


def draw_severity(
    rng: np.random.Generator, defect_type: str, part_name: str, category: str
) -> str:
    probabilities = np.array(SEVERITY_BY_DEFECT_TYPE[defect_type], dtype=float)

    if category == "Brake" or part_name == "Airbag Control Module":
        probabilities[2:] *= SAFETY_CRITICAL_BOOST  # High and Critical
    probabilities = probabilities / probabilities.sum()

    return rng.choice(SEVERITY_LEVELS, p=probabilities)


def draw_status(rng: np.random.Generator, incident_dates: pd.Series) -> np.ndarray:
    """Old incidents are mostly closed, recent ones are mostly still open."""
    age_days = (pd.Timestamp(DATA_END) - incident_dates).dt.days.to_numpy()
    status = np.empty(len(incident_dates), dtype=object)

    for mask, probabilities in [
        (age_days > 90, STATUS_OLD),
        ((age_days > 30) & (age_days <= 90), STATUS_MIDDLE),
        (age_days <= 30, STATUS_RECENT),
    ]:
        status[mask] = rng.choice(STATUS_LEVELS, size=mask.sum(), p=probabilities)

    return status


def generate_incidents(
    rng: np.random.Generator, vehicles: pd.DataFrame, parts: pd.DataFrame
) -> pd.DataFrame:
    """Build the quality_incidents table (N_INCIDENTS rows)."""
    # 1. When, which vehicle and which part - normal incidents
    n_base = N_INCIDENTS - N_SPIKE_INCIDENTS
    base_dates = generate_base_dates(rng, n_base)
    base_vehicle_ids = assign_vehicles(rng, base_dates, vehicles)
    base_part_ids = assign_parts(rng, base_dates, base_vehicle_ids, vehicles, parts)
    base = pd.DataFrame(
        {
            "incident_date": base_dates,
            "vehicle_id": base_vehicle_ids,
            "part_id": base_part_ids,
            "is_spike": False,
        }
    )

    # 2. Planted pattern 1: faulty Supplier B batch
    spike = generate_spike_incidents(rng, vehicles, parts)

    incidents = pd.concat([base, spike], ignore_index=True)
    incidents = incidents.sort_values("incident_date", kind="stable").reset_index(drop=True)
    incidents.insert(0, "incident_id", range(1, len(incidents) + 1))

    # 3. Defect details, one incident at a time
    details = incidents.merge(
        vehicles[["vehicle_id", "production_line"]], on="vehicle_id", how="left"
    ).merge(parts[["part_id", "part_name", "category"]], on="part_id", how="left")

    sources, types, severities, complaints = [], [], [], []
    for row in details.itertuples():
        source = draw_defect_source(
            rng, row.category, row.production_line, row.incident_date, row.is_spike
        )
        defect_type = draw_defect_type(rng, row.category, source, row.is_spike)
        severity = draw_severity(rng, defect_type, row.part_name, row.category)
        complaint = bool(rng.random() < COMPLAINT_PROBABILITY[severity])

        sources.append(source)
        types.append(defect_type)
        severities.append(severity)
        complaints.append(complaint)

    incidents["defect_type"] = types
    incidents["defect_source"] = sources
    incidents["severity"] = severities
    incidents["customer_complaint"] = complaints
    incidents["status"] = draw_status(rng, incidents["incident_date"])

    return incidents[
        [
            "incident_id",
            "vehicle_id",
            "part_id",
            "incident_date",
            "defect_type",
            "defect_source",
            "severity",
            "customer_complaint",
            "status",
        ]
    ]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(
    suppliers: pd.DataFrame,
    parts: pd.DataFrame,
    vehicles: pd.DataFrame,
    incidents: pd.DataFrame,
) -> None:
    """Basic sanity checks. Raises AssertionError if something is wrong."""
    # Suppliers and parts
    assert len(suppliers) == 10, "Expected 10 suppliers"
    assert len(parts) == 30, "Expected 30 parts"

    assert suppliers["supplier_id"].is_unique, "supplier_id must be unique"
    assert parts["part_id"].is_unique, "part_id must be unique"

    assert parts["supplier_id"].notna().all(), "A part has an unknown supplier"
    assert parts["supplier_id"].isin(suppliers["supplier_id"]).all(), (
        "A part points to a supplier that does not exist"
    )
    assert (parts["unit_cost"] > 0).all(), "unit_cost must be positive"

    # Vehicles
    assert len(vehicles) == N_VEHICLES, f"Expected {N_VEHICLES} vehicles"
    assert vehicles["vehicle_id"].is_unique, "vehicle_id must be unique"
    assert vehicles.notna().all().all(), "vehicles table has missing values"
    assert vehicles["production_year"].between(2021, 2025).all(), (
        "production_year out of range"
    )
    assert vehicles["fuel_type"].isin(["Petrol", "Diesel", "Electric", "Hybrid"]).all(), (
        "Unknown fuel type"
    )
    electric = vehicles["fuel_type"] == "Electric"
    assert (vehicles.loc[electric, "model"] == "Electric Crossover").all(), (
        "Only the Electric Crossover can be electric"
    )
    assert (vehicles.loc[electric, "production_year"] >= 2022).all(), (
        "Electric Crossover cannot be produced before 2022"
    )

    # Quality incidents
    assert len(incidents) == N_INCIDENTS, f"Expected {N_INCIDENTS} incidents"
    assert incidents["incident_id"].is_unique, "incident_id must be unique"
    assert incidents.notna().all().all(), "quality_incidents has missing values"
    assert incidents["vehicle_id"].isin(vehicles["vehicle_id"]).all(), (
        "An incident points to a vehicle that does not exist"
    )
    assert incidents["part_id"].isin(parts["part_id"]).all(), (
        "An incident points to a part that does not exist"
    )
    assert incidents["incident_date"].between(DATA_START, DATA_END).all(), (
        "incident_date out of range"
    )
    assert incidents["severity"].isin(SEVERITY_LEVELS).all(), "Unknown severity"
    assert incidents["status"].isin(STATUS_LEVELS).all(), "Unknown status"

    # An incident cannot happen before the vehicle entered service
    check = incidents.merge(
        vehicles[["vehicle_id", "production_year", "fuel_type"]], on="vehicle_id"
    ).merge(parts[["part_id", "part_name"]], on="part_id")
    in_service_date = pd.to_datetime(
        check["production_year"].astype(str) + f"-{IN_SERVICE_MONTH:02d}-01"
    )
    assert (check["incident_date"] >= in_service_date).all(), (
        "An incident happened before the vehicle entered service"
    )

    # Parts must exist on the vehicle type
    is_electric = check["fuel_type"] == "Electric"
    assert not check.loc[is_electric, "part_name"].isin(ELECTRIC_EXCLUDED_PARTS).any(), (
        "An electric vehicle has an incident on a part it does not have"
    )
    battery = check["part_name"] == "Battery Module"
    assert check.loc[battery, "fuel_type"].isin(BATTERY_FUEL_TYPES).all(), (
        "Battery Module incident on a vehicle without a battery module"
    )

    print("Validation passed.")


# ---------------------------------------------------------------------------
# Summary (helps you check that the planted patterns are visible)
# ---------------------------------------------------------------------------
def print_incident_summary(
    suppliers: pd.DataFrame,
    parts: pd.DataFrame,
    vehicles: pd.DataFrame,
    incidents: pd.DataFrame,
) -> None:
    data = (
        incidents.merge(parts, on="part_id")
        .merge(suppliers, on="supplier_id")
        .merge(vehicles, on="vehicle_id")
    )

    print("\nIncidents per year:")
    print(incidents["incident_date"].dt.year.value_counts().sort_index().to_string())

    print("\nIncidents per month in 2024 (look for the spike):")
    in_2024 = incidents[incidents["incident_date"].dt.year == 2024]
    print(in_2024["incident_date"].dt.month.value_counts().sort_index().to_string())

    print("\nTop 10 failing parts:")
    print(data["part_name"].value_counts().head(10).to_string())

    print("\nDefect source distribution (%):")
    print((data["defect_source"].value_counts(normalize=True) * 100).round(1).to_string())

    print("\nSupplier share of 'Supplier Defect' incidents (%):")
    supplier_defects = data[data["defect_source"] == "Supplier Defect"]
    print(
        (supplier_defects["supplier_name"].value_counts(normalize=True) * 100)
        .round(1)
        .head(5)
        .to_string()
    )

    print("\nAssembly Error share by production line, 2025 (%):")
    in_2025 = data[data["incident_date"].dt.year == 2025]
    share = in_2025.groupby("production_line")["defect_source"].apply(
        lambda s: round((s == "Assembly Error").mean() * 100, 1)
    )
    print(share.to_string())

    print("\nSeverity distribution (%):")
    print((data["severity"].value_counts(normalize=True) * 100).round(1).to_string())

    print(f"\nCustomer complaint rate: {data['customer_complaint'].mean() * 100:.1f}%")

    print("\nStatus distribution:")
    print(data["status"].value_counts().to_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    suppliers = generate_suppliers()
    parts = generate_parts(suppliers)
    vehicles = generate_vehicles(rng)
    incidents = generate_incidents(rng, vehicles, parts)

    validate(suppliers, parts, vehicles, incidents)

    suppliers.to_csv(RAW_DATA_DIR / "suppliers.csv", index=False)
    parts.to_csv(RAW_DATA_DIR / "parts.csv", index=False)
    vehicles.to_csv(RAW_DATA_DIR / "vehicles.csv", index=False)
    incidents.to_csv(RAW_DATA_DIR / "quality_incidents.csv", index=False)

    print(f"suppliers.csv:         {len(suppliers)} rows")
    print(f"parts.csv:             {len(parts)} rows")
    print(f"vehicles.csv:          {len(vehicles)} rows")
    print(f"quality_incidents.csv: {len(incidents)} rows")
    print(f"Saved to: {RAW_DATA_DIR}")

    print_incident_summary(suppliers, parts, vehicles, incidents)

    print("\nFirst 5 incidents:")
    print(incidents.head().to_string(index=False))


if __name__ == "__main__":
    main()