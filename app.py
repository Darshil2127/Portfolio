from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Your Marketaux API Key
MARKETAUX_API_KEY = "VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp"

# Route to show stock or crypto news based on symbol (e.g. AAPL, TSLA, BTC-USD)
@app.route('/news/<symbol>')
def get_news(symbol):
    url = f"https://api.marketaux.com/v1/news/all?symbols={symbol.upper()}&filter_entities=true&language=en&api_token={MARKETAUX_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('data', [])
        return render_template('news.html', articles=articles, symbol=symbol.upper())
    else:
        return f"Error fetching news: {response.status_code}"

# Optional default route
@app.route('/')
def home():
    return '''
        <h2>Welcome to FinFuse</h2>
        <p>Use <code>/news/AAPL</code> or <code>/news/BTC-USD</code> to see stock or crypto news.</p>
    '''

if __name__ == '__main__':
    app.run(debug=True)
