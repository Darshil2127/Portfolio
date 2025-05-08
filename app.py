from flask import Flask, request, render_template_string
import requests
import pandas as pd
import os

app = Flask(__name__)
MARKETAUX_API_KEY = os.environ.get("MARKETAUX_API_KEY", "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp")

# Simple HTML Template
HTML_TEMPLATE = """
<!doctype html>
<title>FinFuse - Portfolio News</title>
<h1>Upload Your CSV Portfolio</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
{% if results %}
  <h2>News Summary</h2>
  {% for ticker, news_list in results.items() %}
    <h3>{{ ticker }}</h3>
    {% for article in news_list %}
      <p><a href="{{ article['url'] }}" target="_blank">{{ article['title'] }}</a></p>
    {% endfor %}
  {% endfor %}
{% endif %}
"""

def get_news(ticker):
    url = f"https://api.marketaux.com/v1/news/all"
    params = {
        'symbols': ticker,
        'filter_entities': True,
        'language': 'en',
        'api_token': MARKETAUX_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if 'data' in data:
            return data['data'][:3]  # Limit to 3 articles
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
    return []

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    results = {}
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                df = pd.read_csv(file)
                tickers = df['Ticker'].dropna().unique()
                for ticker in tickers:
                    news = get_news(ticker.strip())
                    results[ticker] = news if news else [{'title': 'No news found', 'url': '#'}]
            except Exception as e:
                results = {"Error": [{'title': str(e), 'url': '#'}]}
    return render_template_string(HTML_TEMPLATE, results=results)

# Health check
@app.route('/ping')
def ping():
    return "App is running fine!"

if __name__ == '__main__':
    app.run(debug=True)
