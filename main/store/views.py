

from django.shortcuts import render
from .models import Products
# Create your views here.

def product(request):
    try :
        products = Products.objects.all()
    except Exception as e :
        products = []
        print(f'db error {e}')
    return render(request, 'store/product.html',{'products':products})
def selected_product(request, product_id):
    try :
        product = Products.objects.get(id=product_id)
    except Exception as e :
        product = None
        print(f'db error {e}')
    return render(request, 'store/product_info.html',{'product':product})