import json
from pathlib import Path
from decimal import Decimal
from atm.oop.domain import CheckingAccount, SavingsAccount

DATA_FILE = Path(__file__).resolve().parent.parent / "static" / "js" / "initial_data.json"

# CHANGED: starting balances are lower, so that AFTER the seed transactions below,
# checking = ₱8,240.50 and savings = ₱12,860.22 (matches your dashboard)
'''checking_account = CheckingAccount("4821", 5410.50)
savings_account = SavingsAccount("9017", 12110.22)'''

# initial_data.json
# DATA_FILE = Path(__file__).with_name("initial_data.json")


'''accounts = {
    "checking": checking_account,
    "savings": savings_account
}'''

# the keys used in the JSON ("checking", "savings") -> the class that handles them
# ACCOUNT_CLASSES = {
#     "checking": CheckingAccount,
#     "savings": SavingsAccount,
# }

history = []

def _peso(value):
    return f"₱{value:,.2f}"

def _load_raw_data():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Initial data file not found: {DATA_FILE}")
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)

_raw_data = _load_raw_data()

USER_NAME = _raw_data["user"]["full_name"]
PIN = str(_raw_data["user"]["pin"])

_checking_cfg = _raw_data["accounts"]["checking"]
_checking_limits = _checking_cfg["limits"]

_savings_cfg = _raw_data["accounts"]["savings"]
_savings_limits = _savings_cfg["limits"]

checking_account = CheckingAccount(
    account_number=_checking_cfg["account_number"],
    balance=Decimal(str(_checking_cfg["balance"])),
    max_transaction=Decimal(str(_checking_limits["max_transaction"])),
    daily_max=Decimal(str(_checking_limits["daily_max"])),
    min_remain_balance=Decimal(str(_checking_limits.get("min_remain_balance", _checking_limits.get("overdraft_protection", "500.00")))),
)

savings_account = SavingsAccount(
    account_number=_savings_cfg["account_number"],
    balance=Decimal(str(_savings_cfg["balance"])),
    max_transaction=Decimal(str(_savings_limits["max_transaction"])),
    daily_max=Decimal(str(_savings_limits["daily_max"])),
    min_remain_balance=Decimal(str(_savings_limits["min_remain_balance"])),
)

accounts = {
    "checking": checking_account,
    "savings": savings_account
}

def _build_history_from_json(raw_transactions, account_map):
    """
    Converts JSON transaction entries into template-ready rows.
    Computes running 'after' balances from oldest to newest so each row reflects
    the balance right after that historical transaction occurred.
    """
    running_balances = {
        key: acc.balance for key, acc in account_map.items()
    }

    # Walk newest-to-oldest to reverse-calculate pre-transaction balances
    reversed_rows = []
    for tx in raw_transactions:
        acc_key = tx["account"]
        acc = account_map[acc_key]
        tx_type = tx["type"]
        amount = Decimal(str(tx["amount"]))
        is_in = tx_type == "deposit"

        after_balance = running_balances[acc_key]
        sign = "+" if is_in else "-"

        reversed_rows.append({
            "title": tx["title"],
            "date": tx["date"],
            "ref": tx["reference"],
            "account": acc.account_type,
            "short": acc.account_type.split()[0],
            "last4": acc.account_number,
            "kind": "in" if is_in else "out",
            "type": "Deposit" if is_in else "Withdrawal",
            "signed": f"{sign}{_peso(amount)}",
            "after": _peso(after_balance),
            "_raw": {
                "title": tx["title"],
                "date": tx["date"],
                "account": acc_key,
                "type": tx_type,
                "amount": float(amount),
                "reference": tx["reference"],
            },
        })

        # Step backward to find the balance before this transaction
        if is_in:
            running_balances[acc_key] = after_balance - amount
        else:
            running_balances[acc_key] = after_balance + amount

    return reversed_rows

history = _build_history_from_json(_raw_data.get("transactions", []), accounts)

def record_transaction(acc_key, title, date_str, tx_type, amount, reference):
    """Prepends a new transaction row to `history` and mirrors it in raw JSON data."""
    acc = accounts[acc_key]
    amt = Decimal(str(amount))
    is_in = tx_type == "deposit"
    sign = "+" if is_in else "-"

    row = {
        "title": title,
        "date": date_str,
        "ref": reference,
        "account": acc.account_type,
        "short": acc.account_type.split()[0],
        "last4": acc.account_number,
        "kind": "in" if is_in else "out",
        "type": "Deposit" if is_in else "Withdrawal",
        "signed": f"{sign}{_peso(amt)}",
        "after": _peso(acc.balance),
        "_raw": {
            "title": title,
            "date": date_str,
            "account": acc_key,
            "type": tx_type,
            "amount": float(amt),
            "reference": reference,
        },
    }
    history.insert(0, row)
    return row


def save_data():
    """Writes current account balances and transactions back to initial_data.json."""
    _raw_data["user"]["full_name"] = USER_NAME
    _raw_data["user"]["pin"] = PIN

    _raw_data["accounts"]["checking"]["balance"] = float(checking_account.balance)
    _raw_data["accounts"]["savings"]["balance"] = float(savings_account.balance)

    _raw_data["transactions"] = [
        item.get("_raw")
        for item in history
        if item.get("_raw") is not None
    ]

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(_raw_data, file, indent=2)

# ---------- new ---------
# def _load():
#     with open(DATA_FILE, encoding="utf-8") as file:
#         return json.load(file)

# data = _load()

# accounts = {}
# for key, info in data["accounts"].items():
#     account_class = ACCOUNT_CLASSES.get(key)
#     if account_class is None:
#         raise ValueError(f'initial_data.json: unknown account "{key}". Use: {list(ACCOUNT_CLASSES)}')
#     accounts[key] = account_class(info["account_number"], info["balance"], **info.get("limits", {}))

def _log(acc, tx, title, kind):
    """Record a finished transaction in the format tx_row.html expects."""
    is_in = kind == "in"
    history.insert(0, {
        "title": title,
        "date": tx.timestamp.strftime("%b %d, %Y"),
        "ref": f"ABC-{tx.reference_number}",
        "account": acc.account_type,
        "short": acc.account_type.split()[0],
        "last4": acc.account_number,
        "kind": kind,
        "type": "Deposit" if is_in else "Withdrawal",
        "signed": ("+" if is_in else "-") + _peso(tx.amount),
        "after": _peso(acc.balance),
    })


# seed transaction history (oldest first, so the newest ends up on top)
'''_log(checking_account, checking_account.deposit(2450.00), "Payroll deposit", "in")
_log(checking_account, checking_account.withdraw(100.00), "ATM withdrawal", "out")
_log(savings_account, savings_account.deposit(750.00), "Monthly savings", "in")
_log(checking_account, checking_account.deposit(480.00), "Cash deposit", "in")

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
]'''

def get_payload():
    return {
        "user": USER_NAME,
        "accounts": {
            "checking": {
                "account_number": checking_account.account_number,
                "balance": float(checking_account.check_balance()),
                "type": checking_account.account_type,
                "withdrawn_today": float(checking_account.withdrawn_today),
                "remaining_daily": float(checking_account.daily_max - checking_account.withdrawn_today),
            },
            "savings": {
                "account_number": savings_account.account_number,
                "balance": float(savings_account.check_balance()),
                "type": savings_account.account_type,
                "withdrawn_today": float(savings_account.withdrawn_today),
                "remaining_daily": float(savings_account.daily_max - savings_account.withdrawn_today),
            },
        },
        "transactions": _raw_data.get("transactions", []),
    }
