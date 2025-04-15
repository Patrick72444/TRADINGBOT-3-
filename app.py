from flask import Flask, request
from binance.um_futures import UMFutures
import os
import time
import requests

app = Flask(__name__)

# Binance Testnet
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
client = UMFutures(key=API_KEY, secret=API_SECRET, base_url="https://testnet.binancefuture.com")

# Configuración del bot
symbol = "BTCUSDT"
capital = 1000  # tu capital base en USDT
leverage = 2
SL_PERCENT = -6  # Stop Loss -6%

# Telegram
TELEGRAM_TOKEN = "8163150195:AAFKm-QOZ5lJn_2wvyggwhLOgbjqu2xl71o"
TELEGRAM_CHAT_ID = "5086466173"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")

# Estado actual de la operación
current_position = None
entry_price = None
entry_timestamp = None

def close_position():
    global current_position, entry_price, entry_timestamp

    # Recalcular quantity para el cierre
    price = float(client.ticker_price(symbol=symbol)["price"])
    quantity = round((capital * leverage) / price, 4)

    if current_position == "long":
        client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
        send_telegram(f"📤 Cerrada LONG a mercado")
    elif current_position == "short":
        client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
        send_telegram(f"📤 Cerrada SHORT a mercado")

    current_position = None
    entry_price = None
    entry_timestamp = None

@app.route('/webhook', methods=['POST'])
def webhook():
    global current_position, entry_price, entry_timestamp

    data = request.json
    signal = data.get('signal')
    now = time.time()

    # Configuración de margen aislado y apalancamiento
    try:
        client.change_margin_type(symbol=symbol, marginType="ISOLATED")
    except:
        pass
    client.change_leverage(symbol=symbol, leverage=leverage)

    # Calcular precio actual y tamaño de la posición
    price = float(client.ticker_price(symbol=symbol)["price"])
    quantity = round((capital * leverage) / price, 4)

    # Verificar Stop Loss dinámico
    if current_position == "long" and entry_price:
        pnl_pct = ((price - entry_price) / entry_price) * 100
        if pnl_pct <= SL_PERCENT:
            close_position()
            send_telegram(f"🛑 SL LONG alcanzado: {pnl_pct:.2f}%")
            return {"message": f"SL LONG alcanzado: {pnl_pct:.2f}%"}

    if current_position == "short" and entry_price:
        pnl_pct = ((entry_price - price) / entry_price) * 100
        if pnl_pct <= SL_PERCENT:
            close_position()
            send_telegram(f"🛑 SL SHORT alcanzado: {pnl_pct:.2f}%")
            return {"message": f"SL SHORT alcanzado: {pnl_pct:.2f}%"}

    # Procesar señal
    if signal == "buy":
        if current_position != "long":
            close_position()
            client.new_order(symbol=symbol, side="BUY", type="MARKET", quantity=quantity)
            current_position = "long"
            entry_price = price
            entry_timestamp = now
            send_telegram(f"🚀 Entrada LONG a {price:.2f} | qty: {quantity}")
            return {"message": f"Entrada LONG a {price:.2f}"}
        else:
            return {"message": "Ya estás en LONG"}

    elif signal == "sell":
        if current_position != "short":
            close_position()
            client.new_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
            current_position = "short"
            entry_price = price
            entry_timestamp = now
            send_telegram(f"🔻 Entrada SHORT a {price:.2f} | qty: {quantity}")
            return {"message": f"Entrada SHORT a {price:.2f}"}
        else:
            return {"message": "Ya estás en SHORT"}

    elif signal == "close":
        if current_position:
            close_position()
            send_telegram("✅ Posición cerrada manualmente")
            return {"message": "Cierre manual ejecutado"}
        else:
            return {"message": "No hay posición abierta"}

    return {"message": "Señal no reconocida"}

# Correr en Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


