from datetime import datetime # to import built - in data
import random


class Account:
    def __init__(self, account_number, balance, account_type):
        self.account_number = account_number
        self.balance = balance
        self.account_type = account_type
        self.transaction_history = []

    # validate amount
    def validate_amount(self, amount):
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            raise ValueError("Invalid input. Please enter a numeric amount.")

        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        return amount

    # deposit validation
    def deposit(self, amount):
        amount = self.validate_amount(amount)

        self.balance += amount

        transaction = Transaction(datetime.now(), "Deposit", amount, None)

        self.transaction_history.append(transaction)

        return self.balance

    # withdraw validation
    def withdraw(self, amount):
        amount = self.validate_amount(amount)

        if amount > self.balance:
            raise ValueError("Insufficient balance. Withdrawal denied.")

        self.balance -= amount

        transaction = Transaction(datetime.now(), "Withdrawal", amount, None)

        self.transaction_history.append(transaction)

        return self.balance

    # check account balance
    def check_balance(self):
        return self.balance
        
class Transaction:
    def __init__(self, timestamp, type, amount, reference_number):
        self.timestamp = datetime.now()
        self.type = type
        self.amount = amount
        self.reference_number = reference_number or random.randint(100000, 999999)
        