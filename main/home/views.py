from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import CustomerSignupForm
from store.models import Products
# Create your views here.
def home(request):
    products = Products.objects.filter(is_available=True)
    return render(request, 'home/index.html', {'products': products}   )


def customer_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get('next', '')
        if url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
            return redirect(next_url)
        return redirect('home')
    return render(request, 'accounts/login.html', {'form': form})


def customer_signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = CustomerSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Your account has been created.')
        return redirect('home')
    return render(request, 'accounts/signup.html', {'form': form})


def customer_logout(request):
    if request.method == 'POST':
        logout(request)
    return redirect('home')
