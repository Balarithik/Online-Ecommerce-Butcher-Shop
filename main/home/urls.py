from . import views
from django.urls import path


urlpatterns = [
    path('',views.home,name='home'), 
    path('login/', views.customer_login, name='customer_login'),
    path('signup/', views.customer_signup, name='customer_signup'),
    path('logout/', views.customer_logout, name='customer_logout'),
    path('account/', views.customer_account, name='customer_account'),
    path('account/delete/', views.delete_customer_account, name='delete_customer_account'),
]
