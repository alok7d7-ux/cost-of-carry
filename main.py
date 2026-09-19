import json
import math
import datetime
import urllib.request

# List of Nifty 50 Stock Tickers (NSE)
NIFTY_50_STOCKS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BPCL",
    "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB",
    "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK",
    "LT", "LTIM", "M&M", "MARUTI", "NTPC",
    "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE",
    "SHRIRAMFIN", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM",
    "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "ULTRACEMCO"
]

def get_last_thursday(year, month):
    """Calculates the last Thursday of a given month (NSE Expiry Day)."""
    if month == 12:
        last_day = datetime.date(year, 12, 31)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    offset = (last_day.weekday() - 3) % 7
    return last_day - datetime.timedelta(days=offset)

def fetch_stock_spot(symbol):
    """Fetches stock spot price directly via Yahoo Finance endpoint."""
    ticker_symbol = f"{symbol}.NS"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_symbol}?range=5d&interval=1d"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            result = data['chart']['result'][0]
            close_prices = result['indicators']['quote'][0]['close']
            valid_prices = [p for p in close_prices if p is not None]
            if valid_prices:
                return valid_prices[-1]
    except Exception:
        pass
    return None

def calculate_theoretical_future(spot_price, expiry_date, risk_free_rate, dividend_yield):
    """Calculates theoretical fair value and cost of carry for a given expiry date."""
    today = datetime.date.today()
    days_to_expiry = max((expiry_date - today).days, 1)
    T = days_to_expiry / 365.0

    net_rate = risk_free_rate - dividend_yield
    fair_value = spot_price * math.exp(net_rate * T)
    coc = fair_value - spot_price
    coc_pct = (coc / spot_price) * 100

    return {
        "expiry": expiry_date.strftime("%Y-%m-%d"),
        "days": days_to_expiry,
        "fair_value": round(fair_value, 2),
        "coc": round(coc, 2),
        "coc_pct": round(coc_pct, 2)
    }

def main():
    print("Fetching Nifty 50 Spot Prices & Calculating Cost of Carry...\n")
    
    RISK_FREE_RATE = 0.065  # ~6.5% RBI Repo Rate
    DIVIDEND_YIELD = 0.012  # ~1.2% Average Dividend Yield
    
    today = datetime.date.today()
    
    # Calculate Expiries
    curr_expiry = get_last_thursday(today.year, today.month)
    if curr_expiry < today:
        next_month_date = today.replace(day=28) + datetime.timedelta(days=4)
        curr_expiry = get_last_thursday(next_month_date.year, next_month_date.month)

    following_month_date = curr_expiry.replace(day=28) + datetime.timedelta(days=4)
    next_expiry = get_last_thursday(following_month_date.year, following_month_date.month)

    header = f"{'Symbol':<12} | {'Spot (₹)':<10} | {'Near Fut':<10} | {'Near CoC':<10} | {'CoC %':<8} | {'Next Fut':<10} | {'Spread':<10}"
    print("=" * len(header))
    print(header)
    print("=" * len(header))

    high_coc_alerts = []

    for symbol in NIFTY_50_STOCKS:
        spot_price = fetch_stock_spot(symbol)
        if spot_price is None:
            continue

        curr_fut = calculate_theoretical_future(spot_price, curr_expiry, RISK_FREE_RATE, DIVIDEND_YIELD)
        next_fut = calculate_theoretical_future(spot_price, next_expiry, RISK_FREE_RATE, DIVIDEND_YIELD)
        calendar_spread = round(next_fut["fair_value"] - curr_fut["fair_value"], 2)
        spread_pct = round((calendar_spread / spot_price) * 100, 2)

        print(f"{symbol:<12} | {round(spot_price, 2):<10.2f} | {curr_fut['fair_value']:<10.2f} | {curr_fut['coc']:<10.2f} | {curr_fut['coc_pct']:<7.2f}% | {next_fut['fair_value']:<10.2f} | {calendar_spread:<10.2f}")

        # Check for > 0.6% threshold
        if curr_fut['coc_pct'] >= 0.6 or spread_pct >= 0.6:
            high_coc_alerts.append({
                "Symbol": symbol,
                "Near_CoC_Pct": curr_fut['coc_pct'],
                "Spread_Pct": spread_pct
            })

    print("=" * len(header))

    # Display Scanner Alerts
    print("\n" + "#" * 60)
    print("          FLAGGED STOCKS (CoC % or Spread % >= 0.6%)")
    print("#" * 60)
    
    if high_coc_alerts:
        for alert in high_coc_alerts:
            print(f"-> {alert['Symbol']}: Near CoC = {alert['Near_CoC_Pct']}%, Calendar Spread % = {alert['Spread_Pct']}%")
        print("\nINTRADAY RULE: Highly inflated premium detected.")
        print("1. Directional Move: Buy Near-Fut IF price is above VWAP with volume.")
        print("2. Spread Arbitrage: Short Near-Fut + Buy Spot/Next-Fut if premium is overextended.")
    else:
        print("No stocks currently exceeding 0.6% CoC threshold.")
    
    print("#" * 60 + "\n")

if __name__ == "__main__":
    main()
