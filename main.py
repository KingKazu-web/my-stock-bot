import os
import yfinance as yf
import smtplib
import requests
from email.message import EmailMessage
import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

print("--- Starting Pro Intelligence Bot: Executive Edition ---")

# 1. SETUP SECRETS
SENDER_EMAIL = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

# 2. OPTIMIZED ASSET LIST
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
    trusted_domains = "reuters.com,cnbc.com,bloomberg.com,forbes.com,fortune.com,marketwatch.com"
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
    return "No direct financial news found.", "#"

def run_tracker():
    today_str = datetime.date.today().strftime("%B %d, %Y")
    all_changes = [] 
    report_body = ""

    # 3. ANALYZE ASSETS & BUILD BODY
    for category, items in ASSETS.items():
        report_body += f"<h2 style='background: #dfe6e9; padding: 10px; border-radius: 5px; color: #2d3436; margin-top: 30px;'>{category}</h2>"
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
                <div style="border-left: 6px solid {color}; padding: 10px 15px; margin-bottom: 15px; background: #fafafa;">
                    <b style="font-size: 1.1em;">{ticker}: ${price:.2f} 
                    (<span style="color: {color};">{change:+.2f}%</span>)</b><br>
                    <span style="font-size: 0.9em; color: #636e72;">🎭 Mood: <b>{sentiment}</b></span><br>
                    📰 <a href="{link}" style="color: #0984e3; text-decoration: none; font-weight: 500;">{headline}</a>
                </div>
                """
            except Exception as e:
                print(f"Error {ticker}: {e}")

    # 4. BUILD THE EXECUTIVE SUMMARY BLOCK
    summary_html = ""
    if all_changes:
        best = max(all_changes, key=lambda x: x[1])
        worst = min(all_changes, key=lambda x: x[1])
        avg_move = sum([x[1] for x in all_changes]) / len(all_changes)
        
        if avg_move > 0.4: vibe = "📈 Bullish Momentum"
        elif avg_move < -0.4: vibe = "📉 Bearish Pressure"
        else: vibe = "⚖️ Neutral / Sideways"

        summary_html = f"""
        <div style="background: #2d3436; color: #ffffff; padding: 25px; border-radius: 12px; margin-bottom: 30px; font-family: 'Segoe UI', Arial, sans-serif;">
            <h3 style="margin-top: 0; color: #00cec9; letter-spacing: 1px;">📋 EXECUTIVE SUMMARY</h3>
            <p style="font-size: 1.2em; margin-bottom: 10px;"><b>Market Vibe:</b> {vibe}</p>
            <p style="color: #b2bec3;">The tracked portfolio moved an average of <b>{avg_move:+.2f}%</b> today.</p>
            <div style="display: flex; border-top: 1px solid #636e72; pt: 15px; margin-top: 15px;">
                <div style="flex: 1;">
                    <span style="color: #55efc4; font-size: 0.9em;">🚀 TOP BULL</span><br>
                    <b>{best[0]}</b> ({best[1]:+.2f}%)
                </div>
                <div style="flex: 1; border-left: 1px solid #636e72; padding-left: 20px;">
                    <span style="color: #ff7675; font-size: 0.9em;">🐻 TOP BEAR</span><br>
                    <b>{worst[0]}</b> ({worst[1]:+.2f}%)
                </div>
            </div>
        </div>
        """

    # 5. CONSTRUCT FINAL HTML
    full_html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px;">
        <h1 style="color: #2d3436; margin-bottom: 25px;">🏛️ Market Intelligence Report</h1>
        {summary_html}
        {report_body}
        <p style="font-size: 0.8em; color: #b2bec3; margin-top: 40px; text-align: center;">
            Generated by Gemini 3 Flash Bot • {today_str}
        </p>
    </body>
    </html>
    """

    # 6. EMAIL SENDING (One-Subject Safety)
    msg = EmailMessage()
    top_move = max([abs(x[1]) for x in all_changes]) if all_changes else 0
    final_subject = f"Market Intel: {today_str}"
    if top_move > 4.0:
        final_subject = f"🚨 VOLATILITY ALERT: {today_str}"
        
    msg['Subject'] = final_subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = SENDER_EMAIL
    msg.add_alternative(full_html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Executive Report Sent: {final_subject}")
    except Exception as e:
        print(f"❌ Dispatch Failed: {e}")

if __name__ == "__main__":
    run_tracker()
