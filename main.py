import os
import yfinance as yf
import smtplib
from email.message import EmailMessage

# 1. Get secrets from GitHub (NOT hardcoded)
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")

def run_tracker():
    watchlist = ["AAPL", "NVDA", "GOOGL", "TSLA"]
    report = "Daily Market Summary:\n\n"
    
    for ticker in watchlist:
        stock = yf.Ticker(ticker)
        data = stock.history(period="2d")
        if len(data) < 2: continue
        
        price = data['Close'].iloc[-1]
        change = ((price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        report += f"{ticker}: ${price:.2f} ({change:.2f}%)\n"

    # 2. Send Email
    msg = EmailMessage()
    msg.set_content(report)
    msg['Subject'] = "Daily Stock Report"
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Email sent successfully!")

if __name__ == "__main__":
    run_tracker()
