import os
import yfinance as yf
import smtplib
import requests
import datetime
from email.message import EmailMessage

print("--- Starting Pro Intelligence Bot: Failsafe Heatmap Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. ASSETS
ASSETS = {
    "STOCKS": {"AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", "AMZN": "Amazon", "META": "Meta"},
    "CRYPTO": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"},
    "MACRO": {"GC=F": "Gold", "CL=F": "Crude Oil", "^TNX": "10-Yr Bond", "^GSPC": "S&P 500"}
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

def get_heat_square(change):
    if change > 3: return "🟩"  # Strong Green
    if change > 0: return "🍏"  # Light Green
    if change > -3: return "🍎" # Light Red
    return "🟥"                 # Strong Red

def get_pro_news_data(ticker, name):
    if not NEWS_API_KEY: return "Key missing.", "#"
    trusted = "reuters.com,cnbc.com,bloomberg.com,forbes.com"
    url = f'https://newsapi.org/v2/everything?q="{name}"&domains={trusted}&language=en&sortBy=relevancy&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        articles = requests.get(url).json().get('articles', [])
        if articles: return articles[0]['title'], articles[0]['url']
    except: pass
    return "No direct financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%b %d, %Y")
    market_why = get_market_why()
    all_changes = []
    heatmap_row = ""
    report_body = ""

    for category, items in ASSETS.items():
        report_body += f"<h3 style='border-bottom: 2px solid #eee; padding-top: 15px;'>{category}</h3>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="7d")
                if len(hist) < 2: continue
                
                prices = hist['Close'].tolist()
                price, change = prices[-1], ((prices[-1] - prices[-2]) / prices[-2]) * 100
                all_changes.append((name, change))
                
                heatmap_row += get_heat_square(change)
                momentum = get_momentum_meter(prices)
                headline, link = get_pro_news_data(ticker, name)
                
                color = "#27ae60" if change > 0 else "#e74c3c"
                report_body += f"""
                <div style="margin-bottom: 12px; padding: 10px; border-left: 4px solid {color}; background: #fafafa;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{ticker}</b> <span style="font-family: monospace; color: #636e72;">{momentum}</span>
                    </div>
                    <b style="color: {color};">${price:.2f} ({change:+.2f}%)</b><br>
                    <small>📰 <a href="{link}" style="color: #0984e3; text-decoration: none;">{headline[:65]}...</a></small>
                </div>
                """
            except Exception as e: print(f"Error {ticker}: {e}")

    # 4. EXECUTIVE SUMMARY WITH HEATMAP
    best = max(all_changes, key=lambda x: x[1]) if all_changes else ("N/A", 0)
    worst = min(all_changes, key=lambda x: x[1]) if all_changes else ("N/A", 0)
    
    summary_html = f"""
    <div style="background: #2d3436; color: white; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
        <h2 style="margin: 0; color: #00cec9;">🏛️ Market Pulse: {today_str}</h2>
        <div style="font-size: 24px; margin: 15px 0; letter-spacing: 4px;">{heatmap_row}</div>
        <p style="margin: 10px 0; font-style: italic; color: #dfe6e9; border-left: 3px solid #00cec9; padding-left: 10px;">
            " {market_why} "
        </p>
        <div style="display: flex; gap: 20px; border-top: 1px solid #636e72; padding-top: 15px; font-size: 0.9em;">
            <div style="flex: 1;"><small style="color: #55efc4;">🚀 BULL</small><br><b>{best[0]}</b></div>
            <div style="flex: 1;"><small style="color: #ff7675;">🐻 BEAR</small><br><b>{worst[0]}</b></div>
        </div>
    </div>
    """

    full_html = f"<html><body style='font-family: sans-serif; max-width: 600px; margin: auto;'>{summary_html}{report_body}</body></html>"

    msg = EmailMessage()
    msg['Subject'] = f"Intel Dashboard: {today_str}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(full_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Failsafe Dashboard Delivered!")

if __name__ == "__main__":
    run_tracker()
