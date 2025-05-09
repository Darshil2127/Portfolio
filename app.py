import os
import time
import pandas as pd
import requests
from flask import Flask, render_template, request
import openai

app = Flask(__name__)

# API Keys
ALPHA_API_KEY = "HMTZ4KZAG65XW27N"
MARKETAUX_API = "https://api.marketaux.com/v1/news/all?api_token=VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp&limit=10&filter_entities=true"
openai.api_key = "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"

# Get current price from Alpha Vantage
def get_current_price(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        price = data.get("Global Quote", {}).get("05. price", None)
        if price:
            return float(price)
    except:
        pass
    return 0.0

# Generate AI decision + reasoning
def get_ai_suggestion(ticker, news_summary, buy_price, current_price):
    try:
        prompt = (
            f"You are a financial analyst. Based on the data below, give a BUY, SELL, or HOLD signal for the stock, "
            f"and explain in 1 short sentence why.\n\n"
            f"Ticker: {ticker}\n"
            f"Buy Price: {buy_price}\n"
            f"Current Price: {current_price}\n"
            f"News Summary: {news_summary}\n\n"
            f"Reply in this format:\nDecision: [BUY/SELL/HOLD]\nReason: [one sentence]"
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )

        content = response["choices"][0]["message"]["content"].strip()
        lines = content.split("\n")
        decision = "HOLD"
        reason = ""

        for line in lines:
            if line.upper().startswith("DECISION"):
                decision = line.split(":")[-1].strip().upper()
            elif line.upper().startswith("REASON"):
                reason = line.split(":", 1)[-1].strip()

        if decision not in ["BUY", "SELL", "HOLD"]:
            decision = "HOLD"

        return decision, reason

    except:
        return "HOLD", "Could not generate suggestion."

# Upload and process CSV
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            df = pd.read_csv(file)
            total_invested, current_value = 0.0, 0.0

            # Fetch news
            try:
                news_data = requests.get(MARKETAUX_API).json().get("data", [])
                news_text = " ".join([article.get("description", "") for article in news_data])
            except:
                news_data = []
                news_text = ""

            # Process portfolio
            for index, row in df.iterrows():
                ticker = row["Ticker"]
                buy_price = row["Buy Price"]
                quantity = row["Quantity"]

                current = get_current_price(ticker)
                df.at[index, "Current Price"] = current
                df.at[index, "Total Value"] = current * quantity

                decision, reason = get_ai_suggestion(ticker, news_text, buy_price, current)
                df.at[index, "AI Suggestion"] = decision
                df.at[index, "AI Reason"] = reason

                total_invested += buy_price * quantity
                current_value += current * quantity

                time.sleep(15)  # to avoid hitting API limits

            gain_loss = current_value - total_invested

            return render_template("dashboard.html",
                                   portfolio=df.to_dict(orient="records"),
                                   invested=total_invested,
                                   current=current_value,
                                   gain=gain_loss,
                                   news=news_data)

    return render_template("index.html")

# Optional static dashboard test route
@app.route("/dashboard")
def dashboard():
    df = pd.read_csv("sample_portfolio.csv")
    total_invested, current_value = 0.0, 0.0

    try:
        news_data = requests.get(MARKETAUX_API).json().get("data", [])
        news_text = " ".join([article.get("description", "") for article in news_data])
    except:
        news_data = []
        news_text = ""

    for index, row in df.iterrows():
        ticker = row["Ticker"]
        buy_price = row["Buy Price"]
        quantity = row["Quantity"]

        current = get_current_price(ticker)
        df.at[index, "Current Price"] = current
        df.at[index, "Total Value"] = current * quantity

        decision, reason = get_ai_suggestion(ticker, news_text, buy_price, current)
        df.at[index, "AI Suggestion"] = decision
        df.at[index, "AI Reason"] = reason

        total_invested += buy_price * quantity
        current_value += current * quantity
        time.sleep(15)

    gain_loss = current_value - total_invested

    return render_template("dashboard.html",
                           portfolio=df.to_dict(orient="records"),
                           invested=total_invested,
                           current=current_value,
                           gain=gain_loss,
                           news=news_data)

if __name__ == "__main__":
    app.run(debug=True)
