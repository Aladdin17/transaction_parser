"""
File: json.py
Author: Christien Alden
Purpose: Strategy pattern to export transactions to simple JSON format
"""
from common.classes import Transaction, Exporter
from typing import List
import json

class JSON(Exporter):
    def export(self, transactions : List[Transaction]) -> str:
        # check if there are transactions to write
        self.log.action(f'Checking that there are transactions to convert')
        if len(transactions) == 0:
            self.log.error('No transactions to write')
            raise
        self.log.success()

        # write transactions to json format
        self.log.action(f'Writing transactions to JSON format')
        transaction_dict = [transaction.to_dict() for transaction in transactions]
        json_string = json.dumps(transaction_dict, indent = 4)
        self.log.success()

        return json_string
