import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot: Zero-Redirect Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. OPTIMIZED ASSET LIST
ASSETS = {
    "STOCKS": {
        "AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", 
        "AMZN": "Amazon stock", "META": "Meta Platforms", "GOOGL": "Alphabet Google",
        "MSFT": "Microsoft", "AVGO": "Broadcom", "LLY": "Eli Lilly", "BRK-B": "Berkshire Hathaway"
    },
    "CRYPTO": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "XRP-USD": "XRP Ripple"
    },
    "MACRO": {
        "GC=F": "Gold Price", "CL=F": "Crude Oil", "^TNX": "10-Year Treasury",
        "XLF": "Financial Sector", "XLI": "Industrial Sector", "XLU": "Utilities Sector"
    }
}

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if not text or "found" in text: return "⚪ Neutral"
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "🟢 Positive"
    if score <= -0.05: return "🔴 Negative"
    return "⚪ Neutral"

def get_pro_news_data(ticker, name, category):
    """The 'Fortress' News Fetcher: Only high-tier, direct-link sources"""
    if not NEWS_API_KEY: return "Key missing.", "#"
    
    # We restrict to these domains to avoid the Yahoo Consent Wall and Junk deals
    trusted_domains = "reuters.com,cnbc.com,bloomberg.com,forbes.com,fortune.com,marketwatch.com"
    
    # Advanced Search Query
    query = f'"{name}"'
    if category == "STOCKS":
        query += " AND (stock OR earnings OR analyst)"
    elif category == "CRYPTO":
        query += " AND (crypto OR price OR bitcoin)"

    url = (f'https://newsapi.org/v2/everything?'
           f'q={query}&'
           f'domains={trusted_domains}&'
           f'language=en&'
           f'sortBy=relevancy&'
           f'pageSize=1&' 
           f'apiKey={NEWS_API_KEY}')
    
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            article = data['articles'][0]
            # Double check to ensure NO yahoo links snuck in
            if "yahoo.com" not in article['url'] and "slickdeals" not in article['url']:
                return article['title'], article['url']
    except Exception as e:
        print(f"News Error for {ticker}: {e}")
        
    return "No direct financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    all_changes = [] 
    
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, sans-serif; color: #2d3436; line-height: 1.6;">
        <h1 style="color: #0984e3; border-bottom: 3px solid #0984e3; padding-bottom: 10px;">🏛️ Executive Market Intel: {today_str}</h1>
    """
    
    report_body = ""

    for category, items in ASSETS.items():
        report_body += f"<h2 style='background: #dfe6e9; padding: 8px 15px; border-radius: 5px; color: #2d3436;'>{category}</h2>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if hist.empty or len(hist) < 2: continue
                
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                all_changes.append((name, change))

                headline, link = get_pro_news_data(ticker, name, category)
                sentiment = get_sentiment(headline)
                
                color = "#27ae60" if change > 0 else "#e74c3c"
                report_body += f"""
                <div style="margin-bottom: 20px; border-left: 6px solid {color}; padding: 5px 15px; background: #fafafa;">
                    <b style="font-size: 1.1em;">{ticker}: ${price:.2f} 
                    (<span style="color: {color};">{change:+.2f}%</span>)</b><br>
                    <span style="font-size: 0.9em; color: #636e72;">🎭 Sentiment: <b>{sentiment}</b></span><br>
                    📰 <a href="{link}" style="color: #0984e3; text-decoration: none; font-weight: 500;">{headline}</a>
                </div>
                """
            except Exception as e:
                print(f"Error {ticker}: {e}")

    summary_html = ""
    if all_changes:
        best = max(all_changes, key=lambda x: x[1])
        worst = min(all_changes, key=lambda x: x[1])
        summary_html = f"""
        <div style="background: #f1f2f6; border: 1px solid #ced4da; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
            <b style="font-size: 1.2em; color: #2d3436;">📊 MARKET SNAPSHOT</b><br>
            <span style="color: #27ae60; font-weight: bold;">▲ Leader:</span> {best[0]} ({best[1]:.2f}%)<br>
            <span style="color: #e74c3c; font-weight: bold;">▼ Laggard:</span> {worst[0]} ({worst[1]:.2f}%)
        </div>
        """

    html_content += summary_html + report_body + "</body></html>"

    msg = EmailMessage()
    msg['Subject'] = f"Market Intel: {today_str}"
    if all_changes and max([abs(x[1]) for x in all_changes]) > 4.0:
        msg['Subject'] = f"🚨 VOLATILITY ALERT: {today_str}"
        
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Executive Report Delivered. No more redirects!")

if __name__ == "__main__":
    run_tracker()
