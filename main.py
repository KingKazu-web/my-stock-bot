import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime

# --- SETTINGS & SECRETS ---
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# This helps NewsAPI find better results by using names instead of just symbols
COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", 
    "AMZN": "Amazon", "META": "Meta Platforms", "GOOGL": "Google",
    "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", 
    "AVGO": "Broadcom", "TSLA": "Tesla"
}

def get_pro_news(ticker):
    """Fetches the latest headline using NewsAPI with improved search"""
    query = COMPANY_NAMES.get(ticker, ticker)
    
    # We look for the company name in the title of the news
    url = f'https://newsapi.org/v2/everything?qInTitle={query}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # If the API returns an error, we want to know what it is
        if data.get('status') == 'error':
            return f"API Error: {data.get('message')}"
            
        if data.get('articles') and len(data['articles']) > 0:
            return data['articles'][0]['title']
        else:
            # Fallback: Search everything (not just titles) if title search fails
            fallback_url = f'https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
            fb_res = requests.get(fallback_url).json()
            if fb_res.get('articles'):
                return fb_res['articles'][0]['title']
                
    except Exception as e:
        return f"System Error: {str(e)}"
    
    return "No recent news found."

def run_tracker():
    # The Top 10 S&P 500 Tickers
    watchlist = list(COMPANY_NAMES.keys())
    
    today_str = datetime.date.today().strftime("%B %d, %Y")
    report = f"📊 S&P 500 TOP 10 - INTELLIGENCE REPORT ({today_str})\n"
    report += "--------------------------------------------------\n\n"
    
    for ticker in watchlist:
        print(f"Processing {ticker}...") # This helps us see progress in GitHub Logs
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        
        if len(hist) < 2:
            report += f"⚪ {ticker}: Data temporarily unavailable.\n"
            continue
        
        price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change = ((price - prev_price) / prev_price) * 100
        
        # Get News
        headline = get_pro_news(ticker)
        
        # Status Label
        status = "Watching"
        if change <= -2.0: status = "🔥 OPPORTUNITY (Dip)"
        elif change >= 2.0: status
