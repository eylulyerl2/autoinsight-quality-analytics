"""
AutoInsight - synthetic data generation.

Step 1: suppliers and parts.
Step 2: vehicles.

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

# Incidents will be generated between these dates (used in later steps)
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
# Generators
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
# Validation
# ---------------------------------------------------------------------------
def validate(
    suppliers: pd.DataFrame, parts: pd.DataFrame, vehicles: pd.DataFrame
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

    print("Validation passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    suppliers = generate_suppliers()
    parts = generate_parts(suppliers)
    vehicles = generate_vehicles(rng)

    validate(suppliers, parts, vehicles)

    suppliers.to_csv(RAW_DATA_DIR / "suppliers.csv", index=False)
    parts.to_csv(RAW_DATA_DIR / "parts.csv", index=False)
    vehicles.to_csv(RAW_DATA_DIR / "vehicles.csv", index=False)

    print(f"suppliers.csv: {len(suppliers)} rows")
    print(f"parts.csv:     {len(parts)} rows")
    print(f"vehicles.csv:  {len(vehicles)} rows")
    print(f"Saved to: {RAW_DATA_DIR}")

    print("\nVehicles per model:")
    print(vehicles["model"].value_counts().to_string())
    print("\nVehicles per production year:")
    print(vehicles["production_year"].value_counts().sort_index().to_string())
    print("\nVehicles per fuel type:")
    print(vehicles["fuel_type"].value_counts().to_string())
    print("\nFirst 5 vehicles:")
    print(vehicles.head().to_string(index=False))


if __name__ == "__main__":
    main()