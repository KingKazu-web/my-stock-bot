import os
import yfinance as yf
import smtplib
import datetime
from email.message import EmailMessage

print("--- Starting Market Intelligence Bot: Bulletproof Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")

# 2. ASSETS
ASSETS = {
    "STOCKS": {
        "AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", 
        "AMZN": "Amazon", "META": "Meta Platforms"
    },
    "CRYPTO": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"
    },
    "MACRO": {
        "GC=F": "Gold", "CL=F": "Crude Oil", 
        "^TNX": "Treasury", "^GSPC": "S&P 500"
    }
}

def get_market_why():
    """Siphons top news from the S&P 500 for the global catalyst."""
    try:
        market = yf.Ticker("^GSPC")
        news = market.news
        if news:
            return news[0].get('title', "Market showing standard volatility.")
        return "No major global catalysts reported."
    except:
        return "Global market context currently unavailable."

def get_momentum_meter(prices):
    if not prices or len(prices) < 2: return "[  ?  ]"
    low, high, current = min(prices), max(prices), prices[-1]
    if high == low: return "[▬▬●▬▬]"
    pos = int(((current - low) / (high - low)) * 5)
    meter = ["▬"] * 6
    meter[min(pos, 5)] = "●"
    return f"[{''.join(meter)}]"

def calculate_rsi(prices, periods=14):
    if len(prices) < periods: return "N/A"
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0)), losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[-periods:]) / periods
    avg_loss = sum(losses[-periods:]) / periods
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def get_pro_news_data(ticker, name):
    """Uses yfinance news - completely free, no API key needed."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if news:
            title = news[0].get('title', f'Latest {name} news')
            link = f"https://finance.yahoo.com/quote/{ticker}/news"
            return title, link
    except:
        pass
    return f"View latest {name} news on Yahoo.", f"https://finance.yahoo.com/quote/{ticker}/news"

def run_tracker():
    today_str = datetime.date.today().strftime("%b %d, %Y")
    market_why = get_market_why()
    report_body = ""
    all_changes = []
    advancers, decliners = 0, 0
    vol_detected = False

    for category, items in ASSETS.items():
        report_body += f"<h3 style='border-bottom: 2px solid #eee; padding-top: 15px; color: #34495e;'>{category}</h3>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="35d")
                if len(hist) < 2: continue
                
                prices = hist['Close'].tolist()
                price, change = prices[-1], ((prices[-1] - prices[-2]) / prices[-2]) * 100
                all_changes.append(change)
                if change > 0: advancers += 1
                else: decliners += 1

                curr_vol, avg_vol = hist['Volume'].iloc[-1], hist['Volume'].iloc[-31:-1].mean()
                conviction = "⚡" if curr_vol > (avg_vol * 1.5) else ""
                if conviction: vol_detected = True

                rsi_val = calculate_rsi(prices)
                momentum = get_momentum_meter(prices[-7:])
                rsi_s = "🔥" if (isinstance(rsi_val, float) and rsi_val > 70) else "❄️" if (isinstance(rsi_val, float) and rsi_val < 30) else ""

                color = "#27ae60" if change > 0 else "#e74c3c"
                headline, link = get_pro_news_data(ticker, name)
                
                report_body += f"""
                <div style="margin-bottom: 12px; padding: 10px; border-left: 4px solid {color}; background: #fafafa;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{ticker} {conviction}</b> <span style="font-family: monospace;">{momentum}</span>
                    </div>
                    <b style="color: {color};">${price:.2f} ({change:+.2f}%)</b> | RSI: {rsi_val} {rsi_s}<br>
                    <small>📰 <a href="{link}" style="color: #0984e3; text-decoration: none;">{headline[:75]}...</a></small>
                </div>
                """
            except Exception as e: print(f"Error {ticker}: {e}")

    legend_html = """
    <div style="background: #f1f2f6; padding: 15px; border-radius: 8px; font-size: 0.82em; color: #2f3542; margin-top: 25px; line-height: 1.5;">
        <b>📌 REPORT LEGEND</b><br>
        • <b>Momentum:</b> <code>[●▬▬▬▬]</code> 7-day low | <code>[▬▬●▬▬]</code> Average | <code>[▬▬▬▬●]</code> 7-day high.<br>
        • <b>RSI:</b> 🔥 Hot (> 70) | ❄️ Cold (< 30).<br>
        • <b>Conviction:</b> ⚡ High Volume (>1.5x average).
    </div>
    """

    summary_html = f"""
    <div style="background: #2d3436; color: white; padding: 25px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #00cec9;">🏛️ Market Pulse: {today_str}</h2>
        <p style="margin: 15px 0; border-left: 3px solid #00cec9; padding-left: 10px; font-style: italic;">"{market_why}"</p>
        <div style="display: flex; gap: 15px; font-size: 0.9em; border-top: 1px solid #444; padding-top: 10px;">
            <span>📈 Up: <b>{advancers}</b></span> <span>📉 Down: <b>{decliners}</b></span>
        </div>
    </div>
    """

    full_html = f"<html><body style='font-family: sans-serif; max-width: 600px; margin: auto;'>{summary_html}{report_body}{legend_html}</body></html>"
    msg = EmailMessage()
    msg['Subject'] = f"{'⚡ ' if vol_detected else ''}Intel: {today_str} ({advancers}/{decliners})"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(full_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Dispatch Successful.")

if __name__ == "__main__":
    run_tracker()
