from django.urls import path
from . import views
app_name = "atm"
urlpatterns = [
    path("",views.home, name="home"),
]