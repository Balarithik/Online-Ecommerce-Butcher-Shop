from . import views
from django.urls import path,include

urlpatterns = [
    path('', views.aboutus, name='aboutus'),
    path('home', include('home.urls')),
]