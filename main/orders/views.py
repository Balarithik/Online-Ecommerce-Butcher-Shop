from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib import messages
from orders.forms import OrderForm
from home.models import CustomerAddress, CustomerProfile
from store.models import Products
from .models import Order

def Checkout(request, product_id=None, qty='1'):
    if product_id is None:
        first_product = Products.objects.filter(is_available=True).first()
        if not first_product:
            messages.info(request, "No products are currently available.")
            return redirect('products')
        return redirect('Checkout', product_id=first_product.id, qty='1')

    product = get_object_or_404(Products, id=product_id, is_available=True)
    initial_data = {'quantity': qty}
    saved_addresses = CustomerAddress.objects.none()
    selected_address = None
    
    if request.user.is_authenticated:
        initial_data['name'] = request.user.get_full_name() or request.user.username
        profile = CustomerProfile.objects.filter(user=request.user).first()
        if profile and profile.mobile:
            initial_data['mobile'] = profile.mobile
        saved_addresses = request.user.saved_addresses.all()
        requested_address_id = request.GET.get('address_id')
        if requested_address_id:
            selected_address = saved_addresses.filter(pk=requested_address_id).first()
        if selected_address is None:
            selected_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()
        if selected_address:
            initial_data['name'] = selected_address.recipient_name
            initial_data['mobile'] = selected_address.mobile
            initial_data['address'] = selected_address.formatted_address
        else:
            last_order = Order.objects.filter(user=request.user).order_by('-order_id').first()
            if last_order:
                initial_data['mobile'] = initial_data.get('mobile') or last_order.mobile
                initial_data['address'] = last_order.location
                initial_data['cut_preference'] = last_order.cut_preference
                initial_data['delivery_slot'] = last_order.delivery_slot
    elif 'customer_phone' in request.session:
        initial_data['name'] = request.session.get('customer_name', '')
        initial_data['mobile'] = request.session.get('customer_phone', '')
        initial_data['address'] = request.session.get('customer_address', '')

    form = OrderForm(initial=initial_data)
    available_products = Products.objects.filter(is_available=True).exclude(id=product.id)[:4]

    return render(request, 'orders/checkout.html', {
        'product': product,
        'form': form,
        'qty': qty,
        'available_products': available_products,
        'saved_addresses': saved_addresses,
        'selected_address': selected_address,
    })

@require_POST
def Orders(request, product_id):
    selected_address = None
    order_data = request.POST.copy()
    saved_address_id = order_data.get('saved_address_id')
    if request.user.is_authenticated and saved_address_id:
        selected_address = get_object_or_404(
            request.user.saved_addresses,
            pk=saved_address_id,
        )
        order_data['name'] = selected_address.recipient_name
        order_data['mobile'] = selected_address.mobile
        order_data['address'] = selected_address.formatted_address
    elif request.user.is_authenticated and request.user.saved_addresses.exists():
        return HttpResponseBadRequest("Choose one of your saved delivery addresses.")

    form = OrderForm(order_data)
    if form.is_valid():
        name = form.cleaned_data.get('name', '').strip()
        mobile = form.cleaned_data.get('mobile', '').strip()
        location = form.cleaned_data.get('address', '').strip()
        latitude = form.cleaned_data.get('latitude')
        longitude = form.cleaned_data.get('longitude')
        instructions = form.cleaned_data.get('instructions', '').strip()
        quantity = form.cleaned_data.get('quantity', Decimal('1.000'))
        delivery_slot = request.POST.get('delivery_slot', 'Express Delivery (45-60 Mins)').strip()
        cut_preference = request.POST.get('cut_preference', 'Curry Cut (Medium)').strip()
        payment_method = request.POST.get('payment', 'Cash on Delivery').strip()
        
        product = Products.objects.filter(id=product_id, is_available=True).first()
        if product is None:
            return HttpResponseBadRequest("This product is no longer available.")
        
        product_name = product.name
        price = (product.price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        user = request.user if request.user.is_authenticated else None

        order = Order(
            user=user,
            product_name=product_name,
            name=name,
            mobile=mobile,
            location=location,
            latitude=latitude,
            longitude=longitude,
            instructions=instructions,
            delivery_slot=delivery_slot,
            cut_preference=cut_preference,
            payment_method=payment_method,
            product_id=product_id,
            quantity=quantity,
            price=price,
            status='pending'
        )
        order.save()

        # Save session for convenience
        request.session['customer_name'] = name
        request.session['customer_phone'] = mobile
        request.session['customer_address'] = location
        request.session['last_order_id'] = order.order_id

        return render(request, 'orders/order_confirmation.html', {
            'order': order,
            'order_id': order.order_id,
            'name': name,
            'mobile': mobile,
            'location': location,
            'instructions': instructions,
            'delivery_slot': delivery_slot,
            'cut_preference': cut_preference,
            'payment_method': payment_method,
            'quantity': quantity,
            'price': price,
            'product': product,
        })

    product = get_object_or_404(Products, id=product_id, is_available=True)
    saved_addresses = request.user.saved_addresses.all() if request.user.is_authenticated else CustomerAddress.objects.none()
    if request.user.is_authenticated and saved_address_id:
        selected_address = saved_addresses.filter(pk=saved_address_id).first()
    return render(request, 'orders/checkout.html', {
        'product': product,
        'form': form,
        'qty': request.POST.get('quantity', '1'),
        'saved_addresses': saved_addresses,
        'selected_address': selected_address,
    }, status=400)


def my_orders(request):
    mobile_query = request.GET.get('mobile', '').strip()
    orders = []
    
    if request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user).order_by('-order_id')
    elif mobile_query:
        cleaned_mobile = ''.join(filter(str.isdigit, mobile_query))
        if len(cleaned_mobile) == 12 and cleaned_mobile.startswith('91'):
            cleaned_mobile = cleaned_mobile[2:]
        orders = Order.objects.filter(mobile__icontains=cleaned_mobile).order_by('-order_id')
    elif 'customer_phone' in request.session:
        orders = Order.objects.filter(mobile=request.session['customer_phone']).order_by('-order_id')
    elif 'last_order_id' in request.session:
        orders = Order.objects.filter(order_id=request.session['last_order_id'])

    return render(request, 'orders/my_orders.html', {
        'orders': orders,
        'mobile_query': mobile_query
    })


def cart_view(request):
    products = Products.objects.filter(is_available=True)
    return render(request, 'orders/cart.html', {
        'products': products
    })
