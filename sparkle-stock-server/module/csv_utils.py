import csv

CSV_FILE_PATH = "/Users/seyong/Documents/dev/python/sparkle-stock-server/module/data/INTC20092024.csv"

def get_csv_line_by_time(seconds):
    with open(CSV_FILE_PATH, newline='') as csvfile:
        reader = csv.reader(csvfile)
        lines = list(reader)
        line_index = round(seconds // 1) + 1
        try:
            return lines[line_index][2]
        except:
            return False


def get_current_price(seconds):
    price = float(get_csv_line_by_time(seconds))
    return price

def get_history(seconds):
    with open(CSV_FILE_PATH, newline='') as csvfile:
        reader = csv.reader(csvfile)
        lines = list(reader)
        line_index = round(seconds // 1) + 1
        return [float(lines[i][2]) for i in range(1,line_index+1)]

def get_all():
    with open(CSV_FILE_PATH, newline='') as csvfile:
        reader = csv.reader(csvfile)
        lines = list(reader)
        return [float(lines[i][2]) for i in range(1,len(lines))]

def get_max():
    with open(CSV_FILE_PATH, newline='') as csvfile:
        reader = csv.reader(csvfile)
        lines = list(reader)
        return float(lines[len(lines)-1][2])