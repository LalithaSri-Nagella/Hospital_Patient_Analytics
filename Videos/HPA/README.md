# Hospital Patient Data Analysis System

A modern, full-stack hospital administration dashboard and demographic data analysis system built for university demonstration and academic review.

Built with **Python (Flask)**, **MySQL**, **Pandas**, **NumPy**, **Bootstrap 5**, and **Chart.js**.

---

## 📂 Modular Architecture & Directory Structure

The project follows a clean, segregated, and easy-to-understand layout:

```text
hospital-patient-analytics/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py               # Flask application factory & Blueprint registration
│   │   ├── main.py                   # Main backend application runner
│   │   ├── db.py                     # MySQL connection manager & parameterized query executor
│   │   │
│   │   ├── routes/                   # Modular route controllers (Blueprints)
│   │   │   ├── __init__.py
│   │   │   ├── patients.py           # Patient CRUD & filter routes (/patients)
│   │   │   ├── departments.py        # Department CRUD & integrity routes (/departments)
│   │   │   ├── visits.py             # Visit logging & filter routes (/visits)
│   │   │   └── analytics.py          # Dashboard (/) & analytics reporting routes (/analytics)
│   │   │
│   │   ├── services/                 # Business logic & scientific data processing
│   │   │   ├── __init__.py
│   │   │   └── analytics_service.py  # Pandas & NumPy analysis, metrics & CSV generators
│   │   │
│   │   ├── templates/                # Jinja2 HTML presentation templates
│   │   │   ├── base.html             # Responsive layout with medical sidebar & topbar
│   │   │   ├── dashboard.html        # 4 live KPI cards, 3 Chart.js graphs, recent visits table
│   │   │   ├── patients.html         # Patient directory with search, filter, pagination
│   │   │   ├── patient_form.html     # Patient create and edit form with server validation
│   │   │   ├── visits.html           # Visit registry with date range and department filters
│   │   │   ├── visit_form.html       # Visit recording form with live database dropdowns
│   │   │   ├── departments.html      # Department list with total visit counters & safeguards
│   │   │   ├── department_form.html  # Department create and edit form with uniqueness check
│   │   │   ├── analytics.html        # Comprehensive Pandas analytics, 4 charts & breakdown table
│   │   │   └── error.html            # Clean custom error views (400, 404, 500, DatabaseError)
│   │   │
│   │   └── static/                   # Static frontend assets
│   │       ├── css/
│   │       │   └── style.css         # Medical theme (soft blue accents, light grey cards)
│   │       └── js/
│   │           └── main.js           # Responsive sidebar, alerts, deletion confirmations
│   │
│   ├── config.py                     # Environment configuration loader (Dev, Test)
│   ├── requirements.txt              # Python dependency manifest
│   ├── .env                          # Local database credentials (git-ignored)
│   └── .env.example                  # Environment variables template
│
├── database/
│   ├── schema.sql                    # MySQL DDL (tables, primary/foreign keys, indexes)
│   └── seed.sql                      # Fictional demonstration data (departments, patients, visits)
│
├── tests/                            # Automated Pytest suite (uses isolated test DB)
│   ├── conftest.py                   # Pytest fixtures and isolated test database setup
│   ├── test_patients.py              # Patient CRUD, validation, and filter tests
│   ├── test_departments.py           # Department CRUD and foreign-key protection tests
│   ├── test_visits.py                # Visit CRUD, dropdowns, and date validation tests
│   └── test_analytics.py             # Stats calculation, empty dataset handling, CSV tests
│
├── run.py                            # Convenient top-level launcher (py run.py)
├── verify_app.py                     # End-to-end automated system verification script
├── test_mysql_connection.py          # Dedicated MySQL connection & schema test script
├── .gitignore                        # Git ignore configuration
└── README.md                         # Project documentation and guide
```

---

## 🌟 Key System Features

### 1. Live Operational Dashboard (`/`)
- **Real-Time KPIs**: Total registered patients, total recorded visits, active departments, and visits logged in the current month.
- **Dynamic Chart.js Visualizations**:
  - **Monthly Visit Trends**: Smooth area-line chart showing 12-month patient intake trajectories.
  - **Visits by Department**: Ranked bar chart visualizing patient volume across medical units.
  - **Visit Types Breakdown**: Interactive doughnut chart highlighting encounter types (*Emergency, Inpatient, Outpatient, Follow-up, Routine Checkup*).
- **Recent Visits Log**: Instant inspection table displaying recent admissions and outpatient visits.
- **Live Database Feed**: All metrics and charts query live MySQL tables—never hardcoded.

### 2. Patient Management (`/patients`)
- Demographic tracking: **Patient ID** (auto-generated), **Age Group** (`0-17`, `18-35`, `36-50`, `51-65`, `65+`), and **Gender**.
- Add, view, edit, and delete patients with confirmation prompts.
- Search by Patient ID, filter by age group and gender, multi-column sorting, and responsive pagination.
- Full server-side and client-side validation.
- **Privacy Standard**: Fictional demographic information only. No patient names, phone numbers, or clinical diagnoses are collected.

### 3. Visit Management (`/visits`)
- Tracks encounter records: **Visit ID**, **Patient ID**, **Department**, **Visit Date**, and **Visit Type**.
- Dynamic dropdown selectors populated directly from active database records.
- Date range filtering (*From Date* / *To Date*), department filtering, and visit type filtering.
- Multi-column sorting and pagination.
- Instant CSV export of filtered visit records.

### 4. Department Management & Integrity Safeguards (`/departments`)
- Lists all hospital departments with real-time visit count aggregations.
- Add and edit medical divisions with uniqueness constraints.
- **Foreign Key Referential Integrity**: Departments referenced by existing visits are strictly protected and cannot be deleted until visits are reassigned or removed. A clear diagnostic alert explains this safeguard to the user.

### 5. Advanced Analytics & Reporting (`/analytics`)
- In-depth statistical aggregations computed on-the-fly using **Pandas DataFrames** and **NumPy arrays**:
  - Total Visits vs. **Unique Patients** (clearly distinguished to measure patient return intensity).
  - Average visits per day across active operational dates.
  - Peak visit date identification and busiest department detection.
  - Most frequent encounter classification.
  - Department breakdown table with percentage share and primary encounter mode.
- Working date range filters with quick presets (*All Time*, *Last 30 Days*, *Last 90 Days*, *Year to Date*).
- Resilient design: Handles empty datasets cleanly with user-friendly empty states.
- Two dedicated CSV export endpoints:
  - **Export Filtered Visits (CSV)**: Raw tabular records matching active filters.
  - **Export Summary (CSV)**: Executive summary KPIs and departmental breakdowns.

### 6. Security & Error Handling
- Parameterized SQL queries throughout to eliminate SQL injection risks.
- Session-based CSRF token verification on all state-changing `POST` requests.
- Graceful handling of 400, 404, 500, and database connection exceptions with dedicated error views.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Architecture** | Python 3.10+, Flask 3.x with Modular Blueprints |
| **Data Analysis** | Pandas, NumPy |
| **Database** | MySQL Server 8.0+ / MariaDB (via PyMySQL) |
| **Frontend** | HTML5, Vanilla CSS, JavaScript, Bootstrap 5.3, Bootstrap Icons |
| **Data Visualizations** | Chart.js 4.4 |
| **Automated Testing** | Pytest 8.x |

---

## 🚀 Running the Application

### 1. Start the Server
From the project folder, run:
```powershell
py run.py
```
*(Or navigate to backend and run)*:
```powershell
py backend/app/main.py
```

### 2. Access in Your Browser
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Testing & Verification

### 1. Run Automated Pytest Suite (31 Tests)
Validates all routes, validations, foreign key protections, analytics, and CSV exports using an isolated test database (`hospital_analytics_test`):
```powershell
py -m pytest tests/ -v
```

### 2. Run Database Connection Test
```powershell
py test_mysql_connection.py
```

### 3. Run Full System Verification
```powershell
py verify_app.py
```
