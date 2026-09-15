from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from orders.forms import OrderForm
from store.models import Products
from .models import Order

# Create your views here.
# views.py


def Checkout(request, product_id, qty):
    product = get_object_or_404(Products, id=product_id, is_available=True)
    form = OrderForm(initial={'quantity': qty})
    return render(request, 'orders/checkout.html', {'product': product, 'form': form, 'qty': qty})

@require_POST
def Orders(request, product_id):
    form = OrderForm(request.POST)
    if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            mobile = form.cleaned_data.get('mobile', '').strip()
            location = form.cleaned_data.get('address', '').strip()
            instructions = form.cleaned_data.get('instructions', '').strip()
            quantity = form.cleaned_data.get('quantity', 1.0)
            
            product = Products.objects.filter(id=product_id, is_available=True).first()
            if product is None:
                return HttpResponseBadRequest("This product is no longer available.")
            product_name = product.name
            # Price and total deliberately come only from the database/form validation.
            price = (product.price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            orders = Order(
                product_name=product_name,
                name=name,
                mobile=mobile,
                location=location,
                instructions=instructions,
                product_id=product_id,
                quantity=quantity,
                price=price
            )
            orders.save()
            return render(request, 'orders/order_confirmation.html', {
                'order_id': orders.order_id,
                'name': name,
                'mobile': mobile,
                'location': location,
                'instructions': instructions,
                'quantity': quantity,
                'price': price
            })
    product = get_object_or_404(Products, id=product_id, is_available=True)
    return render(request, 'orders/checkout.html', {
        'product': product,
        'form': form,
        'qty': request.POST.get('quantity', '1'),
    }, status=400)
