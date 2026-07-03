
from main import settings
from django.conf.urls.static import static


urlpatterns = [
    path('Orders/<int:product_id>/', views.Orders, name='Orders'),
]   

