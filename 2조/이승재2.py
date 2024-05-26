from sparklestock import Stock
import time
stock = Stock('http://3.34.181.14')
stock.login('ajaj','sadcc')
my_asset = {}

while True:
    my_asset = stock.check_my_asset()
    print(my_asset)
    price = stock.get_current_price()
    if (price < 55) and (my_asset['money'] > 100*price):
        print("주가: ", price)
        stock.buy_stock(100)
        time.sleep(1)

    if price > 55:
        print("주가: ", price)
        stock.sell_stock(100)
        time.sleep(1)

    if price * 100 > my_asset['money'] / 20:
        stock.sell_stock(1000)