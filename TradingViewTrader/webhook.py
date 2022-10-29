from flask import Flask, request
import os

from TradingViewTrader.logic import logic

# Trading View..
# 52.89.214.238
# 34.212.75.30
# 54.218.53.128
# 52.32.178.7

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        res = request.json
        # print("Data received from Webhook is: ", res)
        if res['key'] == os.environ.get("WEBHOOK_KEY"):
            logic(res)
        with open('orders.txt', 'a') as f:
            print(request.json, file=f)
        print('*'*100)
        return {"status:": "Webhook received!"}


# assert os.environ.get('BINANCE_API') and os.environ.get('BINANCE_SECRET')
app.run(host='0.0.0.0', port=8080)
