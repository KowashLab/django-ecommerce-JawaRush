from decimal import Decimal
from typing import Any, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from products.models import Product
from users.models import Address
from .models import Order, OrderItem
from .forms import CheckoutForm


def cart_detail(request):
    """Display shopping cart and remove stale (deleted/inactive) products from session."""
    cart = request.session.get('cart', {})
    items, total = _get_cart_items(cart)

    # Remove stale products from session
    valid_ids = {str(item['product'].id) for item in items}
    cleaned_cart = {k: v for k, v in cart.items() if k in valid_ids}
    if len(cleaned_cart) != len(cart):
        request.session['cart'] = cleaned_cart

    return render(request, 'cart.html', {
        'cart_items': items,
        'cart_total': total,
    })


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = request.session.get('cart', {})
    key = str(product_id)

    current_qty = cart.get(key, 0)
    new_qty = current_qty + 1
    if new_qty > product.stock:
        new_qty = product.stock

    if new_qty > 0:
        cart[key] = new_qty

    request.session['cart'] = cart
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect(request.META.get('HTTP_REFERER', 'cart_detail'))


@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    key = str(product_id)

    cart.pop(key, None)

    request.session['cart'] = cart
    return redirect('cart_detail')


@require_POST
def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = request.session.get('cart', {})
    key = str(product_id)

    if key not in cart:
        return redirect('cart_detail')

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    quantity = max(1, quantity)
    quantity = min(quantity, product.stock)

    cart[key] = quantity
    request.session['cart'] = cart
    return redirect('cart_detail')


def _get_cart_items(cart: dict[str, int]) -> tuple[list[dict[str, Any]], Decimal]:
    """Build cart items list and total from session cart dict."""
    items: list[dict[str, Any]] = []
    total = Decimal('0')
    for product_id, quantity in cart.items():
        product: Optional[Product] = Product.objects.filter(id=product_id, is_active=True).first()
        if product is None:
            continue
        subtotal = product.price * quantity
        total += subtotal
        items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })
    return items, total


def create_order_email_text(order: Order) -> str:
    """Format order details for email notification to customer and admins."""
    items = order.items.select_related('product').all()
    item_lines = "\n".join(f"{item.product.name} - {item.quantity}" for item in items)

    return (
        f"Order ID: {order.id}\n"
        f"Name: {order.full_name}\n"
        f"Phone: {order.phone}\n"
        f"Address: {order.shipping_address}\n"
        f"\n"
        f"Items:\n"
        f"{item_lines}\n"
        f"\n"
        f"Total: {order.total_price}"
    )


def send_order_notification(order: Order) -> None:
    """Send order email to customer and admin addresses."""
    body = create_order_email_text(order)
    subject = f"Order #{order.id}"
    from_email = settings.DEFAULT_FROM_EMAIL

    if order.user and order.user.email:
        send_mail(subject, body, from_email, [order.user.email], fail_silently=True)

    admin_emails = [addr for _, addr in settings.ADMINS]
    if admin_emails:
        send_mail(subject, body, from_email, admin_emails, fail_silently=True)


def checkout(request):
    """Handle checkout flow: validate cart, accept shipping/payment, create order atomically."""
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart_detail')

    cart_items, cart_total = _get_cart_items(cart)
    saved_addresses = Address.objects.none()
    selected_address_id = None

    if request.user.is_authenticated:
        saved_addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if not cart_items:
        return redirect('cart_detail')

    if request.method == 'POST':
        use_saved_address = request.user.is_authenticated and saved_addresses.exists()
        form = CheckoutForm(request.POST, use_saved_address=use_saved_address)
        selected_address_id = request.POST.get('address_id')
        if form.is_valid():
            shipping_full_name = form.cleaned_data['full_name']
            shipping_phone = form.cleaned_data['phone']
            shipping_text = form.cleaned_data['shipping_address']

            if use_saved_address:
                selected_address = None
                if selected_address_id:
                    selected_address = saved_addresses.filter(id=selected_address_id).first()

                if selected_address is None:
                    selected_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()

                if selected_address is None:
                    form.add_error(None, 'Please add an address in your account before checkout.')
                else:
                    selected_address_id = str(selected_address.id)
                    shipping_full_name = selected_address.full_name
                    shipping_phone = selected_address.phone
                    shipping_text = (
                        f"{selected_address.city}, {selected_address.address_line}, {selected_address.postal_code}"
                    )

            if form.errors:
                return render(request, 'checkout.html', {
                    'form': form,
                    'cart_items': cart_items,
                    'cart_total': cart_total,
                    'saved_addresses': saved_addresses,
                    'selected_address_id': selected_address_id,
                })

            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        full_name=shipping_full_name,
                        phone=shipping_phone,
                        shipping_address=shipping_text,
                        payment_method=form.cleaned_data['payment_method'],
                        total_price=Decimal('0'),
                    )

                    total = Decimal('0')
                    for product_id, quantity in cart.items():
                        product = Product.objects.filter(id=product_id, is_active=True).first()
                        if product is None:
                            continue
                        quantity = min(quantity, product.stock)
                        if quantity < 1:
                            continue

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.price,
                        )
                        product.stock -= quantity
                        product.save(update_fields=['stock'])
                        total += product.price * quantity

                    order.total_price = total
                    order.save()

                    if not order.items.exists():
                        order.delete()
                        return redirect('cart_detail')
            except Exception:
                # Any error inside atomic block rolls back order and order items.
                messages.error(request, 'Failed to place order. Please try again.')
                return redirect('cart_detail')

            request.session['cart'] = {}

            send_order_notification(order)

            return render(request, 'order_confirmation.html', {
                'order': order,
            })
    else:
        use_saved_address = request.user.is_authenticated and saved_addresses.exists()
        form = CheckoutForm(use_saved_address=use_saved_address)
        if use_saved_address:
            default_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()
            if default_address:
                selected_address_id = str(default_address.id)

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'saved_addresses': saved_addresses,
        'selected_address_id': selected_address_id,
    })


@require_POST
def process_payment(request, order_id):
    """Update order status to PAID after successful payment."""
    order = get_object_or_404(Order, id=order_id)
    if request.user.is_authenticated:
        if order.user != request.user:
            return redirect('home')
    else:
        if order.user is not None:
            return redirect('home')
    if order.status != Order.Status.PENDING:
        return redirect('home')
    order.status = Order.Status.PAID
    order.save()
    return render(request, 'payment_success.html', {'order': order})
