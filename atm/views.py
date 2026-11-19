from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from .oop import sample_accounts as bank
from .oop.domain import ATMError

CORRECT_PIN = bank.PIN
MAX_ATTEMPTS = 4
RECENT_COUNT = 5
USER_NAME = bank.USER_NAME


def peso(value):
    return f"₱{value:,.2f}"


def account_state(acc):
    """Everything the page shows for one account, already formatted as text."""
    remaining = acc.daily_max - acc.withdrawn_today
    min_balance = getattr(acc, "min_remain_balance", None)
    return {
        "name": acc.account_type,
        "last4": acc.account_number,
        "max_transaction": peso(acc.max_transaction),
        "daily_max": peso(acc.daily_max),
        "min_remain_balance": peso(min_balance) if min_balance is not None else None,
        "balance": peso(acc.balance),
        "withdrawn": peso(acc.withdrawn_today),
        "meter": float(acc.withdrawn_today / acc.daily_max * 100),
        "limits": f"Withdrawn today: {peso(acc.withdrawn_today)} • {peso(remaining)} remaining",
    }


def total_balance():
    return peso(sum(a.balance for a in bank.accounts.values()))


def history_label():
    n = len(bank.history)
    return f"{n} transaction{'' if n == 1 else 's'} across checking and savings"


# ---------- PIN page ----------
def pin_state(request):
    return {
        "pin": bank.PIN,
        "attempts_left": request.session.get("attempts_left", MAX_ATTEMPTS),
        "locked": request.session.get("pin_locked", False),
    }

def pin_entry(request):
    return render(request, "atm/pin_entry.html", pin_state(request))


@require_POST
def verify_pin(request):
    state = pin_state(request)
    if state["locked"]:
        return JsonResponse(
            {"ok": False, "locked": True, "attempts_left": 0, "message": "PIN locked."},
            status=403,
        )

    if request.POST.get("pin") == CORRECT_PIN:
        request.session["attempts_left"] = MAX_ATTEMPTS
        request.session["authenticated"] = True
        return JsonResponse({"ok": True, "redirect": reverse("atm:dashboard")})

    left = state["attempts_left"] - 1
    request.session["attempts_left"] = left
    request.session["pin_locked"] = left <= 0
    return JsonResponse(
        {
            "ok": False,
            "locked": left <= 0,
            "attempts_left": left,
            "message": f"Incorrect PIN. {left} attempt{'' if left == 1 else 's'} remaining.",
        },
        status=400,
    )


@require_POST
def unlock_pin(request):
    request.session["attempts_left"] = MAX_ATTEMPTS
    request.session["pin_locked"] = False
    return JsonResponse({"ok": True, "attempts_left": MAX_ATTEMPTS})


# ---------- dashboard ----------
def dashboard(request):
    if not request.session.get("authenticated"):
        return redirect("atm:pin_entry")

    user_name = bank.USER_NAME
    parts = user_name.split()
    initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else parts[0][:2].upper()

    return render(
        request,
        "atm/dashboard.html",
        {
            "user_name": user_name,
            "first_name": parts[0],
            "initials": initials,
            "accounts": {key: account_state(acc) for key, acc in bank.accounts.items()},
            "total": total_balance(),
            "recent": bank.history[:RECENT_COUNT],
            "recent_max": RECENT_COUNT,
            "history": bank.history,
            "history_count": history_label(),
        },
    )


@require_POST
def transact(request):
    key, kind = request.POST.get("account"), request.POST.get("type")
    acc = bank.accounts.get(key)
    if acc is None or kind not in ("deposit", "withdrawal"):
        return JsonResponse({"ok": False, "message": "Invalid request."}, status=400)

    try:
        amount = request.POST.get("amount")
        tx = acc.deposit(amount) if kind == "deposit" else acc.withdraw(amount)
    except ATMError as error:
        return JsonResponse({"ok": False, "message": str(error)}, status=400)

    is_in = kind == "deposit"
    row = bank.record_transaction(
        acc_key=key,
        title="Cash deposit" if is_in else "ATM withdrawal",
        date_str=tx.timestamp.strftime("%b %d, %Y"),
        tx_type=kind,
        amount=tx.amount,
        reference=f"ABC-{tx.reference_number}",
    )
    bank.save_data()

    return JsonResponse(
        {
            "ok": True,
            "message": f"{'Deposited' if is_in else 'Withdrew'} {peso(tx.amount)} successfully.",
            "accounts": {k: account_state(a) for k, a in bank.accounts.items()},
            "total": total_balance(),
            "rows": {
                "recent": render_to_string("atm/tx_row.html", {"row": row, "full": False}),
                "history": render_to_string("atm/tx_row.html", {"row": row, "full": True}),
            },
            "history_count": history_label(),
        }
    )