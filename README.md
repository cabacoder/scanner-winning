# 📈 Yahoo Daily Gainer Scanner Bot

A robust Python bot that scans **Yahoo Finance's Top Daily Gainers**, enriches them with deep technical data, and applies specific volatility/growth filters to identify trading opportunities.

Includes a built-in **Portfolio Tracker** (`portfolio_manager.py`) that performs "paper trades" on identified stocks and tracks their performance over time.

## 🚀 Features

- **Live Gainers Scan**: Scrapes real-time data from Yahoo Finance.
- **Deep Analysis**: Fetches detailed metrics for each stock using `yfinance`:
  - Returns: Weekly, Monthly, YTD, 52-Week.
  - Technicals: RSI (14), Volume, Market Cap.
  - Fundamentals: PE Ratio, EPS.
- **Smart Filtering**: Automatically catégorizes stocks into 3 checklists:
  - 🔥 **Simmering Growth**: Momentum building (10-20% 52W Return).
  - 🚀 **The Rockets**: Extreme momentum (>50% 52W Return).
  - 🔄 **The Turnarounds**: Beaten down but waking up (Neg 52W Return, >10% Monthly).
- **Auto-Portfolio Tracker**:
  - Automatically "invests" simulated $1,000 in every filtered stock.
  - Creates separate daily portfolio files (`Portfolios/Portfolio_YYYY-MM-DD.csv`).
  - Updates **ALL** past portfolios with live prices in every run to track total PnL.
- **CSV Export**: Saves detailed scan results to `Daily_Scans/`.

## 🛠️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/cabacoder/scanner-winning.git
    cd scanner-winning
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install pandas yfinance requests beautifulsoup4
    ```

## ⚡ Usage

### Manual Run
Run the scanner to fetch gainers, filter them, and update your portfolios:
```bash
python scanner_bot.py
```

### Daily Automation
Use the included shell script to run the bot easily (handles venv activation):
```bash
./run_daily.sh
```

**Scheduled Cron Job (Mac/Linux)**:
To run automatically every weekday at market close (e.g., 4:30 PM):
1. Open crontab: `crontab -e`
2. Add:
   ```bash
   30 16 * * 1-5 /path/to/scanner-winning/run_daily.sh >> /tmp/scanner.log 2>&1
   ```

## 📊 Logic & Checklists

The bot applies the following logic to filter stocks:

| List | Condition | Logic |
| :--- | :--- | :--- |
| **Simmering Growth** | **52-W Ret:** 10% - 20% <br> **Monthly Ret:** > 5% | Strong sustainable momentum without being overextended. |
| **The Rockets** | **52-W Ret:** > 50% <br> **Monthly Ret:** > 10% | Parabolic moves. High risk, high reward. |
| **The Turnarounds** | **52-W Ret:** < 0% (Negative) <br> **Monthly Ret:** > 10% | Beaten-down stocks showing strong recent reversal signs. |

## 📁 Project Structure

- `scanner_bot.py`: Main script for scanning and filtering.
- `portfolio_manager.py`: Handles simulated trading and portfolio updates.
- `Daily_Scans/`: Folder containing raw CSV results of daily scans.
- `Portfolios/`: Folder containing tracked portfolios for each day.
- `run_daily.sh`: Helper script for automation.

## 🤝 Contributing
Feel free to fork and submit PRs if you want to add more filters or indicators!

## 📜 License
MIT
