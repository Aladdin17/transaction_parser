"""
File: convert_statement_to_csv.py
Purpose: Read statement and extract transations to CSV file.
"""
from utils import Log
from datetime import datetime
from pypdf import PdfReader
from typing import List, Tuple
import argparse
import csv
import os
import re
import sys

class Transaction:
    def __init__(self, date : datetime = None, description : str = None, debit : float = None, credit : float = None, balance : float = None):
        self.date = date
        self.description = description
        self.debit = debit
        self.credit = credit
        self.balance = balance

    def __repr__(self):
        return f'Transaction(date={self.date}, description={self.description}, debit={self.debit}, credit={self.credit}, balance={self.balance})'

def extract_text_from_pdf(file_path : str):
    text : str = ""
    reader = PdfReader(file)
    num_pages = len(reader.pages)
    for page_num in range(num_pages):
        page = reader.pages[page_num]
        text += page.extract_text() + "\n"

    return text

def strip_dollar_sign(value : str) -> float:
    return float(value.replace('$','').replace(',', ''))

def convert_to_date(day : str, month : str, year : str) -> datetime:
    date_str = f'{year}-{month}-{day}'
    return datetime.strptime(date_str, '%y-%b-%d')

def extract_transactions(text) -> List[str]:
    # parse lines until we find the start of the transactions
    lines : List[str] = text.split('\n')

    # slice the lines to start at the first transaction, 2 lines after the 'TRANSACTION DETAILS' line
    for line_num, line in enumerate(lines):
        if line.startswith('TRANSACTION DETAILS'):
            lines = lines[line_num + 2:]
            break

    # for each line we want to extract it then test if its valid
    transactions : List[str] = []
    sentinel_values : List[str] = ['Date', 'Page', 'TRANSACTION']

    for line_num, line in enumerate(lines):
        # skip over values that are definitely not transactions
        if not line:
            continue

        # we have reached the end of the transactions
        if line.startswith('TOTAL'):
            break

        fields = line.split()
        if fields[0] in sentinel_values:
            continue

        transactions.append(line)

    return transactions

def parse_single_line_transaction(transaction : str, balance : float) -> Tuple[Transaction, float]:
    invalid_transaction_descriptions : List[str] = ['CARRIED FORWARD', 'BROUGHT FORWARD']
    new_transaction = Transaction()
    date_regex = r'(?P<day>\d{2}) (?P<month>\w{3}) (?P<year>\d{2})'
    date_match = re.match(date_regex, transaction)
    new_transaction.date = convert_to_date(date_match.group('day'), date_match.group('month'), date_match.group('year'))

    # strip the date from the transaction string
    transaction = transaction[date_match.end():].strip()

    # if this is the opening balance we need to extract the amount
    if transaction.startswith('OPENING BALANCE'):
        balance_regex = r'(?P<balance>\$.*\.\d{2})'
        balance_match = re.search(balance_regex, transaction)
        balance = strip_dollar_sign(balance_match.group('balance'))
        return None, balance

    # we don't process these listings as they are purely informational
    if any(transaction.startswith(prefix) for prefix in invalid_transaction_descriptions):
        return None, balance

    # now we actually process the transaction, any ill formed transactions will just
    # be ignored, this should cover any fees or other transactions that don't actually
    # affect the balance
    whole_regex = r'(?P<description>.*) (?P<amount>\$.*\.\d{2}) (?P<balance>\$.*\.\d{2})'
    whole_match = re.match(whole_regex, transaction)
    if whole_match is None:
        return None, balance

    # populate the transaction object
    new_transaction.description = whole_match.group('description')
    new_transaction.balance = strip_dollar_sign(whole_match.group('balance'))

    # determine if this is a debit or credit
    if new_transaction.balance > balance:
        new_transaction.credit = strip_dollar_sign(whole_match.group('amount'))
    else:
        new_transaction.debit = strip_dollar_sign(whole_match.group('amount'))

    return new_transaction, new_transaction.balance


def parse_multi_line_transaction(transaction1 : str, transaction2 : str, balance : float) -> Tuple[Transaction, float]:
    new_transaction = Transaction()
    date_regex = r'(?P<day>\d{2}) (?P<month>\w{3}) (?P<year>\d{2})'
    date_match = re.match(date_regex, transaction1)
    new_transaction.date = convert_to_date(date_match.group('day'), date_match.group('month'), date_match.group('year'))

    # strip the date from the transaction string
    transaction1 = transaction1[date_match.end():].strip()

    # process the first transaction and we are looking for just one amount and part of a description
    whole_regex1 = r'(?P<description>.*) (?P<amount>\$.*\.\d{2})'
    whole_match1 = re.match(whole_regex1, transaction1)
    if whole_match1 is None:
        # if this is ill-formed we will just ignore it
        # this should cover the case in which the first line does not have a credit/debit
        return None, balance

    whole_regex2 = r'(?P<description>.*) (?P<balance>\$.*\.\d{2})'
    whole_match2 = re.match(whole_regex2, transaction2)
    if whole_match2 is None:
        # if this is ill-formed we will just ignore it
        # this should cover the case in which the second line does not have a balance
        return None, balance

    # populate the transaction object
    new_transaction.description = whole_match1.group('description') + ' ' + whole_match2.group('description')
    new_transaction.balance = strip_dollar_sign(whole_match2.group('balance'))

    # determine if this is a debit or credit
    if new_transaction.balance > balance:
        new_transaction.credit = strip_dollar_sign(whole_match1.group('amount'))
    else:
        new_transaction.debit = strip_dollar_sign(whole_match1.group('amount'))

    return new_transaction, new_transaction.balance

def parse_transactions(transactions : List[str]) -> List[Transaction]:
    parsed_transactions : List[Transaction] = []
    multiline : bool = False
    balance : float = 0.0
    for index, transaction in enumerate(transactions):
        # we do not process the last transaction as it will be the CLOSING BALANCE
        if index == len(transactions) - 1:
            break

        if multiline:
            multiline = False
            continue

        # use regex to match the date
        date_regex = r'(?P<day>\d{2}) (?P<month>\w{3}) (?P<year>\d{2})'
        date_match_next = re.match(date_regex, transactions[index + 1])
        multiline = True if date_match_next is None else False

        if multiline:
            new_transaction, balance = parse_multi_line_transaction(transaction, transactions[index + 1], balance)
            if new_transaction is not None:
                parsed_transactions.append(new_transaction)
        else:
            new_transaction, balance = parse_single_line_transaction(transaction, balance)
            if new_transaction is not None:
                parsed_transactions.append(new_transaction)

    return parsed_transactions

def write_transactions_to_csv(transactions : List[Transaction], stream) -> None:
    if transactions is None:
        raise(ValueError('No transactions to write.'))

    # write transactions
    writer = csv.writer(stream, dialect = 'excel', delimiter = ',')
    writer.writerow(['Date', 'Description', 'Debit', 'Credit', 'Balance'])
    for transaction in transactions:
        writer.writerow([transaction.date.strftime('%Y-%m-%d'), transaction.description, transaction.debit, transaction.credit, transaction.balance])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = 'Extract transactions from PDF to CSV.'
    )

    parser.add_argument('file', type = str, help = 'Statement to extract transactions from.')
    parser.add_argument('-o', dest = 'output', type = str, required = False, help = 'Output file.')
    parser.add_argument('-q', dest = 'quiet', action = 'store_true', help = 'Suppress all output.')

    # parse arguments setup program
    args = parser.parse_args()
    file_path : str = os.path.relpath(args.file)
    log = Log(quiet = args.quiet, fill_width = 60, fill_char = '.')

    # validate file extension
    if not args.file.lower().endswith('.pdf'):
        print('File must have a .pdf extension.', file = sys.stderr)
        sys.exit(1)

    # extract text and parse it into transactions
    try:
        with open(file_path, 'rb') as file:
            log.action(f'Extracting text from \'{file_path}\'', 5)
            extracted_text = extract_text_from_pdf(file_path)
            log.success()
    except Exception as e:
        log(f'Error: {e}')
        sys.exit(1)

    # convert text to transactions
    try:
        log.action('Parsing transactions', 5)
        extracted_transactions : List[str] = extract_transactions(extracted_text)
        parsed_transactions : List[Transaction] = parse_transactions(extracted_transactions)
        log.success()
    except Exception as e:
        log('error')
        log(f'\t{e}')
        sys.exit(1)

    # write to stdout if no output file is specified
    try:
        if not args.output:
            log(log.pad('Writing transactions to stdout', 5))
            write_transactions_to_csv(parsed_transactions, sys.stdout)
            sys.exit(0)
    except Exception as e:
        log(f'\n\t{e}')
        sys.exit(1)

    # write to file if output file is specified
    try:
        with open(args.output, 'w', newline = '') as stream:
            log.action(f'Writing transactions to \'{args.output}\'', 5)
            write_transactions_to_csv(parsed_transactions, stream)
            log.success()

            log(f'\n{len(parsed_transactions)} transactions processed.')
            sys.exit(0)
    except Exception as e:
        log('error')
        log(f'\t{e}')
        sys.exit(1)
