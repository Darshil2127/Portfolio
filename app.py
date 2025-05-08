import os
import requests
import pandas as pd
from flask import Flask, request, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

# Alpha Vantage API key
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "2S7DC1BF8WZ46PX2")

def fetch_price(ticker):
    """Fetch current stock price using Alpha Vantage API"""
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        price_str = data.get("Global Quote", {}).get("05. price", None)
        return float(price_str) if price_str else 0.0
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return 0.0

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            return "Invalid file format. Please upload a CSV file.", 400

        try:
            df = pd.read_csv(file)
        except Exception as e:
            return f"Error reading CSV file: {e}", 400

        # Ensure required columns are present
        if not {'Ticker', 'Quantity', 'Buy Price'}.issubset(df.columns):
            return "Invalid CSV format. Required columns: Ticker, Quantity, Buy Price", 400

        portfolio = []
        total_invested = 0
        current_value = 0

        for _, row in df.iterrows():
            ticker = row['Ticker']
            quantity = int(row['Quantity'])
            buy_price = float(row['Buy Price'])

            current_price = fetch_price(ticker)

            total_value = quantity * current_price
            invested = quantity * buy_price

            # AI suggestion logic
            if current_price > buy_price * 1.05:
                suggestion = "SELL"
            elif current_price < buy_price * 0.95:
                suggestion = "BUY"
            else:
                suggestion = "HOLD"

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

        return render_template('dashboard.html',
                               portfolio=portfolio,
                               total_invested=round(total_invested, 2),
                               current_value=round(current_value, 2),
                               gain_loss=gain_loss)

    return render_template("dashboard.html", portfolio=None)

if __name__ == "__main__":
    app.run(debug=True)
