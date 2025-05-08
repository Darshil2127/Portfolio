import os
import requests
import pandas as pd
from flask import Flask, render_template, request

os.environ["OPENBLAS_NUM_THREADS"] = "1"

app = Flask(__name__)

# Dummy recommendation logic
def dummy_ai_analysis(tickers):
    recommendations = []
    for ticker in tickers:
        action = "Buy" if hash(ticker) % 2 == 0 else "Sell"
        recommendations.append({"ticker": ticker, "recommendation": action})
    return recommendations

# Fetch real-time financial news
import requests

def fetch_finance_news(category='business'):
    api_key = '2dbe2186699b47bb881b39254f2a38ea'
    
    # Custom keyword for crypto since NewsAPI has no crypto category
    if category == 'crypto':
        url = f'https://newsapi.org/v2/everything?q=crypto&language=en&sortBy=publishedAt&apiKey={api_key}'
    else:
        url = f'https://newsapi.org/v2/top-headlines?category={category}&language=en&apiKey={api_key}'

    response = requests.get(url)
    articles = response.json().get('articles', [])
    return articles[:6]  # Return top 6 articles

  # Return top 5 articles

@app.route("/", methods=["GET", "POST"])
def index():
    category = request.args.get("category", "business")

    if request.method == "POST":
        file = request.files["portfolio"]
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            tickers = df["Ticker"].tolist()
            recommendations = dummy_ai_analysis(tickers)
            news = fetch_finance_news(category)
            return render_template("dashboard.html", recommendations=recommendations, news=news)

    news = fetch_finance_news(category)
    return render_template("index.html", news=news)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
