#!/bin/bash

# Navigate to the script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the scanner bot
python scanner_bot.py

# Git Automation: Commit and Push results
echo "Pushing updates to GitHub..."
git add Daily_Scans/ Portfolios/ Active_Watchlist_Summary.csv
git commit -m "Auto-Update: Daily Scan & Portfolio $(date)"
git push origin main

# Deactivate (optional, script ends anyway)
deactivate
