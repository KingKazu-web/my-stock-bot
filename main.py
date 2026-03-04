import os
import yfinance as yf
import smtplib
import datetime
import io
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

print("--- Starting Market Intelligence Bot: Ultimate Edition ---")

# ── SECRETS ────────────────────────────────────────────────────────────────────
SENDER_EMAIL       = os.environ.get("MY_EMAIL")
EMAIL_APP_PASSWORD = os.environ.get("MY_PASSWORD")

# ── ASSETS ─────────────────────────────────────────────────────────────────────
ASSETS = {
    "STOCKS": {
        "AAPL": "Apple", "NVDA": "Nvidia", "TSLA": "Tesla",
        "AMZN": "Amazon", "META": "Meta Platforms"
    },
    "CRYPTO": {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana"
    },
    "MACRO": {
        "GC=F": "Gold", "CL=F": "Crude Oil",
        "^TNX": "10Y Treasury", "^GSPC": "S&P 500"
    }
}

# ── WATCHLIST (alerts only if moves > 3%) ─────────────────────────────────────
WATCHLIST = {
    "MSFT": "Microsoft", "GOOGL": "Alphabet", "AMD": "AMD",
    "JPM": "JPMorgan", "XOM": "Exxon"
}

SECTORS = {
    "XLK": "Tech", "XLF": "Financials", "XLE": "Energy",
    "XLV": "Healthcare", "XLI": "Industrials", "XLP": "Staples",
    "XLY": "Cons. Disc.", "XLU": "Utilities", "XLRE": "Real Estate",
    "XLB": "Materials", "XLC": "Comm. Svcs"
}

# ── HELPERS ────────────────────────────────────────────────────────────────────

def get_market_headline():
    try:
        news = yf.Ticker("^GSPC").news
        if news:
            content = news[0].get('content', news[0])
            return content.get('title', "Market showing standard volatility.")
        return "No major global catalysts reported."
    except:
        return "Global market context currently unavailable."

def get_pro_news_data(ticker, name):
    try:
        news = yf.Ticker(ticker).news
        if news:
            content = news[0].get('content', news[0])
            title = content.get('title', f'Latest {name} news')
            link = (
                content.get('canonicalUrl', {}).get('url') or
                content.get('clickThroughUrl', {}).get('url') or
                f"https://finance.yahoo.com/quote/{ticker}/news"
            )
            return title, link
    except:
        pass
    return f"View latest {name} news on Yahoo.", f"https://finance.yahoo.com/quote/{ticker}/news"

def calculate_rsi(prices, periods=14):
    if len(prices) < periods: return "N/A"
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains[-periods:]) / periods
    avg_loss = sum(losses[-periods:]) / periods
    if avg_loss == 0: return 100
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 1)

def get_momentum_meter(prices):
    if not prices or len(prices) < 2: return "[  ?  ]"
    low, high, current = min(prices), max(prices), prices[-1]
    if high == low: return "[▬▬●▬▬]"
    pos = int(((current - low) / (high - low)) * 5)
    meter = ["▬"] * 6
    meter[min(pos, 5)] = "●"
    return f"[{''.join(meter)}]"

def get_52w_badge(current, low_52, high_52):
    if low_52 is None or high_52 is None: return ""
    if ((high_52 - current) / high_52) * 100 <= 5:
        return '<span style="background:#27ae60;color:white;padding:1px 5px;border-radius:4px;font-size:0.75em;">🏆 52W HIGH</span>'
    if ((current - low_52) / low_52) * 100 <= 5:
        return '<span style="background:#e74c3c;color:white;padding:1px 5px;border-radius:4px;font-size:0.75em;">⚠️ 52W LOW</span>'
    return ""

def get_vix_label(vix_val):
    if vix_val is None: return "❓ Unknown", "#888"
    if vix_val < 15:   return f"😎 Calm ({vix_val:.1f})", "#27ae60"
    if vix_val < 20:   return f"😐 Neutral ({vix_val:.1f})", "#f39c12"
    if vix_val < 30:   return f"😰 Fearful ({vix_val:.1f})", "#e67e22"
    return                    f"😱 Extreme Fear ({vix_val:.1f})", "#e74c3c"

def make_sparkline(prices, color):
    """Returns PNG bytes — attached via CID so Gmail renders it properly."""
    try:
        fig, ax = plt.subplots(figsize=(4, 0.7))
        ax.plot(prices, color=color, linewidth=1.5)
        ax.fill_between(range(len(prices)), prices, min(prices), alpha=0.15, color=color)
        ax.axis('off')
        fig.patch.set_alpha(0)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=80, transparent=True)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except:
        return None

def get_earnings_warning(ticker):
    try:
        cal = yf.Ticker(ticker).calendar
        if cal is None: return ""
        dates = cal.get('Earnings Date', []) if isinstance(cal, dict) else []
        if not dates: return ""
        next_date = dates[0] if hasattr(dates[0], 'date') else None
        if next_date is None: return ""
        days_away = (next_date.date() - datetime.date.today()).days
        if 0 <= days_away <= 7:
            return f'<span style="background:#8e44ad;color:white;padding:1px 5px;border-radius:4px;font-size:0.75em;">📅 EARNINGS in {days_away}d</span>'
    except:
        pass
    return ""

# ── SECTOR HEATMAP ─────────────────────────────────────────────────────────────

def build_sector_heatmap():
    cells = ""
    for ticker, label in SECTORS.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) < 2: continue
            chg = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            intensity = min(abs(chg) / 2, 1.0)
            if chg > 0:
                r = int(39  + (0   - 39)  * intensity)
                g = int(174 + (255 - 174) * intensity)
                b = int(96  + (0   - 96)  * intensity)
            else:
                r = int(231 + (255 - 231) * intensity)
                g = int(76  + (0   - 76)  * intensity)
                b = int(60  + (0   - 60)  * intensity)
            bg        = f"rgb({r},{g},{b})"
            txt_color = "white" if intensity > 0.3 else "#333"
            cells += f"""
            <div style="background:{bg};color:{txt_color};padding:8px 4px;border-radius:6px;text-align:center;font-size:0.78em;">
                <b>{label}</b><br>{chg:+.1f}%
            </div>"""
        except:
            pass
    return f"""
    <div style="margin-top:20px;">
        <h3 style="border-bottom:2px solid #eee;color:#34495e;">📊 SECTOR HEATMAP</h3>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;">{cells}</div>
    </div>"""

# ── WATCHLIST ALERTS ───────────────────────────────────────────────────────────

def build_watchlist_alerts():
    alerts = ""
    for ticker, name in WATCHLIST.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) < 2: continue
            chg = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            if abs(chg) >= 3:
                color = "#27ae60" if chg > 0 else "#e74c3c"
                arrow = "▲" if chg > 0 else "▼"
                alerts += f'<div style="padding:6px 10px;margin:4px 0;border-left:4px solid {color};background:#fafafa;"><b>{name} ({ticker})</b> <span style="color:{color};">{arrow} {chg:+.2f}%</span></div>'
        except:
            pass
    if not alerts:
        return ""
    return f"""
    <div style="margin-top:20px;">
        <h3 style="border-bottom:2px solid #eee;color:#34495e;">👀 WATCHLIST ALERTS (≥3% move)</h3>
        {alerts}
    </div>"""

# ── TOP MOVERS PODIUM ──────────────────────────────────────────────────────────

def build_podium(all_data):
    if not all_data: return ""
    sorted_data = sorted(all_data, key=lambda x: x['change'], reverse=True)
    winner = sorted_data[0]
    loser  = sorted_data[-1]
    return f"""
    <div style="display:flex;gap:12px;margin-bottom:20px;">
        <div style="flex:1;background:#eafaf1;border:2px solid #27ae60;border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:1.5em;">🥇</div>
            <b>{winner['name']}</b><br>
            <span style="color:#27ae60;font-size:1.1em;font-weight:bold;">{winner['change']:+.2f}%</span>
        </div>
        <div style="flex:1;background:#fdf2f2;border:2px solid #e74c3c;border-radius:10px;padding:12px;text-align:center;">
            <div style="font-size:1.5em;">📉</div>
            <b>{loser['name']}</b><br>
            <span style="color:#e74c3c;font-size:1.1em;font-weight:bold;">{loser['change']:+.2f}%</span>
        </div>
    </div>"""

# ── MAIN ───────────────────────────────────────────────────────────────────────

def run_tracker():
    today_str       = datetime.date.today().strftime("%b %d, %Y")
    day_of_week     = datetime.date.today().strftime("%A")
    market_headline = get_market_headline()

    # VIX Fear & Greed
    vix_val = None
    try:
        vix_hist = yf.Ticker("^VIX").history(period="2d")
        if not vix_hist.empty:
            vix_val = vix_hist['Close'].iloc[-1]
    except: pass
    vix_label, vix_color = get_vix_label(vix_val)

    report_body  = ""
    all_data     = []
    spark_images = {}   # cid_key -> PNG bytes
    advancers = decliners = 0
    vol_detected = False

    for category, items in ASSETS.items():
        report_body += f"<h3 style='border-bottom:2px solid #eee;padding-top:15px;color:#34495e;'>{category}</h3>"

        for ticker, name in items.items():
            print(f"🔍 Analyzing {name}...")
            try:
                stock = yf.Ticker(ticker)
                hist  = stock.history(period="1y")
                if len(hist) < 2: continue

                prices  = hist['Close'].tolist()
                price   = prices[-1]
                change  = ((prices[-1] - prices[-2]) / prices[-2]) * 100
                low_52  = min(prices[-252:]) if len(prices) >= 252 else min(prices)
                high_52 = max(prices[-252:]) if len(prices) >= 252 else max(prices)

                all_data.append({'name': name, 'ticker': ticker, 'change': change})
                if change > 0: advancers += 1
                else:          decliners += 1

                curr_vol   = hist['Volume'].iloc[-1]
                avg_vol    = hist['Volume'].iloc[-31:-1].mean()
                conviction = "⚡" if curr_vol > (avg_vol * 1.5) else ""
                if conviction: vol_detected = True

                rsi_val  = calculate_rsi(prices)
                momentum = get_momentum_meter(prices[-7:])
                rsi_s    = "🔥" if isinstance(rsi_val, float) and rsi_val > 70 else \
                           "❄️" if isinstance(rsi_val, float) and rsi_val < 30 else ""

                color    = "#27ae60" if change > 0 else "#e74c3c"
                badge_52 = get_52w_badge(price, low_52, high_52)
                earn_tag = get_earnings_warning(ticker)

                # Sparkline: use CID attachment so Gmail renders it
                cid_key   = re.sub(r'[^a-zA-Z0-9]', '_', ticker)
                spark_png = make_sparkline(prices[-30:], color)
                if spark_png:
                    spark_images[cid_key] = spark_png
                    spark_html = f'<img src="cid:{cid_key}" style="width:100%;max-width:400px;height:50px;display:block;margin:6px 0;">'
                else:
                    spark_html = ""

                headline, link = get_pro_news_data(ticker, name)

                report_body += f"""
                <div style="margin-bottom:14px;padding:12px;border-left:4px solid {color};background:#fafafa;border-radius:0 6px 6px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span><b>{ticker}</b> {conviction} {badge_52} {earn_tag}</span>
                        <span style="font-family:monospace;font-size:0.85em;">{momentum}</span>
                    </div>
                    <b style="color:{color};font-size:1.05em;">${price:.2f} ({change:+.2f}%)</b>
                    &nbsp;|&nbsp; RSI: {rsi_val} {rsi_s}
                    &nbsp;|&nbsp; <span style="font-size:0.8em;color:#666;">52W: ${low_52:.0f} – ${high_52:.0f}</span>
                    {spark_html}
                    <small>📰 <a href="{link}" style="color:#0984e3;text-decoration:none;">{headline[:80]}...</a></small>
                </div>"""

            except Exception as e:
                print(f"  ⚠️  Error on {ticker}: {e}")

    # Friday digest note
    weekly_note = ""
    if day_of_week == "Friday":
        weekly_note = '<div style="background:#fff3cd;border:1px solid #ffc107;padding:10px;border-radius:8px;margin-bottom:16px;">📆 <b>It\'s Friday!</b> Review your week and consider rebalancing over the weekend.</div>'

    podium_html    = build_podium(all_data)
    sector_html    = build_sector_heatmap()
    watchlist_html = build_watchlist_alerts()

    legend_html = """
    <div style="background:#f1f2f6;padding:15px;border-radius:8px;font-size:0.82em;color:#2f3542;margin-top:25px;line-height:1.8;">
        <b>📌 LEGEND</b><br>
        • <b>Momentum:</b> <code>[●▬▬▬▬]</code> 7-day low → <code>[▬▬▬▬●]</code> 7-day high<br>
        • <b>RSI:</b> 🔥 Overbought (&gt;70) | ❄️ Oversold (&lt;30)<br>
        • <b>Conviction:</b> ⚡ Volume &gt;1.5× average<br>
        • <b>52W HIGH/LOW:</b> Within 5% of yearly extreme<br>
        • <b>Earnings:</b> 📅 Earnings within 7 days<br>
        • <b>Watchlist:</b> Alerts fire only on ≥3% moves
    </div>"""

    summary_html = f"""
    <div style="background:#2d3436;color:white;padding:25px;border-radius:12px;margin-bottom:20px;">
        <h2 style="margin:0;color:#00cec9;">🏛️ Market Pulse — {today_str}</h2>
        <p style="margin:12px 0;border-left:3px solid #00cec9;padding-left:10px;font-style:italic;font-size:0.9em;">"{market_headline}"</p>
        <div style="display:flex;gap:20px;font-size:0.9em;border-top:1px solid #444;padding-top:10px;flex-wrap:wrap;">
            <span>📈 Advancers: <b>{advancers}</b></span>
            <span>📉 Decliners: <b>{decliners}</b></span>
            <span style="color:{vix_color};">🧠 Sentiment: <b>{vix_label}</b></span>
        </div>
    </div>
    {weekly_note}
    {podium_html}
    """

    full_html = f"""
    <html><body style="font-family:sans-serif;max-width:640px;margin:auto;color:#2d3436;">
    {summary_html}
    {report_body}
    {sector_html}
    {watchlist_html}
    {legend_html}
    </body></html>"""

    # ── BUILD EMAIL WITH CID IMAGE ATTACHMENTS ─────────────────────────────────
    msg = MIMEMultipart('related')
    subject_emoji = "⚡ " if vol_detected else ""
    subject_day   = "📆 WEEKLY WRAP | " if day_of_week == "Friday" else ""
    msg['Subject'] = f"{subject_emoji}{subject_day}Market Intel: {today_str} ({advancers}↑ {decliners}↓) | {vix_label}"
    msg['From']    = SENDER_EMAIL
    msg['To']      = SENDER_EMAIL

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(full_html, 'html'))

    # Attach each sparkline PNG with its CID so the HTML can reference it
    for cid_key, png_bytes in spark_images.items():
        img = MIMEImage(png_bytes, 'png')
        img.add_header('Content-ID', f'<{cid_key}>')
        img.add_header('Content-Disposition', 'inline')
        msg.attach(img)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("✅ Dispatch Successful.")

if __name__ == "__main__":
    run_tracker()
