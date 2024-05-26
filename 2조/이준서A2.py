from sparklestock import Stock
import time
stock = Stock("http://3.34.181.14")
stock.login(id='24142', pw='24142')
while True:
   stock.buy_stock(50)
   asset = stock.check_my_asset()
   print(asset)
   stock.sell_stock(20)