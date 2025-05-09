import os
import pandas as pd
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "2S7DC1BF8WZ46PX2")

def get_current_price(ticker):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
    response = requests.get(url)
    data = response.json()
    try:
        return float(data["Global Quote"]["05. price"])
    except (KeyError, ValueError):
        return 0.0

def get_ai_suggestion(buy_price, current_price):
    if current_price > buy_price:
        return "SELL"
    else:
        return "BUY"

@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html", portfolio=None)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "POST":
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"

        df = pd.read_csv(file)
        portfolio = []

        total_invested = 0.0
        total_current_value = 0.0

        for _, row in df.iterrows():
            ticker = row['Ticker']
            quantity = row['Quantity']
            buy_price = row['Buy Price']

            current_price = get_current_price(ticker)
            total_value = current_price * quantity
            ai_suggestion = get_ai_suggestion(buy_price, current_price)

            total_invested += quantity * buy_price
            total_current_value += total_value

            portfolio.append({
                "ticker": ticker,
                "quantity": quantity,
                "buy_price": f"${buy_price}",
                "current_price": f"${current_price:.2f}",
                "total_value": f"${total_value:.2f}",
                "ai_suggestion": ai_suggestion
            })

        gain_loss = total_current_value - total_invested

        return render_template("dashboard.html",
                               portfolio=portfolio,
                               total_invested=f"${total_invested}",
                               total_current_value=f"${total_current_value:.2f}",
                               gain_loss=f"${gain_loss:.2f}")

    return render_template("dashboard.html", portfolio=None)
