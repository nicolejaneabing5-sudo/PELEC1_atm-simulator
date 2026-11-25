from datetime import datetime, date
import random
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def money(value):
    return Decimal(str(value)).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )


MIN_DEPOSIT = Decimal('500')       # minimum deposit
MIN_WITHDRAWAL = Decimal('100')    # minimum withdrawal
STEP = Decimal('50')               # amounts must be multiples of this (no coins)


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
        self._daily_date = date.today()

    @property
    def balance(self):
        """Controlled read access to the balance."""
        return self._balance

    def _roll_day(self):
        today = date.today()
        if self._daily_date != today:
            self._daily_date = today
            self._daily_withdraw = Decimal('0.00')

    @property
    def withdrawn_today(self):
        self._roll_day()
        return self._daily_withdraw

    def check_balance(self):
        return self._balance

    def validate_amount(self, amount, minimum=None, action='deposit'):
        try:
            amt = money(amount)
        except (InvalidOperation, ValueError, TypeError):
            raise ATMError('Invalid input. Please enter a numeric amount.')

        if not amt.is_finite():
            raise ATMError('Invalid input. Please enter a numeric amount.')

        if amt <= 0:
            raise ATMError('Amount must be greater than zero.')

        # no cents ang dapat madawat
        if amt != amt.to_integral_value():
            if action == 'withdrawal':
                raise ATMError('This ATM dispenses bills only. Please enter a whole peso amount.')
            raise ATMError('Cents are not accepted. Please enter a whole peso amount.')

        # no coins (must be a multiple of STEP)
        if amt % STEP != 0:
            if action == 'withdrawal':
                raise ATMError(
                    f'This ATM dispenses bills only. Please enter an amount '
                    f'in multiples of {peso(STEP)}.'
                )
            raise ATMError(
                f'Coins are not accepted. Please deposit an amount '
                f'in multiples of {peso(STEP)}.'
            )

        if minimum is not None and amt < minimum:
            raise ATMError(f'The minimum amount is {peso(minimum)}.')

        return amt

    # Deposit validation
    def deposit(self, amount):
        amt = self.validate_amount(amount, MIN_DEPOSIT)

        new_balance = self._balance + amt
        self._balance = money(new_balance)

        transaction = Transaction(datetime.now(), 'Deposit', amt, None)
        self.transaction_history.append(transaction)

        return transaction

    # Withdraw validation
    def withdraw(self, amount):
        raise NotImplementedError('Subclasses must implement withdraw().')


class SavingsAccount(Account):
    def __init__(
        self,
        account_number,
        balance,
        max_transaction=Decimal('10000.00'),
        daily_max=Decimal('50000.00'),
        min_remain_balance=Decimal('500.00')
    ):
        super().__init__(account_number, balance, 'Savings Account')

        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.min_remain_balance = money(min_remain_balance)

    def withdraw(self, amount):
        self._roll_day()
        amt = self.validate_amount(amount, MIN_WITHDRAWAL, 'withdrawal')
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
            raise ATMError('Operation results in an invalid balance.')

        self._balance = money(new_balance)
        self._daily_withdraw += amt

        transaction = Transaction(datetime.now(), 'WITHDRAWAL (Saving)', amt, None)
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
        super().__init__(account_number, balance, 'Checking Account')

        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.min_remain_balance = money(min_remain_balance)

    def withdraw(self, amount):
        self._roll_day()
        amt = self.validate_amount(amount, MIN_WITHDRAWAL, 'withdrawal')
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

        transaction = Transaction(datetime.now(), 'WITHDRAWAL (Checking)', amt, None)
        self.transaction_history.append(transaction)

        return transaction