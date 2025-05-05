
from flask import Flask, render_template, request, redirect
import pandas as pd

app = Flask(__name__)

def dummy_ai_analysis(tickers):
    recommendations = []
    for ticker in tickers:
        action = "Buy" if hash(ticker) % 2 == 0 else "Sell"
        recommendations.append({"ticker": ticker, "recommendation": action})
    return recommendations

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["portfolio"]
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            tickers = df["Ticker"].tolist()
            recommendations = dummy_ai_analysis(tickers)
            return render_template("dashboard.html", recommendations=recommendations)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
