import os
import pandas as pd
import requests
from flask import Flask, render_template, request
import openai

app = Flask(__name__)

FINNHUB_API_KEY = "d0f3ps1r01qsv9ef5ta0d0f3ps1r01qsv9ef5tag"
MARKETAUX_API_TOKEN = "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp"
openai.api_key = "sk-proj-..."  # your real OpenAI key

def get_current_price(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        data = requests.get(url, timeout=8).json()
        return float(data.get("c", 0))
    except:
        return 0

def get_batch_ai_suggestions(stocks, news_summary):
    try:
        prompt = (
            "You are a smart stock advisor. Based on the portfolio and recent news, suggest action (BUY/SELL/HOLD) for each stock:\n"
            "News:\n" + news_summary[:1000] + "\n\nPortfolio:\n" +
            "\n".join([f"{s['Ticker']}: Buy at ${s['Buy Price']}, current ${s['Current Price']}" for s in stocks]) +
            "\n\nGive output in this format:\nTICKER - DECISION: REASON"
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700,
            temperature=0.5
        )

        lines = response.choices[0].message.content.strip().split("\n")
        suggestions = {}
        for line in lines:
            if "-" in line and ":" in line:
                parts = line.split("-", 1)
                ticker = parts[0].strip().upper()
                decision_part = parts[1].split(":", 1)
                if len(decision_part) == 2:
                    decision = decision_part[0].strip().upper()
                    reason = decision_part[1].strip()
                    suggestions[ticker] = (decision, reason)

        return suggestions
    except Exception as e:
        print("[ERROR] OpenAI fallback:", e)
        return {}


@app.route("/", methods=["GET", "POST"])
def dashboard():
    portfolio_data = []
    news = []
    invested = current = gain = 0
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            df = pd.read_csv(file)
            symbols = ",".join(df["Ticker"].tolist())

            # Market news
            try:
                url = f"https://api.marketaux.com/v1/news/all?symbols={symbols}&language=en&api_token={MARKETAUX_API_TOKEN}"
                news = requests.get(url).json().get("data", [])
                summary = " ".join([n.get("description", "") for n in news])
            except:
                news = []
                summary = ""

            for _, row in df.iterrows():
                ticker = row["Ticker"]
                qty = row["Quantity"]
                buy = row["Buy Price"]
                now = get_current_price(ticker)
                total = now * qty
                invested += buy * qty
                current += total
                portfolio_data.append({
                    "Ticker": ticker,
                    "Quantity": qty,
                    "Buy Price": buy,
                    "Current Price": round(now, 2),
                    "Total Value": round(total, 2)
                })

            ai = get_ai_decision(portfolio_data, summary)
            for stock in portfolio_data:
                stock["AI Suggestion"], stock["AI Reason"] = ai.get(stock["Ticker"], ("HOLD", "AI fallback"))

            gain = round(current - invested, 2)

    return render_template("dashboard.html",
                           portfolio=portfolio_data,
                           invested=round(invested, 2),
                           current=round(current, 2),
                           gain=gain,
                           news=news)
