"""
AutoInsight - synthetic data generation, part 2.

Step 4: part replacements.
Step 5: corrective actions.

This script reads the CSV files created by generate_data.py, so run that first:
    python src/generate_data.py
    python src/generate_service_data.py

All data is synthetic. All costs are in TRY (Turkish Lira) at constant 2025 prices
(no inflation adjustment, so cost changes over time come from volume and part mix).
"""

import numpy as np
import pandas as pd

# Shared settings and helpers from the first script
from generate_data import (
    DATA_END,
    IN_SERVICE_MONTH,
    RAW_DATA_DIR,
    SEED,
    SPIKE_END,
    SPIKE_START,
    weighted_choice,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
N_REPLACEMENTS = 3000
N_EXTRA_REPLACEMENTS = 250  # second part replaced during the same service visit
N_CORRECTIVE_ACTIONS = 2000

SNAPSHOT = pd.Timestamp(DATA_END)  # "today" inside the dataset

# ---------------------------------------------------------------------------
# Part replacement settings
# ---------------------------------------------------------------------------
# --- Which incidents lead to a replacement? ----------------------------------
REPLACEMENT_PROBABILITY = {"Low": 0.35, "Medium": 0.55, "High": 0.75, "Critical": 0.90}
NON_CLOSED_FACTOR = 0.5  # incidents that are still open are less likely to have one
# Extra parts are more likely on serious incidents
EXTRA_SEVERITY_WEIGHT = {"Low": 1, "Medium": 1, "High": 2, "Critical": 3}

# --- Service centers ---------------------------------------------------------
SERVICE_CENTER_WEIGHTS = {
    "Service Center 1": 0.20,
    "Service Center 2": 0.18,
    "Service Center 3": 0.15,
    "Service Center 4": 0.12,
    "Service Center 5": 0.12,
    "Service Center 6": 0.10,
    "Service Center 7": 0.07,
    "Service Center 8": 0.06,
}
# Speed factor: 1.0 = normal, bigger = slower.
# Planted pattern 3: Service Center 5 is much slower than the others.
SERVICE_CENTER_SPEED = {
    "Service Center 1": 0.9,
    "Service Center 2": 1.0,
    "Service Center 3": 1.0,
    "Service Center 4": 1.0,
    "Service Center 5": 1.8,
    "Service Center 6": 1.0,
    "Service Center 7": 1.3,
    "Service Center 8": 1.1,
}

# --- Timeline ----------------------------------------------------------------
SERVICE_DELAY_MEAN_DAYS = 3  # days between the incident and the service visit
# Average days to receive a part, by supplier country
SUPPLIER_LEAD_DAYS = {
    "Turkey": 2,
    "Poland": 5,
    "Romania": 5,
    "Germany": 5,
    "India": 9,
    "Japan": 10,
    "South Korea": 10,
    "China": 12,
    "Mexico": 11,
}
IN_STOCK_PROBABILITY = 0.25  # part is already at the service center (no waiting)
# Planted pattern 1 (continued): during the faulty batch period, Supplier B
# parts are hard to get, so waiting times are longer.
SHORTAGE_SUPPLIER = "Supplier B"
SHORTAGE_MULTIPLIER = 1.8
# Average repair days after the part arrives, by severity
REPAIR_DAYS_BY_SEVERITY = {"Low": 1, "Medium": 2, "High": 3, "Critical": 5}

# --- Warranty ----------------------------------------------------------------
WARRANTY_YEARS = 3
BATTERY_WARRANTY_YEARS = 8  # Battery Module has a longer warranty

# --- Costs (TRY, constant 2025 prices, no inflation adjustment) --------------
# parts.unit_cost is used as the price in every year.
LABOR_RATE = 700  # TRY per hour
LABOR_HOURS = {
    "Engine": 6.0,
    "Transmission": 8.0,
    "Electronics": 2.0,
    "Electrical": 2.5,
    "Brake": 1.5,
    "Cooling": 3.0,
    "HVAC": 3.5,
    "Suspension": 2.5,
    "Steering": 3.0,
    "Fuel System": 2.5,
    "Body & Interior": 1.5,
}
EXTRA_LABOR_FACTOR = 0.4  # the vehicle is already in the workshop
# Transportation cost of a part, by supplier country
TRANSPORT_BASE = {
    "Turkey": 150,
    "Poland": 600,
    "Romania": 550,
    "Germany": 650,
    "India": 1100,
    "Japan": 1300,
    "South Korea": 1300,
    "China": 1400,
    "Mexico": 1500,
}
TRANSPORT_SIZE_FACTOR = {"Engine": 1.5, "Transmission": 1.5, "HVAC": 1.5, "Electronics": 0.4}
IN_STOCK_TRANSPORT_FACTOR = 0.3  # local stock is cheap to move

# ---------------------------------------------------------------------------
# Corrective action settings
# ---------------------------------------------------------------------------
# --- Which incidents get a corrective action? --------------------------------
ACTION_SEVERITY_WEIGHT = {"Low": 0.12, "Medium": 0.30, "High": 0.55, "Critical": 0.80}
ACTION_SOURCE_WEIGHT = {
    "Supplier Defect": 1.3,
    "Manufacturing Error": 1.2,
    "Design Issue": 1.2,
    "Assembly Error": 1.1,
    "Material Failure": 1.1,
    "Unknown": 0.6,
    "Customer Misuse": 0.3,
}
ACTION_COMPLAINT_FACTOR = 1.3
ACTION_SPIKE_FACTOR = 2.0  # the faulty Supplier B batch gets extra attention
ACTION_LATEST_INCIDENT_GAP_DAYS = 3  # very recent incidents have no action yet

# --- Root cause and action (matched pairs), by defect source -----------------
ROOT_CAUSES = {
    "Manufacturing Error": [
        ("Machine calibration drift", "Recalibrate equipment and update process control plan"),
        ("Incorrect torque settings", "Correct torque specification and add torque monitoring"),
        ("Insufficient process control", "Introduce statistical process control on the line"),
        ("Operator training gap", "Retrain operators and add in-line inspection"),
    ],
    "Supplier Defect": [
        ("Supplier process deviation", "Issue supplier corrective action request (SCAR)"),
        ("Out-of-tolerance component batch", "Quarantine affected batch and replace parts"),
        ("Inadequate supplier quality inspection", "Tighten incoming inspection for supplier parts"),
        ("Supplier material substitution", "Audit the supplier and require approved materials"),
    ],
    "Assembly Error": [
        ("Incorrect assembly sequence", "Update work instructions and assembly sequence"),
        ("Missing or unclear work instruction", "Rewrite work instructions with photos"),
        ("Assembly tool wear", "Replace worn tools and add tool maintenance schedule"),
        ("Operator training gap", "Add poka-yoke check at the assembly station"),
    ],
    "Material Failure": [
        ("Substandard raw material", "Change material specification"),
        ("Heat treatment deviation", "Require heat treatment certificates from supplier"),
        ("Material fatigue under load", "Switch to a higher grade material"),
        ("Corrosion due to coating defect", "Improve coating process and add corrosion test"),
    ],
    "Design Issue": [
        ("Insufficient design margin", "Raise design margin through an engineering change"),
        ("Software logic flaw", "Release a software update"),
        ("Thermal design limitation", "Redesign cooling and heat protection"),
        ("Tolerance stack-up in design", "Revise tolerances in the design drawings"),
    ],
    "Customer Misuse": [
        ("Improper use by customer", "Update owner manual and customer communication"),
        ("Missed maintenance schedule", "Send service reminders to customers"),
        ("Non-approved modification", "Add warning about modifications to warranty terms"),
    ],
    "Unknown": [
        ("Root cause not identified", "Extended monitoring and data collection"),
        ("Intermittent fault not reproducible", "Collect field data and repeat diagnostics"),
    ],
}

# --- Responsible department, by defect source --------------------------------
DEPARTMENTS = {
    "Manufacturing Error": {"Production": 0.8, "Quality Assurance": 0.2},
    "Supplier Defect": {"Supplier Quality": 0.8, "Quality Assurance": 0.2},
    "Assembly Error": {"Production": 0.85, "Quality Assurance": 0.15},
    "Material Failure": {"Supplier Quality": 0.5, "Quality Assurance": 0.5},
    "Design Issue": {"Design Engineering": 0.9, "Quality Assurance": 0.1},
    "Customer Misuse": {"Customer Service": 0.9, "Quality Assurance": 0.1},
    "Unknown": {"Quality Assurance": 1.0},
}
# How long an action takes (min days, max days), by department
ACTION_DURATION_DAYS = {
    "Production": (15, 60),
    "Supplier Quality": (30, 90),
    "Quality Assurance": (20, 60),
    "Design Engineering": (60, 150),
    "Customer Service": (5, 20),
}
ACTION_START_DELAY_MEAN_DAYS = 6

# --- Recurrence (did the problem come back after the action?) ----------------
# Planted pattern 4: some departments and parts have more recurrences
RECURRENCE_BASE = {
    "Production": 0.15,
    "Supplier Quality": 0.30,
    "Quality Assurance": 0.25,
    "Design Engineering": 0.12,
    "Customer Service": 0.35,
}
RECURRENCE_PART_MULTIPLIER = {"Water Pump": 1.6, "Infotainment Display": 1.4}
RECURRENCE_SUPPLIER_MULTIPLIER = {"Supplier B": 1.4}
MAX_RECURRENCE_PROBABILITY = 0.85


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def days(values) -> pd.TimedeltaIndex:
    """Turn a list of day counts into timedeltas so they can be added to dates."""
    return pd.to_timedelta(np.asarray(values), unit="D")


def load_tables() -> dict:
    """Read the tables created by generate_data.py."""
    return {
        "suppliers": pd.read_csv(RAW_DATA_DIR / "suppliers.csv"),
        "parts": pd.read_csv(RAW_DATA_DIR / "parts.csv"),
        "vehicles": pd.read_csv(RAW_DATA_DIR / "vehicles.csv"),
        "incidents": pd.read_csv(
            RAW_DATA_DIR / "quality_incidents.csv", parse_dates=["incident_date"]
        ),
    }


def build_part_info(parts: pd.DataFrame, suppliers: pd.DataFrame) -> pd.DataFrame:
    """One row per part, including its supplier name and country."""
    info = parts.merge(suppliers, on="supplier_id")
    info = info.rename(columns={"category": "part_category", "country": "supplier_country"})
    return info[
        [
            "part_id",
            "part_name",
            "part_category",
            "unit_cost",
            "supplier_name",
            "supplier_country",
        ]
    ]


# ---------------------------------------------------------------------------
# Part replacements
# ---------------------------------------------------------------------------
def add_timeline(rng: np.random.Generator, replacements: pd.DataFrame) -> pd.DataFrame:
    """Service center, service date, part arrival date and resolution date."""
    n = len(replacements)

    # Service center (some are slower than others)
    centers = weighted_choice(rng, SERVICE_CENTER_WEIGHTS, n)
    speed = pd.Series(centers).map(SERVICE_CENTER_SPEED).to_numpy()
    replacements["service_center"] = centers

    # Days until the service visit
    service_delay = np.round(rng.gamma(2.0, SERVICE_DELAY_MEAN_DAYS / 2 * speed)).astype(int)

    # Days waiting for the part
    lead_days = replacements["supplier_country"].map(SUPPLIER_LEAD_DAYS).to_numpy(dtype=float)
    wait = rng.gamma(3.0, lead_days / 3.0)
    in_stock = rng.random(n) < IN_STOCK_PROBABILITY
    wait[in_stock] = 0

    shortage = (replacements["supplier_name"] == SHORTAGE_SUPPLIER) & replacements[
        "incident_date"
    ].between(SPIKE_START, SPIKE_END)
    wait = np.where(shortage, wait * SHORTAGE_MULTIPLIER, wait)
    wait = np.round(wait).astype(int)

    # Days to repair after the part arrives
    repair_lambda = replacements["severity"].map(REPAIR_DAYS_BY_SEVERITY).to_numpy(dtype=float)
    repair = 1 + rng.poisson(repair_lambda * speed)

    service_date = replacements["incident_date"] + days(service_delay)
    arrival_date = service_date + days(wait)
    resolution_date = arrival_date + days(repair)

    # Nothing can happen after the snapshot date
    closed = replacements["status"] == "Closed"
    service_date = service_date.clip(upper=SNAPSHOT)
    arrival_date = arrival_date.where(arrival_date <= SNAPSHOT).where(~closed, arrival_date.clip(upper=SNAPSHOT))
    resolution_date = resolution_date.clip(upper=SNAPSHOT).where(closed)  # open cases: no resolution

    replacements["service_date"] = service_date
    replacements["part_arrival_date"] = arrival_date
    replacements["resolution_date"] = resolution_date
    replacements["in_stock"] = in_stock
    return replacements


def add_warranty(replacements: pd.DataFrame) -> pd.DataFrame:
    """Warranty depends on the vehicle age. Customer misuse is never covered."""
    production_date = pd.to_datetime(
        replacements["production_year"].astype(str) + f"-{IN_SERVICE_MONTH:02d}-01"
    )
    age_years = (replacements["incident_date"] - production_date).dt.days / 365.25
    limit = np.where(
        replacements["part_name"] == "Battery Module", BATTERY_WARRANTY_YEARS, WARRANTY_YEARS
    )
    covered = (age_years <= limit) & (replacements["defect_source"] != "Customer Misuse")
    replacements["warranty_status"] = np.where(covered, "In Warranty", "Out of Warranty")
    return replacements


def add_costs(rng: np.random.Generator, replacements: pd.DataFrame) -> pd.DataFrame:
    """Part, labor and transportation cost (TRY, constant 2025 prices)."""
    n = len(replacements)

    replacement_cost = replacements["unit_cost"].to_numpy() * rng.uniform(0.95, 1.10, n)

    labor_hours = replacements["part_category"].map(LABOR_HOURS).to_numpy() * rng.uniform(0.7, 1.4, n)
    labor_factor = np.where(replacements["is_extra"], EXTRA_LABOR_FACTOR, 1.0)
    labor_cost = labor_hours * LABOR_RATE * labor_factor

    size_factor = replacements["part_category"].map(TRANSPORT_SIZE_FACTOR).fillna(1.0).to_numpy()
    transport_cost = (
        replacements["supplier_country"].map(TRANSPORT_BASE).to_numpy(dtype=float)
        * size_factor
        * rng.uniform(0.8, 1.3, n)
    )
    transport_cost = np.where(replacements["in_stock"], transport_cost * IN_STOCK_TRANSPORT_FACTOR, transport_cost)

    replacements["replacement_cost"] = replacement_cost.round(2)
    replacements["labor_cost"] = labor_cost.round(2)
    replacements["transportation_cost"] = transport_cost.round(2)
    return replacements


def generate_replacements(
    rng: np.random.Generator,
    incidents: pd.DataFrame,
    part_info: pd.DataFrame,
    vehicles: pd.DataFrame,
) -> pd.DataFrame:
    """Build the part_replacements table (N_REPLACEMENTS rows)."""
    # 1. Choose which incidents lead to a replacement
    n_primary = N_REPLACEMENTS - N_EXTRA_REPLACEMENTS
    weights = incidents["severity"].map(REPLACEMENT_PROBABILITY) * np.where(
        incidents["status"] == "Closed", 1.0, NON_CLOSED_FACTOR
    )
    chosen = rng.choice(
        len(incidents), size=n_primary, replace=False, p=(weights / weights.sum()).to_numpy()
    )
    primary = (
        incidents.iloc[chosen]
        .merge(vehicles[["vehicle_id", "production_year"]], on="vehicle_id")
        .merge(part_info, on="part_id")
        .reset_index(drop=True)
    )

    # 2. Timeline and warranty (decided per incident)
    primary = add_timeline(rng, primary)
    primary = add_warranty(primary)
    primary["is_extra"] = False

    # 3. Some incidents need a second (related) part during the same visit.
    #    It is a different part from the same category, same visit, same dates.
    parts_by_category = part_info.groupby("part_category")["part_id"].apply(list).to_dict()
    has_related = primary["part_category"].map(lambda c: len(parts_by_category[c]) >= 2)
    candidates = primary[has_related]
    extra_weights = candidates["severity"].map(EXTRA_SEVERITY_WEIGHT)
    extra_index = rng.choice(
        candidates.index.to_numpy(),
        size=N_EXTRA_REPLACEMENTS,
        replace=False,
        p=(extra_weights / extra_weights.sum()).to_numpy(),
    )
    extra = primary.loc[extra_index].copy()
    extra["part_id"] = [
        rng.choice([p for p in parts_by_category[category] if p != part_id])
        for category, part_id in zip(extra["part_category"], extra["part_id"])
    ]
    part_columns = [c for c in part_info.columns if c != "part_id"]
    extra = extra.drop(columns=part_columns).merge(part_info, on="part_id", how="left")
    extra["is_extra"] = True

    replacements = pd.concat([primary, extra], ignore_index=True)

    # 4. Costs
    replacements = add_costs(rng, replacements)

    # 5. Final table
    replacements = replacements.sort_values("service_date", kind="stable").reset_index(drop=True)
    replacements.insert(0, "replacement_id", range(1, len(replacements) + 1))
    return replacements[
        [
            "replacement_id",
            "incident_id",
            "part_id",
            "service_date",
            "replacement_cost",
            "labor_cost",
            "transportation_cost",
            "warranty_status",
            "resolution_date",
            "service_center",
            "part_arrival_date",
        ]
    ]


# ---------------------------------------------------------------------------
# Corrective actions
# ---------------------------------------------------------------------------
def generate_corrective_actions(
    rng: np.random.Generator, incidents: pd.DataFrame, part_info: pd.DataFrame
) -> pd.DataFrame:
    """Build the corrective_actions table (N_CORRECTIVE_ACTIONS rows)."""
    data = incidents.merge(part_info[["part_id", "part_name", "supplier_name"]], on="part_id")
    latest = SNAPSHOT - pd.Timedelta(days=ACTION_LATEST_INCIDENT_GAP_DAYS)
    data = data[data["incident_date"] <= latest].reset_index(drop=True)

    # 1. Choose which incidents get a corrective action
    weights = (
        data["severity"].map(ACTION_SEVERITY_WEIGHT)
        * data["defect_source"].map(ACTION_SOURCE_WEIGHT)
        * np.where(data["customer_complaint"], ACTION_COMPLAINT_FACTOR, 1.0)
    )
    faulty_batch = (
        (data["supplier_name"] == SHORTAGE_SUPPLIER)
        & (data["defect_source"] == "Supplier Defect")
        & data["incident_date"].between(SPIKE_START, SPIKE_END)
    )
    weights = weights * np.where(faulty_batch, ACTION_SPIKE_FACTOR, 1.0)

    chosen = rng.choice(
        len(data), size=N_CORRECTIVE_ACTIONS, replace=False, p=(weights / weights.sum()).to_numpy()
    )
    actions = data.iloc[chosen].sort_values("incident_id").reset_index(drop=True)
    n = len(actions)

    # 2. Root cause, action and department
    root_causes, corrective_actions, departments = [], [], []
    for source in actions["defect_source"]:
        pairs = ROOT_CAUSES[source]
        root_cause, action = pairs[rng.integers(len(pairs))]
        root_causes.append(root_cause)
        corrective_actions.append(action)
        departments.append(weighted_choice(rng, DEPARTMENTS[source], 1)[0])

    # 3. Dates and status
    start_delay = 1 + rng.poisson(ACTION_START_DELAY_MEAN_DAYS, n)
    duration = [rng.integers(ACTION_DURATION_DAYS[d][0], ACTION_DURATION_DAYS[d][1] + 1) for d in departments]
    start_date = actions["incident_date"] + days(start_delay)
    end_date = start_date + days(duration)

    not_started = start_date > SNAPSHOT
    completed = ~not_started & (end_date <= SNAPSHOT)
    status = np.where(not_started, "Open", np.where(completed, "Completed", "In Progress"))

    # 4. Did the problem come back? Only known for completed actions.
    recurrence = []
    for is_completed, department, part_name, supplier_name in zip(
        completed, departments, actions["part_name"], actions["supplier_name"]
    ):
        if not is_completed:
            recurrence.append(pd.NA)
            continue
        probability = RECURRENCE_BASE[department]
        probability *= RECURRENCE_PART_MULTIPLIER.get(part_name, 1.0)
        probability *= RECURRENCE_SUPPLIER_MULTIPLIER.get(supplier_name, 1.0)
        probability = min(probability, MAX_RECURRENCE_PROBABILITY)
        recurrence.append(bool(rng.random() < probability))

    result = pd.DataFrame(
        {
            "incident_id": actions["incident_id"],
            "root_cause": root_causes,
            "corrective_action": corrective_actions,
            "responsible_department": departments,
            "action_start_date": start_date.where(~not_started),  # not started: no date
            "action_end_date": end_date.where(completed),  # only completed actions have an end date
            "action_status": status,
            "recurrence_after_action": pd.array(recurrence, dtype="boolean"),
        }
    )
    result.insert(0, "action_id", range(1, len(result) + 1))
    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(
    tables: dict, replacements: pd.DataFrame, actions: pd.DataFrame
) -> None:
    """Basic sanity checks. Raises AssertionError if something is wrong."""
    incidents = tables["incidents"]
    parts = tables["parts"]

    # Part replacements
    assert len(replacements) == N_REPLACEMENTS, f"Expected {N_REPLACEMENTS} replacements"
    assert replacements["replacement_id"].is_unique, "replacement_id must be unique"
    assert replacements["incident_id"].isin(incidents["incident_id"]).all(), (
        "A replacement points to an incident that does not exist"
    )
    assert replacements["part_id"].isin(parts["part_id"]).all(), (
        "A replacement points to a part that does not exist"
    )
    cost_columns = ["replacement_cost", "labor_cost", "transportation_cost"]
    assert (replacements[cost_columns] > 0).all().all(), "Costs must be positive"
    assert replacements["warranty_status"].isin(["In Warranty", "Out of Warranty"]).all()

    data = replacements.merge(incidents, on="incident_id")
    assert (replacements["service_date"].to_numpy() >= data["incident_date"].to_numpy()).all(), (
        "Service happened before the incident"
    )
    assert (replacements["service_date"] <= SNAPSHOT).all(), "Service date after snapshot"

    arrived = replacements["part_arrival_date"].notna()
    assert (
        replacements.loc[arrived, "part_arrival_date"] >= replacements.loc[arrived, "service_date"]
    ).all(), "Part arrived before the service date"

    resolved = replacements["resolution_date"].notna()
    assert (
        replacements.loc[resolved, "resolution_date"] >= replacements.loc[resolved, "part_arrival_date"]
    ).all(), "Resolved before the part arrived"
    assert (replacements["resolution_date"].dropna() <= SNAPSHOT).all(), "Resolution date after snapshot"
    assert (resolved == (data["status"] == "Closed")).all(), (
        "resolution_date must exist exactly for closed incidents"
    )

    # Corrective actions
    assert len(actions) == N_CORRECTIVE_ACTIONS, f"Expected {N_CORRECTIVE_ACTIONS} actions"
    assert actions["action_id"].is_unique, "action_id must be unique"
    assert actions["incident_id"].is_unique, "Only one action per incident in this dataset"
    assert actions["incident_id"].isin(incidents["incident_id"]).all(), (
        "An action points to an incident that does not exist"
    )

    action_data = actions.merge(incidents, on="incident_id")
    started = actions["action_start_date"].notna()
    assert (
        actions.loc[started, "action_start_date"].to_numpy()
        > action_data.loc[started, "incident_date"].to_numpy()
    ).all(), "Action started before the incident"

    ended = actions["action_end_date"].notna()
    assert (
        actions.loc[ended, "action_end_date"] >= actions.loc[ended, "action_start_date"]
    ).all(), "Action ended before it started"

    completed = actions["action_status"] == "Completed"
    assert (ended == completed).all(), "End date must exist exactly for completed actions"
    assert (actions["recurrence_after_action"].notna() == completed).all(), (
        "Recurrence is only known for completed actions"
    )
    assert (actions["action_status"] == "Open").eq(~started).all(), (
        "Open actions have not started"
    )

    print("Validation passed.")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def print_summary(
    tables: dict, replacements: pd.DataFrame, actions: pd.DataFrame
) -> None:
    incidents = tables["incidents"]
    part_info = build_part_info(tables["parts"], tables["suppliers"])

    data = replacements.merge(incidents[["incident_id", "incident_date"]], on="incident_id").merge(
        part_info, on="part_id"
    )
    data["total_cost"] = (
        data["replacement_cost"] + data["labor_cost"] + data["transportation_cost"]
    )
    data["resolution_days"] = (data["resolution_date"] - data["incident_date"]).dt.days
    data["wait_days"] = (data["part_arrival_date"] - data["service_date"]).dt.days

    print("\nWarranty status (%):")
    print((data["warranty_status"].value_counts(normalize=True) * 100).round(1).to_string())

    print(f"\nAverage resolution time: {data['resolution_days'].mean():.1f} days")
    print("\nAverage resolution time by service center (days):")
    print(data.groupby("service_center")["resolution_days"].mean().round(1).to_string())

    print(
        "\nCorrelation between part waiting time and resolution time: "
        f"{data['wait_days'].corr(data['resolution_days']):.2f}"
    )

    print(f"\nTotal quality cost: {data['total_cost'].sum():,.0f} TRY")
    print("Total cost by incident year (TRY):")
    print(data.groupby(data["incident_date"].dt.year)["total_cost"].sum().round(0).to_string())

    part_share = data[["replacement_cost", "labor_cost", "transportation_cost"]].sum()
    print("\nCost split (%):")
    print((part_share / part_share.sum() * 100).round(1).to_string())

    print("\nTop 5 parts by total cost (TRY):")
    print(data.groupby("part_name")["total_cost"].sum().sort_values(ascending=False).head(5).round(0).to_string())

    print("\nMost replaced parts:")
    print(data["part_name"].value_counts().head(5).to_string())

    print("\nCorrective action status:")
    print(actions["action_status"].value_counts().to_string())

    done = actions[actions["action_status"] == "Completed"].merge(
        incidents[["incident_id", "part_id"]], on="incident_id"
    ).merge(part_info, on="part_id")
    done["recurred"] = done["recurrence_after_action"].astype(bool)

    print(f"\nRecurrence rate (completed actions): {done['recurred'].mean() * 100:.1f}%")
    print("\nRecurrence rate by department (%):")
    print((done.groupby("responsible_department")["recurred"].mean() * 100).round(1).to_string())

    print("\nHighest recurrence by part (at least 15 completed actions, %):")
    by_part = done.groupby("part_name")["recurred"].agg(["mean", "count"])
    by_part = by_part[by_part["count"] >= 15].sort_values("mean", ascending=False)
    print((by_part["mean"] * 100).round(1).head(5).to_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # A different seed offset keeps this step independent from the first script
    rng = np.random.default_rng(SEED + 1)

    tables = load_tables()
    part_info = build_part_info(tables["parts"], tables["suppliers"])

    replacements = generate_replacements(rng, tables["incidents"], part_info, tables["vehicles"])
    actions = generate_corrective_actions(rng, tables["incidents"], part_info)

    validate(tables, replacements, actions)

    replacements.to_csv(RAW_DATA_DIR / "part_replacements.csv", index=False)
    actions.to_csv(RAW_DATA_DIR / "corrective_actions.csv", index=False)

    print(f"part_replacements.csv: {len(replacements)} rows")
    print(f"corrective_actions.csv: {len(actions)} rows")
    print(f"Saved to: {RAW_DATA_DIR}")

    print_summary(tables, replacements, actions)

    print("\nFirst 5 part replacements:")
    print(replacements.head().to_string(index=False))
    print("\nFirst 5 corrective actions:")
    print(actions.head().to_string(index=False))


if __name__ == "__main__":
    main()