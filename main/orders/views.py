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

def Orders(request, product_id):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name', '').strip()
            mobile = form.cleaned_data.get('mobile', '').strip()
            location = form.cleaned_data.get('address', '').strip()
            instructions = form.cleaned_data.get('instructions', '').strip()
            quantity = form.cleaned_data.get('quantity', 1.0)
            
            try:
                product = Products.objects.get(id=product_id)
                product_name = product.name
                # Calculate the price dynamically to prevent client-side price tampering
                price = product.price * quantity
            except Products.DoesNotExist:
                return HttpResponse("Selected product does not exist.", status=400)
            except Exception as e:
                print(f'db error {e}')
                return HttpResponse("Database error occurred.", status=500)

            # Auto-increment order_id
            order_id = Order.objects.latest('order_id').order_id + 1 if Order.objects.exists() else 1
            
            orders = Order(
                order_id=order_id,
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
            # Re-render checkout with validation errors
            try:
                product = Products.objects.get(id=product_id)
            except Exception as e:
                product = None
                print(f'db error {e}')
            qty = request.POST.get('quantity', '1')
            return render(request, 'orders/checkout.html', {
                'product': product,
                'form': form,
                'qty': qty
            })
    return HttpResponse("Invalid request method. Please submit the form using POST.")
