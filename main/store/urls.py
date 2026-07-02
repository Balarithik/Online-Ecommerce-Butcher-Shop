
from . import views
from django.urls import path
from orders import views as order_views
from main import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.product, name='products'),
    path('Checkout/<int:product_id>/<str:qty>/', order_views.Checkout, name='Checkout'),
    path('selected_product/<int:product_id>/', views.selected_product, name='selected_product'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
