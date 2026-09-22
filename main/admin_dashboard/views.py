# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect , HttpResponse ,get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Sum
from store.models import Products
from orders.models import Order
from .forms import ProductForm


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            # Look for next in POST first, then GET, fallback to dashboard
            next_url = request.POST.get("next") or request.GET.get("next")
            if not next_url or not next_url.startswith('/') or next_url.startswith('//'):
                next_url = "admin_dashboard"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials or not a superuser.")
    return render(request, "admin/admin_login.html")



@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_dashboard(request):
    products = Products.objects.all()
    orders = Order.objects.all().order_by('-order_id')
    total_products = products.count()
    total_orders = orders.count()
    orders_delivered = orders.filter(status='delivered').count()
    orders_pending = orders.filter(status='pending').count()
    total_revenue = orders.exclude(status='cancelled').aggregate(total=Sum('price'))['total'] or 0

    return render(request, "admin/admin_dashboard.html", {
        'total_products': total_products,
        'available_products': products.filter(is_available=True).count(),
        'total_orders': total_orders,
        'orders_delivered': orders_delivered,
        'orders_pending': orders_pending,
        'total_revenue': total_revenue,
        'recent_orders': orders[:8],
    })

@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_product(request):
    products = Products.objects.all().order_by('name')
    return render(request, "admin/products.html", {
        'products': products,
        'total_products': products.count(),
        'available_products': products.filter(is_available=True).count(),
        'unavailable_products': products.filter(is_available=False).count(),
    })



@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_orders(request):
    orders = Order.objects.all().order_by('-order_id')
    return render(request, "admin/orders.html", {
        'orders': orders,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'delivered_orders': orders.filter(status='delivered').count(),
        'cancelled_orders': orders.filter(status='cancelled').count(),
    })


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def add_product_modal(request):
    if request.method == "GET":
        return render(request, "admin/addnewproductpopup.html")

    elif request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            price = form.cleaned_data.get('price')
            description = form.cleaned_data.get('description', '').strip()
            image1 = form.cleaned_data.get('image1')
            image2 = form.cleaned_data.get('image2')
            image3 = form.cleaned_data.get('image3')
            image4 = form.cleaned_data.get('image4')
            is_available = form.cleaned_data.get('is_available')

            Products.objects.create(
                name=name,
                price=price,
                description=description,
                image1=image1,
                image2=image2,
                image3=image3,
                image4=image4,
                is_available=is_available,
            )
            print(f"Product Added {name}")
            return redirect("admin_products")
        else:
            # re-render the modal with validation errors
            return HttpResponse("you've missed some required fields", status=400)

    return HttpResponse(f"Invalid request method ({request.method})", status=405)


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def edit_product_modal(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()   # ✅ updates product directly
            print("Product Updated")
            return redirect('admin_products')
    else:
        form = ProductForm(instance=product)

    return render(request, "admin/editproductpopup.html", {"form": form, "product": product})

@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    product.delete()
    print(f"Product {product_id} deleted")
    
    # Return 204 response for HTMX or redirect for standard delete
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
            print(f"Order {order_id} status updated to {new_status}")
            return redirect('admin_orders')  # or wherever you want to go

    return render(
        request,
        "admin/order_updation.html",
        {
            "order": order,
            "product": product,
            "status_choices": Order.status_choices,
        }
    )
