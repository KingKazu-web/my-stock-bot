import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime

print("--- Starting Script ---")

# 1. Check Secrets (Safely)
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

if not SENDER_EMAIL or not EMAIL_APP_PASSWORD:
    print("❌ ERROR: Email or Password secrets are missing!")
if not NEWS_API_KEY:
    print("⚠️ WARNING: News API Key is missing!")

COMPANY_NAMES = {"AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla"} # Shorter list for testing

def get_pro_news(ticker):
    query = COMPANY_NAMES.get(ticker, ticker)
    url = f'https://newsapi.org/v2/everything?qInTitle={query}&language=en&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles'):
            return data['articles'][0]['title']
    except Exception as e:
        return f"News Error: {e}"
    return "No news found."

def run_tracker():
    report = "📊 TEST REPORT\n\n"
    for ticker in COMPANY_NAMES.keys():
        print(f"🔍 Fetching {ticker}...")
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close'].iloc[-1]
        report += f"{ticker}: ${price:.2f}\n"
        report += f"📰 {get_pro_news(ticker)}\n\n"

    print("✉️ Attempting to send email...")
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = "Stock Test"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            print(f"Connecting to Gmail as {SENDER_EMAIL}...")
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            print("Login successful!")
            smtp.send_message(msg)
            print("✅ EMAIL SENT SUCCESSFULLY!")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")

if __name__ == "__main__":
    run_tracker()
    print("--- Script Finished ---")
