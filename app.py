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
    import requests
    api_key = '2dbe2186699b47bb881b39254f2a38ea'
    
    if category == 'crypto':
        url = f'https://newsapi.org/v2/everything?q=crypto&language=en&sortBy=publishedAt&apiKey={api_key}'
    else:
        url = f'https://newsapi.org/v2/top-headlines?category={category}&language=en&apiKey={api_key}'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        return data.get('articles', [])[:6]
    except requests.exceptions.RequestException as e:
        print("NewsAPI Request Error:", e)
        print("Status Code:", response.status_code if 'response' in locals() else "N/A")
        print("Response Content:", response.text if 'response' in locals() else "N/A")
        return []
    except ValueError as e:
        print("JSON Decode Error:", e)
        print("Response was not valid JSON.")
        return []


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
