from . import views
from django.urls import path ,include 


urlpatterns = [
    path('',views.home,name='home'), 
    path('login/', views.customer_login, name='customer_login'),
    path('signup/', views.customer_signup, name='customer_signup'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('selected_product/<int:product_id>/', include('store.urls'), name='selected_product'),
]

