from flask import Blueprint
from flask_cors import CORS, cross_origin
from flask import request
import yfinance as yf
from flask import jsonify


BB = Blueprint('BB', __name__)

### Sample request body for /getBBands

# {
#     "context": {
#         "ticker": "MSFT",
#         "start": "2018-01-01",
#         "end": "2020-11-30",
#         "window": 20,
#         "sdfactor": 2,
#         "investment": 10000
#     }
# }


@BB.route("/getBBands", methods=["POST"])
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

        selling = False
        ordered_signals = []
        liquid_amount = int(context["investment"])
        invested_amount = 0
        num_shares = 0
        last_total = liquid_amount

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

                if (close[idx - window] <= avg - sdfactor * (sd_sum ** 0.5)) and selling == False:
                    num_shares = liquid_amount // close[idx - window]
                    liquid_amount -= num_shares * close[idx - window]
                    invested_amount += num_shares * close[idx - window]
                    total_amount = liquid_amount + invested_amount
                    pnl = total_amount - last_total
                    last_total = total_amount
                    ordered_signals.append({
                        "date": values.iloc[idx - window].name.strftime("%Y-%m-%d"),
                        "signal": 1,
                        "price": close[idx - window],
                        "invested_amount": invested_amount,
                        "liquid_amount": liquid_amount,
                        "total_amount": total_amount,
                        "pnl": pnl,
                    })
                    selling = True
                elif (close[idx - window] >= avg + sdfactor * (sd_sum ** 0.5)) and selling == True:
                    liquid_amount += num_shares * close[idx - window]
                    invested_amount = 0
                    total_amount = liquid_amount + invested_amount
                    pnl = total_amount - last_total
                    last_total = total_amount
                    ordered_signals.append({
                        "date": values.iloc[idx - window].name.strftime("%Y-%m-%d"),
                        "signal": -1,
                        "price": close[idx - window],
                        "invested_amount": invested_amount,
                        "liquid_amount": liquid_amount,
                        "total_amount": total_amount,
                        "pnl": pnl,
                    })
                    selling = False



            idx += 1

        data = {
            "data": res, 
            "data_length": idx - window,
            "ordered_signals": ordered_signals,
            "ordered_signals_len": len(ordered_signals),
            }

        return jsonify(data)