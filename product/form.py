from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    """
    Form to create a new product
    """
    class Meta:
        """
        Meta class to define the model and fields
        """
        model = Product
        fields = ['name', 'barcode', 'price', 'stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        } 