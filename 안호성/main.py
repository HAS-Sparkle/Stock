from model import StockTrader
from sparklestock import Stock

import pandas as pd
from datetime import datetime, timedelta


def init_stock_system() -> Stock:
    system = Stock("http://3.34.181.14")
    system.login("betatester", "thisismypassword")

    print("Init Complete")

    if system.check_my_asset().get('stock') > 0:
        system.sell_stock(system.check_my_asset().get('stock'))

    print(system.check_my_asset())

    return system


def get_formated_history(stock_system: Stock):
    history: list = stock_system.get_price_history()

    # 시작 날짜 설정
    start_date = datetime.now().date() - timedelta(days=len(history))

    # 날짜 인덱스 생성
    dates = [start_date + timedelta(days=i) for i in range(len(history))]

    # DataFrame 생성
    df = pd.DataFrame(data={'Date': dates, 'Close': history})

    return df


def get_initial_stock_trader(stock_system: Stock, target_return=1.05, periods=5, purchase_price=0):
    df = get_formated_history(stock_system)

    trader = StockTrader(stock_system=stock_system, initial_data=df,
                         capital=stock_system.check_my_asset().get('money'),
                         target_return=target_return, periods=periods, purchase_price=purchase_price)

    return trader


def main():
    stock_system = init_stock_system()
    trader = get_initial_stock_trader(stock_system, target_return=1.01, periods=5)

    i_date = datetime.now().date()

    current_history = pd.DataFrame(data={'Date': [], 'Close': []})
    history_len = len(stock_system.get_price_history())

    while True:
        try:
            while True:
                if len(stock_system.get_price_history()) > history_len + len(current_history):
                    current_price = stock_system.get_current_price()
                    break
            current_history.loc[i_date] = current_price
            trader.fetch()
            trader.trade(i_date, current_price)
            res = trader.check_model(current_price)
            if res == "restart":
                print("!!Alert: restarting model!!")
                purchase_price = trader.get_purchase_price()
                trader = get_initial_stock_trader(stock_system, target_return=1.01, periods=5,
                                                  purchase_price=purchase_price)

                i_date = datetime.now().date()

                current_history = pd.DataFrame(data={'Date': [], 'Close': []})
                history_len = len(stock_system.get_price_history())
            trader.update_model(current_history)  # TODO: 시간 넘치면 빼기.
            i_date += timedelta(days=1)
        except KeyboardInterrupt:
            stock_system.sell_stock(trader.stocks_owned)
            break
        except Exception as e:
            print(e)
            purchase_price = trader.get_purchase_price()
            trader = get_initial_stock_trader(stock_system, target_return=1.01, periods=5,
                                              purchase_price=purchase_price)

            i_date = datetime.now().date()

            current_history = pd.DataFrame(data={'Date': [], 'Close': []})
            history_len = len(stock_system.get_price_history())
        finally:
            pass
            # trader.summarize_trading(last_price=current_history.iloc[-1]['Close'])


if __name__ == '__main__':
    main()
