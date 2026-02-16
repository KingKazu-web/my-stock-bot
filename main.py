import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot: Clean Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. REFINED ASSET LIST (Optimized for better search results)
ASSETS = {
    "STOCKS": {
        "AAPL": "Apple Inc", "MSFT": "Microsoft", "NVDA": "Nvidia Stock", 
        "AMZN": "Amazon.com Inc", "META": "Meta Platforms", "GOOGL": "Alphabet Google",
        "TSLA": "Tesla Motors", "AVGO": "Broadcom Inc", "LLY": "Eli Lilly", "BRK-B": "Berkshire Hathaway"
    },
    "CRYPTO": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "XRP-USD": "XRP Ripple"
    },
    "MACRO": {
        "GC=F": "Gold Price", "CL=F": "Crude Oil Market", "^TNX": "10-Year Treasury",
        "XLF": "Financial Sector ETF", "XLI": "Industrial Sector ETF", "XLU": "Utilities Sector ETF"
    }
}

analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    if not text or "found" in text: return "⚪ Neutral"
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05: return "🟢 Positive"
    if score <= -0.05: return "🔴 Negative"
    return "⚪ Neutral"

def get_pro_news_data(ticker, name, category):
    """Fetches high-quality news while filtering out 'junk' domains and Yahoo redirects"""
    if not NEWS_API_KEY: return "Key missing.", "#"
    
    # Create a targeted search query based on category
    if category == "CRYPTO":
        query = f'"{name}" AND (crypto OR blockchain OR price)'
    else:
        query = f'"{name}" AND (stock OR market OR earnings)'

    # Specifically exclude domains that cause issues or provide 'deals' rather than news
    exclude = "slickdeals.net,amazon.com,ebay.com,walmart.com,deals.com,yahoo.com/consent"
    
    url = (f'https://newsapi.org/v2/everything?'
           f'q={query}&'
           f'excludeDomains={exclude}&'
           f'language=en&'
           f'sortBy=relevancy&'
           f'pageSize=5&' 
           f'apiKey={NEWS_API_KEY}')
    
    try:
        response = requests.get(url)
        data = response.json()
        if data.get('articles') and len(data['articles']) > 0:
            # Prefer articles that aren't from the main yahoo domain to avoid redirect walls
            for article in data['articles']:
                if "finance.yahoo.com" not in article['url']:
                    return article['title'], article['url']
            
            # Fallback to the first result
            return data['articles'][0]['title'], data['articles'][0]['url']
    except Exception as e:
        print(f"News Error for {ticker}: {e}")
        
    return "No relevant financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    all_changes = [] 
    
    # Start building the HTML Email
    html_content = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6;">
        <h1 style="color: #2c3e50; border-bottom: 2px solid #2c3e50;">🏛️ Market Intelligence: {today_str}</h1>
    """
    
    report_body = ""

    for category, items in ASSETS.items():
        report_body += f"<h2 style='background: #ecf0f1; padding: 5px 10px; border-radius: 3px;'>{category}</h2>"
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
                
                # Visual styling: Green for up, Red for down
                border_color = "#27ae60" if change > 0 else "#e74c3c"
                report_body += f"""
                <div style="margin-bottom: 20px; border-left: 5px solid {border_color}; padding: 0 15px;">
                    <span style="font-size: 1.1em; font-weight: bold;">{ticker}: ${price:.2f} 
                    (<span style="color: {border_color};">{change:+.2f}%</span>)</span><br>
                    <span style="font-size: 0.9em;">🎭 Mood: <b>{sentiment}</b></span><br>
                    📰 <a href="{link}" style="color: #3498db; text-decoration: none;">{headline}</a>
                </div>
                """
            except Exception as e:
                print(f"Error {ticker}: {e}")

    # Build the Top Summary
    summary_html = ""
    if all_changes:
        best = max(all_changes, key=lambda x: x[1])
        worst = min(all_changes, key=lambda x: x[1])
        summary_html = f"""
        <div style="background: #fdfefe; border: 1px solid #dcdde1; padding: 15px; border-radius: 8px; margin-bottom: 25px;">
            <b style="font-size: 1.2em;">📊 PERFORMANCE SUMMARY</b><br>
            <span style="color: #27ae60;">🔥 Top Performer:</span> {best[0]} ({best[1]:.2f}%)<br>
            <span style="color: #e74c3c;">🧊 Laggard:</span> {worst[0]} ({worst[1]:.2f}%)
        </div>
        """

    html_content += summary_html + report_body + "</body></html>"

    # --- EMAIL SENDING ---
    msg = EmailMessage()
    top_move = max([abs(x[1]) for x in all_changes]) if all_changes else 0
    msg['Subject'] = f"Market Intel: {today_str}"
    if top_move > 4.0:
        msg['Subject'] = f"🚨 VOLATILITY ALERT: {today_str}"
        
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.set_content("Use an HTML email client to view the full report.")
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print("✅ Success! Clean HTML Newsletter delivered.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    run_tracker()
