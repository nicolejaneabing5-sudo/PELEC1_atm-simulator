from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .models import ActivityLog
from .oop import sample_accounts as bank
from .oop.domain import ATMError, CheckingAccount, SavingsAccount
from .views import CORRECT_PIN, MAX_ATTEMPTS


# ---------- account rules (no database needed) ----------
class SavingsAccountTests(SimpleTestCase):
    def setUp(self):
        self.acc = SavingsAccount("2222", 100000)

    def test_deposit_adds_to_balance(self):
        self.acc.deposit("500")
        self.assertEqual(self.acc.balance, Decimal("100500.00"))

    def test_deposit_is_recorded_in_history(self):
        self.acc.deposit("500")
        self.assertEqual(len(self.acc.transaction_history), 1)

    def test_rejects_bad_amounts(self):
        for bad in ["0", "-5", "abc", "NaN", "Infinity", None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ATMError):
                    self.acc.deposit(bad)

    def test_per_transaction_limit(self):
        with self.assertRaises(ATMError):
            self.acc.withdraw("10000.01")

    def test_withdraw_exactly_the_limit_is_allowed(self):
        self.acc.withdraw("10000")
        self.assertEqual(self.acc.balance, Decimal("90000.00"))

    def test_daily_limit(self):
        for _ in range(5):                 # 5 x 10,000 = 50,000 (the daily max)
            self.acc.withdraw("10000")
        with self.assertRaises(ATMError):
            self.acc.withdraw("1")

    def test_minimum_balance(self):
        acc = SavingsAccount("3333", 1000)
        with self.assertRaises(ATMError):
            acc.withdraw("500.01")         # would leave less than 500
        acc.withdraw("500")                # leaves exactly 500
        self.assertEqual(acc.balance, Decimal("500.00"))


class CheckingAccountTests(SimpleTestCase):
    def setUp(self):
        self.acc = CheckingAccount("1111", 100000)

    def test_per_transaction_limit(self):
        with self.assertRaises(ATMError):
            self.acc.withdraw("25000.01")

    def test_withdraw_exactly_the_limit_is_allowed(self):
        self.acc.withdraw("25000")
        self.assertEqual(self.acc.balance, Decimal("75000.00"))

    def test_daily_limit(self):
        self.acc.withdraw("25000")
        self.acc.withdraw("25000")
        with self.assertRaises(ATMError):
            self.acc.withdraw("1")

    def test_minimum_balance(self):
        acc = CheckingAccount("4444", 1000)
        with self.assertRaises(ATMError):
            acc.withdraw("600")

    def test_negative_starting_balance_is_rejected(self):
        with self.assertRaises(ATMError):
            CheckingAccount("5555", -1)


# ---------- views (login, transactions, logging) ----------
class ATMViewTests(TestCase):
    def setUp(self):
        # Give every test fresh accounts so tests never affect each other
        # or your real sample data. Keeps the same dictionary keys you already use.
        fresh = {}
        for key, acc in bank.accounts.items():
            cls = SavingsAccount if isinstance(acc, SavingsAccount) else CheckingAccount
            fresh[key] = cls(acc.account_number, 100000)

        for p in (
            patch.dict(bank.accounts, fresh, clear=True),
            patch.object(bank, "history", []),
        ):
            p.start()
            self.addCleanup(p.stop)

        self.checking = next(k for k, a in fresh.items() if isinstance(a, CheckingAccount))
        self.savings = next(k for k, a in fresh.items() if isinstance(a, SavingsAccount))

    def login(self):
        return self.client.post(reverse("atm:verify_pin"), {"pin": CORRECT_PIN})

    def transact(self, account, kind, amount):
        return self.client.post(
            reverse("atm:transact"), {"account": account, "type": kind, "amount": amount}
        )

    # --- PIN ---
    def test_correct_pin_logs_in(self):
        response = self.login()
        self.assertTrue(response.json()["ok"])
        self.assertEqual(self.client.get(reverse("atm:dashboard")).status_code, 200)

    def test_wrong_pin_reduces_attempts(self):
        response = self.client.post(reverse("atm:verify_pin"), {"pin": "0000"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["attempts_left"], MAX_ATTEMPTS - 1)

    def test_pin_locks_after_max_attempts(self):
        for _ in range(MAX_ATTEMPTS):
            self.client.post(reverse("atm:verify_pin"), {"pin": "0000"})
        response = self.login()            # even the correct PIN is refused now
        self.assertEqual(response.status_code, 403)

    # --- protection ---
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("atm:dashboard"))
        self.assertRedirects(response, reverse("atm:pin_entry"))

    def test_transaction_requires_login(self):
        response = self.transact(self.checking, "deposit", "100")
        self.assertEqual(response.status_code, 401)

    def test_lock_session_logs_out(self):
        self.login()
        self.client.get(reverse("atm:lock_session"))
        response = self.client.get(reverse("atm:dashboard"))
        self.assertRedirects(response, reverse("atm:pin_entry"))

    # --- transactions ---
    def test_deposit_updates_balance(self):
        self.login()
        response = self.transact(self.checking, "deposit", "500")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(bank.accounts[self.checking].balance, Decimal("100500.00"))

    def test_withdrawal_updates_balance(self):
        self.login()
        self.transact(self.checking, "withdrawal", "1000")
        self.assertEqual(bank.accounts[self.checking].balance, Decimal("99000.00"))

    def test_insufficient_funds(self):
        self.login()
        response = self.transact(self.checking, "withdrawal", "100000.01")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Insufficient funds", response.json()["message"])

    def test_over_limit_withdrawal_is_rejected(self):
        self.login()
        response = self.transact(self.savings, "withdrawal", "10000.01")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(bank.accounts[self.savings].balance, Decimal("100000.00"))

    def test_junk_amount_is_rejected(self):
        self.login()
        for bad in ["abc", "-5", "0", ""]:
            with self.subTest(amount=bad):
                self.assertEqual(self.transact(self.checking, "deposit", bad).status_code, 400)

    def test_unknown_account_is_rejected(self):
        self.login()
        self.assertEqual(self.transact("nope", "deposit", "100").status_code, 400)

    # --- activity log ---
    def test_successful_deposit_is_logged(self):
        self.login()
        self.transact(self.checking, "deposit", "500")
        entry = ActivityLog.objects.get(action="DEPOSIT")
        self.assertTrue(entry.success)
        self.assertEqual(entry.amount, Decimal("500.00"))

    def test_failed_withdrawal_is_logged(self):
        self.login()
        self.transact(self.checking, "withdrawal", "100000.01")
        entry = ActivityLog.objects.get(action="WITHDRAWAL")
        self.assertFalse(entry.success)