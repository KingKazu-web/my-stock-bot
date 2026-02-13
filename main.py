import os
import yfinance as yf
import smtplib
from email.message import EmailMessage

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
        
        # --- THE DETECTIVE WORK ---
        news = stock.news
        headline = "No recent news found."
        
        if news and len(news) > 0:
            first_story = news[0]
            # Try to find the title under different common names
            headline = first_story.get('title') or first_story.get('text') or "Headline found but could not be read."
        
        # Add to report
        indicator = "📈" if change > 0 else "📉"
        report += f"{indicator} {ticker}: ${price:.2f} ({change:.2f}%)\n"
        report += f"📰 Latest: {headline}\n"
        report += "-------------------------------------\n"

    # Send the Email
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = f"Market Intel: {datetime.date.today()}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Report sent!")

if __name__ == "__main__":
    # We need to import datetime inside the function or at top
    import datetime 
    run_tracker()
