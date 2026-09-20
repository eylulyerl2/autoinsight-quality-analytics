# Business Requirements

Project: **AutoInsight — Automotive Quality & Warranty Analytics**

## 1. Problem Statement

Automotive manufacturers face quality problems throughout a vehicle's life: defective parts, assembly errors, supplier issues and design flaws. Each problem creates warranty claims, part replacements, service labor, logistics costs and unhappy customers. When these records are scattered across systems, it is hard to see the bigger picture:

- Which parts fail the most and which cost the most?
- Where do defects actually come from (suppliers, production lines, design)?
- How long do problems take to resolve, and how much do they cost?
- Do corrective actions really stop problems from coming back?

**AutoInsight** answers these questions by building a quality and warranty database from (synthetic) incident, replacement and corrective action records, and turning it into SQL analyses and a management dashboard.

Core question: *How can an automotive company detect and reduce quality problems using data?*

## 2. Stakeholders

| Stakeholder | What they need from the analysis |
|-------------|----------------------------------|
| Quality manager | Overall incident trends, complaint rate, recurring failures |
| Production engineer | Defects by production line and factory, manufacturing vs. assembly errors |
| Service manager | Resolution times, service center performance, part waiting times |
| Warranty department | Warranty vs. non-warranty split, warranty cost per case and per model |
| Supplier quality specialist | Supplier-related defects by supplier and part, cost of supplier defects |
| Operations manager | High-level KPIs, total quality cost, biggest cost drivers |

## 3. Business Questions

### 3.1 General quality
1. How many quality incidents occurred in the last 12 months, and per year?
2. How does the number of incidents change month by month?
3. Which vehicle model has the most incidents?
4. What percentage of incidents came from customer complaints?
5. What percentage of incidents were resolved under warranty?

### 3.2 Part analysis
6. Which are the top 10 failing parts?
7. Which part was replaced the most?
8. Which part caused the most expensive quality problems?
9. Which part has the highest recurrence rate?
10. Which parts have few failures but high cost?

### 3.3 Root cause analysis
11. What is the most common defect source?
12. In which parts are supplier defects concentrated?
13. Which production line has the most defects?
14. Was there a spike in defects during a specific period?
15. Does the same defect type appear across multiple vehicle models?

### 3.4 Service and resolution time
16. What is the average resolution time (in days)?
17. Which defect type takes the longest to resolve?
18. Which service center or department takes the longest to complete cases?
19. What is the average cost of warranty cases?
20. Does part waiting time affect resolution time?

### 3.5 Financial analysis
21. What is the total quality cost (in TRY)?
22. Which 5 parts generate the most cost?
23. What is the ratio of part cost to labor cost?
24. How much do supplier-related defects cost the company?
25. What is the yearly cost of recurring defects?

## 4. KPIs

| KPI | Definition |
|-----|------------|
| Total Quality Incidents | Number of records in `quality_incidents` |
| Total Part Replacements | Number of records in `part_replacements` |
| Total Quality Cost (TRY) | Sum of `replacement_cost` + `labor_cost` + `transportation_cost` |
| Average Resolution Time (days) | Average of `resolution_date` − `incident_date` for resolved cases |
| Customer Complaint Rate | Incidents with `customer_complaint = true` ÷ total incidents |
| Recurring Failure Rate | Corrective actions with `recurrence_after_action = true` ÷ total corrective actions |

Supporting metrics: warranty share of cases, average cost per incident, average part waiting time (`part_arrival_date` − `service_date`), supplier defect share.

## 5. Assumptions

- All data is **synthetic**. No real company, supplier or customer data is used.
- All costs are in **TRY (Turkish Lira)**.
- The data covers several years (exact range decided in Phase 2), so yearly comparisons are possible.
- Every incident is linked to exactly one vehicle and one part.
- An incident may have zero or more part replacements and zero or more corrective actions.
- Resolution time is calculated as `resolution_date` − `incident_date`; incidents that are still open have no resolution date.
- Total quality cost only includes replacement-related costs (part, labor, transportation). Indirect costs such as brand damage or lost sales are not included.
- A failure is counted as "recurring" when `recurrence_after_action` is true.
- Severity levels are Low, Medium, High and Critical.
- Defect sources: Manufacturing Error, Supplier Defect, Assembly Error, Material Failure, Design Issue, Customer Misuse, Unknown.
- Defect types: Electrical Failure, Leakage, Noise, Breakage, Overheating, Incorrect Installation, Performance Issue, Software Error.
- Supplier names and service centers are generic (Supplier A, Service Center 1, ...).
- Some parts are deliberately given higher failure probability so the analysis produces meaningful patterns.

## 6. Project Scope

**In scope (v1)**
- Synthetic data generation with Python
- Data cleaning and validation with Pandas
- Relational database in PostgreSQL
- SQL queries that answer the business questions above
- A four-page Power BI dashboard (Quality Overview, Part Failure Analysis, Root Cause Analysis, Warranty & Cost Analysis)
- Documentation on GitHub

**Out of scope (v1)**
- Connecting to or configuring a real SAP system
- Real customer or company data
- Machine learning models
- Real-time data streaming
- A complex web application