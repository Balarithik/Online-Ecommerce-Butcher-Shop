# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect , HttpResponse ,get_object_or_404
from django.contrib import messages
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


@login_required(login_url='/admin_login/')
def add_product_modal(request):
    if request.method == "GET":
        return render(request, "admin/addnewproductpopup.html")

    elif request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price', '').strip()
            description = request.POST.get('description', '').strip()
            image1 = request.FILES.get('image1')
            image2 = request.FILES.get('image2')
            image3 = request.FILES.get('image3')
            image4 = request.FILES.get('image4')

            Products.objects.create(
                name=name,
                price=price,
                description=description,
                image1=image1,
                image2=image2,
                image3=image3,
                image4=image4
            )
            print(f"Product Added {name}")
            return redirect("admin_products")
        else:
            # re-render the modal with validation errors
            return HttpResponse("you've missed some required fields", status=400)

    return HttpResponse(f"Invalid request method ({request.method})", status=405)


@login_required(login_url='/admin_login/')
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
def delete_product(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    product.delete()
    print(f"Product {product_id} deleted")
    return redirect('admin_products')

    # HTMX expects a response it can swap into the DOM.
    # Returning an empty response tells HTMX to remove the row.
    return HttpResponse(status=204)



@login_required(login_url='/admin_login/')
def update_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    product = get_object_or_404(Products, id=order.product_id)

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
