from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from orders.models import Order
from .forms import RegisterForm, LoginForm, ProfileForm, AddressForm
from .models import Address

User = get_user_model()


def register_view(request):
    """Register new user with password validation. Redirect authenticated users to home."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            try:
                validate_password(password)
            except ValidationError as e:
                form.add_error('password', e)
            else:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=password,
                )
                login(request, user)
                return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    """Authenticate user and create session. Redirect authenticated users to home."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('account')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})


@login_required(login_url='login')
def account_view(request):
    """User account dashboard with address management, order history, and status filtering."""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_address':
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user

                if address.is_default or not addresses.exists():
                    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                    address.is_default = True

                address.save()
                messages.success(request, 'Address added successfully.')
                return redirect('account')
        elif action == 'set_default':
            address_id = request.POST.get('address_id')
            selected = Address.objects.filter(user=request.user, id=address_id).first()
            if selected:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
                selected.is_default = True
                selected.save(update_fields=['is_default'])
                messages.success(request, 'Default address updated.')
                return redirect('account')
            messages.error(request, 'Address not found.')
            address_form = AddressForm()
        else:
            address_form = AddressForm()
    else:
        address_form = AddressForm()

    orders = Order.objects.filter(user=request.user)

    status = request.GET.get('status')
    if status and status in Order.Status.values:
        orders = orders.filter(status=status)

    return render(request, 'account.html', {
        'orders': orders,
        'addresses': addresses,
        'address_form': address_form,
        'statuses': Order.Status.choices,
        'current_status': status,
    })
