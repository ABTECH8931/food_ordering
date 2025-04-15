from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.db.models import Prefetch, Sum
from django.db.models import Q
from django.contrib.auth.views import LogoutView
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import TemplateView
from .models import Category, MenuItem, Order, OrderItem
from .forms import OrderForm, AddToOrderForm
from .models import Order
from food_ordering import models


class AboutView(TemplateView):
    template_name = 'food_ordering/about.html'

class ContactView(TemplateView):
    template_name = 'food_ordering/contact.html'

def menu_view(request):
    """Display menu with categories"""
    categories = Category.objects.prefetch_related(
        Prefetch('menu_items', 
                queryset=MenuItem.objects.filter(is_available=True),
                to_attr='available_items')
    ).all()
    
    return render(request, 'food_ordering/menu.html', {
        'categories': [cat for cat in categories if cat.available_items]
    })

def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item.get('quantity', 0) for item in cart.values())
    return {'cart_count': count}

# views.py
def category_menu_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    return render(request, 'food_ordering/category_detail.html', {
        'category': category  # Only pass the category
    })


def category_menu_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    menu_items = MenuItem.objects.filter(category=category, is_available=True)
    return render(request, 'food_ordering/category_menu.html', {
        'category': category,
        'menu_items': menu_items
    })

def start_order(request):
    # Check for existing draft order
    order_id = request.session.get('current_order_id')
    if order_id:
        order = Order.objects.filter(id=order_id, status='draft').first()
        if order:
            return redirect('food_ordering:view_current_order')
    
    # Create new order
    order = Order.objects.create(status='draft')
    request.session['current_order_id'] = order.id
    return redirect('food_ordering:menu')

@transaction.atomic
def add_to_order(request, menu_item_id):
    order_id = request.session.get('current_order_id')
    if not order_id:
        messages.warning(request, "Please start an order first")
        return redirect('food_ordering:start_order')
    
    order = get_object_or_404(Order, id=order_id)
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)

    if request.method == 'POST':
        form = AddToOrderForm(request.POST)
        if form.is_valid():
            try:
                # Add to database
                order_item = order.add_item(
                    menu_item=menu_item,
                    quantity=form.cleaned_data['quantity'],
                    special_requests=form.cleaned_data.get('special_requests', '')
                )
                # Add to session cart
                cart = request.session.get('cart', {})
                item_key = f'item_{order_item.id}'
                cart[item_key] = {
                    'id': order_item.id,
                    'menu_item_id': menu_item.id,
                    'name': menu_item.name,
                    'quantity': form.cleaned_data['quantity'],
                    'price': float(menu_item.price),
                    'special_requests': form.cleaned_data.get('special_requests', '')
                }
                request.session['cart'] = cart
                request.session.modified = True
                messages.success(request, f"Added {menu_item.name} to your order")
                return redirect('food_ordering:view_order_detail', order_id=order.id)
            except Exception as e:
                messages.error(request, f"Error adding item: {str(e)}")
                return redirect('food_ordering:add_item_to_order_form', menu_item_id=menu_item_id)
        else:
            return render(request, 'food_ordering/add_to_order.html', {
                'menu_item': menu_item,
                'form': form,
                'order': order,
            })
    else:
        return redirect('food_ordering:add_item_to_order_form', menu_item_id=menu_item_id)
            
def view_current_order(request):
    """Handle /order/view/ (current order from session)"""
    order_id = request.session.get('current_order_id')
    if not order_id:
        messages.info(request, "You don't have an active order")
        return redirect('food_ordering:menu')
    return redirect('food_ordering:view_order_detail', order_id=order_id)

def view_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('order_items__menu_item'),
        id=order_id
    )
    # Get session cart for comparison (optional)
    cart = request.session.get('cart', {})
    print(f"Session cart: {cart}")
    print(f"Order ID: {order.id}")
    print(f"Order items count: {order.order_items.count()}")
    for item in order.order_items.all():
        print(f"- {item.quantity}x {item.menu_item.name}")
    
    return render(request, 'food_ordering/view_order.html', {
        'order': order,
        'order_items': order.order_items.all(),
        'cart': cart  # Pass session cart to template if needed
    })

def order_confirmation(request, order_id):
    """Show order confirmation"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'food_ordering/order_confirmation.html', {
        'order': order
    })

def menu_search_view(request):
    query = request.GET.get('q', '')
    results = MenuItem.objects.filter(name__icontains=query) if query else []
    return render(request, 'food_ordering/menu_search.html', {
        'results': results,
        'query': query
    })

def update_order_item(request, item_id):
    """Update quantity of an order item"""
    if request.method == 'POST':
        order_item = get_object_or_404(OrderItem, id=item_id)
        new_quantity = int(request.POST.get('quantity', 1))
        
        if new_quantity > 0:
            order_item.quantity = new_quantity
            order_item.save()
            order_item.order.update_total()  # Update total after quantity change
            messages.success(request, "Quantity updated")
        else:
            messages.error(request, "Quantity must be at least 1")
            
    return redirect('food_ordering:view_order_detail', order_id=order_item.order.id)

def remove_order_item(request, item_id):
    """Remove an item from the order"""
    order_id = request.session.get('current_order_id')
    if not order_id:
        messages.error(request, "No active order found")
        return redirect('food_ordering:menu')

    try:
        # Ensure the OrderItem belongs to the current order
        order_item = OrderItem.objects.get(id=item_id, order__id=order_id)
        order = order_item.order
        order_item.delete()
        # Update order total after deletion
        order.update_total()
        messages.success(request, "Item removed from order")
    except OrderItem.DoesNotExist:
        messages.warning(request, "Item not found in order")

    # Sync session-based cart
    cart = request.session.get('cart', {})
    item_key = f'item_{item_id}'
    if item_key in cart:
        del cart[item_key]
        request.session['cart'] = cart
        request.session.modified = True

    return redirect('food_ordering:view_current_order')
    
def account_view(request):
    # For session-based orders, we'll show orders tied to the current session
    if not request.session.session_key:
        # Create a session if one doesn't exist
        request.session.create()
    
    # Get orders for the current session
    orders = Order.objects.filter(
        session_key=request.session.session_key
    ).order_by('-created_at')
    
    return render(request, 'food_ordering/account.html', {
        'orders': orders,
        # Include session key for debugging (optional)
        'session_key': request.session.session_key[:8] + '...' if request.session.session_key else None
    })

def order_history(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'food_ordering/order_detail.html', {'order': order})

def create_order_form(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = 'draft'  # Changed from 'pending'
            order.session_key = request.session.session_key
            order.save()
            request.session['current_order_id'] = order.id
            messages.success(request, "Order created! Add items to your cart.")
            return redirect('food_ordering:menu')
    else:
        form = OrderForm()
    return render(request, 'food_ordering/create_order_form.html', {'form': form})

@transaction.atomic
def submit_order(request):
    order_id = request.session.get('current_order_id')
    if not order_id:
        messages.error(request, "No active order found")
        return redirect('food_ordering:menu')
    
    order = get_object_or_404(Order, id=order_id)
    order.status = 'completed'
    order.save()
    # Clear session
    request.session['cart'] = {}
    if 'current_order_id' in request.session:
        del request.session['current_order_id']
    request.session.modified = True
    messages.success(request, "Order submitted successfully!")
    return redirect('food_ordering:order_confirmation', order_id=order.id)

def checkout(request, order_id):  # Accept order_id from URL
    order = get_object_or_404(Order, id=order_id, status='draft')
    
    if request.method == 'POST':
        order.status = 'submitted'
        order.save()
        # Clear cart session if needed
        if 'cart' in request.session:
            del request.session['cart']
        messages.success(request, "Order submitted successfully!")
        return redirect('food_ordering:order_confirmation', order_id=order.id)
    
    return render(request, 'food_ordering/checkout.html', {
        'order': order,
        'order_items': order.order_items.all()
    })

def add_item_to_order_form(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)
    form = AddToOrderForm()
    order_id = request.session.get('current_order_id')
    order = None
    if order_id:
        order = get_object_or_404(Order, id=order_id)

    return render(request, 'food_ordering/add_to_order.html', {
        'menu_item': menu_item,
        'form': form,
        'order': order,
    })