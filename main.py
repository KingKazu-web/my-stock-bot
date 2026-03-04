import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot: Final Robust Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. DEFINED ASSETS
ASSETS = {
    "STOCKS": {
        "AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla", 
        "AMZN": "Amazon stock", "META": "Meta Platforms", "GOOGL": "Alphabet Google",
        "MSFT": "Microsoft", "AVGO": "Broadcom", "LLY": "Eli Lilly", "BRK-B": "Berkshire Hathaway"
    },
    "CRYPTO": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "XRP-USD": "XRP Ripple"
    },
    "MACRO": {
        "GC=F": "Gold Price", "CL=F": "Crude Oil", "^TNX": "10-Year Treasury",
        "XLF": "Financial Sector", "XLI": "Industrial Sector", "XLU": "Utilities Sector"
    }
}

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if not text or "No" in text: return "⚪ Neutral"
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "🟢 Positive"
    if score <= -0.05: return "🔴 Negative"
    return "⚪ Neutral"

def get_pro_news_data(ticker, name, category):
    """The 'Fortress' News Fetcher: Only high-tier, direct-link sources."""
    if not NEWS_API_KEY: return "Key missing.", "#"
    
    # Restrict to trusted domains to avoid Yahoo Consent and Junk deals
    trusted_domains = "reuters.com,cnbc.com,bloomberg.com,forbes.com,fortune.com,marketwatch.com"
    
    # Advanced Search Query
    query = f'"{name}"'
    if category == "STOCKS": query += " AND (stock OR earnings OR analyst)"
    elif category == "CRYPTO": query += " AND (crypto OR price)"

    url = (f'https://newsapi.org/v2/everything?'
           f'q={query}&'
           f'domains={trusted_domains}&'
           f'language=en&'
           f'sortBy=relevancy&'
           f'pageSize=1&' 
           f'apiKey={NEWS_API_KEY}')
    
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            article = data['articles'][0]
            return article['title'], article['url']
    except:
        pass
    return "No recent financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    all_changes = [] 
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h1 style="color: #0984e3; border-bottom: 2px solid #0984e3;">🏛️ Executive Market Intel: {today_str}</h1>
    """
    
    report_body = ""
    for category, items in ASSETS.items():
        report_body += f"<h2 style='background: #f1f2f6; padding: 5px; margin-top:20px;'>{category}</h2>"
        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="5d")
                if hist.empty or len(hist) < 2: continue
                
                price = hist['Close'].iloc[-1]
                change = ((price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                all_changes.append((name, change))

                headline, link = get_pro_news_data(ticker, name, category)
                sentiment = get_sentiment(headline)
                
                color = "#27ae60" if change > 0 else "#e74c3c"
                report_body += f"""
                <div style="border-left: 5px solid {color}; padding-left: 10px; margin-bottom: 10px;">
                    <b>{ticker}: ${price:.2f} (<span style="color: {color};">{change:+.2f}%</span>)</b><br>
                    🎭 Mood: {sentiment} | 📰 <a href="{link}">{headline}</a>
                </div>
                """
            except Exception as e:
                print(f"Error {ticker}: {e}")

    html_content += report_body + "</body></html>"

    # --- EMAIL SENDING (One-Subject Fix) ---
    msg = EmailMessage()
    top_move = max([abs(x[1]) for x in all_changes]) if all_changes else 0
    final_subject = f"Market Intel: {today_str}"
    if top_move > 4.0:
        final_subject = f"🚨 VOLATILITY ALERT: {today_str}"
        
    msg['Subject'] = final_subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Success! Report sent: {final_subject}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    run_tracker()
