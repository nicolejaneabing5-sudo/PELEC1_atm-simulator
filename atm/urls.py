from django.urls import path
from . import views
app_name = "atm"
urlpatterns = [
    path("", views.pin_entry, name="pin_entry"),
    path("verify-pin/", views.verify_pin, name="verify_pin"),
    path("unlock-pin/", views.unlock_pin, name="unlock_pin"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("transact/", views.transact, name="transact"),
]