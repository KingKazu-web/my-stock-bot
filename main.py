import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime

print("--- Starting Stock Bot ---")

# 1. Grab Secrets from the Robot
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# Safety Check: Let us know in the logs if something is missing
if not SENDER_EMAIL: print("❌ Missing Secret: MY_EMAIL")
if not EMAIL_APP_PASSWORD: print("❌ Missing Secret: MY_PASSWORD")
if not NEWS_API_KEY: print("❌ Missing Secret: NEWS_API_KEY")

COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", 
    "AMZN": "Amazon", "META": "Meta Platforms", "GOOGL": "Google",
    "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", 
    "AVGO": "Broadcom", "TSLA": "Tesla"
}

def get_pro_news(ticker):
    """Fetches news specifically using the NewsAPI Key"""
    if not NEWS_API_KEY:
        return "News key not configured."
    
    query = COMPANY_NAMES.get(ticker, ticker)
    url = f'https://newsapi.org/v2/everything?qInTitle={query}&language=en&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}'
    
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            return data['articles'][0]['title']
    except Exception as e:
        return f"News Error: {e}"
    return "No recent headlines found."

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    report = f"📊 S&P 500 TOP 10 REPORT - {today_str}\n"
    report += "--------------------------------------------------\n\n"
    
    for ticker in COMPANY_NAMES.keys():
        print(f"🔍 Analyzing {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if len(hist) < 2:
                report += f"⚪ {ticker}: Data unavailable.\n\n"
                continue
                
            price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2]
            change = ((price - prev_price) / prev_price) * 100
            
            headline = get_pro_news(ticker)
            indicator = "🟢" if change > 0 else "🔴"
            
            report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
            report += f"📰 {headline}\n\n"
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

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
