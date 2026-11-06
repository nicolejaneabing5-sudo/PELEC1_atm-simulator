from django.urls import path
from . import views
app_name = "atm"
urlpatterns = [
    path("",views.pin_entry, name="pin_entry"),
    path("pin-entry/", views.pin_entry, name="pin_entry"),
]