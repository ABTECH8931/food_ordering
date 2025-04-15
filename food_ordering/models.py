from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=100, blank=True, null=True) 
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    delivery_address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_item(self, menu_item, quantity=1, special_requests=''):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        order_item, created = OrderItem.objects.get_or_create(
            order=self,
            menu_item=menu_item,
            defaults={
                'quantity': quantity,
                'special_requests': special_requests
            }
        )
        if not created:
            order_item.quantity += quantity
            if special_requests:
                if order_item.special_requests:
                    order_item.special_requests += f"\n{special_requests}"
                else:
                    order_item.special_requests = special_requests
            order_item.save()
        self.update_total()  # Calls the new method
        return order_item
    
    def update_total(self):
        """Recalculates the order total based on all items"""
        self.total_price = sum(
            item.menu_item.price * item.quantity 
            for item in self.order_items.all()
        )
        self.save()

    def __str__(self):
        return f"Order #{self.id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    special_requests = models.TextField(blank=True)

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"