#!/bin/bash

# Navigate to the script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the scanner bot
python scanner_bot.py

# Deactivate (optional, script ends anyway)
deactivate
