# AutoInsight — Automotive Quality & Warranty Analytics

An end-to-end data analytics project that looks at automotive quality problems the way a quality analyst would: generate realistic data, store it in a relational database, query it with SQL, and turn it into a management dashboard with root cause insights.

> **Status:** Work in progress (Phase 0 complete)

## Business Question

> How can an automotive company detect and reduce quality problems using data?

The project is driven by questions such as:

- How many quality incidents happen each year, and what causes them?
- Which parts generate the most failures, replacements and customer complaints?
- How long does it take to resolve an issue?
- How much do quality problems cost the company (in TRY)?
- Do corrective actions actually stop problems from recurring?

## Who Is This For?

Quality managers, production engineers, service managers, warranty departments, supplier quality specialists and operations managers.

## Scope

The first version is split into five modules:

| # | Module | Description |
|---|--------|-------------|
| 1 | Vehicles & parts | Vehicle models, production details, parts and suppliers |
| 2 | Quality incidents | Defect types, defect sources, severity and dates |
| 3 | Replacements & warranty | Replaced parts, service time, warranty status and costs |
| 4 | Root cause & corrective actions | Problem source, action taken, and whether the problem recurred |
| 5 | Analysis & dashboard | KPIs, charts, filters and an executive summary view |

### Out of Scope (v1)

- Connecting to a real SAP system or configuring SAP
- Using real customer or company data
- Machine learning models
- Real-time data streaming
- A complex web application

These may be added in future versions.

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Synthetic data generation and analysis |
| Pandas | Data cleaning and exploration |
| PostgreSQL | Relational database |
| SQL | Analysis queries |
| Power BI | Dashboard and visualization |
| Git / GitHub | Version control and portfolio |
| Markdown | Documentation |

## Data

**All data in this project is synthetic.** No real company or customer data is used. Supplier names are generic (Supplier A, Supplier B, ...). All costs are in **TRY (Turkish Lira)**.

The data is generated in a controlled way, for example some parts are given a higher failure probability than others, so that the analysis produces meaningful patterns. The data will cover several years so that yearly comparisons are possible (exact range is defined in Phase 2).

### Data Model

| Table | Description | Target rows |
|-------|-------------|-------------|
| `vehicles` | Model, production year, production line, factory, fuel type | 2,000 |
| `parts` | Part name, category, supplier, unit cost | 30 |
| `suppliers` | Supplier name, country, category | 10 |
| `quality_incidents` | Defect type, defect source, severity, customer complaint, status | 5,000 |
| `part_replacements` | Service date, part / labor / transportation cost, warranty status, resolution date | 3,000 |
| `corrective_actions` | Root cause, action taken, responsible department, dates, recurrence | 2,000 |

An ER diagram will be added to `docs/` during Phase 0.

## Planned Dashboard

A four-page Power BI dashboard:

1. **Quality Overview** — executive KPIs (total incidents, total quality cost, average resolution time, customer complaint rate, recurring failure rate) and monthly trends
2. **Part Failure Analysis** — top failing parts, most replaced parts, cost by part, supplier and part relationships
3. **Root Cause Analysis** — Pareto analysis of defect sources, defects by production line, supplier defect rates, corrective action status
4. **Warranty & Cost Analysis** — warranty vs. non-warranty cases, part / labor / logistics cost breakdown, cost by vehicle model

## Roadmap

- [x] **Phase 0** — Project setup (repository, README, scope)
- [ ] **Phase 1** — Industry and data requirements (`docs/business_requirements.md`)
- [ ] **Phase 2** — Synthetic data generation with Python
- [ ] **Phase 3** — PostgreSQL database and SQL analysis
- [ ] **Phase 4** — Power BI dashboard and insights

## Repository Structure

```
autoinsight-quality-analytics/
├── README.md
├── docs/                          # Documentation, ER diagram, requirements
│   └── business_requirements.md
├── data/
│   ├── raw/                       # Generated raw data
│   └── processed/                 # Cleaned data
├── notebooks/                     # Exploration and analysis notebooks
├── sql/                           # Schema and analysis queries
├── src/                           # Python scripts (data generation)
└── dashboard/                     # Power BI files and screenshots
```

## Author

Eylül Yerli — [GitHub](https://github.com/eylulyerl2)
