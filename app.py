from flask import Flask, render_template, request
import pandas as pd
import requests

app = Flask(__name__)
ALPHA_VANTAGE_API_KEY = "2S7DC1BF8WZ46PX2"
MARKETAUX_API_KEY = "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp"

def fetch_current_price(ticker):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    try:
        return float(data["Global Quote"]["05. price"])
    except:
        return 0.0

def get_ai_suggestion(current_price, buy_price):
    if current_price >= 1.05 * buy_price:
        return "SELL"
    elif current_price <= 0.95 * buy_price:
        return "BUY"
    else:
        return "HOLD"

def fetch_news(ticker):
    url = f"https://api.marketaux.com/v1/news/all?symbols={ticker}&filter_entities=true&language=en&api_token={MARKETAUX_API_KEY}"
    response = requests.get(url)
    try:
        articles = response.json().get("data", [])[:5]
        return [{
            "title": article["title"],
            "url": article["url"],
            "published_at": article["published_at"],
            "description": article.get("description", "")
        } for article in articles]
    except:
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        df = pd.read_csv(file)

        portfolio_data = []
        total_invested = 0
        current_value = 0
        all_news = []

        for _, row in df.iterrows():
            ticker = row["Ticker"]
            quantity = row["Quantity"]
            buy_price = row["Buy Price"]

            current_price = fetch_current_price(ticker)
            total_value = current_price * quantity
            ai_suggestion = get_ai_suggestion(current_price, buy_price)

            total_invested += quantity * buy_price
            current_value += total_value

            portfolio_data.append({
                "ticker": ticker,
                "quantity": quantity,
                "buy_price": round(buy_price, 2),
                "current_price": round(current_price, 2),
                "total_value": round(total_value, 2),
                "ai_suggestion": ai_suggestion
            })

            news = fetch_news(ticker)
            all_news.extend(news)

        gain_loss = round(current_value - total_invested, 2)
        return render_template("dashboard.html",
                               portfolio_data=portfolio_data,
                               total_invested=round(total_invested, 2),
                               current_value=round(current_value, 2),
                               gain_loss=gain_loss,
                               news_data=all_news)

    return '''
    <h2>Upload your Portfolio CSV File</h2>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    '''

if __name__ == "__main__":
    app.run(debug=True)
