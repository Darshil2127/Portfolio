import os
import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")  # Alpha Vantage key
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY")  # Marketaux key

def fetch_price(symbol):
    try:
        if "-USD" in symbol:  # For crypto
            url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={symbol.split('-')[0]}&to_currency=USD&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url).json()
            return float(response["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        else:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url).json()
            return float(response["Global Quote"]["05. price"])
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return 0.0

@app.route('/')
def index():
    return render_template('dashboard.html', portfolio=[], total_invested='$0.00', current_value='$0.00', gain_loss='$0.00')

@app.route('/dashboard', methods=['POST'])
def dashboard():
    file = request.files['file']
    if not file:
        return redirect(url_for('index'))

    df = pd.read_csv(file)
    total_invested = 0
    current_value = 0
    portfolio = []

    for _, row in df.iterrows():
        ticker = row['Ticker']
        qty = float(row['Quantity'])
        buy_price = float(row['Buy Price'])
        current_price = fetch_price(ticker)
        value = current_price * qty
        suggestion = "BUY" if current_price < buy_price else "SELL"

        portfolio.append({
            'ticker': ticker,
            'quantity': qty,
            'buy_price': f"${buy_price}",
            'current_price': f"${round(current_price, 2)}",
            'total_value': f"${round(value, 2)}",
            'suggestion': suggestion
        })

        total_invested += qty * buy_price
        current_value += value

    gain_loss = current_value - total_invested

    return render_template(
        'dashboard.html',
        portfolio=portfolio,
        total_invested=f"${total_invested:.2f}",
        current_value=f"${current_value:.2f}",
        gain_loss=f"${gain_loss:.2f}"
    )

@app.route('/news/<ticker>')
def news(ticker):
    try:
        url = f"https://api.marketaux.com/v1/news/all?symbols={ticker}&api_token={MARKETAUX_API_KEY}&limit=5"
        news_data = requests.get(url).json().get('data', [])
        return render_template('news.html', ticker=ticker, news=news_data)
    except Exception as e:
        return f"Error fetching news for {ticker}: {e}"

if __name__ == '__main__':
    app.run(debug=True)
