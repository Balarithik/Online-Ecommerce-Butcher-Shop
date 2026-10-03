from . import views
from django.urls import path


urlpatterns = [
    path('',views.home,name='home'), 
    path('login/', views.customer_login, name='customer_login'),
    path('signup/', views.customer_signup, name='customer_signup'),
    path('logout/', views.customer_logout, name='customer_logout'),
]
