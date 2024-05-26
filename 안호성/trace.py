from sparklestock import Stock
from time import sleep


def init_stock_system() -> Stock:
    system = Stock("http://3.34.181.14")
    system.login("id", "pw")

    print("Init Complete")
    print(system.check_my_asset())

    return system


if __name__ == '__main__':
    stock_system = init_stock_system()
    temp = stock_system.check_my_asset()
    last_money = temp['money']
    while True:
        if stock_system.check_my_asset() != temp:
            temp = stock_system.check_my_asset()
            print(temp)
            if temp['stock'] == 0:
                if temp['money'] > last_money:
                    print("You've earned money!", temp['money'] - last_money)
                elif temp['money'] < last_money:
                    print("You've lost money!", last_money - temp['money'])
                last_money = temp['money']
            elif temp['stock'] > 0:
                print("You've bought stock!", temp['stock'])
            print()
        sleep(1)
