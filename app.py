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

def fetch_finance_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        'apiKey': '2dbe2186699b47bb881b39254f2a38ea',  # Your API key
        'category': 'business',  # You can adjust the category if needed
        'country': 'us',  # You can adjust the country if needed
    }
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        try:
            articles = response.json().get('articles', [])
            return articles
        except ValueError:
            print("Error: Response is not in JSON format.")
            return []
    else:
        print(f"Error: Received {response.status_code} from NewsAPI.")
        return []
  # Return top 5 articles

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["portfolio"]
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            tickers = df["Ticker"].tolist()
            recommendations = dummy_ai_analysis(tickers)
            news = fetch_finance_news()
            return render_template("dashboard.html", recommendations=recommendations, news=news)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
