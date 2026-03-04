import os
import yfinance as yf
import smtplib
import requests
import datetime
from email.message import EmailMessage
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot: AI Insights Edition ---")

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

analyzer = SentimentIntensityAnalyzer()

def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return f"{r['data'][0]['value']} ({r['data'][0]['value_classification']})"
    except: return "N/A"

def get_market_why():
    """Fetches the top global financial story to explain 'The Why'."""
    if not NEWS_API_KEY: return "Market context unavailable."
    url = f'https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        data = requests.get(url).json()
        if data['articles']:
            return data['articles'][0]['title']
    except: pass
    return "No major global catalyst identified today."

def get_sparkline_url(data_list, color="blue"):
    if not data_list: return ""
    data_str = ",".join([str(round(x, 2)) for x in data_list])
    return f"https://quickchart.io/chart?c={{type:'sparkline',data:{{datasets:[{{data:[{data_str}],borderColor:'{color}',fill:false}}]}}}}&w=100&h=30"

def get_pro_news_data(ticker, name):
    if not NEWS_API_KEY: return "Key missing.", "#"
    trusted = "reuters.com,cnbc.com,bloomberg.com,forbes.com,marketwatch.com"
    url = f'https://newsapi.org/v2/everything?q="{name}"&domains={trusted}&language=en&sortBy=relevancy&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        articles = requests.get(url).json().get('articles', [])
        if articles: return articles[0]['title'], articles[0]['url']
    except: pass
    return "No direct financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%b %d, %Y")
    market_why = get_market_why()
    fng_index = get_fear_greed()
    all_changes = []
    report_body = ""

    for category, items in ASSETS.items():
        report_body += f"<h3 style='border-bottom: 2px solid #eee; padding-top: 20px; color: #2d3436;'>{category}</h3>"
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
                
                chart_color = "#27ae60" if change > 0 else "#e74c3c"
                spark_url = get_sparkline_url(prices, chart_color)
                headline, link = get_pro_news_data(ticker, name)
                
                report_body += f"""
                <div style="margin-bottom: 15px; display: flex; align-items: center; background: #fdfdfd; padding: 10px; border-radius: 5px;">
                    <div style="flex: 1;">
                        <b style="font-size: 1.1em;">{ticker}</b>: ${price:.2f} 
                        <span style="color: {chart_color}; font-weight: bold;">{change:+.2f}%</span><br>
                        <small>📰 <a href="{link}" style="color: #0984e3; text-decoration: none;">{headline[:70]}...</a></small>
                    </div>
                    <img src="{spark_url}" width="100" height="30" style="margin-left: 10px;">
                </div>
                """
            except Exception as e: print(f"Error {ticker}: {e}")

    # EXECUTIVE SUMMARY RE-INTEGRATED
    best = max(all_changes, key=lambda x: x[1]) if all_changes else ("None", 0)
    worst = min(all_changes, key=lambda x: x[1]) if all_changes else ("None", 0)
    avg_move = sum([x[1] for x in all_changes]) / len(all_changes) if all_changes else 0

    summary_html = f"""
    <div style="background: #2d3436; color: white; padding: 25px; border-radius: 12px; margin-bottom: 30px;">
        <h2 style="margin: 0; color: #00cec9;">🏛️ Market Pulse: {today_str}</h2>
        <p style="margin: 15px 0; font-style: italic; color: #dfe6e9; border-left: 3px solid #00cec9; padding-left: 10px;">
            " {market_why} "
        </p>
        <div style="display: flex; gap: 20px; border-top: 1px solid #636e72; padding-top: 15px;">
            <div style="flex: 1;">
                <small style="color: #b2bec3;">FEAR & GREED</small><br><b>{fng_index}</b>
            </div>
            <div style="flex: 1;">
                <small style="color: #55efc4;">TOP BULL</small><br><b>{best[0]} ({best[1]:+.2f}%)</b>
            </div>
            <div style="flex: 1;">
                <small style="color: #ff7675;">TOP BEAR</small><br><b>{worst[0]} ({worst[1]:+.2f}%)</b>
            </div>
        </div>
    </div>
    """

    full_html = f"<html><body style='font-family: Arial, sans-serif; max-width: 650px; margin: auto; color: #2d3436;'>{summary_html}{report_body}</body></html>"

    msg = EmailMessage()
    msg['Subject'] = f"Intel Dashboard: {today_str} ({avg_move:+.1f}%)"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(full_html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Executive Dashboard Delivered!")

if __name__ == "__main__":
    run_tracker()
