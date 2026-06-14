from django.shortcuts import render,redirect
from django.http import HttpResponse
from orders.forms import OrderForm
from store.models import Products
from .models import Order

# Create your views here.
# views.py


def Checkout(request, product_id, qty):
    try:
        product = Products.objects.get(id=product_id)
        form = OrderForm()
    except Exception as e:
        product = None
        print(f'db error {e}')
    return render(request, 'orders/checkout.html', {'product': product, 'form': form, 'qty': qty})

def Orders(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Option 1: Save directly to DB
            #order = form.save()

            # Option 2: Just pass cleaned data to confirmation page
            name = request.POST.get('name', '').strip()
            Product_id = request.POST.get('product_id')
            mobile = request.POST.get('mobile', '').strip()
            location = request.POST.get('address', '').strip()
            instructions = request.POST.get('instructions', '').strip()
            quantity = request.POST.get('quantity', 1)
            price = request.POST.get('price', 0)
            order_id = Order.objects.latest('order_id').order_id + 1 if Order.objects.exists() else 1

            orders = Order(
                order_id=order_id,
                name=name,
                mobile=mobile,
                location=location,
                instructions=instructions,
                product_id=Product_id,
                quantity=quantity,
                price=price
            )
            orders.save()
            print(f"Order saved: {orders}")

            return render(request, 'orders/order_confirmation.html', {
                'order_id': order_id,
                'name': name,
                'mobile': mobile,
                'location': location,
                'instructions': instructions,
                'quantity': quantity,
                'price': price
            })
        else:
            # Re-render checkout with errors
            return redirect(request,Checkout)
    return HttpResponse("Invalid request method. Please submit the form using POST.")
