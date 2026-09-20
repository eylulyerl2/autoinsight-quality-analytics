# ER Diagram

Entity-relationship diagram for the AutoInsight database (v1 draft).

```mermaid
erDiagram
    suppliers ||--o{ parts : supplies
    vehicles ||--o{ quality_incidents : "has"
    parts ||--o{ quality_incidents : "involved in"
    quality_incidents ||--o{ part_replacements : "leads to"
    parts ||--o{ part_replacements : "is replaced in"
    quality_incidents ||--o{ corrective_actions : "triggers"

    suppliers {
        int supplier_id PK
        string supplier_name
        string country
        string supplier_category
    }

    parts {
        int part_id PK
        string part_name
        string category
        int supplier_id FK
        decimal unit_cost
    }

    vehicles {
        int vehicle_id PK
        string model
        int production_year
        string production_line
        string factory
        string fuel_type
    }

    quality_incidents {
        int incident_id PK
        int vehicle_id FK
        int part_id FK
        date incident_date
        string defect_type
        string defect_source
        string severity
        boolean customer_complaint
        string status
    }

    part_replacements {
        int replacement_id PK
        int incident_id FK
        int part_id FK
        date service_date
        decimal replacement_cost
        decimal labor_cost
        decimal transportation_cost
        string warranty_status
        date resolution_date
        string service_center "added: service performance analysis"
        date part_arrival_date "added: part waiting time analysis"
    }

    corrective_actions {
        int action_id PK
        int incident_id FK
        string root_cause
        string corrective_action
        string responsible_department
        date action_start_date
        date action_end_date
        string action_status
        boolean recurrence_after_action
    }
```

## Relationships

| Relationship | Meaning |
|--------------|---------|
| `suppliers` → `parts` | One supplier supplies many parts; each part has one supplier. |
| `vehicles` → `quality_incidents` | One vehicle can have many quality incidents. |
| `parts` → `quality_incidents` | One part can be involved in many incidents. |
| `quality_incidents` → `part_replacements` | One incident can lead to zero or more part replacements (not every incident needs a replacement, which is why there are fewer replacements than incidents). |
| `parts` → `part_replacements` | One part can be replaced many times. |
| `quality_incidents` → `corrective_actions` | One incident can trigger zero or more corrective actions. |

## Design Notes

- **`part_id` in both `quality_incidents` and `part_replacements`:** kept on purpose. The incident records which part failed; the replacement records which part was actually replaced. In the generated data they will usually match, and an incident could involve more than one replaced part.
- **`service_center` (added):** the original schema had no way to answer "which service takes longer to complete repairs?". Values will be generic (Service Center 1, 2, ...).
- **`part_arrival_date` (added):** needed to answer "does part waiting time affect resolution time?" (waiting time = `part_arrival_date` − `service_date`).
- **Resolution time** is calculated as `resolution_date` − `incident_date`.
- **Total quality cost** per replacement = `replacement_cost` + `labor_cost` + `transportation_cost` (all in TRY).