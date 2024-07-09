"""
File: converter.py
Purpose: Takes a CSV file and converts the data into a format that Firefly III can import.
"""
import csv
import argparse

class Transaction():
    def __init__(self, bsb, account, processed_date, payment_date, description, amount):
        self.bsb = bsb
        self.account = account
        self.date = processed_date
        self.description = description
        self.amount = amount
        self.payment_date = payment_date

    def __str__(self):
        return f'{self.date}, {self.description}, {self.amount}, {self.category}, {self.account}'

    def to_dict(self):
        return {
            'date': self.date,
            'description': self.description,
            'amount': self.amount,
            'category': self.category,
            'account': self.account
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = 'Convert CSV file to Firefly III format.'
    )

    parser.add_argument('file', type = str, help = 'CSV to convert')
    parser.add_argument('output', type = str, help = 'Output file.')

    # parse arguments setup program
    args = parser.parse_args()

    with open(args.file, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        data = list(reader)
