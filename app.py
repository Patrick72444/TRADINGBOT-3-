from flask import Flask, request
from binance.um_futures import UMFutures
import os
import time

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = UMFutures(key=API_KEY, secret=API_SECRET, base_url="https://testnet.binancefuture.com")

# CONFIGURACIÓN
symbol = "BTCUSDT"
capital = 1000  # capital real en USDT
leverage = 2
SL_PERCENT = -6  # -6% de stop loss

# Estado de la posición
current_position = None  # 'long' o 'short'
entry_price = None
entry_timestamp = None

def close_position():
    global current_position, entry_price, entry_timestamp
    if current_position == "long":
        client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
    elif current_position == "short":
        client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
    current_position = None
    entry_price = None
    entry_timestamp = None

@app.route('/webhook', methods=['POST'])
def webhook():
    global current_position, entry_price, entry_timestamp, quantity

    data = request.json
    signal = data.get('signal')
    now = time.time()

    # Establecer margen aislado y apalancamiento x2 (solo la primera vez por símbolo)
    try:
        client.change_margin_type(symbol=symbol, marginType="ISOLATED")
    except:
        pass  # ya está aislado
    client.change_leverage(symbol=symbol, leverage=leverage)

    # Obtener precio actual
    price = float(client.ticker_price(symbol=symbol)["price"])
    quantity = round((capital * leverage) / price, 4)

    # Check de SL dinámico
    if current_position == "long" and entry_price is not None:
        pnl_pct = ((price - entry_price) / entry_price) * 100
        if pnl_pct <= SL_PERCENT:
            close_position()
            return {"message": f"🛑 SL alcanzado en LONG: {pnl_pct:.2f}%"}

    if current_position == "short" and entry_price is not None:
        pnl_pct = ((entry_price - price) / entry_price) * 100
        if pnl_pct <= SL_PERCENT:
            close_position()
            return {"message": f"🛑 SL alcanzado en SHORT: {pnl_pct:.2f}%"}

    # PROCESAR SEÑALES
    if signal == 'buy':
        if current_position != 'long':
            close_position()
            client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
            current_position = 'long'
            entry_price = price
            entry_timestamp = now
            return {"message": f"🚀 Entrada LONG a {price}, qty: {quantity}"}
        else:
            return {"message": "⚠️ Ya hay una posición LONG"}

    elif signal == 'sell':
        if current_position != 'short':
            close_position()
            client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
            current_position = 'short'
            entry_price = price
            entry_timestamp = now
            return {"message": f"🔻 Entrada SHORT a {price}, qty: {quantity}"}
        else:
            return {"message": "⚠️ Ya hay una posición SHORT"}

    elif signal == 'close':
        if current_position:
            close_position()
            return {"message": "✅ Posición cerrada manualmente"}
        else:
            return {"message": "⚠️ No hay posición abierta"}

    return {"message": "⚠️ Señal no reconocida"}
