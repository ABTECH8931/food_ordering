# food_ordering/context_processors.py
from .models import Order

def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item.get('quantity', 0) for item in cart.values())
    return {'cart_count': count}