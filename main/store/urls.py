
from . import views
from django.urls import path
from orders import views as order_views

urlpatterns = [
    path('', views.product, name='products'),
    path('Checkout/<int:product_id>/<str:qty>/', order_views.Checkout, name='Checkout'),
    path('selected_product/<int:product_id>/', views.selected_product, name='selected_product'),
]

