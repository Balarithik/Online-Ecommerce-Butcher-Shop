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
            return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid credentials or not a superuser.")
    return render(request, "admin/admin_login.html")

@login_required
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


def admin_product(request):
    products = Products.objects.all()
    return render(request, "admin/products.html",{'products':products})

def admin_orders(request):
    orders = Order.objects.all()
    return render(request, "admin/orders.html",{'orders':orders})