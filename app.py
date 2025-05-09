import os
import pandas as pd
import requests
from flask import Flask, render_template, request

app = Flask(__name__)
ALPHA_API_KEY = "HMTZ4KZAG65XW27N"
MARKETAUX_API = "https://api.marketaux.com/v1/news/all?api_token=b4a0c3289954e7fdd84253d28aabf7ed&limit=5&filter_entities=true"

def get_current_price(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return float(data["Global Quote"]["05. price"])
    except:
        return 0.0

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            df = pd.read_csv(file)
            return render_template("dashboard.html", portfolio=df.to_dict(orient="records"))
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    df = pd.read_csv("sample_portfolio.csv")
    total_invested, current_value = 0.0, 0.0

    for index, row in df.iterrows():
        current = get_current_price(row["Ticker"])
        df.at[index, "Current Price"] = current
        total = current * row["Quantity"]
        df.at[index, "Total Value"] = total
        df.at[index, "AI Suggestion"] = "SELL" if current < row["Buy Price"] else "BUY"
        total_invested += row["Buy Price"] * row["Quantity"]
        current_value += total

    gain_loss = current_value - total_invested

    try:
        news = requests.get(MARKETAUX_API).json()["data"]
    except:
        news = []

    return render_template("dashboard.html", 
                           portfolio=df.to_dict(orient="records"), 
                           invested=total_invested, 
                           current=current_value, 
                           gain=gain_loss,
                           news=news)

if __name__ == "__main__":
    app.run(debug=True)
