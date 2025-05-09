import os
import pandas as pd
import requests
from flask import Flask, render_template, request
import openai

app = Flask(__name__)

# API Keys
FINNHUB_API_KEY = "d0f3ps1r01qsv9ef5ta0d0f3ps1r01qsv9ef5tag"
MARKETAUX_API_TOKEN = "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp"
openai.api_key = "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"

# Finnhub: Get real-time stock price
def get_current_price(symbol):
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url, timeout=8)
        data = response.json()
        return float(data.get("c", 0.0))
    except Exception as e:
        print(f"[ERROR] Finnhub error for {symbol}: {e}")
        return 0.0

# OpenAI suggestion with fallback logic
def get_batch_ai_suggestions(stocks, news_summary):
    try:
        prompt = (
            "You are a financial advisor. Based on the portfolio and recent market news, "
            "give a decision (BUY / SELL / HOLD) for each stock. Use this format:\n"
            "TICKER - DECISION: REASON\n"
            f"News Summary:\n{news_summary}\n\n"
            f"Portfolio:\n" +
            "\n".join([f"{s['Ticker']}: Buy at {s['Buy Price']}, current {s['Current Price']}" for s in stocks])
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4
        )

        content = response["choices"][0]["message"]["content"]
        print("[DEBUG] OpenAI output:\n", content)
        lines = content.strip().split("\n")
        result = {}

        for line in lines:
            if "-" in line and ":" in line:
                parts = line.split("-", 1)
                ticker = parts[0].strip().upper()
                decision_part = parts[1].strip().split(":", 1)
                if len(decision_part) == 2:
                    decision = decision_part[0].strip().upper()
                    reason = decision_part[1].strip()
                    result[ticker] = (decision, reason)

        return result
    except Exception as e:
        print(f"[ERROR] OpenAI AI fallback: {e}")
        return {}

# Route to render index
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            df = pd.read_csv(file).head(3)
            tickers = ",".join(df["Ticker"].tolist())
            total_invested = current_value = 0.0

            try:
                news_url = f"https://api.marketaux.com/v1/news/all?symbols={tickers}&language=en&limit=10&api_token={MARKETAUX_API_TOKEN}"
                news_data = requests.get(news_url).json().get("data", [])
                news_summary = " ".join([a.get("description", "") for a in news_data])
            except Exception as e:
                print(f"[ERROR] MarketAux error: {e}")
                news_data = []
                news_summary = ""

            enriched = []
            for _, row in df.iterrows():
                ticker = row["Ticker"]
                buy_price = row["Buy Price"]
                quantity = row["Quantity"]

                current_price = get_current_price(ticker)
                total_value = current_price * quantity
                total_invested += buy_price * quantity
                current_value += total_value

                enriched.append({
                    "Ticker": ticker,
                    "Buy Price": buy_price,
                    "Quantity": quantity,
                    "Current Price": current_price,
                    "Total Value": total_value
                })

            ai_results = get_batch_ai_suggestions(enriched, news_summary)
            for stock in enriched:
                suggestion, reason = ai_results.get(stock["Ticker"], ("HOLD", "AI fallback: no response"))
                stock["AI Suggestion"] = suggestion
                stock["AI Reason"] = reason

            gain_loss = current_value - total_invested

            return render_template("dashboard.html",
                                   portfolio=enriched,
                                   invested=total_invested,
                                   current=current_value,
                                   gain=gain_loss,
                                   news=news_data)
    return render_template("index.html")

# Live news for refresh
@app.route("/api/news")
def live_news():
    try:
        symbols = "AAPL,MSFT,TSLA,BTC-USD,ETH-USD,SPY,QQQ"
        url = f"https://api.marketaux.com/v1/news/all?symbols={symbols}&language=en&limit=10&api_token={MARKETAUX_API_TOKEN}"
        news_data = requests.get(url).json().get("data", [])
        return {"news": news_data}
    except:
        return {"news": []}

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")
