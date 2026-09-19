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

def fetch_last_close(symbol):
    """Fetches the latest close price for a given ticker."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
    except Exception:
        pass
    return None

def calculate_contract_metrics(spot_price, futures_ticker, risk_free_rate, dividend_yield, expiry_date):
    """Calculates Fair Value and Cost of Carry for a specific futures contract."""
    futures_price = fetch_last_close(futures_ticker)
    
    # Fallback to spot price if futures tick is not directly available
    if futures_price is None:
        futures_price = spot_price

    today = datetime.date.today()
    days_to_expiry = max((expiry_date - today).days, 1)
    T = days_to_expiry / 365.0

    # Theoretical Fair Value Formula: F = S * e^((r - q) * T)
    net_rate = risk_free_rate - dividend_yield
    fair_value = spot_price * math.exp(net_rate * T)

    actual_coc = futures_price - spot_price
    mispricing = futures_price - fair_value

    return {
        "Futures Price": round(futures_price, 2),
        "Fair Value": round(fair_value, 2),
        "CoC (₹)": round(actual_coc, 2),
        "Mispricing (₹)": round(mispricing, 2),
        "Days to Expiry": days_to_expiry
    }

def main():
    print("Fetching Nifty 50 Current Month & Next Month Futures data...")
    
    # Market Parameters
    RISK_FREE_RATE = 0.065  # ~6.5% RBI Repo Rate
    DIVIDEND_YIELD = 0.012  # ~1.2% Average Dividend Yield
    
    # NSE Monthly Expiry Dates (Last Thursday of current & next month)
    CURRENT_MONTH_EXPIRY = datetime.date(2026, 9, 24)
    NEXT_MONTH_EXPIRY = datetime.date(2026, 10, 29)

    results = []

    for symbol in NIFTY_50_STOCKS:
        spot_ticker = f"{symbol}.NS"
        curr_fut_ticker = f"{symbol}1!.NS"  # Front-month continuous contract
        next_fut_ticker = f"{symbol}2!.NS"  # Next-month continuous contract

        spot_price = fetch_last_close(spot_ticker)
        if spot_price is None:
            continue

        # Current Month Metrics
        curr_metrics = calculate_contract_metrics(
            spot_price=spot_price,
            futures_ticker=curr_fut_ticker,
            risk_free_rate=RISK_FREE_RATE,
            dividend_yield=DIVIDEND_YIELD,
            expiry_date=CURRENT_MONTH_EXPIRY
        )

        # Next Month Metrics
        next_metrics = calculate_contract_metrics(
            spot_price=spot_price,
            futures_ticker=next_fut_ticker,
            risk_free_rate=RISK_FREE_RATE,
            dividend_yield=DIVIDEND_YIELD,
            expiry_date=NEXT_MONTH_EXPIRY
        )

        results.append({
            "Symbol": symbol,
            "Spot (₹)": round(spot_price, 2),
            "Near Fut (₹)": curr_metrics["Futures Price"],
            "Near FairVal (₹)": curr_metrics["Fair Value"],
            "Near CoC (₹)": curr_metrics["CoC (₹)"],
            "Next Fut (₹)": next_metrics["Futures Price"],
            "Next FairVal (₹)": next_metrics["Fair Value"],
            "Next CoC (₹)": next_metrics["CoC (₹)"],
            "Calendar Spread (₹)": round(next_metrics["Futures Price"] - curr_metrics["Futures Price"], 2)
        })

    print("\n" + "=" * 125)
    print("                 NIFTY 50 STOCKS - CURRENT MONTH & NEXT MONTH FUTURES ANALYSIS")
    print("=" * 125)

    if results:
        pd.set_option("display.max_rows", 60)
        pd.set_option("display.width", 1000)
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
    else:
        print("Failed to fetch market data.")

    print("=" * 125 + "\n")

if __name__ == "__main__":
    main()
