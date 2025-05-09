import os
from flask import Flask, render_template, request, redirect
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY") or "2S7DC1BF8WZ46PX2"
MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY") or "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp"

def fetch_current_price(ticker):
    if '-USD' in ticker:
        url = f'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={ticker.split("-")[0]}&to_currency=USD&apikey={ALPHA_VANTAGE_API_KEY}'
        response = requests.get(url).json()
        try:
            return float(response["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        except:
            return 0.0
    else:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
        response = requests.get(url).json()
        try:
            return float(response["Global Quote"]["05. price"])
        except:
            return 0.0

def get_news(ticker):
    url = f"https://api.marketaux.com/v1/news/all?symbols={ticker}&language=en&api_token={MARKETAUX_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json().get('data', [])
        return news_data[:5]
    return []

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            total_invested = 0
            current_value = 0
            portfolio_data = []

            for _, row in df.iterrows():
                ticker = row['Ticker']
                quantity = row['Quantity']
                buy_price = row['Buy Price']
                invested = quantity * buy_price
                current_price = fetch_current_price(ticker)
                value_now = quantity * current_price

                suggestion = "BUY" if current_price >= buy_price else "SELL"

                portfolio_data.append({
                    'ticker': ticker,
                    'quantity': quantity,
                    'buy_price': f"${buy_price}",
                    'current_price': f"${round(current_price, 2)}",
                    'total_value': f"${round(value_now, 2)}",
                    'suggestion': suggestion
                })

                total_invested += invested
                current_value += value_now

            gain_loss = current_value - total_invested

            return render_template("dashboard.html",
                                   portfolio=portfolio_data,
                                   total_invested=f"${total_invested}",
                                   current_value=f"${round(current_value, 2)}",
                                   gain_loss=f"${round(gain_loss, 2)}")
    return redirect('/')

@app.route('/news/<ticker>')
def news(ticker):
    articles = get_news(ticker)
    return render_template("news.html", ticker=ticker, articles=articles)

if __name__ == '__main__':
    app.run(debug=True)
