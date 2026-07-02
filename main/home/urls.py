from . import views
from django.urls import path ,include 

from main import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',views.home,name='home'), 
    path('selected_product/<int:product_id>/', include('store.urls'), name='selected_product'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)