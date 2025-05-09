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

# Generate AI suggestion using OpenAI
def get_ai_suggestion(ticker, news_summary, buy_price, current_price):
    try:
        prompt = (
            f"You are an investment advisor. Based on this news and the stock performance:\n\n"
            f"Ticker: {ticker}\n"
            f"Buy Price: {buy_price}\n"
            f"Current Price: {current_price}\n\n"
            f"Recent Market News: {news_summary}\n\n"
            f"Should the user BUY, HOLD, or SELL this stock? Reply with one word only."
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0
        )

        suggestion = response["choices"][0]["message"]["content"].strip().upper()
        if suggestion in ["BUY", "SELL", "HOLD"]:
            return suggestion
        else:
            return "HOLD"
    except:
        return "HOLD"

# Main route (Upload CSV)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            df = pd.read_csv(file)
            total_invested, current_value = 0.0, 0.0

            # Get news summary
            try:
                news_data = requests.get(MARKETAUX_API).json().get("data", [])
                news_text = " ".join([article["description"] or "" for article in news_data])
            except:
                news_data = []
                news_text = ""

            for index, row in df.iterrows():
                ticker = row["Ticker"]
                buy_price = row["Buy Price"]
                quantity = row["Quantity"]
                current = get_current_price(ticker)
                df.at[index, "Current Price"] = current

                total = current * quantity
                df.at[index, "Total Value"] = total
                ai_suggestion = get_ai_suggestion(ticker, news_text, buy_price, current)
                df.at[index, "AI Suggestion"] = ai_suggestion

                total_invested += buy_price * quantity
                current_value += total
                time.sleep(15)  # to respect Alpha Vantage rate limits

            gain_loss = current_value - total_invested

            return render_template("dashboard.html",
                                   portfolio=df.to_dict(orient="records"),
                                   invested=total_invested,
                                   current=current_value,
                                   gain=gain_loss,
                                   news=news_data)

    return render_template("index.html")

# Optional route for testing without upload
@app.route("/dashboard")
def dashboard():
    df = pd.read_csv("sample_portfolio.csv")
    total_invested, current_value = 0.0, 0.0

    try:
        news_data = requests.get(MARKETAUX_API).json().get("data", [])
        news_text = " ".join([article["description"] or "" for article in news_data])
    except:
        news_data = []
        news_text = ""

    for index, row in df.iterrows():
        ticker = row["Ticker"]
        buy_price = row["Buy Price"]
        quantity = row["Quantity"]
        current = get_current_price(ticker)
        df.at[index, "Current Price"] = current

        total = current * quantity
        df.at[index, "Total Value"] = total
        ai_suggestion = get_ai_suggestion(ticker, news_text, buy_price, current)
        df.at[index, "AI Suggestion"] = ai_suggestion

        total_invested += buy_price * quantity
        current_value += total
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
