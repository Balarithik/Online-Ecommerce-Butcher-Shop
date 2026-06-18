# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from store.models import Products
from orders.models import Order






def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            # Look for next in POST first, then GET, fallback to dashboard
            next_url = request.POST.get("next") or request.GET.get("next") or "admin_dashboard"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid credentials or not a superuser.")
    return render(request, "admin/admin_login.html")


@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_dashboard(request):
    products = Products.objects.all()
    orders = Order.objects.all()



    total_products = products.count()
    total_orders = orders.count()
    try :
        orders_delivered = orders.filter(status='Delivered').count()
    except:
        orders_delivered = None 
    try:
        orders_pending = orders.filter(status='Pending').count()
    except:
        orders_pending = None

    return render(request, "admin/admin_dashboard.html", {'products': products, 'orders': orders, 'total_products': total_products, 'total_orders': total_orders, 'orders_delivered': orders_delivered, 'orders_pending': orders_pending})

@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_product(request):
    products = Products.objects.all()
    return render(request, "admin/products.html",{'products':products})
@login_required(login_url='/admin_login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/admin_login/')
def admin_orders(request):
    orders = Order.objects.all()
    return render(request, "admin/orders.html",{'orders':orders})
