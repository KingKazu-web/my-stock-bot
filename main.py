import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Market Intelligence Bot ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. ASSET LIST (Stocks + Crypto)
COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", 
    "AMZN": "Amazon", "META": "Meta Platforms", "GOOGL": "Google",
    "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", 
    "AVGO": "Broadcom", "TSLA": "Tesla",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "XRP-USD": "XRP Ripple"
}

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    """Analyzes headline and returns mood"""
    if not text or "found" in text: return "⚪ Neutral"
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "🟢 Positive"
    if score <= -0.05: return "🔴 Negative"
    return "⚪ Neutral"

def get_pro_news(ticker):
    """Fetches news via NewsAPI"""
    if not NEWS_API_KEY: return "News key missing."
    query = COMPANY_NAMES.get(ticker, ticker)
    url = f'https://newsapi.org/v2/everything?qInTitle={query}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            return data['articles'][0]['title']
    except:
        pass
    return "No recent headlines found."

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    report = f"📊 DAILY MARKET INTELLIGENCE - {today_str}\n"
    report += "--------------------------------------------------\n\n"
    
    big_moves = False 

    for ticker, name in COMPANY_NAMES.items():
        print(f"🔍 Analyzing {name} ({ticker})...")
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            # THE FIX: Added the missing colon after hist.empty below
            if hist.empty or len(hist) < 2:
                report += f"⚪ {ticker}: Data temporarily unavailable.\n\n"
                continue
                
            price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((price - prev_price) / prev_price) * 100
            
            # Trigger Alert if move is > 3%
            if abs(change) >= 3.0: 
                big_moves = True 

            headline = get_pro_news(ticker)
            sentiment = get_sentiment(headline)
            
            indicator = "📈" if change > 0 else "📉"
            report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
            report += f"🎭 MOOD: {sentiment}\n"
            report += f"📰 NEWS: {headline}\n"
            report += "--------------------------------------------------\n"
        except Exception as e:
            print(f"Error on {ticker}: {e}")

    # --- EMAIL SECTION ---
    print("✉️ Preparing email...")
    msg = EmailMessage()
    msg.set_content(report)
    
    subject = f"Market Intel: {today_str}"
    if big_moves:
        subject = f"⚠️ ALERT: High Volatility Detected! - {today_str}"
    
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ SUCCESS: Intelligence report delivered!")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")

if __name__ == "__main__":
    run_tracker()
