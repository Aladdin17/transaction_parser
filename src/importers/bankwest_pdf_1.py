"""
File: bankwest_pdf_1.py
Author: Christien Alden
Purpose: Strategy pattern to scrape transactions from Bankwest PDF statement
Details:
    - Valid Statement Ranges: ?? to ??
"""
from common.classes import Transaction, Importer
from datetime import datetime
from pypdf import PdfReader
from typing import List, Tuple
import re

def extract_text_from_pdf(file):
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
    new_transaction.processing_date = convert_to_date(date_match.group('day'), date_match.group('month'), date_match.group('year'))

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
    new_transaction.narration = whole_match.group('description')
    new_transaction.balance = strip_dollar_sign(whole_match.group('balance'))
    new_transaction.amount = strip_dollar_sign(whole_match.group('amount'))

    # invert the amount if it is a debit
    if new_transaction.balance < balance:
        new_transaction.amount *= -1.0

    return new_transaction, new_transaction.balance

def parse_multi_line_transaction(transaction1 : str, transaction2 : str, balance : float) -> Tuple[Transaction, float]:
    new_transaction = Transaction()
    date_regex = r'(?P<day>\d{2}) (?P<month>\w{3}) (?P<year>\d{2})'
    date_match = re.match(date_regex, transaction1)
    new_transaction.processing_date = convert_to_date(date_match.group('day'), date_match.group('month'), date_match.group('year'))

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
    new_transaction.narration = whole_match1.group('description') + ' ' + whole_match2.group('description')
    new_transaction.balance = strip_dollar_sign(whole_match2.group('balance'))
    new_transaction.amount = strip_dollar_sign(whole_match1.group('amount'))

    # invert the amount if it is a debit
    if new_transaction.balance < balance:
        new_transaction.amount *= -1.0

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

class BankwestPDF1(Importer):
    def extract(self, file_path) -> List[Transaction]:
        # validate file extension
        self.log.action(f'Validating file extension', 5)
        if not file_path.lower().endswith('.pdf'):
            self.log.error('File must have a PDF extension')
            raise
        self.log.success()

        # extract text and parse it into transactions
        self.log.action(f'Extracting text from file', 5)
        try:
            with open(file_path, 'rb') as file:
                extracted_text = extract_text_from_pdf(file)
                self.log.success()
        except Exception as error:
            self.log.error(error)
            raise

        # convert text to transactions
        self.log.action('Parsing transactions', 5)
        extracted_transactions : List[str] = extract_transactions(extracted_text)
        parsed_transactions : List[Transaction] = parse_transactions(extracted_transactions)
        self.log.success()

        self.log(f'{len(parsed_transactions)} transactions imported')
        return parsed_transactions
