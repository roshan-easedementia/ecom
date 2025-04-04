from django.contrib import admin

# Register your models here.
from . models import *


class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'is_active')


class WishListAdmin(admin.ModelAdmin):
    list_display = ('guest', 'user', 'product')


class OrderProductInline(admin.TabularInline):
    model=  OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra=0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'status', 'is_ordered', 'created_at')
    list_filter = ('status', 'is_ordered')
    search_fields = ('order_number', 'first_name', 'last_name', 'phone', 'email')
    list_per_page = 20
    inlines = [OrderProductInline]

class OrderProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'product_price', 'payment', 'order', 'quantity', 'created_at')


class CouponAdmin(admin.ModelAdmin):
    list_display = ('coupon_code', 'discount_amount', 'minimum_amount', 'valid_from', 'valid_to ')




admin.site.register(UserProfile)
admin.site.register(OTP)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(ShippingAddress)
admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(WishList, WishListAdmin)
admin.site.register(Guest)
admin.site.register(Coupon)
admin.site.register(Wallet)
admin.site.register(Coupon_Redeemed_Details)