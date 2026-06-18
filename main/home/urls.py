from . import views
from django.urls import path ,include   

urlpatterns = [
    path('',views.home,name='home'), 
    path('selected_product/<int:product_id>/', include('store.urls'), name='selected_product'),
]