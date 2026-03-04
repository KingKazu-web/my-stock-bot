import os
import yfinance as yf
import smtplib
import requests
import datetime
from email.message import EmailMessage
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot: Dashboard Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. ASSETS
ASSETS = {
    "STOCKS": {"AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", "AMZN": "Amazon"},
    "CRYPTO": {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum"},
    "MACRO": {"GC=F": "Gold", "CL=F": "Crude Oil", "^TNX": "10-Yr Bond"}
}

analyzer = SentimentIntensityAnalyzer()

def get_fear_greed():
    """Fetches real-time Crypto Fear & Greed Index."""
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        val = r['data'][0]['value']
        cls = r['data'][0]['value_classification']
        return f"{val} ({cls})"
    except: return "N/A"

def get_sparkline_url(data_list, color="blue"):
    """Generates a QuickChart sparkline URL for the last 7 days."""
    if not data_list: return ""
    data_str = ",".join([str(round(x, 2)) for x in data_list])
    return f"https://quickchart.io/chart?c={{type:'sparkline',data:{{datasets:[{{data:[{data_str}],borderColor:'{color}',fill:false}}]}}}}&w=100&h=30"

def get_pro_news_data(ticker, name):
    if not NEWS_API_KEY: return "Key missing.", "#"
    trusted = "reuters.com,cnbc.com,bloomberg.com,forbes.com"
    url = f'https://newsapi.org/v2/everything?q="{name}"&domains={trusted}&language=en&sortBy=relevancy&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        articles = requests.get(url).json().get('articles', [])
        if articles: return articles[0]['title'], articles[0]['url']
    except: pass
    return "No recent financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%b %d, %Y")
    fng_index = get_fear_greed()
    all_changes = []
    report_body = ""

    for category, items in ASSETS.items():
        report_body += f"<h3 style='border-bottom: 1px solid #eee; padding-top: 15px;'>{category}</h3>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="7d")
                if len(hist) < 2: continue
                
                prices = hist['Close'].tolist()
                price = prices[-1]
                change = ((price - prices[-2]) / prices[-2]) * 100
                all_changes.append((name, change))
                
                chart_color = "green" if change > 0 else "red"
                spark_url = get_sparkline_url(prices, chart_color)
                
                headline, link = get_pro_news_data(ticker, name)
                
                report_body += f"""
                <div style="margin-bottom: 15px; display: flex; align-items: center;">
                    <div style="flex: 1;">
                        <b>{ticker}</b>: ${price:.2f} 
                        <span style="color: {'green' if change > 0 else 'red'};">{change:+.2f}%</span><br>
                        <small>📰 <a href="{link}" style="color: #0984e3; text-decoration: none;">{headline[:60]}...</a></small>
                    </div>
                    <img src="{spark_url}" width="100" height="30" style="margin-left: 10px; vertical-align: middle;">
                </div>
                """
            except Exception as e: print(f"Error {ticker}: {e}")

    # EXECUTIVE SUMMARY
    avg_move = sum([x[1] for x in all_changes]) / len(all_changes) if all_changes else 0
    summary_html = f"""
    <div style="background: #2d3436; color: white; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
        <h2 style="margin: 0; color: #00cec9;">🏛️ Executive Brief: {today_str}</h2>
        <p style="margin: 10px 0;">Market Vibe: <b>{avg_move:+.2f}% Average Move</b></p>
        <p style="margin: 5px 0;">Fear & Greed Index: <span style="color: #fab1a0;">{fng_index}</span></p>
    </div>
    """

    full_html = f"<html><body style='font-family: sans-serif; max-width: 600px; margin: auto;'>{summary_html}{report_body}</body></html>"

    msg = EmailMessage()
    msg['Subject'] = f"Market Dashboard: {today_str}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(full_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Dashboard Delivered!")

if __name__ == "__main__":
    run_tracker()
