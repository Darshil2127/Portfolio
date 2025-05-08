import csv
import io
import os
import requests
import pandas as pd  # Make sure pandas is imported
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

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Ensure the file is included in the request
        file = request.files.get(('portfolio')
        if file and file.filename.endswith('.csv'):
            try:
                # Read the CSV into a DataFrame
                df = pd.read_csv(file)

                # Ensure the required columns exist in the CSV
                if not {'Ticker', 'Quantity', 'Buy Price'}.issubset(df.columns):
                    return "Invalid CSV format. Required columns are: Ticker, Quantity, Buy Price", 400

                # Prepare portfolio data
                portfolio = []
                total_invested = 0
                current_value = 0

                for _, row in df.iterrows():
                    ticker = row['Ticker']
                    quantity = int(row['Quantity'])
                    buy_price = float(row['Buy Price'])

                    # Fetch current price from Alpha Vantage
                    price_url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}'
                    response = requests.get(price_url).json()

                    try:
                        current_price = float(response['Global Quote']['05. price'])
                    except (KeyError, ValueError):
                        current_price = 0.0

                    total_value = quantity * current_price
                    invested = quantity * buy_price
                    suggestion = "BUY" if current_price < buy_price else "SELL"

                    portfolio.append({
                        "ticker": ticker,
                        "quantity": quantity,
                        "buy_price": round(buy_price, 2),
                        "current_price": round(current_price, 2),
                        "total_value": round(total_value, 2),
                        "ai_suggestion": suggestion
                    })

                    total_invested += invested
                    current_value += total_value

                gain_loss = round(current_value - total_invested, 2)

                # Render dashboard with portfolio data
                return render_template('dashboard.html', portfolio=portfolio,
                                       total_invested=total_invested,
                                       current_value=current_value,
                                       gain_loss=gain_loss)

            except Exception as e:
                return f"Error processing the CSV file: {str(e)}", 400
        else:
            return "Invalid file format. Please upload a CSV file.", 400

    # If GET request, just render an empty dashboard
    return render_template("dashboard.html", portfolio=None)


if __name__ == "__main__":
    app.run(debug=True)
