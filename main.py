import os
import yfinance as yf
import smtplib
import requests
import datetime
from email.message import EmailMessage

print("--- Starting Pro Intelligence Bot: Conviction Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. ASSETS
ASSETS = {
    "STOCKS": {"AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", "AMZN": "Amazon", "META": "Meta"},
    "CRYPTO": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"},
    "MACRO": {"GC=F": "Gold", "CL=F": "Crude Oil", "^TNX": "10-Yr Bond"}
}

def get_market_why():
    if not NEWS_API_KEY: return "Market context unavailable."
    url = f'https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        data = requests.get(url).json()
        return data['articles'][0]['title'] if data['articles'] else "No major catalyst found."
    except: return "Global market news fetch failed."

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
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[-periods:]) / periods
    avg_loss = sum(losses[-periods:]) / periods
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def get_pro_news_data(ticker, name):
    if not NEWS_API_KEY: return "Key missing.", "#"
    url = f'https://newsapi.org/v2/everything?q="{name}"&language=en&sortBy=relevancy&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        articles = requests.get(url).json().get('articles', [])
        return (articles[0]['title'], articles[0]['url']) if articles else ("No news.", "#")
    except: return ("News error.", "#")

def run_tracker():
    today_str = datetime.date.today().strftime("%b %d, %Y")
    market_why = get_market_why()
    report_body = ""
    volatility_detected = False

    for category, items in ASSETS.items():
        report_body += f"<h3 style='border-bottom: 2px solid #eee; padding-top: 15px; color: #34495e;'>{category}</h3>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="35d") # Extra days for RSI/Volume Avg
                if len(hist) < 2: continue
                
                prices = hist['Close'].tolist()
                price, change = prices[-1], ((prices[-1] - prices[-2]) / prices[-2]) * 100
                
                # VOLUME SPIKE LOGIC
                current_vol = hist['Volume'].iloc[-1]
                avg_vol = hist['Volume'].iloc[-31:-1].mean()
                volume_ratio = current_vol / avg_vol
                conviction_alert = "⚡" if volume_ratio > 1.5 else ""
                if volume_ratio > 1.5: volatility_detected = True

                rsi_val = calculate_rsi(prices)
                momentum = get_momentum_meter(prices[-7:])
                
                # RSI Visual Status
                rsi_status = ""
                if isinstance(rsi_val, float):
                    if rsi_val > 70: rsi_status = "🔥"
                    elif rsi_val < 30: rsi_status = "❄️"

                color = "#27ae60" if change > 0 else "#e74c3c"
                headline, link = get_pro_news_data(ticker, name)
                
                report_body += f"""
                <div style="margin-bottom: 12px; padding: 10px; border-left: 4px solid {color}; background: #fafafa;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{ticker} {conviction_alert}</b> 
                        <span style="font-family: monospace;">{momentum}</span>
                    </div>
                    <b style="color: {color};">${price:.2f} ({change:+.2f}%)</b> | 
                    <small>RSI: {rsi_val} {rsi_status}</small><br>
                    <small>📰 <a href="{link}" style="color: #0984e3; text-decoration: none;">{headline[:70]}...</a></small>
                </div>
                """
            except Exception as e: print(f"Error {ticker}: {e}")

    legend_html = """
    <div style="background: #f1f2f6; padding: 15px; border-radius: 8px; font-size: 0.85em; color: #2f3542; margin-top: 20px;">
        <b>📌 CONVICTION LEGEND</b><br>
        • ⚡ <b>Volume Spike:</b> Today's trading volume is >150% of the monthly average (High Conviction).<br>
        • 🔥/❄️ <b>RSI:</b> Overbought (Hot) or Oversold (Cold).
    </div>
    """

    summary_html = f"""
    <div style="background: #2d3436; color: white; padding: 25px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #00cec9;">🏛️ Market Pulse: {today_str}</h2>
        <p style="margin: 15px 0; border-left: 3px solid #00cec9; padding-left: 10px; font-style: italic;">
            "{market_why}"
        </p>
    </div>
    """

    full_html = f"<html><body style='font-family: sans-serif; max-width: 600px; margin: auto;'>{summary_html}{report_body}{legend_html}</body></html>"

    msg = EmailMessage()
    subject = f"Intel: {today_str}"
    if volatility_detected: subject = f"⚡ HIGH VOLUME ALERT: {today_str}"
    
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(full_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print(f"✅ Conviction Dashboard Delivered! Volume Alert: {volatility_detected}")

if __name__ == "__main__":
    run_tracker()
