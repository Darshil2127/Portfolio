import os
import csv
import io
import requests
from flask import Flask, request, render_template, redirect, url_for
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# API KEYS
ALPHA_VANTAGE_API_KEY = '2S7DC1BF8WZ46PX2'
MARKETAUX_API_KEY = 'VQLCY5MmRKd5NoGznLXmdm62igUwqttW4eEGxZYp'

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Upload CSV
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400

    if file:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        headers = next(csv_input)
        data = list(csv_input)
        
        portfolio = pd.DataFrame(data, columns=headers)
        portfolio['Quantity'] = portfolio['Quantity'].astype(float)
        portfolio['Buy_Price'] = portfolio['Buy_Price'].astype(float)

        portfolio['Invested'] = portfolio['Quantity'] * portfolio['Buy_Price']
        portfolio['Current_Price'] = portfolio['Ticker'].apply(get_current_price)
        portfolio['Current_Value'] = portfolio['Quantity'] * portfolio['Current_Price']
        portfolio['Gain/Loss'] = portfolio['Current_Value'] - portfolio['Invested']
        portfolio['AI_Suggestion'] = portfolio.apply(lambda row: ai_suggest(row), axis=1)

        summary = {
            'Total Invested': round(portfolio['Invested'].sum(), 2),
            'Current Value': round(portfolio['Current_Value'].sum(), 2),
            'Gain/Loss': round(portfolio['Gain/Loss'].sum(), 2)
        }

        return render_template('result.html', tables=[portfolio.to_html(classes='data', index=False)], summary=summary)

    return "Something went wrong", 500

# Get Current Price using Alpha Vantage
def get_current_price(ticker):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        price = float(data['Global Quote']['05. price'])
        return price
    except:
        return 0.0

# Dummy AI-based suggestion
def ai_suggest(row):
    change = (row['Current_Price'] - row['Buy_Price_]()_]()
