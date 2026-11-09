from datetime import datetime # to import built - in data
import random # to import random numbers for reference number
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

def money(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class ATMError(Exception):
    """Expected invalif operation; safe to explain to the user."""

class Transaction:
    def __init__(self, timestamp, type, amount, reference_number):
        self.timestamp = timestamp or datetime.now()
        self.type = type # it stores the two transaction type (Deposit or Withdrawal)
        self.amount = money(amount)
        self.reference_number = reference_number or str(random.randint(100000, 999999))

class Account:
    def __init__(self, account_number, balance, account_type):
        self.account_number = account_number
        self.balance = money(balance)
        self.account_type = account_type # stores the account type (Savings or Checkings)
        if self.__balance < 0:
            raise ATMError("Initial balance cannot be negative.")
        self.transaction_history = []
        
    @property
    def balance(self):
        """Controlled read access to the balance."""
        return self.balance

    # validate amount
    def validate_amount(self, amount):
        try:
            amount = money(amount)
        except (InvalidOperation, ValueError, TypeError):
            raise ATMError("Invalid input. Please enter a numeric amount.")

        if amount <= 0:
            raise ATMError("Amount must be greater than zero.")

        return amount

    # deposit validation
    def deposit(self, amount):
        amount = self.validate_amount(amount)

        # Balance update happens safely after validation passes
        self.__balance = money(self.__balance + amount)

        transaction = Transaction(datetime.now(), "Deposit", amount, None)

        self.transaction_history.append(transaction)

        return self.__balancebalance

    # withdraw validation
    def withdraw(self, amount):
        amount = self.validate_amount(amount)

        if amount > self.__balance:
            raise ATMError("Insufficient balance. Withdrawal denied.")

        self.__balance = money(self.__balance - amount)

        transaction = Transaction(datetime.now(), "Withdrawal", amount, None)

        self.transaction_history.append(transaction)

        return self.__balance

    # check account balance
    def check_balance(self):
        return self.__balance
        

        