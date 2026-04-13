from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from products.models import Product
from .models import Order, OrderItem
from .forms import CheckoutForm


def cart_detail(request):
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


def _get_cart_items(cart):
    """Build cart items list and total from session cart dict."""
    items = []
    total = Decimal('0')
    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id, is_active=True).first()
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


def create_order_email_text(order):
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


def send_order_notification(order):
    body = create_order_email_text(order)
    subject = f"Order #{order.id}"
    from_email = settings.DEFAULT_FROM_EMAIL

    if order.user and order.user.email:
        send_mail(subject, body, from_email, [order.user.email], fail_silently=True)

    admin_emails = [addr for _, addr in settings.ADMINS]
    if admin_emails:
        send_mail(subject, body, from_email, admin_emails, fail_silently=True)


def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart_detail')

    cart_items, cart_total = _get_cart_items(cart)

    if not cart_items:
        return redirect('cart_detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    full_name=form.cleaned_data['full_name'],
                    phone=form.cleaned_data['phone'],
                    shipping_address=form.cleaned_data['shipping_address'],
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

            request.session['cart'] = {}

            send_order_notification(order)

            return render(request, 'order_confirmation.html', {
                'order': order,
            })
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'cart_total': cart_total,
    })


@require_POST
def process_payment(request, order_id):
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
