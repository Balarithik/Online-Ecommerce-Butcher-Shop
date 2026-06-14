from django.shortcuts import render
from store.models import Products
# Create your views here.
def home(request):
    try :
        products = Products.objects.all()
    except Exception as e :
        products = []
        print(f'db error {e}')
    return render(request, 'home/index.html', {'products': products}   )