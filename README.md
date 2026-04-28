# 🛒 Amazon Selenium Tests — Python

Automated end-to-end tests for Amazon.com using **Selenium 4 + pytest**.

| Test | Description |
|------|-------------|
| **Test Case 1** | Search for *iPhone 15 Pro*, add to cart, print price |
| **Test Case 2** | Search for *Samsung Galaxy S24 Ultra*, add to cart, print price |

Both tests run **in parallel** (2 workers via `pytest-xdist`).

---

## 📁 Project Structure

```
amazon-selenium-tests/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Shared fixtures (browser setup/teardown)
│   ├── test_amazon_iphone.py     # Test Case 1 – iPhone
│   └── test_amazon_galaxy.py     # Test Case 2 – Galaxy
│
├── utils/
│   ├── __init__.py
│   └── helpers.py                # Browser factory + Amazon helper functions
│
├── .github/
│   └── workflows/
│       └── selenium_tests.yml    # GitHub Actions CI pipeline
│
├── reports/                      # Auto-created when tests run
│   └── screenshots/              # Failure screenshots
│
├── .gitignore
├── pytest.ini                    # Pytest config (parallel flags, report path)
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.9 – 3.12 | [python.org](https://python.org) |
| Google Chrome | Latest | [google.com/chrome](https://google.com/chrome) |
| Git | Any | [git-scm.com](https://git-scm.com) |

> **ChromeDriver is installed automatically** by `webdriver-manager`.  
> You do **not** need to download it manually.

---

## 🚀 Quick Start — Run Locally

### Step 1 — Clone the repository
```bash
git clone https://github.com/<YOUR_USERNAME>/amazon-selenium-tests.git
cd amazon-selenium-tests
```

### Step 2 — Create & activate a virtual environment
```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Run the tests
```bash
# Run both tests IN PARALLEL (default — 2 workers)
pytest

# Run with visible browser (no headless)
HEADLESS=false pytest          # macOS / Linux
set HEADLESS=false && pytest   # Windows CMD
$env:HEADLESS="false"; pytest  # Windows PowerShell

# Run a single test file
pytest tests/test_amazon_iphone.py
pytest tests/test_amazon_galaxy.py

# Run tests sequentially (no parallelism)
pytest -n 0

# Show full print() output in terminal
pytest -s
```

---

## 🖥️ Sample Console Output

When you run `pytest -s`, each test prints to the console:

```
══════════════════════════════════════════════════════════════
  TEST CASE 1 – iPhone
══════════════════════════════════════════════════════════════
  Product : Apple iPhone 15 Pro, 256GB, Black Titanium
  Price   : $999.00
══════════════════════════════════════════════════════════════

  ✅  iPhone successfully added to cart!

══════════════════════════════════════════════════════════════
  TEST CASE 2 – Samsung Galaxy
══════════════════════════════════════════════════════════════
  Product : Samsung Galaxy S24 Ultra 256GB, Titanium Black
  Price   : $1,199.99
══════════════════════════════════════════════════════════════

  ✅  Galaxy device successfully added to cart!
```

---

## ⚡ Parallel Execution Explained

Parallel execution is configured in **two places**:

### 1. `pytest.ini`
```ini
addopts = -v -n 2 --html=reports/test_report.html --self-contained-html
```
- `-n 2` → spawn **2 pytest-xdist workers**
- Each worker gets its own browser instance
- Test Case 1 and Test Case 2 run **simultaneously**

### 2. `conftest.py` — `scope="function"` fixture
```python
@pytest.fixture(scope="function")
def driver(request):
    browser = create_driver(headless=True)
    yield browser          # ← test runs here (isolated browser)
    browser.quit()
```
Function scope ensures each parallel worker has an **independent browser session** — no shared state.

### Execution flow
```
Worker 1 ──▶  test_amazon_iphone.py  ──▶  Browser A
Worker 2 ──▶  test_amazon_galaxy.py  ──▶  Browser B
              ↓ (both run at the same time)
              pytest collects results & merges report
```

---

## 📊 Test Report

After every run, an HTML report is generated at:
```
reports/test_report.html
```
Open it in any browser. It shows pass/fail status, test durations, and logs.

Failure screenshots are saved to:
```
reports/screenshots/<test_name>_<timestamp>.png
```

---

## 🔄 GitHub Actions — CI/CD

The workflow at `.github/workflows/selenium_tests.yml` runs automatically on every **push** or **pull request** to `main`.

### What the pipeline does:
1. Checks out the code
2. Installs Python 3.11
3. Installs Google Chrome on the Ubuntu runner
4. Installs all pip dependencies
5. Runs `pytest -n 2` in parallel (headless)
6. Uploads the HTML report as a downloadable artifact

### View results on GitHub:
```
Repository → Actions tab → Latest run → Artifacts → test-report
```

---

## 📤 How to Upload to GitHub (Step-by-Step)

### Option A — Using the terminal (recommended)

```bash
# 1. Create a new repo on GitHub (do NOT add README or .gitignore)
#    https://github.com/new  →  Repository name: amazon-selenium-tests

# 2. Inside the project folder:
cd amazon-selenium-tests

# 3. Initialise git
git init

# 4. Stage all files
git add .

# 5. Make the first commit
git commit -m "feat: add Amazon Selenium parallel tests"

# 6. Add the remote (replace <YOUR_USERNAME>)
git remote add origin https://github.com/<YOUR_USERNAME>/amazon-selenium-tests.git

# 7. Push to GitHub
git branch -M main
git push -u origin main
```

### Option B — GitHub Desktop
1. Open **GitHub Desktop** → *File* → *Add Local Repository*
2. Browse to the `amazon-selenium-tests` folder → *Add Repository*
3. Click **Publish repository** (top right)
4. Set name, choose Public/Private, click **Publish Repository**

### Option C — Drag and Drop (simplest)
1. Go to `https://github.com/new`
2. Create a new empty repository
3. On the empty repo page click **uploading an existing file**
4. Drag all project files into the browser window
5. Click **Commit changes**

---

## 🔧 Configuration Reference

| Config | Location | Purpose |
|--------|----------|---------|
| `HEADLESS=false` | Env variable | Show browser window |
| `-n 2` | `pytest.ini` | Number of parallel workers |
| `SEARCH_QUERY` | top of each test file | Change the search term |
| `DEFAULT_WAIT = 15` | `utils/helpers.py` | Global explicit wait (seconds) |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: selenium` | Run `pip install -r requirements.txt` |
| `SessionNotCreatedException` | Chrome and ChromeDriver version mismatch — delete `~/.wdm/` and re-run |
| Tests blocked / CAPTCHA | Amazon geo-blocks automated traffic; use a VPN or run with `HEADLESS=false` to inspect |
| Price shows `None` | Product may require colour/storage selection before showing a price — normal behaviour |
| CI fails with "no display" | Ensure `HEADLESS=true` in the workflow env block (already set) |

---

## 🛠️ Tech Stack

| Library | Version | Role |
|---------|---------|------|
| `selenium` | 4.18 | Browser automation |
| `pytest` | 8.1 | Test runner |
| `pytest-xdist` | 3.5 | Parallel execution |
| `pytest-html` | 4.1 | HTML reports |
| `webdriver-manager` | 4.0 | Auto ChromeDriver install |

---

## 📝 License

MIT — free to use, modify, and distribute.
