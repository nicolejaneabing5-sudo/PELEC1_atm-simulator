from decimal import Decimal
from django.test import SimpleTestCase
from atm.oop.domain import Account, SavingsAccount, CheckingAccount, ATMError, money


class TestAccountBase(SimpleTestCase):

    def setUp(self):
        # create a concrete subclass of Account for testing base methods
        class ConcreteAccount(Account):
            def withdraw(self, amount):
                amt = self.validate_amount(amount)
                new_balance = self._balance - amt
                if new_balance < 0:
                    raise ATMError('Insufficient funds.')
                self._balance = money(new_balance)
                return self._balance

        self.account = ConcreteAccount("1234", Decimal("5000.00"), "Standard")

    def test_initial_balance(self):
        self.assertEqual(self.account.check_balance(), Decimal('5000.00'))

    def test_valid_deposit(self):
        self.account.deposit(Decimal("1000.00"))
        self.assertEqual(self.account.check_balance(), Decimal('6000.00'))

    def test_valid_withdrawal(self):
        self.account.withdraw(Decimal("500.00"))
        self.assertEqual(self.account.check_balance(), Decimal('4500.00'))

    def test_zero_or_negative_deposit_rejection(self):
        with self.assertRaises(ATMError):
            self.account.deposit(Decimal("0.00"))
        with self.assertRaises(ATMError):
            self.account.deposit(Decimal("-100.00"))

    def test_zero_or_negative_withdrawal_rejection(self):
        with self.assertRaises(ATMError):
            self.account.withdraw(Decimal("0.00"))
        with self.assertRaises(ATMError):
            self.account.withdraw(Decimal("-100.00"))

    def test_balance_unchanged_after_failed_withdrawal(self):
        initial_balance = self.account.check_balance()
        with self.assertRaises(ATMError):
            self.account.withdraw(Decimal("6000.00"))
        self.assertEqual(self.account.check_balance(), initial_balance)


class TestSavingsAccountRules(SimpleTestCase):

    def setUp(self):
        self.account = SavingsAccount("9017", Decimal("20000.00"))

    def test_savings_per_transaction_limit(self):
        with self.assertRaises(ATMError):
            self.account.withdraw(Decimal("15000.00"))

    def test_savings_minimum_balance_rule(self):
        account = SavingsAccount("9017", Decimal("1260.00"))
        with self.assertRaises(ATMError):
            account.withdraw(Decimal("1000.00"))

    def test_savings_valid_withdrawal(self):
        self.account.withdraw(Decimal("5000.00"))
        self.assertEqual(self.account.check_balance(), Decimal('15000.00'))

    def test_savings_daily_limit(self):
        account = SavingsAccount("9017", Decimal("100000.00"))
        for _ in range(5):
            account.withdraw(Decimal("10000.00"))

        with self.assertRaises(ATMError):
            account.withdraw(Decimal("10000.00"))


class TestCheckingAccountRules(SimpleTestCase):

    def setUp(self):
        self.account = CheckingAccount("4821", Decimal("20000.00"))

    def test_checking_per_transaction_limit(self):
        with self.assertRaises(ATMError):
            self.account.withdraw(Decimal("30000.00"))

    # CHANGED: replaces the old overdraft tests. Your domain.py now uses a
    # P500 minimum balance instead of overdraft protection.
    def test_checking_minimum_balance_rule(self):
        account = CheckingAccount("4821", Decimal("1000.00"))
        with self.assertRaises(ATMError):
            account.withdraw(Decimal("600.00"))   # would leave P400 (< P500)
        self.assertEqual(account.check_balance(), Decimal('1000.00'))

    def test_checking_can_withdraw_down_to_minimum(self):
        account = CheckingAccount("4821", Decimal("1000.00"))
        account.withdraw(Decimal("500.00"))       # leaves exactly P500
        self.assertEqual(account.check_balance(), Decimal('500.00'))

    def test_checking_daily_limit(self):
        account = CheckingAccount("4821", Decimal("100000.00"))
        for _ in range(2):
            account.withdraw(Decimal("25000.00"))
        with self.assertRaises(ATMError):
            account.withdraw(Decimal("1000.00"))
            
class TestWithdrawalValidation(SimpleTestCase):

    def setUp(self):
        self.savings = SavingsAccount("9017", Decimal("20000.00"))
        self.checking = CheckingAccount("4821", Decimal("20000.00"))

    def test_valid_withdrawal_amounts(self):
        for amount in ["100", "200", "500", "600", "1000"]:
            account = SavingsAccount("9017", Decimal("20000.00"))
            initial_balance = account.check_balance()

            account.withdraw(Decimal(amount))

            self.assertEqual(
                account.check_balance(),
                initial_balance - Decimal(amount)
            )

    def test_invalid_withdrawal_amounts(self):
        for amount in ["50", "250", "1050"]:
            account = SavingsAccount("9017", Decimal("20000.00"))
            with self.assertRaises(ATMError):
                account.withdraw(Decimal(amount))

    def test_checking_invalid_withdrawal(self):
        with self.assertRaises(ATMError):
            self.checking.withdraw(Decimal("1050"))

    def test_minimum_withdrawal(self):
        with self.assertRaises(ATMError):
            self.savings.withdraw(Decimal("50"))