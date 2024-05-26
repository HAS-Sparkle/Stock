from sparklestock import Stock
import matplotlib.pyplot as plt

stock = Stock('http://3.34.181.14')
stock.login('yeonjae','0812')

stock.buy_stock(1000)
while True:
    history = stock.get_price_history()
    M20 = sum(history[-10:-5]) / 5
    price = stock.get_current_price()
    asset = stock.check_my_asset()
    my_stock = asset['stock']
    real_asset = asset["stock"] * price + asset["money"]

#매수
    if (price <= M20 * 0.8) and (asset['money'] >= price * 400):
        stock.buy_stock(500)
    elif (price <= M20 * 0.9) and (asset['money'] >= price * 200):
        stock.buy_stock(300)
    elif (price <= M20 * 0.95) and (asset['money'] >= price * 100):
        stock.buy_stock(100)

#매도
    if (price >= M20 * 1.2) and (my_stock >= 700):
        stock.sell_stock(400)
    elif (price >= M20 * 1.1) and (my_stock >= 400):
        stock.sell_stock(200)
    elif (price >= M20 * 1.05) and (my_stock >= 300):
        stock.sell_stock(100)


    print(asset, real_asset)
    print(price)
    plt.pause(1)