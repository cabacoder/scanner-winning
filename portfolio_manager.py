import pandas as pd
import yfinance as yf
import datetime
import os
import glob
import sys

PORTFOLIOS_DIR = "Portfolios"
CAPITAL_PER_TRADE = 1000.0

def ensure_portfolios_dir():
    """Ensures the portfolios directory exists."""
    if not os.path.exists(PORTFOLIOS_DIR):
        os.makedirs(PORTFOLIOS_DIR)

def get_todays_portfolio_path():
    """Returns the path for today's portfolio file."""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return os.path.join(PORTFOLIOS_DIR, f"Portfolio_{today}.csv")

def save_portfolio(df, filepath):
    """Saves a portfolio dataframe to the specified CSV."""
    df.to_csv(filepath, index=False)
    # print(f"Saved {filepath}")

def add_new_positions(daily_scan_df):
    """Creates a new daily portfolio file with positions from the scan."""
    ensure_portfolios_dir()
    filepath = get_todays_portfolio_path()
    
    if daily_scan_df.empty:
        print("No new stocks to add to portfolio.")
        return

    # Check if file exists, if so we append or overwrite? 
    # User said "creates new tracker". If ran multiple times same day, we probably just want to ensure we don't duplicate.
    # Let's load if exists.
    if os.path.exists(filepath):
        portfolio = pd.read_csv(filepath)
    else:
        columns = [
            'Date', 'Symbol', 'List', 'Entry Price', 'Quantity', 
            'Initial Value', 'Current Price', 'Current Value', 'Return %'
        ]
        portfolio = pd.DataFrame(columns=columns)
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    new_entries = []
    
    # Filter only relevant lists
    focus_lists = ['Simmering Growth', 'Rockets', 'Turnarounds']
    targets = daily_scan_df[daily_scan_df['List'].isin(focus_lists)]
    
    print(f"\n--- Creating/Updating Daily Portfolio: {filepath} ---")

    for _, row in targets.iterrows():
        symbol = row['Symbol']
        price = row['Price']
        list_name = row['List']
        
        if pd.isna(price) or price <= 0:
            continue

        quantity = CAPITAL_PER_TRADE / price
        initial_value = quantity * price
        
        # Avoid duplicates in THIS file
        if not portfolio.empty:
            duplicate = portfolio[portfolio['Symbol'] == symbol]
            if not duplicate.empty:
                # print(f"Skipping {symbol}: Already in today's portfolio.")
                continue

        entry = {
            'Date': today,
            'Symbol': symbol,
            'List': list_name,
            'Entry Price': round(price, 2),
            'Quantity': round(quantity, 4),
            'Initial Value': round(initial_value, 2),
            'Current Price': round(price, 2),
            'Current Value': round(initial_value, 2),
            'Return %': 0.0
        }
        new_entries.append(entry)
        print(f"Added {symbol} ({list_name})")

    if new_entries:
        new_df = pd.DataFrame(new_entries)
        portfolio = pd.concat([portfolio, new_df], ignore_index=True)
        save_portfolio(portfolio, filepath)
        print(f"Saved {len(new_entries)} positions to {filepath}")
    else:
        print("No new positions added (or already existed).")

def update_portfolio_values():
    """Updates metrics for ALL daily portfolio files."""
    ensure_portfolios_dir()
    files = glob.glob(os.path.join(PORTFOLIOS_DIR, "Portfolio_*.csv"))
    
    if not files:
        print("No portfolio files found to update.")
        return

    print(f"\n--- Updating {len(files)} Portfolio Files ---")
    
    total_invested_all = 0.0
    total_value_all = 0.0

    for filepath in sorted(files):
        # sys.stdout.write(f"\rUpdating {filepath}...")
        # sys.stdout.flush()
        
        try:
            portfolio = pd.read_csv(filepath)
            if portfolio.empty:
                continue
                
            updated = False
            for index, row in portfolio.iterrows():
                symbol = row['Symbol']
                try:
                    ticker = yf.Ticker(symbol)
                    price = ticker.fast_info.last_price
                    if not price:
                        price = ticker.info.get('currentPrice', ticker.info.get('regularMarketPrice'))
                    
                    if price:
                        current_val = row['Quantity'] * price
                        roi = ((current_val - row['Initial Value']) / row['Initial Value']) * 100
                        
                        portfolio.at[index, 'Current Price'] = round(price, 2)
                        portfolio.at[index, 'Current Value'] = round(current_val, 2)
                        portfolio.at[index, 'Return %'] = round(roi, 2)
                        updated = True
                except:
                    pass
            
            if updated:
                save_portfolio(portfolio, filepath)
                
            # Aggregate stats
            total_invested_all += portfolio['Initial Value'].sum()
            total_value_all += portfolio['Current Value'].sum()
            
        except Exception as e:
            print(f"Error updating {filepath}: {e}")

    print(f"\nAll portfolios updated.")
    
    # Grand Total
    total_ret = 0.0
    if total_invested_all > 0:
        total_ret = ((total_value_all - total_invested_all) / total_invested_all) * 100
        
    print(f"Total Invested (All Time): ${total_invested_all:,.2f}")
    print(f"Current Value (All Time):  ${total_value_all:,.2f}")
    print(f"Total Return:              {total_ret:.2f}%")

if __name__ == "__main__":
    update_portfolio_values()
