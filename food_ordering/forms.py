from django import forms
from django.core.validators import MinValueValidator
from .models import Order, OrderItem

class OrderForm(forms.ModelForm):
    customer_name = forms.CharField(
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe'
        }),
        max_length=100,
        required=True
    )
    
    delivery_address = forms.CharField(
        label="Delivery Address",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '123 Main St, City, State ZIP'
        }),
        required=False
    )
    
    contact_number = forms.CharField(
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1 (123) 456-7890'
        }),
        max_length=20,
        required=False
    )

    class Meta:
        model = Order
        fields = ['customer_name', 'contact_number', 'delivery_address']
        
    def clean_customer_name(self):
        name = self.cleaned_data['customer_name']
        if len(name.strip()) < 2:
            raise forms.ValidationError("Please enter a valid name")
        return name.strip()

class AddToOrderForm(forms.Form):
    quantity = forms.IntegerField(
        label="Quantity",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'value': 1
        }),
        validators=[MinValueValidator(1)],
        initial=1
    )
    
    special_requests = forms.CharField(
        label="Special Instructions",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any special requests or allergies...'
        }),
        required=False
    )
    
    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity > 20:
            raise forms.ValidationError("Maximum 20 items per selection. Please contact us for bulk orders.")
        return quantity

class OrderStatusForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,  # Use model's choices
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any notes about order status...'
        }),
        required=False
    )

    class Meta:
        model = Order
        fields = ['status', 'notes']