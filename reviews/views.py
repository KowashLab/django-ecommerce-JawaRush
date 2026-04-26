from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from orders.models import Order
from products.models import Product

from .models import Review


def _has_purchased_product(user_id: int, product_id: int) -> bool:
	"""Return True if a user has at least one order containing the product."""
	return Order.objects.filter(user_id=user_id, items__product_id=product_id).exists()


def _parse_rating(raw_rating: str) -> Optional[int]:
	"""Parse rating from POST and validate 1..5 range."""
	try:
		rating = int(raw_rating)
	except (ValueError, TypeError):
		return None
	if 1 <= rating <= 5:
		return rating
	return None


@login_required(login_url='login')
@require_POST
def create_review(request: HttpRequest, slug: str) -> HttpResponse:
	"""Create a review after validating purchase history and preventing duplicate reviews."""
	product = get_object_or_404(Product, slug=slug, is_active=True)

	if not _has_purchased_product(request.user.id, product.id):
		messages.error(request, 'Only customers who purchased this product can leave a review.')
		return redirect('product_detail', slug=product.slug)

	if Review.objects.filter(product=product, user=request.user).exists():
		messages.error(request, 'You have already reviewed this product.')
		return redirect('product_detail', slug=product.slug)

	rating = _parse_rating(request.POST.get('rating', ''))
	comment = request.POST.get('comment', '').strip()

	if rating is None:
		messages.error(request, 'Rating must be an integer from 1 to 5.')
		return redirect('product_detail', slug=product.slug)

	if not comment:
		messages.error(request, 'Comment cannot be empty.')
		return redirect('product_detail', slug=product.slug)

	Review.objects.create(
		product=product,
		user=request.user,
		rating=rating,
		comment=comment,
	)
	messages.success(request, 'Your review has been added.')
	return redirect('product_detail', slug=product.slug)
