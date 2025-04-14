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
    qty = 0.013
    symbol = "BTCUSDT"

    if signal == 'buy':
        # 1. Colocar orden de compra market
        order = client.new_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quantity=qty
        )

        # 2. Obtener precio de entrada real de la orden
        fills = order.get("fills", [])
        entry_price = float(fills[0]["price"]) if fills else 0.0

        # 3. Calcular precios de TP y SL
        tp_price = round(entry_price * 1.015, 2)  # +1.5%
        sl_price = round(entry_price * 0.99, 2)   # -1%

        # 4. Colocar orden Take Profit
        client.new_order(
            symbol=symbol,
            side="SELL",
            type="TAKE_PROFIT_MARKET",
            stopPrice=tp_price,
            quantity=qty,
            timeInForce="GTC"
        )

        # 5. Colocar orden Stop Loss
        client.new_order(
            symbol=symbol,
            side="SELL",
            type="STOP_MARKET",
            stopPrice=sl_price,
            quantity=qty,
            timeInForce="GTC"
        )

        return {"message": f"🟢 Orden BUY ejecutada con TP {tp_price} y SL {sl_price}"}

    elif signal == 'sell':
        # 1. Colocar orden de venta market
        order = client.new_order(
            symbol=symbol,
            side="SELL",
            type="MARKET",
            quantity=qty
        )

        # 2. Obtener precio de entrada real de la orden
        fills = order.get("fills", [])
        entry_price = float(fills[0]["price"]) if fills else 0.0

        # 3. Calcular precios de TP y SL para short
        tp_price = round(entry_price * 0.985, 2)  # -1.5%
        sl_price = round(entry_price * 1.01, 2)   # +1%

        # 4. Colocar orden Take Profit (BUY para cerrar short)
        client.new_order(
            symbol=symbol,
            side="BUY",
            type="TAKE_PROFIT_MARKET",
            stopPrice=tp_price,
            quantity=qty,
            timeInForce="GTC"
        )

        # 5. Colocar orden Stop Loss (BUY para cerrar short)
        client.new_order(
            symbol=symbol,
            side="BUY",
            type="STOP_MARKET",
            stopPrice=sl_price,
            quantity=qty,
            timeInForce="GTC"
        )

        return {"message": f"🔻 Orden SELL ejecutada con TP {tp_price} y SL {sl_price}"}

    return {"message": "⚠️ Señal no reconocida"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
