import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime

# 1. Get Secrets
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

def get_pro_news(ticker):
    """Fetches the latest headline using NewsAPI"""
    url = f'https://newsapi.org/v2/everything?q={ticker}&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data['status'] == 'ok' and data['totalResults'] > 0:
            return data['articles'][0]['title']
    except:
        return "Could not fetch news."
    return "No recent news found."

def run_tracker():
    # Top 10 S&P 500 Tickers
    watchlist = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "BRK-B", "LLY", "AVGO", "TSLA"]
    
    report = f"📊 S&P 500 TOP 10 - INTELLIGENCE REPORT ({datetime.date.today()})\n"
    report += "--------------------------------------------------\n\n"
    
    for ticker in watchlist:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        
        if len(hist) < 2: continue
        
        price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change = ((price - prev_price) / prev_price) * 100
        
        # Get Professional News
        headline = get_pro_news(ticker)
        
        # Logic for "Watch" or "Buy"
        status = "Watching"
        if change <= -2.5: status = "🔥 OPPORTUNITY (Dip)"
        elif change >= 2.5: status = "🚀 MOMENTUM"

        indicator = "🟢" if change > 0 else "🔴"
        report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%) | {status}\n"
        report += f"📰 NEWS: {headline}\n"
        report += "--------------------------------------------------\n"

    # Send Email
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = f"S&P 10 Intel: {datetime.date.today()}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Pro report sent!")

if __name__ == "__main__":
    run_tracker()
