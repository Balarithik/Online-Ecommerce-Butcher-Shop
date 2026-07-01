from . import views
from django.urls import path

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('admin_products/', views.admin_product, name='admin_products'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('add_product_modal/',views.add_product_modal,name='add_product_modal'),
    path('edit_product_modal/<int:product_id>/',views.edit_product_modal,name='edit_product_modal'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('update_order/<int:order_id>/',views.update_order,name='update_order')
] 
