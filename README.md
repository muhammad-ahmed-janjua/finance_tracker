# 📊 Finance Tracker Dashboard (Streamlit)

A demo-ready personal finance dashboard built with **Streamlit** to explore income, expenses, and net trends over time.

This project began as a rapid MVP and is evolving into a clean, extensible finance analysis tool focused on:

- Clear data flow  
- Modular logic  
- Transparent calculations  
- Fast iteration  
- Architectural separation of concerns  

> Debug tables are intentionally retained in the app to support validation, demos, and ongoing development.

---

## 🚀 Overview

The **Finance Tracker Dashboard** allows you to:

- View **Total Income, Total Expenses, and Net Change**
- Explore **monthly net trends**
- Analyse **spending by category**
- Compare **current period vs previous period**
- Toggle **“Exclude Transfers / True Spend” mode**
- Inspect **debug tables** to validate recurring logic and raw transactions

This is not just a UI project — it is structured as a learning-focused system that separates:

- Data loading  
- Transformation  
- Metric computation  
- Rendering logic  

---

## ✨ Features

### 📈 KPI Summary

Displays:

- Total Income  
- Total Expenses  
- Net Change  

All metrics respect selected filters and date ranges.

---

### 📊 Time Series Analysis

- Monthly net totals  
- Visual trend of income vs expenses over time  
- Responsive charting (Plotly recommended)

---

### 🗂 Category Breakdown

- Spending grouped by category  
- Clear visibility into top expense drivers  

---

### 🔄 Period Comparison

“What changed vs previous period” view:

- Top increases  
- Top decreases  
- Graceful empty state handling when no decreases exist  

---

### 🎛 Filters

- Date range selector  
- Exclude transfers / “True Spend” toggle  
- Comparison period logic  

---

### 🧪 Debug Tables (Intentionally Kept)

The following debug tables remain in the dashboard by design:

- Recurring commitments (debug)  
- Recent transactions (debug)  
- Any additional diagnostic tables  

They allow:

- Validation of logic  
- Clear explanation of derived metrics  
- Faster iteration during development  

These are not temporary hacks — they are development tools.

---

## 🛠 Tech Stack

- Python 3.10+  
- Streamlit  
- Pandas  
- Plotly (recommended for charts)

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Create a virtual environment

#### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

If a `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

Otherwise:

```bash
pip install streamlit pandas plotly
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

Streamlit will provide a local URL (usually `http://localhost:8501`).

---

## 📁 Data Requirements

The app expects transaction-level data with a consistent schema.

### Recommended Columns

- `date` — datetime  
- `amount` — numeric (positive = income, negative = expense)  
- `description` — string  
- `cumulative balance` — float

### Ensure

- Dates are parsed properly  
- Amounts are numeric  
- Categories are consistent  

If using CSV input, ensure the file path is correctly referenced in the app.

---

## 🏗 Architecture Philosophy

This project prioritises architectural clarity over pure visual polish.

### Core Principles

- Single source of filtered data  
- Clear separation between:
  - Data loading  
  - Transformation  
  - Metrics  
  - UI rendering  
- Avoid duplicated calculations  
- Keep UI logic lightweight  
- Make adding new features straightforward  

The goal is **extensibility**.

If a new feature is added, it should not require rewriting core logic.

---

## 🛣 Roadmap

Planned improvements:

- “Safe to spend today” calculation  
- Savings projection simulator  
- Recurring detection confidence scoring  
- Merchant-level insights  
- Export filtered summaries  
- Improved UI card layout  
- Better empty states and responsiveness  

---