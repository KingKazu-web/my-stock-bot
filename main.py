import os
import yfinance as yf
import smtplib
from email.message import EmailMessage

# 1. Setup secrets
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")

def run_tracker():
    watchlist = ["AAPL", "NVDA", "GOOGL", "TSLA", "PLTR"]
    report = "📊 DAILY MARKET INTELLIGENCE REPORT\n"
    report += "-------------------------------------\n\n"
    
    for ticker in watchlist:
        stock = yf.Ticker(ticker)
        
        # Get Price Data
        hist = stock.history(period="2d")
        if len(hist) < 2: continue
        
        price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change = ((price - prev_price) / prev_price) * 100
        
        # Get Latest News Headline
        news = stock.news
        headline = "No recent news found."
        if news:
            # Grab the title of the very first news item
            headline = news[0].get('title', 'Headline unavailable')

        # Add to report
        indicator = "📈" if change > 0 else "📉"
        report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
        report += f"📰 Latest: {headline}\n"
        report += "-------------------------------------\n"

    # 2. Send the Email
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = f"Market Update: {len(watchlist)} Stocks Tracked"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Report sent successfully with news!")

if __name__ == "__main__":
    run_tracker()
