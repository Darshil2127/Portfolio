import os
import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
MARKETAUX_API_KEY = os.getenv('MARKETAUX_API_KEY')


def fetch_price(ticker):
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}'
    try:
        response = requests.get(url)
        data = response.json()
        return float(data["Global Quote"]["05. price"])
    except Exception:
        return 0.0


def fetch_news(ticker):
    url = f'https://api.marketaux.com/v1/news/all?symbols={ticker}&filter_entities=true&language=en&api_token={MARKETAUX_API_KEY}'
    try:
        response = requests.get(url)
        articles = response.json().get("data", [])[:5]
        return articles
    except Exception:
        return []


@app.route('/', methods=['GET'])
def index():
    return render_template('dashboard.html', portfolio=[], total_invested="$0.00", current_value="$0.00", gain_loss="$0.00")


@app.route('/dashboard', methods=['POST'])
def dashboard():
    file = request.files.get('file')
    if not file:
        return redirect(url_for('index'))

    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]

    portfolio = []
    total_invested = 0
    current_value = 0

    for _, row in df.iterrows():
        ticker = row['Ticker']
        quantity = float(row['Quantity'])
        buy_price = float(row['Buy Price'])

        current_price = fetch_price(ticker)
        total_val = quantity * current_price
        invested_val = quantity * buy_price

        suggestion = "BUY" if current_price > buy_price else "SELL"

        portfolio.append({
            'ticker': ticker,
            'quantity': quantity,
            'buy_price': f"${buy_price:.2f}",
            'current_price': f"${current_price:.2f}",
            'total_value': f"${total_val:.2f}",
            'suggestion': suggestion
        })

        total_invested += invested_val
        current_value += total_val

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
    articles = fetch_news(ticker)
    return render_template('news.html', ticker=ticker.upper(), articles=articles)


if __name__ == '__main__':
    app.run(debug=True)
