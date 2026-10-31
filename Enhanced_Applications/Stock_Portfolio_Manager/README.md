# 📈 Stock Portfolio Manager — Python Desktop Application

A modern, polished, and beginner-friendly **Stock Portfolio Manager** desktop application developed in Python. Built as an enhancement to the **CodeAlpha Python Programming Internship (Task 2: Stock Portfolio Tracker)**, this project transitions the original console-based script into a full-featured desktop dashboard with permanent SQLite database persistence, interactive Matplotlib data visualization, and RFC-compliant CSV export capabilities.

---

## 🌟 Key Features

### 1. 📊 Modern Financial Dashboard
* **Real-Time Summary Metrics:**
  * **Total Portfolio Value** ($): Sum of all stock holdings calculated in real time.
  * **Stocks Held:** Count of distinct equities currently owned.
  * **Total Shares:** Aggregate share count across all positions.
  * **Top Allocation:** Automatically highlights your highest-value holding and its percentage weight.
* **Portfolio Allocation Chart:**
  * Embedded Matplotlib Donut Chart visualizing asset allocation percentages.
  * Dynamically updates whenever stocks are bought, sold, or reset.
  * Displays a clean empty-state placeholder when no stocks are owned.
* **Recent Activity Feed:**
  * Displays the latest 6 transactions with color-coded badges (`BUY` / `SELL`) and timestamped records.

### 2. 🔄 Stock Management & Trading
* **Predefined Reference Stock Catalog:**
  * `AAPL` — Apple Inc. ($180.00)
  * `TSLA` — Tesla Inc. ($250.00)
  * `GOOGL` — Alphabet Inc. ($140.00)
  * `MSFT` — Microsoft Corporation ($420.00)
  * `AMZN` — Amazon.com Inc. ($190.00)
* **Buy / Add Shares:**
  * Dropdown selector for available stocks.
  * Quick quantity increment buttons (`+1`, `+5`, `+10`).
  * Live total cost estimate as quantity is typed.
  * Increments existing positions seamlessly without creating duplicate rows.
* **Sell / Liquidate Shares:**
  * Dropdown filtered strictly to currently owned stocks.
  * Shows available shares owned and unit price.
  * **"Sell Max"** button to quickly liquidate a complete position.
  * Prevents over-selling (cannot sell more shares than owned).
* **Strict Validation & Confirmations:**
  * Rejects non-numeric, decimal, zero, or negative share inputs.
  * Modal confirmation dialogs before executing purchases or sales.

### 3. 💼 Portfolio Holdings Table
* Formatted table displaying:
  * Stock Ticker Symbol
  * Company Name
  * Shares Owned
  * Fixed Sample Price
  * Position Total Value
  * Portfolio Allocation (%)
  * Last Updated Timestamp
* Summary footer with total portfolio value and quick shortcuts.

### 4. 📜 Transaction Audit Ledger
* Complete audit trail recording every trade:
  * Transaction ID (`#1`, `#2`, ...)
  * Date & Time timestamp
  * Stock Symbol & Company Name
  * Transaction Action (`BUY` / `SELL`)
  * Quantity traded
  * Unit execution price
  * Total transaction amount
* Filter ledger by action: **All**, **Buy Only**, or **Sell Only**.

### 5. 🗄️ Permanent Data Persistence (SQLite)
* Automatic database and table creation on first launch (`data/portfolio.db`).
* Proper context managers ensuring connections are reliably opened and closed.
* Parameterized SQL queries preventing SQL injection and data corruption.
* Holdings table enforces unique stock symbols (`PRIMARY KEY`).

### 6. 📥 CSV Export
* **Export Portfolio Snapshot:** Generates a structured `.csv` report of all holdings and total valuation using native file dialogs.
* **Export Transaction Ledger:** Generates a complete chronological `.csv` history of all trades.

### 7. ⚙️ Safe Portfolio Reset & Diagnostics
* Clear all holdings and reset the transaction log without deleting database files.
* Double-confirmation safety prompts preventing accidental data loss.
* Diagnostics card displaying database file size, record counts, and connection health.

---

## 🎨 Visual Design Direction

* **Theme:** Modern dark financial dashboard powered by `ttkbootstrap` (`superhero` theme).
* **Palette:**
  * **Background:** Deep navy (`#131b2a`)
  * **Sidebar:** Lighter navy (`#1a2436`)
  * **Cards:** Dark slate surfaces (`#1e293b`) with subtle borders (`#334155`)
  * **Accents:** Electric Sky Blue (`#38bdf8`), Mint Teal (`#34d399`), Rose Coral (`#f87171`)
  * **Typography:** Clean Segoe UI typography with high-contrast text hierarchy.

---

## 📁 Project Structure

```text
Stock_Portfolio_Manager/
│
├── reference/                             # Original CodeAlpha reference files (Untouched)
│   ├── CodeAlpha_Task_Instructions.pdf
│   └── stock_portfolio_original.py.PY
│
├── assets/                                # Application icons and visual assets
│   ├── icon.ico
│   └── icon.png
│
├── data/                                  # SQLite persistent database storage
│   └── portfolio.db
│
├── src/                                   # Modular source code
│   ├── __init__.py                        # Package metadata
│   ├── database.py                        # SQLite database operations & context managers
│   ├── portfolio.py                       # Core business logic, pricing & calculations
│   ├── ui.py                              # Desktop GUI (Tkinter & ttkbootstrap)
│   └── charts.py                          # Embedded Matplotlib donut chart
│
├── app.py                                 # Main application launcher
├── requirements.txt                       # Python dependencies
└── README.md                              # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.10+** (Python 3.14 recommended).
* **Tkinter** (included by default in standard Python installations on Windows).

### 1. Clone or Open the Project
Open a terminal in the root directory:
```bash
cd Stock_Portfolio_Manager
```

### 2. Set Up Virtual Environment
Create and activate a virtual environment:
```powershell
# Create .venv
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# (Or Command Prompt)
.\.venv\Scripts\activate.bat
```

### 3. Install Dependencies
Install required packages using `requirements.txt`:
```bash
pip install -r requirements.txt
```

> **Note:** Tkinter is a standard Python library and does not require installation via pip.

### 4. Launch the Application
Run `app.py`:
```bash
python app.py
```

---

## 🧪 Testing & Verification

The application has been verified against the following test scenarios:

1. **Input Validation:**
   * Tested non-numeric inputs (`"abc"`), negative numbers (`-5`), zero (`0`), and empty submissions. Handled gracefully with user-friendly error alerts.
2. **Buy Logic:**
   * Tested purchasing new stocks and adding additional shares to existing holdings.
3. **Sell Logic:**
   * Tested selling partial quantities and selling all remaining shares (auto-removes holding record).
   * Verified that attempts to sell more shares than owned are blocked with an explanatory dialog.
4. **Data Calculations:**
   * Validated real-time calculation of total investment value, share counts, and percentage allocations.
5. **Database Persistence:**
   * Verified that all positions and transaction logs persist intact after closing and reopening the application.
6. **Chart Updates:**
   * Verified that the donut chart dynamically updates slice angles and percentages upon trades and displays an empty state when reset.
7. **CSV Export:**
   * Verified RFC-compliant CSV generation for both portfolio snapshots and transaction history.
8. **Reset Functionality:**
   * Confirmed that the reset option purges holdings and transaction records while keeping the SQLite schema intact.

---

## 📌 Technical Specifications & Assumptions

* **Stock Pricing Model:** In accordance with the original project requirements, stock prices are fixed sample prices (`AAPL: $180`, `TSLA: $250`, `GOOGL: $140`, `MSFT: $420`, `AMZN: $190`) to provide an offline, deterministic student project environment. Live market APIs (e.g., Yahoo Finance) are intentionally omitted.
* **Architecture:** Implements a clean Model-View-Controller (MVC) separation of concerns:
  * `database.py` (Data Layer)
  * `portfolio.py` (Controller & Business Logic Layer)
  * `ui.py` & `charts.py` (Presentation & View Layer)

---

## 📜 License
Developed for educational purposes as part of the **CodeAlpha Python Programming Internship**.
Original reference files in `reference/` are preserved in accordance with project guidelines.
