from sparklestock import Stock
import time

stock = Stock('http://3.34.181.14')
stock.login('채완친구현진', '')

#변동성 목표 설정
def get_volatility_breakout_price():
    price_history = stock.get_price_history()
    print("가격 이력:", price_history)
    if not price_history or not isinstance(price_history, list):
        print("가격 이력이 비어있거나 리스트 형태가 아닙니다.")
        return None, None
    if len(price_history) < 2:
        print("가격 이력이 충분하지 않습니다.")
        return None, None
    yesterday_close_price = price_history[-2]
    today_close_price = price_history[-1]
    volatility = abs(today_close_price - yesterday_close_price)
    target_price = today_close_price + (volatility * 0.5)
    today_open_price = yesterday_close_price
    return target_price, today_open_price

#거래 봇 정의하기
def trading_bot():
    holding_stock = False
    while True:
        target_price, today_open_price = get_volatility_breakout_price()
        if target_price is None:
            continue

        asset_info = stock.check_my_asset()
        print("자산 정보:", asset_info) #자산 정보 확인

        current_price = stock.get_current_price()
        if current_price is None:
            print("현재 가격 정보를 가져올 수 없습니다.")
            continue

        print("자산 정보의 키들:", asset_info.keys())

        cash = asset_info.get('money')
        stock_amount = asset_info.get('stock')

        if cash is None or stock_amount is None:
            print("자산 정보에 'money' 또는 'stock' 키가 없습니다.")
            continue

        if not holding_stock and current_price > target_price: #돈 있을때마다 항상 매수하도록 설정
            amount_to_buy = cash // current_price
            if amount_to_buy > 0:
                stock.buy_stock(amount_to_buy)
                holding_stock = True
                print(f"매수 완료: {amount_to_buy}주")
        elif holding_stock: #3% 오르거나 1% 하락시 매도
            buy_price = today_open_price
            if (current_price - buy_price) / buy_price >= 0.03 or (current_price - buy_price) / buy_price <= -0.01:
                stock.sell_stock(stock_amount)
                holding_stock = False
                print(f"매도 완료: {stock_amount}주")

        print(f"현재 자산: {cash}, 보유 주식 수: {stock_amount}, 현재 가격: {current_price}")
        time.sleep(1) #1초마다 자산, 보유 주식 수, 가격 표시


trading_bot()

