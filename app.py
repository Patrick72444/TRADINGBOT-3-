from flask import Flask, request
from binance.um_futures import UMFutures
import os

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = UMFutures(key=API_KEY, secret=API_SECRET, base_url="https://testnet.binancefuture.com")

# Estado de la posición: 'long', 'short', o None
current_position = None

@app.route('/webhook', methods=['POST'])
def webhook():
    global current_position

    data = request.json
    signal = data.get('signal')

    if signal == 'buy':
        if current_position != 'long':
            client.new_order(
                symbol="BTCUSDT",
                side="BUY",
                type="MARKET",
                quantity=0.002
            )
            current_position = 'long'
            return {"message": "🚀 Orden de COMPRA ejecutada"}
        else:
            return {"message": "⚠️ Ya hay una posición LONG abierta"}

    elif signal == 'sell':
        if current_position != 'short':
            client.new_order(
                symbol="BTCUSDT",
                side="SELL",
                type="MARKET",
                quantity=0.002
            )
            current_position = 'short'
            return {"message": "🔻 Orden de VENTA ejecutada"}
        else:
            return {"message": "⚠️ Ya hay una posición SHORT abierta"}

    elif signal == 'close':
        if current_position == 'long':
            client.new_order(
                symbol="BTCUSDT",
                side="SELL",
                type="MARKET",
                quantity=0.002
            )
            current_position = None
            return {"message": "✅ Posición LONG cerrada"}

        elif current_position == 'short':
            client.new_order(
                symbol="BTCUSDT",
                side="BUY",
                type="MARKET",
                quantity=0.002
            )
            current_position = None
            return {"message": "✅ Posición SHORT cerrada"}

        else:
            return {"message": "⚠️ No hay ninguna posición abierta para cerrar"}

    return {"message": "⚠️ Señal no reconocida"}
