from main import settings
from django.conf.urls.static import static


from . import views
from django.urls import path,include

urlpatterns = [
    path('', views.aboutus, name='aboutus'),
    path('home', include('home.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)