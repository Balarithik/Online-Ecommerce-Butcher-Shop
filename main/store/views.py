

from django.shortcuts import render, get_object_or_404
from .models import Products
# Create your views here.

def product(request):
    products = Products.objects.filter(is_available=True)
    return render(request, 'store/product.html',{'products':products})
def selected_product(request, product_id):
    product = get_object_or_404(Products, id=product_id, is_available=True)
    return render(request, 'store/product_info.html',{'product':product})
