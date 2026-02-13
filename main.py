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
            
            if hist.empty
