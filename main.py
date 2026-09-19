import math
import datetime
import pandas as pd
import yfinance as yf

def calculate_contract_metrics(spot_price, futures_ticker, risk_free_rate, dividend_yield, expiry_date):
    """Calculates Fair Value and Cost of Carry for a single futures contract."""
    futures_data = yf.Ticker(futures_ticker)
    futures_hist = futures_data.history(period="1d")
    
    if futures_hist.empty:
        return None

    futures_price = futures_hist["Close"].iloc[-1]
    
    # Calculate Time to Expiration in years (T)
    today = datetime.date.today()
    days_to_expiry = (expiry_date - today).days
    T = days_to_expiry / 365.0
    
    if T <= 0:
        return None

    # Theoretical Fair Value Formula: F = S * e^((r - q) * T)
    net_rate = risk_free_rate - dividend_yield
    fair_value = spot_price * math.exp(net_rate * T)
    
    # Cost of carry calculations
    actual_coc = futures_price - spot_price
    theoretical_coc = fair_value - spot_price
    mispricing = futures_price - fair_value  # Positive = Overpriced, Negative = Underpriced
    
    return {
        "Contract": futures_ticker,
        "Expiry Date": expiry_date.strftime("%Y-%m-%d"),
        "Days to Expiry": days_to_expiry,
        "Futures Price": round(futures_price, 2),
        "Fair Value": round(fair_value, 2),
        "Actual CoC ($)": round(actual_coc, 2),
        "Theoretical CoC ($)": round(theoretical_coc, 2),
        "Mispricing ($)": round(mispricing, 2),
        "Market State": "Contango" if actual_coc > 0 else "Backwardation"
    }

def main():
    # Target Assets & Parameters
    SPOT_SYMBOL = "^GSPC"              # Spot Symbol (e.g. S&P 500 Index)
    FRONT_MONTH_FUTURES = "ES=F"       # Current Month Contract
    NEXT_MONTH_FUTURES = "ESM26.CME"   # Next Month Contract Ticker
    
    RISK_FREE_RATE = 0.045  # 4.5% Annual Risk-Free Rate
    DIVIDEND_YIELD = 0.013  # 1.3% Annual Dividend Yield
    
    # Define Specific Contract Expiry Dates
    CURRENT_MONTH_EXPIRY = datetime.date(2026, 9, 18)
    NEXT_MONTH_EXPIRY = datetime.date(2026, 12, 18)

    # Fetch Live Spot Price
    spot_data = yf.Ticker(SPOT_SYMBOL)
    spot_price = spot_data.history(period="1d")["Close"].iloc[-1]

    contracts = [
        (FRONT_MONTH_FUTURES, CURRENT_MONTH_EXPIRY, "Current Month"),
        (NEXT_MONTH_FUTURES, NEXT_MONTH_EXPIRY, "Next Month")
    ]

    results = []
    for ticker, expiry, month_label in contracts:
        metrics = calculate_contract_metrics(
            spot_price=spot_price,
            futures_ticker=ticker,
            risk_free_rate=RISK_FREE_RATE,
            dividend_yield=DIVIDEND_YIELD,
            expiry_date=expiry
        )
        if metrics:
            metrics["Period"] = month_label
            results.append(metrics)

    # Print Structured Comparative Table
    print(f"\nSpot Symbol: {SPOT_SYMBOL} | Current Spot Price: {round(spot_price, 2)}")
    print("=" * 95)
    df = pd.DataFrame(results)
    cols = ["Period", "Contract", "Expiry Date", "Days to Expiry", "Futures Price", "Fair Value", "Actual CoC ($)", "Mispricing ($)", "Market State"]
    print(df[cols].to_string(index=False))
    print("=" * 95 + "\n")

if __name__ == "__main__":
    main()
