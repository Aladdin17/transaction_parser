"""
File: csv.py
Author: Christien Alden
Purpose: Strategy pattern to export transactions to simple CSV format
"""
from common.classes import Transaction, Exporter
from typing import List
import csv
import io

class CSV(Exporter):
    def export(self, transactions : List[Transaction]) -> str:
        # check if there are transactions to write
        self.log.action(f'Checking that there are transactions to convert')
        if len(transactions) == 0:
            self.log.error('No transactions to write')
            raise
        self.log.success()

        # write transactions to csv format
        self.log.action(f'Writing transactions to CSV format')
        output = io.StringIO()
        writer = csv.writer(output, lineterminator = '\n')
        writer.writerow(['processing_date', 'transaction_date', 'narration', 'amount', 'balance'])

        for transaction in transactions:
            writer.writerow([
                transaction.processing_date.strftime('%Y-%m-%d') if transaction.processing_date else None,
                transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else None,
                transaction.narration,
                transaction.amount,
                transaction.balance
            ])

        csv_string = output.getvalue()
        output.close()
        self.log.success()

        return csv_string
