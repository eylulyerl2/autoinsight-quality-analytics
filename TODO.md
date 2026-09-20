# AutoInsight — Task List

## Phase 0 — Project Setup
- [x] Create GitHub repository
- [x] Create folder structure
- [x] Write README (scope, tech stack, roadmap)
- [x] Draft ER diagram (`docs/er_diagram.md`)
- [x] Create task list (this file)

## Phase 1 — Industry & Data Requirements
- [ ] Learn the basics: automotive production process, quality control, warranty cases, part replacement flow
- [ ] Understand the difference between defect source, root cause and corrective action
- [ ] Write `docs/business_requirements.md`
  - [ ] Problem statement
  - [ ] Stakeholders
  - [ ] Business questions
  - [ ] KPIs
  - [ ] Assumptions
  - [ ] Project scope

## Phase 2 — Synthetic Data Generation
- [ ] Decide the date range (several years, e.g. 3–4)
- [ ] Set up Python environment (`venv`, `pandas`, `faker`/`numpy`)
- [ ] Generate `suppliers` and `parts`
- [ ] Generate `vehicles`
- [ ] Generate `quality_incidents` (with controlled failure probabilities per part)
- [ ] Generate `part_replacements` and `corrective_actions`
- [ ] Validate data (row counts, foreign keys, date logic, no negative costs)
- [ ] Save CSV files to `data/raw/`

## Phase 3 — Database & SQL Analysis
- [ ] Install PostgreSQL
- [ ] Write `sql/schema.sql` (tables, primary and foreign keys)
- [ ] Load CSV files into PostgreSQL
- [ ] Write analysis queries for each question group
  - [ ] General quality
  - [ ] Part analysis
  - [ ] Root cause analysis
  - [ ] Service and resolution time
  - [ ] Financial analysis
- [ ] Document key findings

## Phase 4 — Power BI Dashboard
- [ ] Connect Power BI to PostgreSQL (or CSV files)
- [ ] Page 1 — Quality Overview
- [ ] Page 2 — Part Failure Analysis
- [ ] Page 3 — Root Cause Analysis
- [ ] Page 4 — Warranty & Cost Analysis
- [ ] Add dashboard screenshots to `dashboard/` and README
- [ ] Write insights summary in README