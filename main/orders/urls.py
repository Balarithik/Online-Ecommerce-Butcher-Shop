from . import views
from django.urls import path   

urlpatterns = [
    path('', views.my_orders, name='my_orders'),
    path('my-orders/', views.my_orders, name='my_orders_explicit'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/data/', views.cart_data_api, name='cart_data_api'),
    path('cart/add/', views.cart_add_api, name='cart_add_api'),
    path('cart/update/', views.cart_update_api, name='cart_update_api'),
    path('cart/remove/', views.cart_remove_api, name='cart_remove_api'),
    path('cart/clear/', views.cart_clear_api, name='cart_clear_api'),
    path('checkout/', views.Checkout, name='checkout_general'),
    path('checkout/<int:product_id>/<str:qty>/', views.Checkout, name='Checkout_direct'),
    path('Orders/<int:product_id>/', views.Orders, name='Orders'),
    path('confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'),
]
