from django.urls import path
from . import views

urlpatterns = [
    path("", views.card_insert, name="card_insert"),       # Root loads the Card Insert screen first!
    path("pin/", views.pin_entry, name="pin_entry"),         # PIN entry is now at /pin/
    path("dashboard/", views.dashboard, name="dashboard"),   # Dashboard
    path("api/transaction/", views.process_transaction, name="process_transaction"),
]