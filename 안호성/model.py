import yfinance as yf
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt
from sparklestock import Stock

from sklearn.metrics.pairwise import cosine_similarity


# 모델 설정 및 훈련
def train_model(data):
    df = data[['Date', 'Close']].copy()
    df.columns = ['ds', 'y']

    model = Prophet(yearly_seasonality=False,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    changepoint_prior_scale=0.95,
                    interval_width=0.95,
                    changepoint_range=0.95)
    model.add_country_holidays(country_name='KOR')

    model.fit(df)
    return model


# 주식을 사고 팔기 위한 클래스
class StockTrader:
    def __init__(self, initial_data, capital, target_return=1.05, periods=5, stock_system: Stock = None,
                 purchase_price=0):
        self.stock_system: Stock = stock_system
        if self.stock_system is not None:
            self.capital = self.stock_system.check_my_asset().get('money')
            self.stocks_owned = self.stock_system.check_my_asset().get('stock')
        else:
            self.capital = capital
            self.stocks_owned = 0
        self.data = initial_data.copy()
        self.model = train_model(self.data)
        self.purchase_price = purchase_price
        self.target_return = target_return
        self.periods = periods
        self.transactions = []  # 거래 내역 저장
        self.test_data = []

    def get_purchase_price(self):
        return self.purchase_price

    def fetch(self):
        self.capital = self.stock_system.check_my_asset().get('money')
        self.stocks_owned = self.stock_system.check_my_asset().get('stock')

    def update_model(self, new_data):
        self.data = pd.concat([self.data, new_data])
        self.data.drop_duplicates(subset='Date', keep='last', inplace=True)
        self.model = train_model(self.data)

    def check_model(self, real_price):
        if len(self.test_data) >= 5:
            cos_sim = cosine_similarity([self.test_data], [self.data['Close'].values[-5:]])
            # print(self.test_data)
            # print(self.data['Close'].values[-5:])
            # print(cos_sim)
            if (cos_sim < 0.95 or cos_sim > 1.05) or (abs(real_price - self.test_data[-1]) > 5) or (
                    ((self.test_data[-1] / real_price) - 1) * 100 < -5):
                return "restart"

    def trade(self, current_date, real_price):
        if self.stock_system is None:
            raise ValueError("Stock System is not initialized")

        future = self.model.make_future_dataframe(periods=self.periods)
        forecast = self.model.predict(future)
        predicted_price = forecast.iloc[-1]['yhat']  # 예측 일수 후의 예상 가격

        if len(self.test_data) >= 5:
            self.test_data.pop(0)
        self.test_data.append(predicted_price)

        # 예상 수익률 계산
        future_return = ((predicted_price / real_price) - 1) * 100

        # 현재 가격, 구매 가격 및 수익률 출력
        current_return = (real_price / self.purchase_price - 1) * 100 if self.stocks_owned > 0 else 0
        print(
                f"{self.periods}일 후의 예상 가격: {predicted_price}, 예상 수익률: {future_return:.2f}%, 현재 실제 가격: {real_price}, 구매 가격: {self.purchase_price}, 현재 수익률: {current_return:.2f}%")

        # 주식 추가 구매 결정: 목표 수익률 달성 가능성 판단
        if predicted_price > real_price * self.target_return:
            desired_quantity = int(self.capital / real_price)

            # min_predicted_price = min(predicted_prices)

            if desired_quantity > 0:  # and min_predicted_price >= real_price:
                self.stocks_owned += desired_quantity
                self.capital -= desired_quantity * real_price
                self.purchase_price = ((self.purchase_price * (
                        self.stocks_owned - desired_quantity) + real_price * desired_quantity) / self.stocks_owned) if self.stocks_owned else real_price
                self.transactions.append((current_date, 'buy', desired_quantity, real_price))
                self.stock_system.buy_stock(desired_quantity)
                print(f"주식 구매 완료: {desired_quantity} 주, 잔고: {self.capital}")

        # 주식 판매 결정 (목표 수익률 달성 시)
        if self.stocks_owned > 0 and real_price >= self.purchase_price * self.target_return:
            self.capital += self.stocks_owned * real_price
            self.transactions.append((current_date, 'sell', self.stocks_owned, real_price))
            self.stock_system.sell_stock(self.stocks_owned)
            print(
                    f"주식 판매 완료: 구매가 {self.purchase_price}, 판매가 {real_price}, 수힉 {(real_price - self.purchase_price) * self.stocks_owned} ,수익률 {((real_price / self.purchase_price) - 1) * 100:.2f}%, 잔고: {self.capital}")
            self.stocks_owned = 0
            self.purchase_price = 0
        # 주식 판매 결정 (손실률 10% 이상)
        if self.stocks_owned > 0 and real_price <= self.purchase_price * 0.9:
            self.capital += self.stocks_owned * real_price
            self.transactions.append((current_date, 'sell', self.stocks_owned, real_price))
            self.stock_system.sell_stock(self.stocks_owned)
            print(
                    f"주식 판매 완료: 구매가 {self.purchase_price}, 판매가 {real_price}, 손실 {(real_price - self.purchase_price) * self.stocks_owned}, 손실률 {((real_price / self.purchase_price) - 1) * 100:.2f}%, 잔고: {self.capital}")
            self.stocks_owned = 0
            self.purchase_price = 0

    def simulate_trading(self, current_date, real_price):
        if self.stock_system is not None:
            raise ValueError("Stock System is initialized, unable to simulate trading")

        future = self.model.make_future_dataframe(periods=self.periods)
        forecast = self.model.predict(future)
        predicted_price = forecast.iloc[-1]['yhat']  # 예측 일수 후의 예상 가격
        # 예측 일수간 예상 가격
        predicted_prices = forecast['yhat'].values[-self.periods:]

        # current_predicted_price = forecast[forecast['ds'] == current_date]['yhat'].values[0]

        # 예상 수익률 계산
        future_return = ((predicted_price / real_price) - 1) * 100

        # 현재 가격, 구매 가격 및 수익률 출력
        current_return = (real_price / self.purchase_price - 1) * 100 if self.stocks_owned > 0 else 0
        print(
                f"현재 날짜: {current_date.date()}, {self.periods}일 동안의 예상 가격: {predicted_prices.tolist()}, 예상 수익률: {future_return:.2f}%, 현재 실제 가격: {real_price}, 구매 가격: {self.purchase_price}, 현재 수익률: {current_return:.2f}%")

        # 주식 추가 구매 결정: 목표 수익률 달성 가능성 판단
        # if predicted_price > real_price * self.target_return:
        if predicted_price > real_price * 1.03:
            desired_quantity = int(self.capital / real_price)

            min_predicted_price = min(predicted_prices)

            if desired_quantity > 0 and min_predicted_price >= real_price:
                self.stocks_owned += desired_quantity
                self.capital -= desired_quantity * real_price
                self.purchase_price = ((self.purchase_price * (
                        self.stocks_owned - desired_quantity) + real_price * desired_quantity) / self.stocks_owned) if self.stocks_owned else real_price
                self.transactions.append((current_date, 'buy', desired_quantity, real_price))
                print(f"주식 구매 완료: {desired_quantity} 주")

        # 주식 판매 결정 (목표 수익률 달성 시)
        if self.stocks_owned > 0 and real_price >= self.purchase_price * self.target_return:
            self.capital += self.stocks_owned * real_price
            self.transactions.append((current_date, 'sell', self.stocks_owned, real_price))
            print(
                    f"주식 판매 완료: 구매가 {self.purchase_price}, 판매가 {real_price}, 수힉 {(real_price - self.purchase_price) * self.stocks_owned} ,수익률 {((real_price / self.purchase_price) - 1) * 100:.2f}%")
            self.stocks_owned = 0
            self.purchase_price = 0
        # 주식 판매 결정 (손실률 5% 이상)
        if self.stocks_owned > 0 and real_price <= self.purchase_price * 0.95:
            self.capital += self.stocks_owned * real_price
            self.transactions.append((current_date, 'sell', self.stocks_owned, real_price))
            print(
                    f"주식 판매 완료: 구매가 {self.purchase_price}, 판매가 {real_price}, 손실 {(real_price - self.purchase_price) * self.stocks_owned}, 손실률 {((real_price / self.purchase_price) - 1) * 100:.2f}%")
            self.stocks_owned = 0
            self.purchase_price = 0

    def summarize_trading(self, last_price=0):
        # 최종 평가손익 출력
        print(f"최종 평가손익: {self.capital + self.stocks_owned * last_price} KRW")
        # 거래 내역 시각화
        df = pd.DataFrame(self.transactions, columns=['Date', 'Action', 'Quantity', 'Price'])
        buys = df[df['Action'] == 'buy']
        sells = df[df['Action'] == 'sell']
        plt.plot(self.data['Date'], self.data['Close'], label='Close Price')
        plt.scatter(buys['Date'], buys['Price'], color='green', label='Buy', s=20, marker='^')
        plt.scatter(sells['Date'], sells['Price'], color='red', label='Sell', s=20, marker='v')
        plt.xlim(pd.Timestamp('2024-01-01'), self.data['Date'].max())
        plt.legend()
        plt.title("Stock Trading Simulation Results")
        plt.xlabel("Date")
        plt.ylabel("Price (KRW)")
        plt.show()


if __name__ == '__main__':
    # Initialize and run the simulation
    initial_data = yf.download('005930.KS', start='2010-01-01', end='2023-12-31')
    initial_df = initial_data.reset_index()[['Date', 'Close']]

    capital = 1000000  # 예시 초기 자본금: 1,000,000 KRW
    trader = StockTrader(initial_df, capital, target_return=1.01, periods=5)
    print("Init Finished")

    real_data = yf.download('005930.KS', start='2024-01-01', end='2024-04-30')
    real_df = real_data.reset_index()[['Date', 'Close']]

    import time

    times = []

    # Execute the trading simulation
    for index, row in real_df.iterrows():
        start_time = time.time()
        trader.update_model(real_df.iloc[:index])  # Updating the model with up-to-date data
        trader.simulate_trading(row['Date'], row['Close'])  # Pass both the date and the actual price for simulation
        times.append(time.time() - start_time)

    # Summarize and visualize the trading performance at the end
    trader.summarize_trading(last_price=real_df.iloc[-1]['Close'])
    print("Average time per iteration: ", sum(times) / len(times))
