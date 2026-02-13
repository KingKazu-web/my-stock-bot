import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
# You'll need to add 'vaderSentiment' to your requirements
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- SETUP ---
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", 
    "AMZN": "Amazon", "META": "Meta Platforms", "GOOGL": "Google",
    "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", 
    "AVGO": "Broadcom", "TSLA": "Tesla"
}

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    """Analyzes text and returns a mood emoji"""
    if not text or "found" in text: return "⚪ Neutral"
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "🟢 Positive"
    if score <= -0.05: return "🔴 Negative"
    return "⚪ Neutral"

def get_pro_news(ticker):
    query = COMPANY_NAMES.get(ticker, ticker)
    url = f'https://newsapi.org/v2/everything?qInTitle={query}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
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
    report = f"📊 MARKET INTELLIGENCE REPORT - {today_str}\n"
    report += "--------------------------------------------------\n\n"
    
    big_moves = False # To check if we need a special subject line

    for ticker in COMPANY_NAMES.keys():
        print(f"Analyzing {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        
        if hist.empty or len(hist) < 2:
            report += f"⚪ {ticker}: Data unavailable.\n\n"
            continue
            
        price = hist['Close'].iloc[-1]
        change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        
        if abs(change) >= 3.0: big_moves = True # Trigger Alert

        headline = get_pro_news(ticker)
        sentiment = get_sentiment(headline)
        
        indicator = "📈" if change > 0 else "📉"
        report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
        report += f"🎭 MOOD: {sentiment}\n"
        report += f"📰 NEWS: {headline}\n"
        report += "--------------------------------------------------\n"

    # --- EMAIL SECTION ---
    msg = EmailMessage()
    msg.set_content(report)
    
    # LEVEL UP: Dynamic Subject Line
    subject = f"Market Intel: {today_str}"
    if big_moves:
        subject = f"⚠️ ALERT: Volatility Detected! - {today_str}"
    
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Report Sent!")

if __name__ == "__main__":
    run_tracker()
