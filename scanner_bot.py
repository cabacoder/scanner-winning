import pandas as pd
import yfinance as yf

import requests
from bs4 import BeautifulSoup
import datetime
import os
import sys

# Display settings
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def get_day_gainers_safe():
    """Fetches Day Gainers by scraping Yahoo Finance directly."""
    print("Fetching Top Daily Gainers from Yahoo Finance...")
    url = "https://finance.yahoo.com/markets/stocks/gainers/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Yahoo Finance table structure can vary, but usually it's in a table with specific classes
        # or we look for standard table rows.
        
        tickers = []
        # Attempt to find the table
        # Strategy: Look for all 'a' tags that link to /quote/SYMBOL?p=SYMBOL
        # Or usually simpler: extract symbols from the specific table.
        
        # New Yahoo Finance layout (2024+):
        # Table rows often have class starting with "row" or similar.
        # Symbols are usually in the first column, link text.
        
        # Let's try pandas read_html first as it's powerful (if table is standard)
        try:
             dfs = pd.read_html(response.text)
             # usually the first table is what we want
             if dfs:
                 df = dfs[0]
                 # Look for 'Symbol' column
                 if 'Symbol' in df.columns:
                     return df['Symbol'].tolist()
        except Exception as  e:
            pass # Fallback to soup

        # Fallback Soup Parsing
        # Look for links like <a href="/quote/XYZ?p=XYZ" ...>XYZ</a>
        # This is a bit loose but effective.
        
        # Better: Look for elements with data-test="quoteLink" or similar?
        # Let's try to match the specific pattern from current YF.
        
        # Common pattern: table > tbody > tr > td > a (text is symbol)
        
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if cols:
                # Symbol is usually first
                txt = cols[0].text.strip()
                # Basic validation: Uppercase, 1-5 letters (dot allowed)
                # Eliminate random text
                if txt and (txt.isupper() or '.' in txt) and len(txt) <= 8:
                     # Check if it looks like a symbol (no spaces)
                     if " " not in txt:
                         tickers.append(txt)

        if not tickers:
             print("Warning: No tickers found via scraping.")
             return []
             
        # Cleanup: sometimes headers get in, filter duplicates
        tickers = list(dict.fromkeys(tickers)) # remove dupes maintain order
        return tickers[:25] # Return top 25-50 to avoid garbage

    except Exception as e:
        print(f"Error fetching gainers: {e}")
        return []

def format_large_number(num):
    """Formats large numbers like Yahoo Finance (e.g., 2.5B, 713M)."""
    if num is None or pd.isna(num):
        return "N/A"
    
    try:
        num = float(num)
    except (ValueError, TypeError):
        return str(num)

    if num >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:.2f}T"
    elif num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:.2f}"

def get_stock_data(ticker_symbol):
    """Fetches real-time and historical data for a ticker and calculates metrics."""
    # print(f"Processing {ticker_symbol}...", end='\r')
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # historical data for calculations (need 1 year for 52-week return, 14 days for RSI)
        # Fetching 1y + 1mo to be safe
        hist = ticker.history(period="1y")
        
        if hist.empty:
            return None

        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
        if not current_price:
             current_price = hist['Close'].iloc[-1]

        # --- Calculations ---
        
        # Weekly Return (5 trading days ago)
        weekly_return = 0.0
        if len(hist) >= 6:
            price_5d_ago = hist['Close'].iloc[-6]
            weekly_return = (current_price - price_5d_ago) / price_5d_ago
            
        # Monthly Return (21 trading days ago)
        monthly_return = 0.0
        if len(hist) >= 22:
             price_1m_ago = hist['Close'].iloc[-22]
             monthly_return = (current_price - price_1m_ago) / price_1m_ago
        
        # YTD Return
        ytd_return = 0.0
        # Get start of year
        current_year = datetime.datetime.now().year
        start_of_year = f"{current_year}-01-01"
        # yfinance history is indexed by date (datetime64[ns, America/New_York])
        # We filter for this year
        hist_ytd = hist[hist.index >= pd.Timestamp(start_of_year, tz=hist.index.tz)]
        
        if not hist_ytd.empty:
            price_start_year = hist_ytd['Open'].iloc[0] # Approx
            ytd_return = (current_price - price_start_year) / price_start_year
        else:
            # If no data for this year yet (e.g. first trading day), fallback or 0
             pass

        # 52-Week Return
        year_return = 0.0
        if len(hist) > 0:
             price_1y_ago = hist['Close'].iloc[0]
             year_return = (current_price - price_1y_ago) / price_1y_ago

        # RSI (14-day)
        rsi = float('nan')
        if len(hist) >= 15:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            # Use EWMA for RSI traditionally, but rolling mean is simpler first pass. 
            # Let's use Wilder's Smoothing for more accuracy matching standard RSI
            # gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
            # loss = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
            
            # Simple RSI:
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            # Handle division by zero if loss is 0
            if pd.isna(rsi):
                 rsi = 100 if gain.iloc[-1] > 0 else 50
        
        # --- Data Gathering ---
        
        data = {
            'Symbol': ticker_symbol,
            'Price': current_price,
            'Change%': info.get('regularMarketChangePercent', 0) * 100, # Scan usually provides this but we refresh
            'Volume': format_large_number(info.get('volume')),
            'Avg Vol (3M)': format_large_number(info.get('averageVolume')),
            'Market Cap': format_large_number(info.get('marketCap')),
            'PE (TTM)': info.get('trailingPE', 'N/A'),
            'EPS (TTM)': info.get('trailingEps', 'N/A'),
            'Beta (5Y)': info.get('beta', 'N/A'),
            'RSI (14)': round(rsi, 2) if not pd.isna(rsi) else 'N/A',
            'Weekly Ret %': round(weekly_return * 100, 2),
            'Monthly Ret %': round(monthly_return * 100, 2),
            'YTD Ret %': round(ytd_return * 100, 2),
            '52W Ret %': round(year_return * 100, 2),
            '52W Range': f"{info.get('fiftyTwoWeekLow', '?')} - {info.get('fiftyTwoWeekHigh', '?')}",
            'Target 1Y': info.get('targetMeanPrice', 'N/A')
        }
        return data

    except Exception as e:
        # print(f"Error fetching data for {ticker_symbol}: {e}")
        return None

def main():
    print(f"--- Yahoo Daily Gainer Scanner Bot ---")
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tickers = get_day_gainers_safe()
    if not tickers:
        print("No tickers found. Exiting.")
        return

    print(f"Found {len(tickers)} tickers. Scanning details (this takes a moment)...")

    results_data = []
    
    # Progress indicator
    total = len(tickers)
    for i, symbol in enumerate(tickers):
        sys.stdout.write(f"\rScanning {i+1}/{total}: {symbol}   ")
        sys.stdout.flush()
        
        stock_data = get_stock_data(symbol)
        if stock_data:
            results_data.append(stock_data)

    print("\nScan Complete.\n")

    if not results_data:
        print("No data retrieved.")
        return

    df = pd.DataFrame(results_data)

    # --- Filtering Logic ---
    
    # 1. Simmering Growth (The "Sweet Spot")
    # 52-Week Return: 10% to 20%
    # Monthly Return: > 5% (Good growth)
    simmering = df[
        (df['52W Ret %'] >= 10) & 
        (df['52W Ret %'] <= 20) &
        (df['Monthly Ret %'] > 5)
    ].copy()

    # 2. The Rockets (Extreme Momentum)
    # 52-Week Return: > 50%
    # Monthly Return: > 10%
    rockets = df[
        (df['52W Ret %'] > 50) & 
        (df['Monthly Ret %'] > 10)
    ].copy()

    # 3. The Turnarounds (Deep Value)
    # 52-Week Return: Negative (< 0%)
    # Monthly Return: > 10% (Performing well recently)
    turnarounds = df[
         (df['52W Ret %'] < 0) & 
         (df['Monthly Ret %'] > 10)
    ].copy()
    
    # Output
    
    def print_list(name, dataframe):
        print(f"\n====== {name} ({len(dataframe)}) ======")
        if dataframe.empty:
            print("No stocks matched criteria.")
        else:
            cols_to_show = ['Symbol', 'Price', 'Monthly Ret %', 'YTD Ret %', '52W Ret %', 'RSI (14)', 'Volume', 'Market Cap']
            print(dataframe[cols_to_show].to_string(index=False))

    print_list("🔥 List 1: Simmering Growth (52W: 10-20%, Mo: >5%)", simmering)
    print_list("🚀 List 2: The Rockets (52W: >50%, Mo: >10%)", rockets)
    print_list("🔄 List 3: The Turnarounds (52W: <0%, Mo: >10%)", turnarounds)

    # Export
    save_dir = "Daily_Scans"
    os.makedirs(save_dir, exist_ok=True)
    filename = f"Scan_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
    path = os.path.join(save_dir, filename)
    
    # Add a 'List' column to the CSV export
    df['List'] = 'Other'
    if not simmering.empty:
        df.loc[simmering.index, 'List'] = 'Simmering Growth'
    if not rockets.empty:
        # Note: A stock could range in multiple, simple overwrite logic for now or concat
        # Using concat logic is better for overlapping matches, but let's just mark strictly
        df.loc[rockets.index, 'List'] = 'Rockets' 
    if not turnarounds.empty:
        df.loc[turnarounds.index, 'List'] = 'Turnarounds'
        
    df.to_csv(path, index=False)
    print(f"\n[Saved full scan results to {path}]")

    # --- Portfolio Tracker Integration ---
    try:
        import portfolio_manager
        print("\n=== Updating Portfolio Tracker ===")
        # 1. Add new positions from this scan
        portfolio_manager.add_new_positions(df)
        
        # 2. Update all existing positions with live prices
        portfolio_manager.update_portfolio_values()
        
    except ImportError:
        print("Warning: portfolio_manager.py not found. Skipping tracker update.")
    except Exception as e:
        print(f"Error in portfolio tracker: {e}")

if __name__ == "__main__":
    main()
