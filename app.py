import yfinance as yf
from flask import Flask
from flask import request
from flask import json
from flask import jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/', methods = ['POST'])
@cross_origin()
def solve():
    context = request.json['context']
    if request.method == 'POST':

        values = yf.Ticker(context['ticker']).history(start=context['start'],  end=context['end'])

        res = {}

        for i in range(0, values.shape[0]):

            res[values.iloc[i].name.strftime("%Y-%m-%d")] = {

                'Open': values.iloc[i]['Open'], 
                'High': values.iloc[i]['High'],
                'Low': values.iloc[i]['Low'],
                'Close': values.iloc[i]['Close'],
                'Volume': values.iloc[i]['Volume'],
                'Dividends': values.iloc[i]['Dividends'],
                'Stock Splits': values.iloc[i]['Stock Splits'],
                
                }

            print(values.iloc[i])

        return jsonify(res)

if __name__ == "__main__":
    app.run()