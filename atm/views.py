from django.shortcuts import render
from django.http import JsonResponse
import json
from .oop.domain import Account

# In-memory account storage for the simulator
accounts_db = {
    "checking": Account("4821", 8240.50, "Checking", overdraft=True),
    "savings": Account("9017", 12860.22, "Savings", overdraft=False)
}

def card_insert(request):
    """Renders the ATM card insertion introductory screen."""
    return render(request, "atm/card_insert.html")

def pin_entry(request):
    """Renders the initial PIN entry page"""
    return render(request, "atm/pin_entry.html")

def dashboard(request):
    """Renders the main ATM dashboard"""
    return render(request, "atm/dashboard.html")

def process_transaction(request):
    """Handles deposits and withdrawals using domain.py logic"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            acc_key = data.get("account")
            tx_type = data.get("type")
            amount = data.get("amount")

            account = accounts_db.get(acc_key)
            if not account:
                return JsonResponse({"error": "Account not found."}, status=400)

            if tx_type == "deposit":
                account.deposit(amount)
            elif tx_type == "withdrawal":
                account.withdraw(amount)
            else:
                return JsonResponse({"error": "Invalid transaction type."}, status=400)

            total_balance = sum(acc.balance for acc in accounts_db.values())

            all_transactions = []
            for key, acc in accounts_db.items():
                for tx in acc.transaction_history:
                    all_transactions.append({
                        "title": tx.type,
                        "date": tx.timestamp.strftime("%b %d, %Y"),
                        "account": "Checking" if key == "checking" else "Savings",
                        "amount": tx.amount
                    })

            return JsonResponse({
                "message": f"{'Deposited' if tx_type == 'deposit' else 'Withdrew'} ${float(amount):,.2f} successfully.",
                "total_balance": total_balance,
                "accounts": {
                    "checking": {"balance": accounts_db["checking"].balance, "withdrawn": accounts_db["checking"].withdrawn_today},
                    "savings": {"balance": accounts_db["savings"].balance, "withdrawn": accounts_db["savings"].withdrawn_today}
                },
                "transactions": all_transactions
            })

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)