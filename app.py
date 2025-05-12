import os
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import openai

app = Flask(__name__)
app.secret_key = "your-secret-key"

FINNHUB_API_KEY = "d0f3ps1r01qsv9ef5ta0d0f3ps1r01qsv9ef5tag"
MARKETAUX_API_TOKEN = "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp"
openai.api_key = "sk-proj-xxx"

stored_portfolio = []
news_data = []

def get_current_price(symbol):
    try:
        res = requests.get(f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}", timeout=5)
        return float(res.json().get("c", 0))
    except:
        return 0

@app.route("/", methods=["GET", "POST"])
def index():
    global stored_portfolio, news_data
    if request.method == "POST":
        file = request.files["file"]
        df = pd.read_csv(file)
        enriched = []
        total_invested = current_value = 0

        for _, row in df.iterrows():
            symbol = row["Ticker"]
            qty = row["Quantity"]
            buy = row["Buy Price"]
            current = get_current_price(symbol)
            value = current * qty
            total_invested += buy * qty
            current_value += value
            enriched.append({
                "Ticker": symbol,
                "Quantity": qty,
                "Buy Price": buy,
                "Current Price": current,
                "Total Value": value
            })

        stored_portfolio = enriched
        session["uploaded"] = True

        try:
            ticker_list = ",".join([s["Ticker"] for s in enriched])
            url = f"https://api.marketaux.com/v1/news/all?symbols={ticker_list}&language=en&limit=10&api_token={MARKETAUX_API_TOKEN}"
            news_data = requests.get(url).json().get("data", [])
        except:
            news_data = []

        return redirect(url_for("dashboard"))

    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("uploaded"):
        return redirect(url_for("index"))

    total_invested = sum(s["Buy Price"] * s["Quantity"] for s in stored_portfolio)
    current_value = sum(s["Total Value"] for s in stored_portfolio)
    gain = current_value - total_invested

    return render_template("dashboard.html",
                           portfolio=stored_portfolio,
                           invested=round(total_invested, 2),
                           current=round(current_value, 2),
                           gain=round(gain, 2),
                           news=news_data)

@app.route("/api/news")
def live_news():
    try:
        symbols = "AAPL,MSFT,GOOGL,TSLA,BTC-USD,ETH-USD,SPY,QQQ"
        url = f"https://api.marketaux.com/v1/news/all?symbols={symbols}&language=en&limit=10&api_token={MARKETAUX_API_TOKEN}"
        return jsonify(news=requests.get(url).json().get("data", []))
    except:
        return jsonify(news=[])

@app.route("/api/ai")
def ai_suggestions():
    symbols = request.args.get("symbols", "")
    if not symbols:
        return {}
    tickers = symbols.split(",")
    try:
        prompt = "Act as a financial advisor. Give a BUY/SELL/HOLD decision with reason for each of the following stocks:\n" + "\n".join(tickers)
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        output = res["choices"][0]["message"]["content"]
        result = {}
        for line in output.strip().splitlines():
            if "-" in line and ":" in line:
                symbol, rest = line.split("-", 1)
                act, reason = rest.split(":", 1)
                result[symbol.strip()] = {
                    "suggestion": act.strip(),
                    "reason": reason.strip()
                }
        return jsonify(result)
    except:
        return jsonify({})
