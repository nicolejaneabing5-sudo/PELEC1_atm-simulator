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
        self._balance = money(balance)
        self.account_type = account_type # stores the account type (Savings or Checkings)
        if self._balance < 0:
            raise ATMError('Initial balance cannot be negative.')
        self.transaction_history = []
        
    @property
    def balance(self):
        """Controlled read access to the balance."""
        return self._balance
    
    # check account balance
    def check_balance(self):
        return self._balance

    # validate amount
    def validate_amount(self, amount):
        try:
            amt = money(amount)
        except (InvalidOperation, ValueError, TypeError):
            raise ATMError('Invalid input. Please enter a numeric amount.')

        if amt <= 0:
            raise ATMError('Amount must be greater than zero.')
        return amt

    # deposit validation
    def deposit(self, amount):
        amt = self.validate_amount(amount)

        # Balance update happens safely after validation passes
        new_balance = self._balance + amt
        self._balance = money(new_balance)

        transaction = Transaction(datetime.now(), 'Deposit', amt, None)
        self.transaction_history.append(transaction)
        return transaction

    # withdraw validation
    def withdraw(self, amount):
            raise NotImplementedError('Subclasses must implement withdraw().')
    
class SavingsAccount(Account):
    def __init__(self, account_number, balance, max_transaction=Decimal('10000.00'), daily_max=Decimal('50000.00'), min_remain_balance=Decimal('500.00')):
        super().__init__(account_number, balance, 'Savings Account')
        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.min_remain_balance = money(min_remain_balance)
        self.__daily_withdraw = Decimal('0.00')
        
    def withdraw(self, amount):
        amt = self.validate_amount(amount)
            
        # Check per-transaction limit (10 000)
        if amt > self.max_transaction:
            raise ATMError(f'Transaction limit exceeded. Maximum withdrawal per transaction is ${self.max_transaction}.')
        
        # Check cumulative daily maximum limit (50 000)
        if (self.__daily_withdraw + amt) > self.daily_max:
            raise ATMError(f'Daily withdrawal limit exceeded.Remaining daily limit is ${self.daily_max - self.__daily_withdraw}.')
        
        # Check minimum remaining balance rule (500)
        if (self.balance - amt) < self.min_remain_balance:
            raise ATMError(f'Savings accout must maintain a minimum balance of ${self.min_remain_balance}')
        
        new_balance = self._balance - amt
        if new_balance < 0:
            raise ATMError('Operation results is an invalid balance.')
        
        self._balance = money(new_balance)
        self.__daily_withdraw += amt
        transaction  = Transaction(datetime.now(), 'WITHDRAWAL (Saving)', amt, None)
        self.transaction_history.append(transaction)
        return transaction
        
class CheckingAccount(Account):
    def __init__(self, account_number, balance, max_transaction=Decimal('25000.00'), daily_max=Decimal('50000.00'), overdraft_protection=Decimal('500')):
        super().__init__(account_number, balance, 'Checking Account')
        self.max_transaction = money(max_transaction)
        self.daily_max = money(daily_max)
        self.overdraft_protection = money(overdraft_protection)
        self.__daily_withdraw = Decimal('0.00')
        
    def withdraw(self, amount):
        amt = self.validate_amount(amount)
        
        # Check per-transaction limit (25 000)
        if amt > self.max_transaction:
            raise ATMError(f'Transaction limit exceeded. Maximum withdrawal per transaction is ${self.max_transaction}.')
        
        # Check cumulative daily maximum limit (50 000)
        if (self.__daily_withdraw + amt) > self.daily_max:
            raise ATMError(f'Daily withdrawal limit exceeded.Remaining daily limit is ${self.daily_max - self.__daily_withdraw}.')
        
        # Check overdraft protection limit
        max_allowed = self.balance + self.overdraft_protection
        if amt > max_allowed:
            raise ATMError(f'Overdraft limit exceeded in an invalid balance exceeding overdraft.')
        
        new_balance = self._balance - amt
        if new_balance < -self.overdraft_protection:
            raise ATMError('Operation results in an invalid balance exceeding overdraft.')
        
        self._balance = money(new_balance)
        self.__daily_withdraw += amt
        transaction  = Transaction(datetime.now(), 'WITHDRAWAL (Checking)', amt, None)
        self.transaction_history.append(transaction)
        return transaction


        

        