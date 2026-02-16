import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot (Newsletter Edition) ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

ASSETS = {
    "STOCKS": {
        "AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", "MSFT": "Microsoft",
        "GOOGL": "Google", "AMZN": "Amazon", "META": "Meta Platforms",
        "AVGO": "Broadcom", "LLY": "Eli Lilly", "BRK-B": "Berkshire Hathaway"
    },
    "CRYPTO": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "XRP-USD": "XRP Ripple"
    },
    "MACRO": {
        "GC=F": "Gold Futures", "CL=F": "Crude Oil", "^TNX": "10-Year Treasury Yield",
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

def get_pro_news_data(name):
    """Returns both the headline and the link"""
    if not NEWS_API_KEY: return "Key missing.", "#"
    url = f'https://newsapi.org/v2/everything?qInTitle={name}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            article = data['articles'][0]
            return article['title'], article['url']
    except:
        pass
    return "No recent news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    all_changes = [] 
    
    # Start building HTML content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h1 style="color: #2c3e50;">🏛️ Market Intelligence: {today_str}</h1>
        <hr>
    """
    
    table_rows = "" # We'll build the asset list here

    for category, items in ASSETS.items():
        table_rows += f"<h3>--- {category} ---</h3>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if hist.empty or len(hist) < 2: continue
                
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                all_changes.append((name, change))

                headline, link = get_pro_news_data(name)
                sentiment = get_sentiment(headline)
                
                color = "green" if change > 0 else "red"
                table_rows += f"""
                <div style="margin-bottom: 15px; border-left: 4px solid {color}; padding-left: 10px;">
                    <b>{ticker}: ${price:.2f} (<span style="color: {color};">{change:.2f}%</span>)</b><br>
                    🎭 Mood: {sentiment} | 📰 <a href="{link}">{headline}</a>
                </div>
                """
            except Exception as e:
                print(f"Error {ticker}: {e}")

    # Build the Summary at the top
    summary_html = ""
    if all_changes:
        best = max(all_changes, key=lambda x: x[1])
        worst = min(all_changes, key=lambda x: x[1])
        summary_html = f"""
        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
            <b>📊 DAILY SUMMARY</b><br>
            🔥 Top Performer: {best[0]} ({best[1]:.2f}%)<br>
            🧊 Laggard: {worst[0]} ({worst[1]:.2f}%)
        </div><br>
        """

    html_content += summary_html + table_rows + "</body></html>"

    # --- EMAIL SECTION ---
    msg = EmailMessage()
    msg['Subject'] = f"Market Intel: {today_str}"
    if any(abs(x[1]) > 4.0 for x in all_changes):
        msg['Subject'] = f"🔥 VOLATILITY ALERT: {today_str}"
        
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.set_content("Please use an HTML-compatible email client to view this report.") # Fallback
    msg.add_alternative(html_content, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Newsletter delivered with live links!")

if __name__ == "__main__":
    run_tracker()
