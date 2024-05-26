import matplotlib.pyplot as plt
from sparklestock import Stock


stock = Stock('http://3.34.181.14')
stock.login(id='aegis', pw='shield')
plt.ion()
fig, ax = plt.subplots()
short_duration = 2
long_duration = 8


buy_threshold = 0.2
sell_threshold = 0.0


y_data = stock.get_price_history()
x_data = [i for i in range(len(y_data))]
y_long_sum = [i for i in y_data]
y_short_sum = [i for i in y_data]
buy_points = []
sell_points = []
t = len(x_data)
prev_up_cross = False
print("done")
while True:
   if len(x_data) > 200:
       x_data = x_data[-200:]
       y_data = y_data[-200:]
       y_short_sum = y_short_sum[-200:]
       y_long_sum = y_long_sum[-200:]
       if buy_points and buy_points[0][0] == x_data[0]:
           buy_points.pop(0)
       if sell_points and sell_points[0][0] == x_data[0]:
           sell_points.pop(0)


   try:
       price = stock.get_current_price()
   except:
       asset = stock.check_my_asset()
       amount = asset['stock']
       stock.sell_stock(amount)
       asset = stock.check_my_asset()
       print(asset)
       exit()
   x_data.append(t)
   y_data.append(price)
   if len(y_data) < long_duration:
       y_long_sum.append(price)
       y_short_sum.append(price)
   else:
       y_long_sum.append(sum(y_data[-long_duration:]) / long_duration)
       y_short_sum.append(sum(y_data[-short_duration:]) / short_duration)
   ax.clear()
   ax.plot(x_data, y_data, color='black')
   ax.plot(x_data, y_long_sum, color='red', linestyle='dotted')
   ax.plot(x_data, y_short_sum, color='green', linestyle='dotted')


   for point in buy_points:




       ax.scatter(point[0], point[1], color='red', label='Buy Signal')
   for point in sell_points:
       ax.scatter(point[0], point[1], color='blue', label='Sell Signal')


   ax.set_title('Stock Price')
   ax.set_xlabel('Time')
   ax.set_ylabel('Price')
   fig.canvas.draw()
   t += 1
   if len(x_data) < long_duration + 1:
       plt.pause(1)
       continue
   asset = stock.check_my_asset()
   try:
       price = stock.get_current_price()
   except:
       asset = stock.check_my_asset()
       amount = asset['stock']
       stock.sell_stock(amount)
       print(asset)
       exit()
   if sum(y_data[-long_duration:]) / long_duration + buy_threshold < sum(y_data[-short_duration:]) / short_duration and not prev_up_cross:
       while True:
           try:
               price = stock.get_current_price()
               amount = asset['money'] // price
               stock.buy_stock(amount)
               break
           except:
               continue
       buy_points.append((x_data[-1], y_data[-1]))
       plt.pause(1)
       prev_up_cross = True
       continue
   if (sum(y_data[-long_duration:]) / long_duration) > (
           (sum(y_data[-short_duration:]) / short_duration) + sell_threshold) and prev_up_cross:
       amount = asset['stock']
       stock.sell_stock(amount)
       sell_points.append((x_data[-1], y_data[-1]))
       plt.pause(1)
       prev_up_cross = False
       continue
   plt.pause(1)

