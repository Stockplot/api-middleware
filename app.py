import yfinance as yf
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from flask_cors import CORS, cross_origin
from decimal import Decimal

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

        close = values["Close"]
        window = int(context["window"])
        sdfactor = float(context["sdfactor"])

        idx = 0
        price_sum = 0

        moving_average = []
        uband = []
        lband = []

        res = {}

        for price in close:

            price_sum += price
            sd_sum = 0

            if idx >= window:
                price_sum -= close[idx - window]
                avg = price_sum / window

                for i in range(idx - window, idx + 1):
                    sd_sum += (close[i] - avg) ** 2
                sd_sum /= window

                res[idx - window] = {
                    "close": close[idx - window],
                    "date": values.iloc[idx - window].name.strftime("%Y-%m-%d"),
                    "moving_average": avg,
                    "upper_band": avg + sdfactor * (sd_sum ** 0.5),
                    "lower_band": avg - sdfactor * (sd_sum ** 0.5),
                }

            idx += 1

        data = {"data": res, "length": idx - window}

        return jsonify(data)


### Sample request body for /getRSI

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "window": 30
#     }
# }


@app.route("/getRSI", methods=["POST"])
@cross_origin()
def RSIndex():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        window = int(context["window"])

        # res = {}

        # for i in range(0, values.shape[0]):
        #     res[i] = {
        #         "date": values.iloc[i].name.strftime("%Y-%m-%d"),
        #         "close": values.iloc[i]["Close"],
        #     }

        points_gain = []
        points_lost = []

        for i in range(0, values.shape[0] - 1):
            change = Decimal(values.iloc[i + 1]["Close"]) - Decimal(
                values.iloc[i]["Close"]
            )
            if change > 0:
                points_gain.append(change)
                points_lost.append(Decimal(0))
            else:
                points_lost.append(change)
                points_gain.append(Decimal(0))

        print(points_lost)
        print(points_gain)

        pl_avg_ar = []
        pg_avg_ar = []
        rs_ar = []
        rsi_ar = []
        date = []

        for i in range(0, values.shape[0] - window):
            pg_avg_ar.append(sum(points_gain[i : i + window]) / window)
            pl_avg_ar.append(sum(points_lost[i : i + window]) * Decimal(-1) / window)

        for i in range(0, len(pg_avg_ar)):
            rs_ar.append(str(pg_avg_ar[i] / pl_avg_ar[i]))
            rsi_ar.append(str(100 - (100 / (1 + Decimal(rs_ar[i])))))

        # pl_avg = sum(points_lost) * Decimal(-1) / len(points_lost)
        # pg_avg = sum(points_gain) / len(points_gain)

        # print(pl_avg)
        # print(pg_avg)

        # rs = pg_avg / pl_avg

        # rsi = 100 - (100 / (1 + rs))

        pg = {}
        pl = {}
        data_log = {}
        date = []

        for i in range(window, values.shape[0]):
            date.append(values.iloc[i].name.strftime("%Y-%m-%d"))

        for i in range(0, values.shape[0] - window):
            data_log[i] = {
                "Date": date[i],
                "RS": rs_ar[i],
                "RSI": rsi_ar[i],
            }

        signal = {}
        for i in range(0, len(data_log)):
            if Decimal(data_log[i]["RSI"]) > Decimal(0) and Decimal(data_log[i]["RSI"]) < Decimal(30):
                signal[i] = {
                    "Date": values.iloc[i].name.strftime("%Y-%m-%d"),
                    "Signal": "1",
                }
            elif Decimal(data_log[i]["RSI"]) > Decimal(70) and Decimal(data_log[i]["RSI"]) < Decimal (100):
                signal[i] = {
                    "Date": values.iloc[i].name.strftime("%Y-%m-%d"),
                    "Signal": "-1",
                }
            else:
                pass

        

       
        #     pl[i] = str(points_lost[i])

        data = {
            "data": data_log,
            "data_len": len(data_log),
            "signal": signal,
            "signal_len": len(signal),
        }

        return jsonify(data)


### Sample request body for /getMACD
# Note - make sure gap b/w start -end > 27 days
# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30"
#     }
# }


@app.route("/getMACD", methods=["POST"])
@cross_origin()
def get_MACD():
    context = request.json["context"]
    if request.method == "POST":

        values = yf.Ticker(context["ticker"]).history(
            start=context["start"], end=context["end"]
        )

        daily_close = []

        for i in range(0, values.shape[0]):
            daily_close.append(
                Decimal(values.iloc[i]["Close"]),
            )

        tweleve_day_ma = []
        twentysix_day_ma = []

        macd_val = []
        mv = {}

        data = {}

        try:
            for i in range(0, values.shape[0] - 12):
                tweleve_day_ma.append(sum(daily_close[i : i + 12]) / 12)

            for i in range(0, values.shape[0] - 26):
                twentysix_day_ma.append(sum(daily_close[i : i + 26]) / 26)

            for i in range(0, len(twentysix_day_ma)):
                macd_val.append(tweleve_day_ma[i + 14] - twentysix_day_ma[i])

            for i in range(0, len(macd_val)):
                mv[i] = str(macd_val[i])

            data = {
                "MACD Values": mv,
            }
            return jsonify(data)

        except:
            print("Date range less than 1 month")
            data = {"Error": "no Data"}
            return


if __name__ == "__main__":
    app.run()
