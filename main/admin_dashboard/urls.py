from . import views
from django.urls import path

urlpatterns = [
    path('admin_login/', views.admin_login, name='admin_login'),    
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin_products/', views.admin_product, name='admin_products'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),

] 