from . import views
from django.urls import path   

urlpatterns = [
    path('', views.my_orders, name='my_orders'),
    path('my-orders/', views.my_orders, name='my_orders_explicit'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.Checkout, name='checkout_general'),
    path('checkout/<int:product_id>/<str:qty>/', views.Checkout, name='Checkout_direct'),
    path('Orders/<int:product_id>/', views.Orders, name='Orders'),
]
   

