from django import forms

from .models import Order


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        label='Full Name',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Value'}),
    )
    phone = forms.CharField(
        max_length=20,
        label='Phone number',
        widget=forms.TextInput(attrs={'class': 'Input', 'placeholder': 'Value', 'type': 'tel'}),
    )
    shipping_address = forms.CharField(
        label='Shipping address',
        widget=forms.Textarea(attrs={'class': 'Textarea', 'placeholder': 'Value', 'rows': 3}),
    )
    payment_method = forms.ChoiceField(
        choices=Order.PaymentMethod.choices,
        initial='card',
        label='Payment method',
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, use_saved_address: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        if use_saved_address:
            self.fields['full_name'].required = False
            self.fields['phone'].required = False
            self.fields['shipping_address'].required = False
