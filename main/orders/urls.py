from . import views
from django.urls import path    

urlpatterns = [
    path('Orders/', views.Orders, name='orders'),
]   