import yfinance as yf
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

### Sample request body for /

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",  
#         "end": "2020-11-30"
#     }
# }


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

### Sample request body for /getBBands

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",  
#         "end": "2020-11-30",
#         "window": 20,
#         "sdfactor": 2
#     }
# }

@app.route("/getBBands", methods=["POST"])
@cross_origin()
def BBands():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        close = values['Close']
        window = context['window']
        sdfactor = context['sdfactor']

        idx = 0
        price_sum = 0

        moving_average = []
        uband = []
        lband = []

        for price in close:
            
            price_sum += price
            sd_sum = 0
            
            if(idx >= window):
                price_sum -= close[idx - window]
                avg = price_sum / window
                moving_average.append(avg)

                for i in range(idx - window, idx + 1):
                    sd_sum += (close[i] - avg) ** 2
                sd_sum /= window
                uband.append(avg + sdfactor * (sd_sum ** 0.5))
                lband.append(avg - sdfactor * (sd_sum ** 0.5))
            
            idx += 1

        print(len(moving_average))
        print(len(uband))
        print(len(lband))

        ma = {}
        ub = {}
        lb = {}

        for i in range(0, len(moving_average)):
            ma[i] = moving_average[i];

        for i in range(0, len(uband)):
            ub[i] = uband[i];

        for i in range(0, len(lband)):
            lb[i] = lband[i];

        data = {
            "moving_average": ma,
            "upper_band": ub,
            "lower_band": lb
        }

        return jsonify(data)


if __name__ == "__main__":
    app.run()
