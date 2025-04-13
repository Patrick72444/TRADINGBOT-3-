
from flask import Flask, request
from binance.um_futures import UMFutures
import os

app = Flask(__name__)

# Obtener claves desde variables de entorno (Render)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = UMFutures(key=API_KEY, secret=API_SECRET, base_url="https://testnet.binancefuture.com")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    signal = data.get('signal')

    if signal == 'buy':
        order = client.new_order(
            symbol="BTCUSDT",
            side="BUY",
            type="MARKET",
            quantity=0.002
        )
        return {"message": "🚀 Orden de COMPRA ejecutada"}

    elif signal == 'sell':
        order = client.new_order(
            symbol="BTCUSDT",
            side="SELL",
            type="MARKET",
            quantity=0.002
        )
        return {"message": "🔻 Orden de VENTA ejecutada"}

    return {"message": "⚠️ Señal no reconocida"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
