"""
File: classes.py
Author: Christien Alden
Purpose: Define classes for transactions
"""
from abc import ABC, abstractmethod
from common.log import Log
from datetime import datetime
from typing import List

class Transaction:
    def __init__(
        self,
        processing_date : datetime = None,
        transaction_date : datetime = None,
        narration : str = None,
        amount : float = None,
        balance : float = None
    ):
        self.processing_date = processing_date
        self.transaction_date = transaction_date
        self.narration = narration
        self.amount = amount
        self.balance = balance

    def to_dict(self) -> dict:
        return {
            'processing_date': self.processing_date.strftime('%Y-%m-%d') if self.processing_date else None,
            'transaction_date': self.transaction_date.strftime('%Y-%m-%d') if self.transaction_date else None,
            'narration': self.narration,
            'amount': self.amount,
            'balance': self.balance
        }

    def __str__(self) -> str:
        return (
            f'{self.processing_date}, '
            f'{self.transaction_date}, '
            f'{self.narration}, '
            f'{self.amount}, '
            f'{self.balance}'
        )

    def __repr__(self) -> str:
        return (
            'Transaction('
            f'processing_date={self.processing_date!r}, '
            f'transaction_date={self.transaction_date!r}, '
            f'narration={self.narration!r}, '
            f'amount={self.amount!r}, '
            f'balance={self.balance!r}'
            ')'
        )

class Importer(ABC):
    def __init__(self, logger : Log):
        self.log = logger

    def __str__(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def extract(self, file_path) -> List[Transaction]:
        pass

class Exporter(ABC):
    def __init__(self, logger : Log) -> None:
        self.log = logger

    def __str__(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def export(self, transactions : List[Transaction]) -> str:
        pass
