from datetime import datetime  # to import built-in date and time
import random  # to import random numbers for reference number
import uuid  # CHANGED: added, for collision-safe reference numbers
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def money(value):
    return Decimal(str(value)).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )


# CHANGED: new helper so error messages show ₱25,000.00 like the UI
def peso(value):
    return f'₱{money(value):,.2f}'


class ATMError(Exception):
    """Expected invalid operation; safe to explain to the user."""
    pass


class Transaction:
    def __init__(self, timestamp, type, amount, reference_number):
        self.timestamp = timestamp or datetime.now()
        self.type = type  # stores the transaction type (Deposit or Withdrawal)
        self.amount = money(amount)
        # CHANGED: uuid instead of random.randint, so references can't collide
        self.reference_number = reference_number or uuid.uuid4().hex[:8].upper()


class Account:
    min_deposit = Decimal('500.00')
    
    def __init__(self, account_number, balance, account_type):
        self.account_number = account_number
        self._balance = money(balance)
        self.account_type = account_type  # stores the account type
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

    # Check account balance
    def check_balance(self):
        return self._balance

    # Validate amount
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
    
    # Validate withdrawal amount
    def validate_withdrawal_amount(self, amount):
        amt = self.validate_amount(amount)

        if amt < Decimal('100.00'):
            raise ATMError(
                'Minimum withdrawal amount is ₱100.00.'
            )

        if amt % Decimal('100.00') != Decimal('0.00'):
            raise ATMError(
                'Invalid withdrawal amount. ATM only dispenses '
                '₱100, ₱500, and ₱1,000 bills.'
            )

        return amt

    # Deposit validation
    def deposit(self, amount):
        amt = self.validate_amount(amount)
        
        if amt < money(self.min_deposit):
            raise ATMError(f'Minimum deposit amount is {peso(self.min_deposit)}.')

        # Balance update happens safely after validation passes
        new_balance = self._balance + amt
        self._balance = money(new_balance)

        transaction = Transaction(
            datetime.now(), 'Deposit', amt, None
        )
        self.transaction_history.append(transaction)

        return transaction

    # Withdraw validation
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
        amt = self.validate_withdrawal_amount(amount)

        # Check per-transaction limit (10 000)
        if amt > self.max_transaction:
            raise ATMError(
                f'Transaction limit exceeded. Maximum withdrawal '
                f'per transaction is {peso(self.max_transaction)}.'  # CHANGED
            )

        # Check cumulative daily maximum limit (50 000)
        if self._daily_withdraw + amt > self.daily_max:
            remaining = self.daily_max - self._daily_withdraw
            raise ATMError(
                f'Daily withdrawal limit exceeded. '
                f'Remaining daily limit is {peso(remaining)}.'  # CHANGED
            )

        # Check minimum remaining balance rule (500)
        if self.balance - amt < self.min_remain_balance:
            raise ATMError(
                f'Savings account must maintain a minimum balance '
                f'of {peso(self.min_remain_balance)}.'  # CHANGED
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
        min_remain_balance=Decimal('500.00')  # CHANGED: was overdraft_protection
    ):
        super().__init__(
            account_number, balance, 'Checking Account'
        )

        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.min_remain_balance = money(min_remain_balance)  # CHANGED

    def withdraw(self, amount):
        amt = self.validate_withdrawal_amount(amount)

        # Check per-transaction limit (25 000)
        if amt > self.max_transaction:
            raise ATMError(
                f'Transaction limit exceeded. Maximum withdrawal '
                f'per transaction is {peso(self.max_transaction)}.'
            )

        # Check cumulative daily maximum limit (50 000)
        if self._daily_withdraw + amt > self.daily_max:
            remaining = self.daily_max - self._daily_withdraw
            raise ATMError(
                f'Daily withdrawal limit exceeded. '
                f'Remaining daily limit is {peso(remaining)}.'
            )

        # CHANGED: minimum remaining balance rule (500), replaces the overdraft checks
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

    