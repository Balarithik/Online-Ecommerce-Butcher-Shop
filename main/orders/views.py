import json
import uuid
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
from orders.forms import OrderForm
from home.models import CustomerAddress, CustomerProfile
from .models import Order, Cart, CartItem, OrderItem
from .notifications import send_order_confirmation


def get_or_create_cart(request, merge_session_key=None):
    """
    Retrieves or creates a user-scoped or session-scoped cart.
    Ensures that authenticated users get a unique Cart tied to their account.
    Merges session cart into user cart if user just logged in.
    """
    current_session_key = request.session.session_key
    if not current_session_key:
        request.session.save()
        current_session_key = request.session.session_key

    if request.user.is_authenticated:
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(user=request.user)
            # Django rotates the session key during login.  Include the key that
            # existed before login so a guest basket follows the customer.
            session_keys = {key for key in (current_session_key, merge_session_key) if key}
            session_carts = Cart.objects.select_for_update().filter(
                session_key__in=session_keys,
                user__isnull=True,
            )
            for session_cart in session_carts:
                for item in session_cart.items.select_related('product'):
                    existing_item = CartItem.objects.filter(cart=cart, product=item.product).first()
                    if existing_item:
                        existing_item.quantity = (
                            existing_item.quantity + item.quantity
                        ).quantize(Decimal('0.001'))
                        existing_item.save(update_fields=['quantity'])
                    else:
                        item.cart = cart
                        item.save(update_fields=['cart'])
                session_cart.delete()
        return cart

    cart, _ = Cart.objects.get_or_create(
        session_key=current_session_key,
        user__isnull=True,
    )
    return cart


def _cart_quantity(value):
    try:
        quantity = Decimal(str(value)).quantize(Decimal('0.001'))
    except (ArithmeticError, ValueError, TypeError):
        raise ValueError
    if not quantity.is_finite() or not Decimal('0.250') <= quantity <= Decimal('100.000'):
        raise ValueError
    return quantity


def _login_redirect(request, target_path):
    messages.info(request, "Please sign in or create an account to place your order.")
    return redirect(f"{reverse('customer_login')}?{urlencode({'next': target_path})}")


def _format_cart_response(cart):
    items_data = []
    items = cart.items.select_related('product').all()
    for item in items:
        prod = item.product
        image_url = prod.image1.url if prod.image1 else 'https://images.unsplash.com/photo-1587593810167-a84920ea0781?w=200'
        items_data.append({
            'id': prod.id,
            'cart_item_id': item.id,
            'name': prod.name,
            'price': float(prod.price),
            'image': image_url,
            'qty': float(item.quantity),
            'cut_preference': item.cut_preference,
            'delivery_slot': item.delivery_slot,
            'subtotal': float(item.subtotal),
        })

    return {
        'items': items_data,
        'count': len(items_data),
        'total': float(cart.total_price()),
    }


def cart_data_api(request):
    cart = get_or_create_cart(request)
    return JsonResponse(_format_cart_response(cart))


@require_POST
def cart_add_api(request):
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    product_id = data.get('product_id') or data.get('id')
    if not product_id:
        return JsonResponse({'error': 'Product ID is required.'}, status=400)

    product = get_object_or_404(Products, id=product_id, is_available=True)
    try:
        qty_val = _cart_quantity(data.get('qty', 1))
    except ValueError:
        return JsonResponse({'error': 'Quantity must be between 0.250 and 100 kg.'}, status=400)
    cut_pref = data.get('cut_preference', 'Curry Cut (Medium)').strip()
    del_slot = data.get('delivery_slot', 'Express Delivery (45-60 Mins)').strip()

    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            'quantity': qty_val,
            'cut_preference': cut_pref,
            'delivery_slot': del_slot
        }
    )
    if not created:
        cart_item.quantity = (cart_item.quantity + qty_val).quantize(Decimal('0.001'))
        if cut_pref:
            cart_item.cut_preference = cut_pref
        if del_slot:
            cart_item.delivery_slot = del_slot
        cart_item.save()

    return JsonResponse(_format_cart_response(cart))


@require_POST
def cart_update_api(request):
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    product_id = data.get('product_id') or data.get('id')
    if not product_id:
        return JsonResponse({'error': 'Product ID is required.'}, status=400)
    delta = data.get('delta')
    qty = data.get('qty')

    cart = get_or_create_cart(request)
    cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()

    if cart_item:
        try:
            if delta is not None:
                new_qty = cart_item.quantity + Decimal(str(delta))
            elif qty is not None:
                new_qty = Decimal(str(qty))
            else:
                new_qty = cart_item.quantity
        except (ArithmeticError, ValueError, TypeError):
            return JsonResponse({'error': 'Quantity must be a valid number.'}, status=400)

        if new_qty < Decimal('0.250'):
            cart_item.delete()
        else:
            try:
                cart_item.quantity = _cart_quantity(new_qty)
            except ValueError:
                return JsonResponse({'error': 'Quantity must be between 0.250 and 100 kg.'}, status=400)
            cart_item.save()

    return JsonResponse(_format_cart_response(cart))


@require_POST
def cart_remove_api(request):
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    product_id = data.get('product_id') or data.get('id')
    cart = get_or_create_cart(request)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    return JsonResponse(_format_cart_response(cart))


@require_POST
def cart_clear_api(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return JsonResponse(_format_cart_response(cart))


def cart_view(request):
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    products = Products.objects.filter(is_available=True)
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'products': products
    })


def Checkout(request, product_id=None, qty='1'):
    # REQUIRE SIGN IN TO ORDER (Requirement 4)
    if not request.user.is_authenticated:
        return _login_redirect(request, request.get_full_path())

    cart = get_or_create_cart(request)

    if product_id is None:
        cart_items = cart.items.select_related('product').filter(product__is_available=True)
        if cart_items.exists():
            first_item = cart_items.first()
            product = first_item.product
            qty = str(first_item.quantity)
        else:
            first_product = Products.objects.filter(is_available=True).first()
            if not first_product:
                messages.info(request, "No products are currently available.")
                return redirect('products')
            return redirect('Checkout', product_id=first_product.id, qty='1')
    else:
        product = get_object_or_404(Products, id=product_id, is_available=True)

    initial_data = {'quantity': qty}
    saved_addresses = request.user.saved_addresses.all()
    selected_address = None
    
    initial_data['name'] = request.user.get_full_name() or request.user.username
    profile = CustomerProfile.objects.filter(user=request.user).first()
    if profile and profile.mobile:
        initial_data['mobile'] = profile.mobile

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

    form = OrderForm(initial=initial_data)
    available_products = Products.objects.filter(is_available=True).exclude(id=product.id)[:4]

    return render(request, 'orders/checkout.html', {
        'product': product,
        'form': form,
        'qty': qty,
        'available_products': available_products,
        'saved_addresses': saved_addresses,
        'selected_address': selected_address,
        'cart': cart,
        'order_token': uuid.uuid4(),
    })


@require_POST
def Orders(request, product_id):
    # REQUIRE SIGN IN TO ORDER (Requirement 4)
    if not request.user.is_authenticated:
        target_path = reverse('Checkout_direct', kwargs={'product_id': product_id, 'qty': request.POST.get('quantity', '1')})
        return _login_redirect(request, target_path)

    selected_address = None
    order_data = request.POST.copy()
    saved_address_id = order_data.get('saved_address_id')
    if saved_address_id:
        selected_address = get_object_or_404(
            request.user.saved_addresses,
            pk=saved_address_id,
        )
        order_data['name'] = selected_address.recipient_name
        order_data['mobile'] = selected_address.mobile
        order_data['address'] = selected_address.formatted_address
    elif request.user.saved_addresses.exists() and not order_data.get('address'):
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
        delivery_slot = form.cleaned_data.get('delivery_slot', 'Express Delivery (45-60 Mins)')
        cut_preference = form.cleaned_data.get('cut_preference', 'Curry Cut (Medium)')
        payment_method = form.cleaned_data.get('payment_method', 'Cash on Delivery')
        
        product = Products.objects.filter(id=product_id, is_available=True).first()
        if product is None:
            return HttpResponseBadRequest("This product is no longer available.")
        
        product_name = product.name
        price = (product.price * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        raw_token = request.POST.get('order_token', '')
        try:
            order_token = uuid.UUID(raw_token) if raw_token else None
        except (TypeError, ValueError, AttributeError):
            return HttpResponseBadRequest("The checkout session is invalid. Please try again.")

        order_defaults = {
            'user': request.user,
            'product_name': product_name,
            'name': name,
            'mobile': mobile,
            'location': location,
            'latitude': latitude,
            'longitude': longitude,
            'instructions': instructions,
            'delivery_slot': delivery_slot,
            'cut_preference': cut_preference,
            'payment_method': payment_method,
            'product_id': product_id,
            'quantity': quantity,
            'price': price,
            'status': 'pending',
        }
        with transaction.atomic():
            if order_token:
                order, created = Order.objects.get_or_create(
                    placement_token=order_token,
                    defaults=order_defaults,
                )
                if order.user_id != request.user.id:
                    return HttpResponseBadRequest("The checkout session is invalid. Please try again.")
            else:
                order = Order.objects.create(**order_defaults)
                created = True

            if created:
                cart = get_or_create_cart(request)
                cart_items = list(cart.items.select_related('product').all())
                if cart_items:
                    for c_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            product=c_item.product,
                            product_name=c_item.product.name,
                            quantity=c_item.quantity,
                            price=c_item.subtotal,
                            cut_preference=c_item.cut_preference,
                        )
                    total_p = sum((ci.subtotal for ci in cart_items), Decimal('0.00'))
                    order.price = total_p
                    order.save(update_fields=['price'])
                    cart.items.all().delete()
                else:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product_name,
                        quantity=quantity,
                        price=price,
                        cut_preference=cut_preference,
                    )
                transaction.on_commit(lambda: send_order_confirmation(order))

        # Save session data for reference
        request.session['customer_name'] = name
        request.session['customer_phone'] = mobile
        request.session['customer_address'] = location
        request.session['last_order_id'] = order.order_id

        return redirect('order_confirmation', order_id=order.order_id)

    product = get_object_or_404(Products, id=product_id, is_available=True)
    saved_addresses = request.user.saved_addresses.all()
    if saved_address_id:
        selected_address = saved_addresses.filter(pk=saved_address_id).first()
    return render(request, 'orders/checkout.html', {
        'product': product,
        'form': form,
        'qty': request.POST.get('quantity', '1'),
        'saved_addresses': saved_addresses,
        'selected_address': selected_address,
        'order_token': request.POST.get('order_token', uuid.uuid4()),
    }, status=400)


def my_orders(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to view your orders.")
        return redirect(f"{reverse('customer_login')}?next={reverse('my_orders')}")

    orders = Order.objects.filter(user=request.user).order_by('-order_id')
    return render(request, 'orders/my_orders.html', {
        'orders': orders,
    })


def order_confirmation_view(request, order_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to view order details.")
        return redirect(f"{reverse('customer_login')}?next={reverse('order_confirmation', kwargs={'order_id': order_id})}")

    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    items = order.get_items()
    return render(request, 'orders/order_confirmation.html', {
        'order': order,
        'order_id': order.order_id,
        'name': order.name,
        'mobile': order.mobile,
        'location': order.location,
        'instructions': order.instructions,
        'delivery_slot': order.delivery_slot,
        'cut_preference': order.cut_preference,
        'payment_method': order.payment_method,
        'quantity': order.quantity,
        'price': order.price,
        'items': items,
    })
