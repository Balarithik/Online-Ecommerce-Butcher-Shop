from . import views
from django.urls import path    

urlpatterns = [
    path('Orders/<int:product_id>/', views.Orders, name='Orders'),
]   