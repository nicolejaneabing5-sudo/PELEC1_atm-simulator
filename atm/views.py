from decimal import Decimal
from django.utils import timezone
from .oop import pin_store

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import ActivityLog
from .oop.domain import ATMError, MIN_WITHDRAWAL
from .oop import sample_accounts as bank

MAX_ATTEMPTS = 4         
RECENT_COUNT = 5
USER_NAME = "Juan Dela Cruz"

LOW_BALANCE = Decimal("1000.00")  


MAX_LOGGED = Decimal("9999999999.99")   

def log(action, success=True, account="", amount=None, balance_after=None, message=""):
    """Save one row in the database so we can see what happened."""
    # A huge amount can't fit the DecimalField (SQLite wouldn't stop it, but the admin would crash). REason why i added this
    # Keep the number out of the column and mention it in the message instead.
    if amount is not None and abs(Decimal(str(amount))) > MAX_LOGGED:
        message = f"{message} (amount too large to store: {amount})"
        amount = None
    if balance_after is not None and abs(Decimal(str(balance_after))) > MAX_LOGGED:
        balance_after = None

    ActivityLog.objects.create(
        action=action,
        success=success,
        account=account,
        amount=amount,
        balance_after=balance_after,
        message=message[:255],
    )

def peso(value):
    return f"₱{value:,.2f}"


def is_authenticated(request):
    return bool(request.session.get("authenticated"))


def low_balance_alert(acc):
    if acc.balance <= LOW_BALANCE:
        return (
            f"Low Balance Warning: {acc.account_type} (•••• {acc.account_number}) "
            f"is down to {peso(acc.balance)}. Consider making a deposit."
        )
    return None


def account_state(acc):
    """Everything the page shows for one account, already formatted as text."""
    withdrawn = acc.withdrawn_today          # also rolls the daily counter over at midnight
    remaining = acc.daily_max - withdrawn
    meter = min(float(withdrawn / acc.daily_max * 100), 100.0)
    return {
        "name": acc.account_type,
        "last4": acc.account_number,
        "balance": peso(acc.balance),
        "withdrawn": peso(withdrawn),
        "max_tx": f"₱{acc.max_transaction:,.0f}",      # NEW
        "daily_max": f"₱{acc.daily_max:,.0f}",         # NEW
        "meter": meter,                       # number, used by JS
        "meter_css": f"{meter:.1f}",          # string, used by the template (no locale commas)
        "limits": f"Withdrawn today: {peso(withdrawn)} • {peso(remaining)} remaining",
    }


def total_balance():
    return peso(sum(a.balance for a in bank.accounts.values()))


def history_label():
    n = len(bank.history)
    return f"{n} transaction{'' if n == 1 else 's'} across checking and savings"


# ---------- PIN page ----------
def pin_state(request):
    return {
        "attempts_left": request.session.get("attempts_left", MAX_ATTEMPTS),
        "locked": request.session.get("pin_locked", False),
    }


@never_cache
def pin_entry(request):
    return render(request, "atm/pin_entry.html", pin_state(request))


@require_POST
def verify_pin(request):
    state = pin_state(request)
    if state["locked"]:
        log("PIN", False, message="Blocked: PIN is locked")
        return JsonResponse(
            {"ok": False, "locked": True, "attempts_left": 0, "message": "PIN locked."},
            status=403,
        )

    if pin_store.check(request.POST.get("pin", "")):
        request.session["attempts_left"] = MAX_ATTEMPTS
        request.session["authenticated"] = True
        log("PIN", True, message="Correct PIN, logged in")
        return JsonResponse({"ok": True, "redirect": reverse("atm:dashboard")})

    left = state["attempts_left"] - 1
    request.session["attempts_left"] = left
    request.session["pin_locked"] = left <= 0
    log("PIN", False, message=f"Wrong PIN, {left} attempt(s) left" + (" - LOCKED" if left <= 0 else ""))
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
    log("UNLOCK", True, message="PIN lock was reset")
    return JsonResponse({"ok": True, "attempts_left": MAX_ATTEMPTS})


def lock_session(request):
    """Really end the session (the 'Lock session' button in the header)."""
    log("LOCK", True, message="Session ended")
    request.session.flush()
    return redirect("atm:pin_entry")


# ---------- dashboard ----------
@never_cache
def dashboard(request):
    if not is_authenticated(request):
        return redirect("atm:pin_entry")

    parts = USER_NAME.split()
    return render(request, "atm/dashboard.html", {
        "user_name": USER_NAME,
        "first_name": parts[0],
        "initials": parts[0][0] + parts[-1][0],
        "accounts": {key: account_state(acc) for key, acc in bank.accounts.items()},
        "total": total_balance(),
        "recent": bank.history[:RECENT_COUNT],
        "recent_max": RECENT_COUNT,
        "history": bank.history,
        "history_count": history_label(),
    })


@require_POST
def transact(request):
    if not is_authenticated(request):
        log("INVALID", False, message="Not logged in / session expired")
        return JsonResponse(
            {"ok": False, "message": "Session expired. Please log in again."}, status=401
        )

    key, kind = request.POST.get("account"), request.POST.get("type")
    acc = bank.accounts.get(key)
    if acc is None or kind not in ("deposit", "withdrawal"):
        log("INVALID", False, message=f"Invalid request: account={key}, type={kind}")
        return JsonResponse({"ok": False, "message": "Invalid request."}, status=400)

    amount = request.POST.get("amount")
    action = kind.upper()

    # Insufficient-funds check runs BEFORE the account's own rules so this
    # message wins when the amount is simply bigger than the balance.
    # validate_amount() handles junk input (NaN, Infinity, letters, <= 0).
    if kind == "withdrawal":
        try:
            requested = acc.validate_amount(amount, MIN_WITHDRAWAL, 'withdrawal')
        except ATMError as error:
            log(action, False, acc.account_type, message=str(error))
            return JsonResponse({"ok": False, "message": str(error)}, status=400)

        if requested > acc.balance:
            log(action, False, acc.account_type, requested, acc.balance, "Insufficient funds")
            return JsonResponse(

                {
                    "ok": False,
                    "message": "Insufficient funds. The amount is higher than your available balance.",
                },
                status=400,
            )

    try:
        tx = acc.deposit(amount) if kind == "deposit" else acc.withdraw(amount)
    except ATMError as error:
        log(action, False, acc.account_type, message=str(error))
        return JsonResponse({"ok": False, "message": str(error)}, status=400)

    log(action, True, acc.account_type, tx.amount, acc.balance, "Success")

    is_in = kind == "deposit"
    row = {
        "title": "Cash deposit" if is_in else "ATM withdrawal",
        "date": tx.timestamp.strftime("%b %d, %Y"),
        "ref": f"ABC-{tx.reference_number}",
        "account": acc.account_type,
        "short": acc.account_type.split()[0],
        "last4": acc.account_number,
        "kind": "in" if is_in else "out",
        "type": "Deposit" if is_in else "Withdrawal",
        "signed": ("+" if is_in else "-") + peso(tx.amount),
        "after": peso(acc.balance),
    }
    bank.history.insert(0, row)

    return JsonResponse({
        "ok": True,
        "message": f"{'Deposited' if is_in else 'Withdrew'} {peso(tx.amount)} successfully.",
        "alert": low_balance_alert(acc),
        "accounts": {k: account_state(a) for k, a in bank.accounts.items()},
        "total": total_balance(),
        "rows": {
            "recent": render_to_string("atm/tx_row.html", {"row": row, "full": False}),
            "history": render_to_string("atm/tx_row.html", {"row": row, "full": True}),
        },
        "history_count": history_label(),
    })

CUSTOMER = {                                   # simulated bank details
    "customer_id": "CUS-0048210",
    "email": "n*****@email.com",
    "mobile": "+63 9•• ••• 4821",
    "customer_since": "Mar 12, 2021",
    "tier": "Regular",
}
ACCOUNT_META = {                               # simulated, per account
    "checking": {"opened": "Mar 12, 2021", "branch": "ABC Bank, Main Branch", "interest": "None"},
    "savings": {"opened": "Jun 03, 2021", "branch": "ABC Bank, Main Branch", "interest": "0.25% per year"},
}
CARD = {"last4": "4821", "expiry": "09/29", "status": "Active"}
PIN_CHANGE_MAX_FAILS = 3


def _unauthorized():
    return JsonResponse({"ok": False, "message": "Session expired. Please log in again."}, status=401)


def _fmt_dt(value):
    return timezone.localtime(value).strftime("%b %d, %Y, %I:%M %p")


@never_cache
def account_info(request):
    if not is_authenticated(request):
        return _unauthorized()

    # newest login is the current one, so the one before it is the "last login"
    logins = list(
        ActivityLog.objects.filter(action="PIN", success=True, message__startswith="Correct PIN")
        .order_by("-created_at")[:2]
    )
    last_login = _fmt_dt(logins[1].created_at) if len(logins) > 1 else "This is your first login"
    changed = pin_store.changed_at()

    accounts = []
    for key, acc in bank.accounts.items():
        meta = ACCOUNT_META[key]
        accounts.append({
            "type": acc.account_type,
            "number": f"•••• •••• {acc.account_number}",
            "status": "Active",
            "opened": meta["opened"],
            "branch": meta["branch"],
            "interest": meta["interest"],
            "balance": peso(acc.balance),
            "min_balance": peso(acc.min_remain_balance),
            "currency": "PHP (₱)",
        })

    return JsonResponse({
        "ok": True,
        "holder": {"name": USER_NAME, **CUSTOMER},
        "accounts": accounts,
        "card": {"number": f"•••• •••• •••• {CARD['last4']}", "expiry": CARD["expiry"], "status": CARD["status"]},
        "security": {
            "last_login": last_login,
            "pin_changed": changed.strftime("%b %d, %Y") if changed else "Never changed",
        },
    })


@never_cache
def withdrawal_limits(request):
    if not is_authenticated(request):
        return _unauthorized()

    items = []
    for acc in bank.accounts.values():
        used = acc.withdrawn_today
        left = acc.daily_max - used
        available = max(Decimal("0"), min(left, acc.balance - acc.min_remain_balance))
        items.append({
            "name": acc.account_type,
            "last4": acc.account_number,
            "max_tx": peso(acc.max_transaction),
            "daily_max": peso(acc.daily_max),
            "used": peso(used),
            "remaining": peso(left),
            "available": peso(available),
            "min_balance": peso(acc.min_remain_balance),
            "pct": round(min(float(used / acc.daily_max * 100), 100.0), 1),
        })
    return JsonResponse({"ok": True, "accounts": items})


@require_POST
def change_pin(request):
    if not is_authenticated(request):
        return _unauthorized()

    current = request.POST.get("current", "")
    new = request.POST.get("new", "")
    confirm = request.POST.get("confirm", "")   
    
    for value in (current, new, confirm):
        if not (value.isascii() and value.isdigit() and len(value) == 4):
            return JsonResponse(
                {"ok": False, "message": "PINs must be exactly 4 digits (numbers only)."},
                status=400,
            )

    def fail(message, status=400, **extra):
        return JsonResponse({"ok": False, "message": message, **extra}, status=status)

    if not pin_store.check(current):
        fails = request.session.get("pin_change_fails", 0) + 1
        request.session["pin_change_fails"] = fails
        log("PIN_CHANGE", False, message=f"Wrong current PIN ({fails}/{PIN_CHANGE_MAX_FAILS})")
        if fails >= PIN_CHANGE_MAX_FAILS:
            log("LOCK", True, message="Session ended: too many wrong PINs on PIN change")
            request.session.flush()
            return fail("Too many wrong attempts. Your session was locked.", 403,
                        locked=True, redirect=reverse("atm:pin_entry"))
        left = PIN_CHANGE_MAX_FAILS - fails
        return fail(f"Current PIN is incorrect. {left} attempt{'' if left == 1 else 's'} left.")

    if not (new.isascii() and new.isdigit() and len(new) == 4):
        return fail("New PIN must be exactly 4 digits.")
    if new == current:
        return fail("New PIN must be different from your current PIN.")
    if new != confirm:
        return fail("The new PIN and confirmation do not match.")

    pin_store.change(new)
    request.session["pin_change_fails"] = 0
    log("PIN_CHANGE", True, message="PIN changed")      # never log the PIN itself
    return JsonResponse({"ok": True, "message": "Your PIN was changed successfully."})