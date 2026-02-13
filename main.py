import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. EXPANDED ASSET LIST
ASSETS = {
    "STOCKS": {
        "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AMZN": "Amazon",
        "META": "Meta Platforms", "GOOGL": "Google", "TSLA": "Tesla",
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

def get_pro_news(ticker, name):
    if not NEWS_API_KEY: return "Key missing."
    url = f'https://newsapi.org/v2/everything?qInTitle={name}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            return data['articles'][0]['title']
    except:
        pass
    return "No recent news found."

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    report_body = ""
    all_changes = [] 
    
    # Process each category
    for category, items in ASSETS.items():
        report_body += f"--- {category} ---\n"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                
                if hist.empty or len(hist) < 2:
                    report_body += f"⚪ {ticker}: Data unavailable.\n\n"
                    continue
                
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                all_changes.append((name, change))

                headline = get_pro_news(ticker, name)
                sentiment = get_sentiment(headline)
                
                indicator = "📈" if change > 0 else "📉"
                report_body += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
                report_body += f"🎭 Mood: {sentiment} | 📰 {headline[:75]}...\n\n"
            except Exception as e:
                print(f"Error {ticker}: {e}")
        report_body += "\n"

    # --- THE FIX: Creating the summary properly ---
    final_report = f"🏛️ GLOBAL MARKET INTELLIGENCE - {today_str}\n"
    final_report += "==================================================\n\n"
    
    if all_changes:
        best = max(all_changes, key=lambda x: x[1])
        worst = min(all_changes, key=lambda x: x[1])
        # We use a standard string and add newlines manually to avoid syntax errors
        summary = f"📊 SUMMARY OF MOVES\n🔥 Top Performer: {best[0]} ({best[1]:.2f}%)\n🧊 Laggard: {worst[0]} ({worst[1]:.2f}%)\n\n"
        final_report = final_report + summary + report_body
    else:
        final_report = final_report + report_body

    # --- EMAIL SECTION ---
    print("✉️ Preparing email...")
    msg = EmailMessage()
    msg.set_content(final_report)
    
    top_move = max([abs(x[1]) for x in all_changes]) if all_changes else 0
    subject = f"Market Intel: {today_str}"
    if top_move > 4.0:
        subject = f"🔥 HIGH VOLATILITY ALERT: {today_str}"

    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Full Report Sent!")

if __name__ == "__main__":
    run_tracker()
