import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime

print("--- Starting Stock Bot ---")

# 1. Grab Secrets
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", 
    "AMZN": "Amazon", "META": "Meta Platforms", "GOOGL": "Google",
    "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", 
    "AVGO": "Broadcom", "TSLA": "Tesla"
}

def get_pro_news(ticker):
    if not NEWS_API_KEY: return "News key missing."
    query = COMPANY_NAMES.get(ticker, ticker)
    url = f'https://newsapi.org/v2/everything?qInTitle={query}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles'):
            return data['articles'][0]['title']
    except:
        pass
    return "No recent headlines found."

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    report = f"📊 S&P 500 TOP 10 REPORT - {today_str}\n"
    report += "--------------------------------------------------\n\n"
    
    for ticker in COMPANY_NAMES.keys():
        print(f"🔍 Analyzing {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            # CHANGE: We fetch 5 days of data instead of 2 to ensure we have enough points
            hist = stock.history(period="5d")
            
            if hist.empty or len(hist) < 2:
                # If history fails, try to get just the current regular price
                price = stock.fast_info['last_price']
                change = 0.0
                report += f"⚪ {ticker}: ${price:.2f} (No change data)\n"
            else:
                price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((price - prev_price) / prev_price) * 100
                indicator = "🟢" if change > 0 else "🔴"
                report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
            
            headline = get_pro_news(ticker)
            report += f"📰 {headline}\n\n"
            
        except Exception as e:
            print(f"Error on {ticker}: {e}")
            report += f"❌ {ticker}: Data error.\n\n"

    # --- EMAIL SECTION ---
    print("✉️ Sending email...")
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = f"Daily Stock Intel: {today_str}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ SUCCESS: Email sent!")
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")

if __name__ == "__main__":
    run_tracker()
    print("--- Script Finished ---")
