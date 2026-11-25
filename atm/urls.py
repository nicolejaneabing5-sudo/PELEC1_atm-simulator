from django.urls import path
from . import views

app_name = "atm"

urlpatterns = [
    path("", views.pin_entry, name="pin_entry"),
    path("dashboard/account-info/", views.account_info, name="account_info"),
    path("dashboard/limits/", views.withdrawal_limits, name="limits"),
    path("dashboard/change-pin/", views.change_pin, name="change_pin"),
    path("verify-pin/", views.verify_pin, name="verify_pin"),
    path("unlock-pin/", views.unlock_pin, name="unlock_pin"),
    path("lock/", views.lock_session, name="lock_session"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/transaction/", views.transact, name="transact"),
]