from . import views
from django.urls import path

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('admin_products/', views.admin_product, name='admin_products'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),

] 
