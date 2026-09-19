import math
import datetime
import pandas as pd
import yfinance as yf

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
    # Start from the last day of the month
    if month == 12:
        last_day = datetime.date(year, 12, 31)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    
    # 3 is Thursday (Monday=0, Tuesday=1, ..., Thursday=3, ..., Sunday=6)
    offset = (last_day.weekday() - 3) % 7
    return last_day - datetime.timedelta(days=offset)

def fetch_stock_spot(symbol):
    """Fetches spot price safely from Yahoo Finance for NSE stocks."""
    ticker_symbol = f"{symbol}.NS"
    try:
        data = yf.Ticker(ticker_symbol)
        hist = data.history(period="5d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    return None

def calculate_theoretical_future(spot_price, expiry_date, risk_free_rate, dividend_yield):
    """Calculates theoretical fair value and cost of carry for a given expiry date."""
    today = datetime.date.today()
    days_to_expiry = max((expiry_date - today).days, 1)
    T = days_to_expiry / 365.0

    net_rate = risk_free_rate - dividend_yield
    fair_value = spot_price * math.exp(net_rate * T)
    coc = fair_value - spot_price

    return {
        "expiry": expiry_date.strftime("%Y-%m-%d"),
        "days": days_to_expiry,
        "fair_value": round(fair_value, 2),
        "coc": round(coc, 2)
    }

def main():
    print("Calculating Current Month & Next Month Cost of Carry for Nifty 50...")
    
    # Financial parameters for NSE Market
    RISK_FREE_RATE = 0.065  # ~6.5% RBI Repo Rate
    DIVIDEND_YIELD = 0.012  # ~1.2% Average Dividend Yield
    
    today = datetime.date.today()
    
    # Calculate Current Month Expiry (Last Thursday of current month)
    curr_expiry = get_last_thursday(today.year, today.month)
    if curr_expiry < today:
        # If today is past this month's expiry, move to next month
        next_month_date = today.replace(day=28) + datetime.timedelta(days=4)
        curr_expiry = get_last_thursday(next_month_date.year, next_month_date.month)

    # Calculate Next Month Expiry (Last Thursday of next month)
    following_month_date = curr_expiry.replace(day=28) + datetime.timedelta(days=4)
    next_expiry = get_last_thursday(following_month_date.year, following_month_date.month)

    results = []

    for symbol in NIFTY_50_STOCKS:
        spot_price = fetch_stock_spot(symbol)
        if spot_price is None:
            continue

        # Current Month Calculations
        curr_fut = calculate_theoretical_future(
            spot_price, curr_expiry, RISK_FREE_RATE, DIVIDEND_YIELD
        )

        # Next Month Calculations
        next_fut = calculate_theoretical_future(
            spot_price, next_expiry, RISK_FREE_RATE, DIVIDEND_YIELD
        )

        calendar_spread = round(next_fut["fair_value"] - curr_fut["fair_value"], 2)

        results.append({
            "Symbol": symbol,
            "Spot (₹)": round(spot_price, 2),
            "Near Expiry": curr_fut["expiry"],
            "Near Fut (₹)": curr_fut["fair_value"],
            "Near CoC (₹)": curr_fut["coc"],
            "Next Expiry": next_fut["expiry"],
            "Next Fut (₹)": next_fut["fair_value"],
            "Next CoC (₹)": next_fut["coc"],
            "Calendar Spread (₹)": calendar_spread
        })

    print("\n" + "=" * 135)
    print("                NIFTY 50 STOCKS - CURRENT & NEXT MONTH FUTURES COST OF CARRY")
    print("=" * 135)

    if results:
        pd.set_option("display.max_rows", 60)
        pd.set_option("display.width", 1000)
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
    else:
        print("No stock data was fetched.")

    print("=" * 135 + "\n")

if __name__ == "__main__":
    main()
