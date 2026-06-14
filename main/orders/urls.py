from . import views
from django.urls import path    

urlpatterns = [
    path('Checkout/<int:product_id>/<str:qty>/', views.Checkout, name='Checkout'),
    path('Orders/', views.Orders, name='orders'),
]   