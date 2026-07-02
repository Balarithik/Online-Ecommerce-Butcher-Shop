from . import views
from django.urls import path   

from main import settings
from django.conf.urls.static import static


urlpatterns = [
    path('Orders/<int:product_id>/', views.Orders, name='Orders'),
]   

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)