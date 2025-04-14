if signal == 'buy':
    qty = 0.013
    symbol = "BTCUSDT"

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
