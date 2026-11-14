from datetime import datetime  # to import built-in data
import random


class Account:
    def __init__(self, account_number, balance, account_type, overdraft=False):
        self.account_number = account_number
        self.balance = float(balance)
        self.account_type = account_type
        self.overdraft = overdraft
        self.withdrawn_today = 0.0
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

        # Deposit amount stays positive
        transaction = Transaction(datetime.now(), "Deposit", amount, None)
        self.transaction_history.insert(0, transaction)  # insert(0) puts newest at top

        return self.balance

    # withdraw validation
    def withdraw(self, amount):
        amount = self.validate_amount(amount)

        LIMIT_PER_TX = 25000
        LIMIT_DAILY = 50000
        OVERDRAFT_LIMIT = 500 if self.overdraft else 0

        if amount > LIMIT_PER_TX:
            raise ValueError(f"The limit is ${LIMIT_PER_TX:,.2f} per transaction.")

        if self.withdrawn_today + amount > LIMIT_DAILY:
            remaining = LIMIT_DAILY - self.withdrawn_today
            raise ValueError(f"This exceeds your daily limit. ${remaining:,.2f} remaining.")

        available = self.balance + OVERDRAFT_LIMIT
        if amount > available:
            raise ValueError("Insufficient balance. Withdrawal denied.")

        self.balance -= amount
        self.withdrawn_today += amount

        # FIXED: Stored as negative (-amount) so JS treats it as a withdrawal (red / minus)
        transaction = Transaction(datetime.now(), "Withdrawal", -amount, None)
        self.transaction_history.insert(0, transaction)  # insert(0) puts newest at top

        return self.balance

    # check account balance
    def check_balance(self):
        return self.balance
        
class Transaction:
    def __init__(self, timestamp, type, amount, reference_number):
        self.timestamp = timestamp or datetime.now()
        self.type = type
        self.amount = amount  # Positive for deposit, negative for withdrawal
        self.reference_number = reference_number or random.randint(100000, 999999)