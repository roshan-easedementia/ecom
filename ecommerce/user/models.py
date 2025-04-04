from django.db import models
from django.contrib.auth import get_user_model
from adminpanel.models import Product, Variation
from django.contrib.auth.models import AbstractUser,User
from django.utils import timezone

# Create your models here.
User = get_user_model()

class OTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=255, default='')
    mobile = models.CharField(max_length=15, default='')
    is_blocked = models.BooleanField(default=False)
    referral_id = models.CharField(max_length=8, default='', unique=True)
    

    def __str__(self):
        return self.user.username
    


class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city =models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.first_name
    

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id
    

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ForeignKey(Variation, on_delete=models.SET_NULL, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)



    def sub_total(self):
        return self.product.price * self.quantity


    def __str__(self):
        return self.product.product_name
    




class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    discount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return self.payment_id





class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Cancelled', 'Cancelled'),
        ('Delivered', 'Delivered'),
        ('Returned', 'Returned'),
    )


    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=150)
    address_line_1 = models.CharField(max_length=150)
    address_line_2 = models.CharField(max_length=150)
    city = models.CharField(max_length=150)
    state = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    pincode = models.CharField(max_length=10)
    order_total = models.FloatField()
    
    status = models.CharField(max_length=10, choices=STATUS, default='New')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    

    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    
    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2}"
    
    # def __str__(self):
    #     return f'{self.order_total}'
    



class OrderProduct(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_price = models.FloatField()
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ordered = models.BooleanField(default=False)
    color = models.CharField(max_length=50)
    size = models.CharField(max_length=50)


    @property
    def get_total(self):
        total = self.product_price * self.quantity
        return total
    

class Guest(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    # Add any other fields you need for a guest

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Invoice(models.Model):
    ordered_product = models.ForeignKey(OrderProduct, on_delete=models.CASCADE)
    invoice_path = models.CharField(max_length=255)  # Store the path to the generated PDF invoice



class WishList(models.Model):
	guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
	product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
	date_added = models.DateField(default=timezone.now)



class Coupon(models.Model):
    coupon_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_amount = models.IntegerField(default=100)
    valid_from = models.DateField()
    valid_to = models.DateField()


    def is_redeemed_by_user(self, user):
        redeemed_details = Coupon_Redeemed_Details.objects.filter(coupon=self, user=user, is_redeemed=True)
        return redeemed_details.exists()


class Coupon_Redeemed_Details(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    date_added = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_redeemed = models.BooleanField(default=False)

    


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    amount = models.FloatField(default=100)
    referral_id = models.CharField(max_length=20, unique=True, null=True)
    referrer = models.ForeignKey(User, related_name='referrals', null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.amount = round(self.amount, 2)
        super().save(*args, **kwargs)
