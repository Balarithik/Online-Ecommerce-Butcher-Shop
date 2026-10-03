# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.conf import settings
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from store.models import Products
from orders.models import Order
from .forms import CloudinaryProductForm


def _product_form_context(form, product=None):
    image_uploads = []
    for number in range(1, 5):
        field_name = f"image{number}"
        public_id = form[f"{field_name}_public_id"].value() or ""
        image_url = ""
        if public_id and settings.CLOUDINARY_CLOUD_NAME:
            image_url = (
                f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}"
                f"/image/upload/{public_id}"
            )
        elif product and getattr(product, field_name):
            image_url = getattr(product, field_name).url
        image_uploads.append({
            "number": number,
            "public_id": public_id,
            "image_url": image_url,
        })

    return {
        "form": form,
        "product": product,
        "cloudinary_cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "cloudinary_upload_preset": settings.CLOUDINARY_UPLOAD_PRESET,
        "image_uploads": image_uploads,
    }


def _assign_cloudinary_images(form, product):
    for number in range(1, 5):
        public_id = form.cleaned_data[f"image{number}_public_id"]
        setattr(product, f"image{number}", public_id or None)


@never_cache
@ensure_csrf_cookie
def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if not next_url or not next_url.startswith('/') or next_url.startswith('//'):
                next_url = "admin_dashboard"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials or not an administrator.")
    return render(request, "admin/admin_login.html", {
        "next_url": request.POST.get("next") or request.GET.get("next", ""),
    })


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_dashboard(request):
    products = Products.objects.all()
    orders = Order.objects.all().order_by('-order_id')
    total_products = products.count()
    total_orders = orders.count()
    orders_delivered = orders.filter(status='delivered').count()
    orders_pending = orders.filter(status__in=['pending', 'preparing', 'out_for_delivery']).count()
    orders_cancelled = orders.filter(status='cancelled').count()
    total_revenue = orders.exclude(status='cancelled').aggregate(total=Sum('price'))['total'] or 0
    total_customers = User.objects.filter(is_superuser=False).count()

    # Express vs Regular count
    express_orders = orders.filter(delivery_slot__icontains='Express').count()

    return render(request, "admin/admin_dashboard.html", {
        'total_products': total_products,
        'available_products': products.filter(is_available=True).count(),
        'unavailable_products': products.filter(is_available=False).count(),
        'total_orders': total_orders,
        'orders_delivered': orders_delivered,
        'orders_pending': orders_pending,
        'orders_cancelled': orders_cancelled,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'express_orders': express_orders,
        'recent_orders': orders[:10],
    })


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_product(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    products = Products.objects.all().order_by('name')

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if status_filter == 'available':
        products = products.filter(is_available=True)
    elif status_filter == 'unavailable':
        products = products.filter(is_available=False)

    return render(request, "admin/products.html", {
        'products': products,
        'total_products': Products.objects.count(),
        'available_products': Products.objects.filter(is_available=True).count(),
        'unavailable_products': Products.objects.filter(is_available=False).count(),
        'query': query,
        'status_filter': status_filter,
    })


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
@require_POST
def toggle_product_availability(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    product.is_available = not product.is_available
    product.save()
    messages.success(request, f"Updated stock status for '{product.name}'.")
    return redirect('admin_products')


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_orders(request):
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    orders = Order.objects.all().order_by('-order_id')

    if query:
        orders = orders.filter(
            Q(name__icontains=query) |
            Q(mobile__icontains=query) |
            Q(location__icontains=query) |
            Q(product_name__icontains=query) |
            Q(order_id__icontains=query)
        )

    if status_filter:
        orders = orders.filter(status=status_filter)

    all_orders = Order.objects.all()

    return render(request, "admin/orders.html", {
        'orders': orders,
        'total_orders': all_orders.count(),
        'pending_orders': all_orders.filter(status__in=['pending', 'preparing']).count(),
        'out_for_delivery_orders': all_orders.filter(status='out_for_delivery').count(),
        'delivered_orders': all_orders.filter(status='delivered').count(),
        'cancelled_orders': all_orders.filter(status='cancelled').count(),
        'query': query,
        'status_filter': status_filter,
    })


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_customers(request):
    query = request.GET.get('q', '').strip()
    customers = User.objects.filter(is_superuser=False).annotate(order_count=Count('orders')).order_by('-date_joined')

    if query:
        customers = customers.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(email__icontains=query)
        )

    return render(request, "admin/customers.html", {
        'customers': customers,
        'total_customers': customers.count(),
        'query': query,
    })


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def add_product_modal(request):
    if request.method == "POST":
        if not settings.CLOUDINARY_UPLOAD_CONFIGURED:
            return HttpResponse(
                "Configure CLOUDINARY_UPLOAD_PRESET in main/.env before uploading product images.",
                status=503,
            )

        form = CloudinaryProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            _assign_cloudinary_images(form, product)
            product.save()
            messages.success(request, f"Product '{product.name}' added successfully.")
            return redirect("admin_products")
        return render(
            request,
            "admin/addnewproductpopup.html",
            _product_form_context(form),
            status=400,
        )

    if request.method == "GET":
        return render(
            request,
            "admin/addnewproductpopup.html",
            _product_form_context(CloudinaryProductForm(initial={"is_available": True})),
        )

    return HttpResponse(f"Invalid request method ({request.method})", status=405)


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def edit_product_modal(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        if not settings.CLOUDINARY_UPLOAD_CONFIGURED:
            return HttpResponse(
                "Configure CLOUDINARY_UPLOAD_PRESET in main/.env before uploading product images.",
                status=503,
            )

        form = CloudinaryProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            _assign_cloudinary_images(form, product)
            product.save()
            messages.success(request, f"Product '{product.name}' updated.")
            return redirect('admin_products')
        return render(
            request,
            "admin/editproductpopup.html",
            _product_form_context(form, product),
            status=400,
        )
    else:
        form = CloudinaryProductForm(instance=product)

    return render(
        request,
        "admin/editproductpopup.html",
        _product_form_context(form, product),
    )


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' deleted.")
    
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    return redirect('admin_products')


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def update_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    product = None
    if order.product_id:
        try:
            product = Products.objects.get(id=order.product_id)
        except Products.DoesNotExist:
            pass

    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_choices = [choice[0] for choice in Order.status_choices]
        if new_status in valid_choices:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order_id} status updated to {new_status}.")
            return redirect('admin_orders')

    return render(
        request,
        "admin/order_updation.html",
        {
            "order": order,
            "product": product,
            "status_choices": Order.status_choices,
        }
    )
