import csv
from son_data import data

def write_data_to_csv(son_data):
    with open('son_archive_data.csv', 'w') as f:
        w = csv.DictWriter(f, son_data[0].keys())
        w.writeheader()
        for row in son_data:
            w.writerow(row)

if __name__ == "__main__":
    write_data_to_csv(data)
