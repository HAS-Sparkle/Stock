from time import sleep

from scipy.stats import linregress
from sparklestock import Stock

from config import QUANTITY

temp: list[float] = []
prices: list[float] = []

stock: Stock = Stock("http://3.34.181.14")
stock.login("full2null", "kmj20080226!S")

while True:
    sleep(1)

    current_price: float = stock.get_current_price()
    print(f"현재 주가: {current_price}")
    temp.append(current_price)

    if len(temp) < 3:
        continue

    prices.append(sum(temp) / len(temp))
    temp.clear()

    if len(prices) < 6:
        continue

    first_high: float = max(prices)
    second_high: float = sorted(prices)[-2]
    first_low: float = min(prices)
    second_low: float = sorted(prices)[1]

    try:
        high_slope: float = linregress(
            [first_high, second_high],
            [prices.index(first_high), prices.index(second_high)],
        ).slope

    except ValueError:
        high_slope: float = 0.0

    try:
        low_slope: float = linregress(
            [first_low, second_low],
            [prices.index(first_low), prices.index(second_low)],
        ).slope

    except ValueError:
        low_slope: float = 0.0

    if high_slope > 0 and low_slope > 0:
        try:
            stock.buy_stock(QUANTITY)

        except ConnectionError:
            pass

    elif high_slope < 0 and low_slope < 0:
        try:
            stock.sell_stock(stock.check_my_asset()["stock"])

        except ConnectionError:
            pass

    elif abs(high_slope) > abs(low_slope):
        if high_slope > 0:
            try:
                stock.buy_stock(QUANTITY)

            except ConnectionError:
                pass

        else:
            try:
                stock.sell_stock(QUANTITY)

            except ConnectionError:
                pass

    else:
        if low_slope > 0:
            try:
                stock.buy_stock(QUANTITY)

            except ConnectionError:
                pass

        else:
            try:
                stock.sell_stock(QUANTITY)

            except ConnectionError:
                pass

    prices.clear()

    print(f"현금 보유량: {stock.check_my_asset()["money"]}")
    print(f"주식 보유량: {stock.check_my_asset()["stock"]}")
