from decimal import Decimal
from atm.oop.domain import CheckingAccount, SavingsAccount

def _row(title, date, ref, acct, short, last4, kind, amount, after):
    sign = "+" if kind == "in" else "-"
    return {"title": title, "date": date, "ref": ref, "account": acct, "short": short,
            "last4": last4, "kind": kind, "type": "Deposit" if kind == "in" else "Withdrawal",
            "signed": f"{sign}₱{amount:,.2f}", "after": f"₱{after:,.2f}"}

history = [
    _row("Cash deposit", "Apr 18, 2025", "ABC-100001", "Checking Account", "Checking", "4821", "in", 480, 10000),
    # add more seed rows as needed
]