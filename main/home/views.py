from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from orders.models import Order
from .forms import CustomerAddressForm, CustomerProfileForm, CustomerSignupForm, CustomerFeedbackForm
from .models import CustomerAddress, CustomerProfile, CustomerFeedback
from store.models import Products




# Create your views here.
def home(request):
    products = Products.objects.filter(is_available=True)
    return render(request, 'home/index.html', {'products': products}   )


@never_cache
@ensure_csrf_cookie
def customer_login(request):
    next_url = request.POST.get('next', '') or request.GET.get('next', '')
    if request.user.is_authenticated:
        if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
            return redirect(next_url)
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        guest_session_key = request.session.session_key
        user = form.get_user()
        login(request, user)
        from orders.views import get_or_create_cart
        get_or_create_cart(request, merge_session_key=guest_session_key)
        next_url = request.POST.get('next', '') or request.GET.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
            return redirect(next_url)
        return redirect('home')
    response = render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url
    })
    return response


@never_cache
@ensure_csrf_cookie
def customer_signup(request):
    next_url = request.POST.get('next', '') or request.GET.get('next', '')
    if request.user.is_authenticated:
        if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
            return redirect(next_url)
        return redirect('home')
    form = CustomerSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        guest_session_key = request.session.session_key
        user = form.save()
        login(request, user)
        from orders.views import get_or_create_cart
        get_or_create_cart(request, merge_session_key=guest_session_key)
        messages.success(request, 'Your account has been created.')
        if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
            return redirect(next_url)
        return redirect('home')
    response = render(request, 'accounts/signup.html', {
        'form': form,
        'next': next_url
    })
    return response



def customer_logout(request):
    if request.method == 'POST':
        logout(request)
    return redirect('home')


@login_required(login_url="customer_login")
def customer_account(request):
    if request.user.is_superuser:
        return redirect("admin_dashboard")

    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    addresses = request.user.saved_addresses.all()
    editing_address = None
    edit_id = request.GET.get("edit_address")
    if edit_id:
        editing_address = get_object_or_404(addresses, pk=edit_id)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_profile":
            profile_form = CustomerProfileForm(request.POST, instance=profile, user=request.user)
            address_form = CustomerAddressForm()
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Your account details have been updated.")
                return redirect("customer_account")
        elif action == "save_address":
            address_id = request.POST.get("address_id")
            editing_address = get_object_or_404(addresses, pk=address_id) if address_id else None
            address_form = CustomerAddressForm(request.POST, instance=editing_address)
            profile_form = CustomerProfileForm(instance=profile, user=request.user)
            if address_form.is_valid():
                with transaction.atomic():
                    address = address_form.save(commit=False)
                    address.user = request.user
                    make_default = request.POST.get("is_default") == "on" or not addresses.exists()
                    if make_default:
                        addresses.update(is_default=False)
                    address.is_default = make_default
                    address.save()
                messages.success(request, "Your delivery address has been saved.")
                return redirect("customer_account")
        elif action == "set_default":
            address = get_object_or_404(addresses, pk=request.POST.get("address_id"))
            with transaction.atomic():
                addresses.update(is_default=False)
                address.is_default = True
                address.save(update_fields=["is_default"])
            messages.success(request, f"{address.label} is now your default delivery address.")
            return redirect("customer_account")
        elif action == "delete_address":
            address = get_object_or_404(addresses, pk=request.POST.get("address_id"))
            was_default = address.is_default
            address.delete()
            if was_default:
                next_address = addresses.first()
                if next_address:
                    next_address.is_default = True
                    next_address.save(update_fields=["is_default"])
            messages.success(request, "The delivery address has been removed.")
            return redirect("customer_account")
        else:
            return redirect("customer_account")
    else:
        profile_form = CustomerProfileForm(instance=profile, user=request.user)
        address_form = CustomerAddressForm(instance=editing_address)

    return render(request, "accounts/account.html", {
        "profile_form": profile_form,
        "address_form": address_form,
        "addresses": addresses,
        "editing_address": editing_address,
    })


@login_required(login_url="customer_login")
@require_POST
def delete_customer_account(request):
    if request.user.is_superuser:
        return redirect("admin_dashboard")

    user = request.user
    with transaction.atomic():
        Order.objects.filter(user=user).update(
            user=None,
            name="Deleted customer",
            mobile=None,
            location="",
            latitude=None,
            longitude=None,
            instructions="",
        )
        user.delete()
    logout(request)
    messages.success(request, "Your account and saved addresses have been deleted.")
    return redirect("home")



@require_POST
def submit_feedback(request):
    # Honeypot field: real visitors never see or fill this input.
    if request.POST.get("website", "").strip():
        return redirect("home")

    form = CustomerFeedbackForm(request.POST)
    if form.is_valid():
        feedback = form.save(commit=False)
        if request.user.is_authenticated:
            feedback.user = request.user
        feedback.save()
        messages.success(request, "Thank you — your feedback has been received.")
    else:
        messages.error(request, "Please check the feedback form and try again.")

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        return redirect(next_url)
    return redirect("home")
