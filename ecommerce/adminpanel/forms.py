from django import forms
from .models import Product

class AddProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [ 'product_name', 'category', 'brand', 'description', 'price', 'image']
