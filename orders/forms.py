from django import forms


PAYMENT_CHOICES = [
    ('card', 'Card'),
    ('cash', 'Cash'),
]


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
        choices=PAYMENT_CHOICES,
        initial='card',
        label='Payment method',
        widget=forms.RadioSelect,
    )
