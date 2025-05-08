import csv
import io
import os
import requests
from flask import Flask, request, render_template
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "2S7DC1BF8WZ46PX2")

def fetch_price(ticker):
    """Fetch current price from Alpha Vantage"""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        price_str = data.get("Global Quote", {}).get("05. price", None)
        return float(price_str) if price_str else 0.0
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return 0.0

def get_ai_suggestion(ticker, buy_price, current_price):
    """Very basic dummy AI suggestion logic"""
    if current_price > buy_price * 1.05:
        return "SELL"
    elif current_price < buy_price * 0.95:
        return "BUY"
    else:
        return "HOLD"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard", methods=["POST"])
def dashboard():
    file = request.files["file"]
    if not file:
        return "No file uploaded.", 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)

    portfolio = []
    total_invested = 0.0
    current_value = 0.0

    for row in csv_input:
        ticker = row["Ticker"].strip().upper()
        quantity = int(row["Quantity"])
        buy_price = float(row["Buy Price"])

        current_price = fetch_price(ticker)
        total_val = current_price * quantity
        ai_suggestion = get_ai_suggestion(ticker, buy_price, current_price)

        total_invested += quantity * buy_price
        current_value += total_val

        portfolio.append({
            "ticker": ticker,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": round(current_price, 2),
            "total_value": round(total_val, 2),
            "ai_suggestion": ai_suggestion
        })

    gain_loss = round(current_value - total_invested, 2)

    return render_template("dashboard.html",
                           portfolio=portfolio,
                           total_invested=round(total_invested, 2),
                           current_value=round(current_value, 2),
                           gain_loss=gain_loss)

if __name__ == "__main__":
    app.run(debug=True)
