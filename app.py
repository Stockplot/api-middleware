import yfinance as yf
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.route("/", methods=["POST"])
@cross_origin()
def solve():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        res = {}

        for i in range(0, values.shape[0]):

            res[i] = {
                "date": values.iloc[i].name.strftime("%Y-%m-%d"),
                "open": values.iloc[i]["Open"],
                "high": values.iloc[i]["High"],
                "low": values.iloc[i]["Low"],
                "close": values.iloc[i]["Close"],
                "volume": values.iloc[i]["Volume"],
                "dividends": values.iloc[i]["Dividends"],
                "stock splits": values.iloc[i]["Stock Splits"],
            }

        data = {
            "length": values.shape[0],
            "data": res,
        }

        return jsonify(data)


if __name__ == "__main__":
    app.run()
