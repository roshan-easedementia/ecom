from django.contrib import admin
from .models import *


# Register your models here.
admin.site.register(Admin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}

    
admin.site.register(Product)
admin.site.register(ProductImage)

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug')


class VariationAdmin(admin.ModelAdmin):
    list_display = ('product', 'variation_category', 'variation_value', 'is_active')
    list_editable = ('is_active',)
    list_filter = list_display = ('product', 'variation_category', 'variation_value', 'is_active')


admin.site.register(Category, CategoryAdmin)
admin.site.register(UserList)
admin.site.register(Brand)
admin.site.register(Variation, VariationAdmin)
admin.site.register(Offer)
admin.site.register(Stock)




