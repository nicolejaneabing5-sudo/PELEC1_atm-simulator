from django.urls import path
from . import views
app_name = "atm"
urlpatterns = [
    path('', views.pin_entry_view, name='pin_entry'),
    path('dashboard/',views.dashboard_view, name='dashboard'),
]