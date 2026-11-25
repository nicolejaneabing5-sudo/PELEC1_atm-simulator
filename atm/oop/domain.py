from datetime import datetime  
import random  
import uuid  
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def money(value):
    return Decimal(str(value)).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )

def peso(value):
    return f'₱{money(value):,.2f}'


class ATMError(Exception):
    """Expected invalid operation; safe to explain to the user."""
    pass


class Transaction:
    def __init__(self, timestamp, type, amount, reference_number):
        self.timestamp = timestamp or datetime.now()
        self.type = type  
        self.amount = money(amount)
        self.reference_number = reference_number or uuid.uuid4().hex[:8].upper()


class Account:
    def __init__(self, account_number, balance, account_type):
        self.account_number = account_number
        self._balance = money(balance)
        self.account_type = account_type  
        if self._balance < 0:
            raise ATMError('Initial balance cannot be negative.')

        self.transaction_history = []
        self._daily_withdraw = Decimal('0.00')

    @property
    def balance(self):
        """Controlled read access to the balance."""
        return self._balance

    @property
    def withdrawn_today(self):
        return self._daily_withdraw

    def check_balance(self):
        return self._balance

    def validate_amount(self, amount):
        try:
            amt = money(amount)
        except (InvalidOperation, ValueError, TypeError):
            raise ATMError(
                'Invalid input. Please enter a numeric amount.'
            )

        if amt <= 0:
            raise ATMError('Amount must be greater than zero.')

        return amt

    def deposit(self, amount):
        amt = self.validate_amount(amount)

        new_balance = self._balance + amt
        self._balance = money(new_balance)

        transaction = Transaction(
            datetime.now(), 'Deposit', amt, None
        )
        self.transaction_history.append(transaction)

        return transaction

    def withdraw(self, amount):
        raise NotImplementedError(
            'Subclasses must implement withdraw().'
        )


class SavingsAccount(Account):
    def __init__(
        self,
        account_number,
        balance,
        max_transaction=Decimal('10000.00'),
        daily_max=Decimal('50000.00'),
        min_remain_balance=Decimal('500.00')
    ):
        super().__init__(
            account_number, balance, 'Savings Account'
        )

        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.min_remain_balance = money(min_remain_balance)

    def withdraw(self, amount):
        amt = self.validate_amount(amount)

        if amt > self.max_transaction:
            raise ATMError(
                f'Transaction limit exceeded. Maximum withdrawal '
                f'per transaction is {peso(self.max_transaction)}.'  
            )

        if self._daily_withdraw + amt > self.daily_max:
            remaining = self.daily_max - self._daily_withdraw
            raise ATMError(
                f'Daily withdrawal limit exceeded. '
                f'Remaining daily limit is {peso(remaining)}.'  
            )

        if self.balance - amt < self.min_remain_balance:
            raise ATMError(
                f'Savings account must maintain a minimum balance '
                f'of {peso(self.min_remain_balance)}.'  
            )

        new_balance = self._balance - amt

        if new_balance < 0:
            raise ATMError(
                'Operation results in an invalid balance.'
            )

        self._balance = money(new_balance)
        self._daily_withdraw += amt

        transaction = Transaction(
            datetime.now(), 'WITHDRAWAL (Saving)', amt, None
        )
        self.transaction_history.append(transaction)

        return transaction


class CheckingAccount(Account):
    def __init__(
        self,
        account_number,
        balance,
        max_transaction=Decimal('25000.00'),
        daily_max=Decimal('50000.00'),
        min_remain_balance=Decimal('500.00') 
    ):
        super().__init__(
            account_number, balance, 'Checking Account'
        )

        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.min_remain_balance = money(min_remain_balance)  

    def withdraw(self, amount):
        amt = self.validate_amount(amount)

        if amt > self.max_transaction:
            raise ATMError(
                f'Transaction limit exceeded. Maximum withdrawal '
                f'per transaction is {peso(self.max_transaction)}.'
            )

        if self._daily_withdraw + amt > self.daily_max:
            remaining = self.daily_max - self._daily_withdraw
            raise ATMError(
                f'Daily withdrawal limit exceeded. '
                f'Remaining daily limit is {peso(remaining)}.'
            )

        if self.balance - amt < self.min_remain_balance:
            raise ATMError(
                f'Checking account must maintain a minimum balance '
                f'of {peso(self.min_remain_balance)}.'
            )

        new_balance = self._balance - amt

        self._balance = money(new_balance)
        self._daily_withdraw += amt

        transaction = Transaction(
            datetime.now(), 'WITHDRAWAL (Checking)', amt, None
        )
        self.transaction_history.append(transaction)

        return transaction

    