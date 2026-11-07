from datetime import datetime # to import built - in data
import random


class Account:
    def __init__(self, account_number, balance, account_type):
        self.account_number = account_number
        self.balance = balance
        self.account_type = account_type
        self.transaction_history = []
        
class Transaction:
    def __init__(self, timestamp, type, amount, reference_number):
        self.timestamp = datetime.now()
        self.type = type
        self.amount = amount
        self.reference_number = reference_number or random.randint
        