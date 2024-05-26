from sparklestock import Stock
import time
import threading

class TradingBot:
    def __init__(self, stock):
        self.stock = stock
        self.running = False
        self.buy_threshold = 0.01  # 3% 하락 시 매수
        self.sell_threshold = 0.01  # 5% 상승 시 매도
        self.initial_price = None
        self.lock = threading.Lock()

    def start(self):
        self.running = True
        self.initial_price = self.stock.get_price_history()[-1]  # 최초 가격 설정
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def run(self):
        while self.running:
            with self.lock:
                self.trade()
            time.sleep(1)
            self.show_assets()

    def trade(self):
        asset_info = self.stock.check_my_asset()
        current_price = self.stock.get_price_history()[-1]

        cash = asset_info['money']
        stock_amount = asset_info['stock']

        if self.initial_price is None:
            self.initial_price = current_price

        price_change = (current_price - self.initial_price) / self.initial_price

        if price_change <= self.buy_threshold and cash >= current_price:
            buy_amount = cash // current_price
            if buy_amount > 0:
                self.stock.buy_stock(buy_amount)
                print(f"매수 완료: {buy_amount}주 @ {current_price}")
                self.initial_price = current_price  # 매수 후 초기 가격 재설정

        elif price_change >= self.sell_threshold and stock_amount > 0:
            self.stock.sell_stock(stock_amount)
            print(f"매도 완료: {stock_amount}주 @ {current_price}")
            self.initial_price = current_price  # 매도 후 초기 가격 재설정

    def show_assets(self): #현재 자산, 가격, 보유 주식 수를 보여줌
        asset_info = self.stock.check_my_asset()
        current_price = self.stock.get_price_history()[-1]
        print(f"현재 자산: {asset_info['money']}, 보유 주식 수: {asset_info['stock']}, 현재 가격: {current_price}")

if __name__ == "__main__":
    stock = Stock('http://3.34.181.14')
    stock.login('채완친구현진', '') #주식서버 로그인

    bot = TradingBot(stock)

    try:
        bot.start()
        while True:
            command = input("봇을 중지하려면 'stop'을 입력하세요: ")
            if command.lower() == 'stop':
                bot.stop()
                break
    except KeyboardInterrupt:
        bot.stop()