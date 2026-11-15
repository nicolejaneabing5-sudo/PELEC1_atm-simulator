from decimal import Decimal
from atm.oop.domain import CheckingAccount, SavingsAccount

# instantiate accounts
checking_account = CheckingAccount("4821", 8240.50)
savings_account = SavingsAccount("9017", 12860.22)

# seed transaction history
checking_account.deposit(2450.00)
checking_account.withdraw(100.00)
savings_account.deposit(750.00)
checking_account.deposit(480.00)

accounts = {
    "checking": checking_account,
    "savings": savings_account
}

transactions = [
    {
        "type": "Deposit",
        "title": "Payroll deposit",
        "account": "Checking Account",
        "amount": 2450.00,
        "date": "Apr 24, 2025"
    },
    {
        "type": "Withdrawal",
        "title": "ATM withdrawal",
        "account": "Checking Account",
        "amount": -100.00,
        "date": "Apr 22, 2025"
    },
    {
        "type": "Deposit",
        "title": "Monthly savings",
        "account": "Savings Account",
        "amount": 750.00,
        "date": "Apr 21, 2025"
    },
    {
        "type": "Deposit",
        "title": "Cash deposit",
        "account": "Checking Account",
        "amount": 480.00,
        "date": "Apr 18, 2025"
    }
]

def get_payload():
    return {
        "user": "Jordan Davis",
        "accounts": {
            "checking": {
                "account_number": checking_account.account_number,
                "balance": float(checking_account.check_balance()),
                "type": checking_account.account_type
            },
            "savings": {
                "account_number": savings_account.account_number,
                "balance": float(savings_account.check_balance()),
                "type": savings_account.account_type
            }
        },
        "transactions": transactions
    }