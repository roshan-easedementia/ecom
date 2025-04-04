from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate,login, get_user_model, logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseRedirect
import random, os
from django_otp import user_has_device, devices_for_user
from .models import OTP, UserProfile, Order, OrderProduct, WishList,Guest,Payment, Coupon, CartItem, Coupon_Redeemed_Details
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from adminpanel.models import Product, Category, Variation, Stock
from user.models import Cart, CartItem, ShippingAddress, OrderProduct, Invoice, Wallet
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import OrderForm
import datetime
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from datetime import date
import string
from django.utils import timezone
from django.urls import reverse


# Create your views here.

def index(request):
    products = Product.objects.filter(is_active=True)
    paginator = Paginator(products, 8)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    category = Category.objects.all()


    # Search functionality
    search_query = request.GET.get('search_product')
    print(search_query)
    if search_query:
        
        products = products.filter(Q(product_name__icontains=search_query) | Q(description__icontains=search_query))

    # Filtering based on price range
    price_range = request.GET.get('price_range')
    print(price_range)
    if price_range:
        
        min_price, max_price = map(int, price_range.split('-'))
        products = products.filter(price__gte=min_price, price__lte=max_price)

    # Sorting
    sort_by = request.GET.get('sort_by')
    
    if sort_by == 'newness':
        products = products.order_by('-created_at')
    elif sort_by == 'price_low_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-price')

    paginator = Paginator(products, 8)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

   

    context = {
        'products': paged_products,
        'user': request.user,
        'category': category,
        # 'page_obj': page_obj, 
    }
    return render(request, 'user_side/index.html', context)


def generate_otp():
    #generate a random otp of 6 digits
    return str(random.randint(100000, 999999))


def login_with_email_and_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id = _cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    #Getting the product variations by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))


                    #Get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)

                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)


                    #To get common product variations in both lists
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()


            except:
                pass
            # If the user has already set up an OTP device (TOTP)
            # Generate OTP
            otp_value = generate_otp()

            # Save the OTP to the database
            otp = OTP.objects.create(user=user)
            otp.otp = otp_value
            otp.save()

            # Send the OTP to the user's email
            send_otp_email(email, otp_value)
            print('******otp_value******', otp_value)
            

            # Prepare the context for OTP verification view
            context = {'user': user, 'is_login': True}
            return redirect('verify_otp_login', email=email)
        else:
            return render(request, 'user_side/login.html', {'error': 'Invalid email or password.'})

    return render(request, 'user_side/login.html')





def send_otp_email(email, otp_value):
    subject = 'OTP Verification'
    message = f'Your OTP for verification is: {otp_value}'
    from_email = 'roshanzacharias20@gmail.com'  # Replace with your email address
    recipient_list = [email]

    # Use the Django send_mail function to send the OTP
    send_mail(subject, message, from_email, recipient_list)




def send_otp_forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            # Handle the case where the user doesn't exist
            # You can display an error message and redirect to the forgot password page
            messages.error(request, 'Invalid Credentials!')
            return redirect('forgot_password')  # Replace with your forgot password URL

        otp_value = generate_otp()  # Generate the OTP
        otp = OTP.objects.create(user=user, otp=otp_value)  # Save the OTP to your OTP model

        send_otp_email(email, otp_value)  # Send the OTP via email

        # Redirect to OTP verification page
        return redirect('verify_otp_reset_password', email=email)  # Replace with your OTP verification URL
    else:
        return redirect('forgot_password')  # Redirect back to the forgot password page if not a POST request



    
def verify_otp(request, email):
    if request.method == 'POST':
        otp_value = request.POST.get('otp')

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            messages.error(request, 'Invalid user ID.')
            return render(request, 'user_side/login.html')

        otp = OTP.objects.filter(user=user, otp=otp_value).first()
        if otp:
            # Validate the OTP and log in the user
            otp.delete()  # Remove the used OTP from the database
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Login successful!')
            return redirect('login_with_email_and_otp')  # Replace 'home' with the name of your home page URL
        else:
            messages.error(request, 'Invalid OTP.')

    return render(request, 'user_side/verify_otp.html', {'email': email})



def verify_otp_login(request, email):
    if request.method == 'POST':
        otp_value = request.POST.get('otp')

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            messages.error(request, 'Invalid email.')
            return redirect('login')

        otp = OTP.objects.filter(user=user, otp=otp_value).first()
        if otp:
            # Validate the OTP and log in the user
            otp.delete()  # Remove the used OTP from the database
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Login successful!')
            return redirect('index')  # Replace 'index.html' with your home page URL
        else:
            messages.error(request, 'Invalid OTP.')

    return render(request, 'user_side/verify_otp_login.html', {'email': email})




def verify_otp_reset_password(request, email):
    if request.method == 'POST':
        otp_value = request.POST.get('otp')

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            # Handle the case where the user doesn't exist
            # You can display an error message and redirect to the forgot password page
            return redirect('forgot_password')  # Replace with your forgot password URL

        otp = OTP.objects.filter(user=user, otp=otp_value).first()
        if otp:
            # Validate the OTP and redirect to the login page
            # You might want to implement further checks here before redirecting
            otp.delete()  # Remove the used OTP from the database
            return redirect('set_new_password', email=email)  
        else:
            # Handle the case of an invalid OTP
            # You can display an error message and redirect to the OTP verification page
            return redirect('verify_otp_reset_password', email=email)  # Replace with your OTP verification URL

    return render(request, 'user_side/verify_otp_reset_password.html', {'email': email})



def set_new_password(request, email):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            # Update the user's password
            user = get_user_model().objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # Redirect to the login page
            return redirect('login')  # Replace with your login URL
        else:
            # Handle the case of password mismatch
            pass

    return render(request, 'user_side/set_new_password.html', {'email': email})





@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('index')


def forgot_password(request):
    return render(request, 'user_side/forgot_password.html')




def generate_unique_referral_id():
    length = 8  # You can adjust the length of the referral ID as needed
    while True:
        referral_id = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if not UserProfile.objects.filter(referral_id=referral_id).exists():
            return referral_id





REFERRAL_BONUS_AMOUNT = 100  # Adjust this value as needed
NEW_USER_BONUS_AMOUNT = 50   # Adjust this value as needed

def register_user(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        confirm_password = request.POST.get('confirm_password')
        referral_code = request.POST.get('ref_code')  # Get the referral ID from the form
        
        # Check if the email is already registered
        if UserProfile.objects.filter(email=email).exists():
            return render(request, 'user_side/user_signup.html', {'error': 'Email already registered.'})
        
        # Check if the passwords match
        if password != confirm_password:
            return render(request, 'user_side/user_signup.html', {'error': 'Passwords do not match.'})
        
        # Create a new User instance and save it to the database
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()

        # Create a new UserProfile instance and save it to the database
        user_profile = UserProfile.objects.create(user=user, email=email, name=name, mobile=mobile)

        # Generate OTP and save it to the database
        otp_value = generate_otp()
        otp = OTP.objects.create(user=user)
        otp.otp = otp_value
        otp.save()

        # Send the OTP to the user's email
        send_otp_email(email, otp_value)
        print('*******send_otp_email*******', otp_value)

        # Generate a unique referral ID for the user
        referral_id = generate_unique_referral_id()
        user_profile.referral_id = referral_id
        user_profile.save()

        # Create a Wallet object for the new user
        user_wallet = Wallet.objects.get_or_create(user=user, defaults={'amount': 0})


        



        # Check if a referral code is provided
        if referral_code:
            try:
                referrer = UserProfile.objects.get(referral_id=referral_code)
                
                # Credit the referrer's wallet
                referrer_wallet = Wallet.objects.get(user=referrer.user)
                referrer_wallet.amount += 250  # Adjust the amount as needed
                referrer_wallet.save()

                # Credit the new user's wallet
                user_wallet = Wallet.objects.get(user=user)
                user_wallet.amount += 250  # Adjust the amount as needed
                user_wallet.save()

            except UserProfile.DoesNotExist:
                messages.error(request, 'Invalid referral code.')
        

        # Prepare the context for OTP verification view
        context = {'user': user_profile.user, 'is_login': False}
        return redirect('verify_otp', email=email)
    
    return render(request, 'user_side/user_signup.html')



def product_detail(request, product_id):
    products = get_object_or_404(Product, pk=product_id)
    in_cart = CartItem.objects.filter(cart__cart_id= _cart_id(request), product=products).exists()
    context = {
        'products': products,
        'in_cart': in_cart,
    }
    return render(request, 'user_side/product-detail.html', context)




def jersey_category(request):
    category = get_object_or_404(Category, category_name='Jersey')
    products = Product.objects.filter(category=category)
    return render(request, 'user_side/category_view.html', {'category': category, 'products': products})


def boot_category(request):
    category = get_object_or_404(Category, category_name='Boot')
    products = Product.objects.filter(category=category)
    return render(request, 'user_side/category_view.html', {'category': category, 'products': products})


def equipments_category(request):
    category = get_object_or_404(Category, category_name='Equipments')
    products = Product.objects.filter(category=category)
    return render(request, 'user_side/category_view.html', {'category': category, 'products': products})

def accessories_category(request):
    category = get_object_or_404(Category, category_name='Accessories')
    products = Product.objects.filter(category=category)
    return render(request, 'user_side/category_view.html', {'category': category, 'products': products})






def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart






def add_cart(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    print("Product:", product)

    # Fetch stock for the product
    stock_entry = Stock.objects.filter(product=product).first()
    print("stock_entry:", stock_entry)

    if not stock_entry or stock_entry.stock <= 0:
        messages.warning(request, 'This item is out of stock.')
        return redirect('product_detail', product_id=product_id)

    if request.user.is_authenticated:
        is_cart_item_exists = CartItem.objects.filter(user=request.user, product=product).exists()
        
        if is_cart_item_exists:
            cart_item = CartItem.objects.get(user=request.user, product=product)
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem(user=request.user, product=product, quantity=1)
            cart_item.save()
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        is_cart_item_exists = CartItem.objects.filter(cart=cart, product=product).exists()
        
        if is_cart_item_exists:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = CartItem(cart=cart, product=product, quantity=1)
            cart_item.save()

    # Reduce stock by 1
    stock_entry.stock -= 1
    stock_entry.save()

    return redirect('shopping_cart')


# def add_cart(request, product_id):
#     color = request.GET.get('color')
#     size = request.GET.get('size')
#     if color is None and size is None:
#         messages.warning(request, 'Please select an option before adding to cart.')
#         return redirect('product_detail', product_id)
    
#     product = Product.objects.get(product_id=product_id)

    
    
#     try:
#         variant = Variation.objects.get(id=size)
#     except:
#         variant = Variation.objects.get(id=color)


#     if variant.stock >= 1:
#         if request.user.is_authenticated:
#             is_cart_item_exists = CartItem.objects.filter(user=request.user, product=product, variations=variant).exists()
#             if is_cart_item_exists:
#                 to_cart = CartItem.objects.get(user=request.user, product=product, variations=variant)
#                 to_cart.quantity += 1
#                 # variant.stock -= 1
#                 to_cart.save()
#                 # variant.save()
#             else:
#                 to_cart = CartItem(user=request.user, product=product, variations=variant, quantity=1)
#                 # variant.stock -= 1
#                 to_cart.save()
#                 # variant.save()

#             return redirect('shopping_cart')

#         else:
#             try:
#                 cart = Cart.objects.get(cart_id=_cart_id(request))
#             except Cart.DoesNotExist:
#                 cart = Cart.objects.create(cart_id = _cart_id(request))

#             cart.save()
#             is_cart_item_exists = CartItem.objects.filter(cart=cart, product=product, variations=variant).exists()
            
#             if is_cart_item_exists:
#                 to_cart = CartItem.objects.get(cart=cart, product=product, variations=variant)
#                 to_cart.quantity += 1
#                 # variant.stock -= 1
#                 to_cart.save()
#                 # variant.save()
#             else:
#                 to_cart = CartItem(cart=cart, product=product, variations=variant, quantity=1)
#                 # variant.stock -= 1
#                 to_cart.save()
#                 # variant.save()
#             return redirect('shopping_cart')
#     else:
        
#         messages.warning(request, 'This item is out of stock.')
#         return redirect('product_detail', product_id)





            



def add_quantity_to_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, product_id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart_item = CartItem.objects.get(product=product, cart__cart_id=_cart_id(request), id=cart_item_id)

        stock_entry = Stock.objects.filter(product=product).first()

        if stock_entry and stock_entry.stock > 0 and cart_item.quantity < stock_entry.stock:
            cart_item.quantity += 1
            cart_item.save()

            stock_entry.stock -= 1
            stock_entry.save()
        else:
            print("Not enough stock")
    except CartItem.DoesNotExist:
        messages.error(request, "This item does not exist in your cart.")
        return redirect('shopping_cart')
    return HttpResponseRedirect(reverse('shopping_cart'))




def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, product_id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        # Fetch stock entry for the product
        stock_entry = Stock.objects.filter(product=product).first()

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()

            # Increase stock when quantity is decreased
            if stock_entry:
                stock_entry.stock += 1
                stock_entry.save()
        else:
            # Restore stock before deleting the item
            if stock_entry:
                stock_entry.stock += cart_item.quantity
                stock_entry.save()

            cart_item.delete()
    except CartItem.DoesNotExist:
        messages.error(request, "This item does not exist in your cart.")

    return redirect('shopping_cart')



def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, product_id=product_id)

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        # Fetch stock entry for the product
        stock_entry = Stock.objects.filter(product=product).first()

        # Restore the stock before deleting the cart item
        if stock_entry:
            stock_entry.stock += cart_item.quantity
            stock_entry.save()

        # Remove the item from the cart
        cart_item.delete()
        messages.success(request, "Item removed from the cart successfully.")

    except CartItem.DoesNotExist:
        messages.error(request, "This item does not exist in your cart.")

    return redirect('shopping_cart')





def cart(request, total=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

    except ObjectDoesNotExist:
        pass  

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items
    }

    return render(request, 'user_side/shoping-cart.html', context)





@login_required(login_url='login')
def user_profile(request):
    user_profile = UserProfile.objects.get(user=request.user)

    context = {
        'user_profile': user_profile,
    }
    return render(request, 'user_side/user_profile.html', context)

@login_required(login_url='login')
def edit_profile(request):
    user_profile = UserProfile.objects.get(user=request.user) # Get the UserProfile instance for the logged-in user

    if request.method == 'POST':
        # Handle the form submission and update the user details
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')

        # Update the user profile fields with the form data
        user_profile.name = full_name
        user_profile.user.username = username
        user_profile.email = email
        user_profile.mobile = mobile

        # Save the changes to the UserProfile and User models
        user_profile.save()
        user_profile.user.save()

        return redirect('user_profile')  # Redirect to the user profile page after successful update
    else:
        return render(request, 'user_side/edit_profile.html', {'user_profile': user_profile})
    

@login_required(login_url='login')
def address_page(request):
    user = request.user
    addresses = ShippingAddress.objects.filter(user=user)
    default_address = addresses.filter(is_default=True).first()

    context = {
        'addresses': addresses,
        'default_address': default_address
    }
    return render(request, 'user_side/address_page.html', context)




@login_required(login_url='login')
def add_address(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')



        #Create a new shipping address instance
        address = ShippingAddress(user=request.user, first_name=first_name, last_name=last_name, phone=phone, email=email, address_line_1=address_line_1, address_line_2=address_line_2, country=country, state=state, city=city, pincode=pincode)
        address.save()


        # Set is_default attribute of the newly added address and reset previous default
        if request.user.is_authenticated:
            ShippingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.is_default = True
            address.save()

        if 'source' in request.GET and request.GET['source'] == 'checkout':
            # If the source is 'checkout', redirect back to the checkout page
            return redirect('checkout')  # Replace 'checkout' with your actual checkout view name

        return redirect('address_page')
    else:
        return render(request, 'user_side/add_address.html')
    



@login_required(login_url='login')
def edit_address(request, address_id):
    address = get_object_or_404(ShippingAddress, pk=address_id)

    if request.method == 'POST':
        # Handle the form submission and update the address details
        address.first_name = request.POST.get('first_name')
        address.last_name = request.POST.get('last_name')
        address.phone = request.POST.get('phone')
        address.email = request.POST.get('email')
        address.address_line_1 = request.POST.get('address_line_1')
        address.address_line_2 = request.POST.get('address_line_2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        address.pincode = request.POST.get('pincode')
        address.save()

        return redirect('address_page')  # Redirect to the address page after successful update

    return render(request, 'user_side/edit_address.html', {'address': address})




@login_required(login_url='login')
def delete_address(request, address_id):
    
    try:
        address = ShippingAddress.objects.get(id=address_id)
        address.delete()
    except ShippingAddress.DoesNotExist:
        pass

    return redirect('address_page')




@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if request.user.check_password(current_password):
            if new_password1 == new_password2:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('user_profile')
            else:
                messages.error(request, 'New passwords do not match.')
        else:
            messages.error(request, 'Invalid old password.')
    
    return render(request, 'user_side/change_password.html')




@login_required(login_url='login')
def order_history(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'user_side/order_history.html', context)



@login_required(login_url='login')
def ordered_product_details(request, order_id):
    order = Order.objects.get(id=order_id)
    ordered_products = OrderProduct.objects.filter(order=order)
    context = {
        'order': order,
        'ordered_products': ordered_products,
    }
    return render(request, 'user_side/ordered_product_details.html', context)




@login_required(login_url='login')
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.user == order.user and order.status != 'Cancelled':
        order.status = 'Cancelled'
        order.save()
        messages.success(request, 'Order has been successfully cancelled.')
        # Add any additional logic, such as updating inventory or sending notifications
    return redirect('order_history')




@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity


    except ObjectDoesNotExist:
        pass

    address_list = ShippingAddress.objects.filter(user=request.user)
    default_address = address_list.filter(is_default=True).first()

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'address_list': address_list,
        'default_address': default_address,
    }

    return render(request, 'user_side/checkout.html', context)






@login_required(login_url='login')
def set_default_address(request, address_id):
    addr_list = ShippingAddress.objects.filter(user=request.user)
    for a in addr_list:
        a.is_default = False
        a.save()
    address = ShippingAddress.objects.get(id=address_id)
    address.is_default=True
    address.save()
    return redirect('checkout')





@login_required(login_url='login')
def place_order(request, total=0, quantity=0):
    current_user = request.user
    coupons = Coupon.objects.all()

    #If the cart count is less than 0, then redirect back to home
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('index')
    

    grand_total = 0
    coupon_discount = 0
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    

    grand_total = total
    

    if request.method == 'POST':
        
        try:
            address = ShippingAddress.objects.get(user=request.user,is_default=True)
        except:
            messages.warning(request, 'No delivery address exixts! Add a address and try again')
            return redirect('checkout')
        
        
        data = Order()
        data.user = current_user
        data.first_name = address.first_name
        data.last_name = address.last_name
        data.phone = address.phone
        data.email = address.email
        data.address_line_1 = address.address_line_1
        data.address_line_2 = address.address_line_2
        data.city = address.city
        data.state = address.state
        data.country = address.country
        data.pincode = address.pincode
        data.order_total = grand_total
        data.ip = request.META.get('REMOTE_ADDR')
        data.save()

        #Generate order number
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr,mt,dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(data.id)
        data.order_number = order_number
        data.save()

    

      

        order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
        context = {
            'order': order,
            'cart_items': cart_items,
            'total': total,
            'grand_total': grand_total,
            'coupons': coupons,
            'coupon_discount':coupon_discount
            
        }
        return render(request, 'user_side/payment.html', context)
    else:
        return redirect('checkout')
    


@login_required(login_url='login')
def apply_coupon(request):

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        order_id = request.POST.get('order_id')
        request.session['coupon_code'] = coupon_code

        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code)
            order = Order.objects.get(id=order_id)

            if coupon.valid_from <= timezone.now().date() <= coupon.valid_to:
                if order.order_total >= coupon.minimum_amount:
                    # Check if the coupon is already redeemed by the user
                    if coupon.is_redeemed_by_user(request.user):
                        messages.error(request, 'Coupon has already been redeemed by you.')
                    else:
                        # Apply the coupon and calculate updated total
                        updated_total = order.order_total - float(coupon.discount_amount)
                        order.order_total = updated_total
                        order.save()

                        # Mark the coupon as redeemed for the user
                        redeemed_details = Coupon_Redeemed_Details(user=request.user, coupon=coupon, is_redeemed=True)
                        redeemed_details.save()

                        # Redirect to payment page with updated order total
                        return redirect('payment', order_id)

                else:
                    messages.error(request, 'Coupon is not applicable for the order total.')
            else:
                messages.error(request, 'Coupon is not applicable for the current date.')

        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')

    

    # Redirect back to the payment page if coupon application fails
    return redirect('payment', order_id)



@login_required(login_url='login')
def payment(request, order_id):

    # try:
    order = Order.objects.get(id=order_id)
    # Check if the coupon is valid for the cart total
        # Redirect back to the cart with the updated total and applied coupon
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('index')
        

    grand_total = 0
    tax = 0
    total = 0
    quantity = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax


    applied_coupon = request.session.get('coupon_code')
    
    if applied_coupon:
        coupon = Coupon.objects.get(coupon_code=applied_coupon)
        
        coupon_discount = coupon.discount_amount
    else:
        coupon_discount = 0
        



    context = {
        'order': order,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': order.order_total,
        'coupon_discount':coupon_discount,
    }


    return render(request, 'user_side/payment.html', context)



def order_confirmed(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
   

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

       


        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'subtotal': subtotal,
            'payment': payment,

        }
        return render(request, 'user_side/order_confirmed.html', context)
    
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('index')



    

        

@login_required(login_url='login')    
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    #Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
        discount = body['discount'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()


    #Move the cart items to orderproduct table

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id 
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.size = item.variations.variation_value
        orderproduct.color = item.variations.variation_value
        orderproduct.save()



    #Clear cart
    cart_items.delete()
    

    #Send order received email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('user_side/order_received_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()


    #Send order number and transaction id back to the sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)

    # return render(request, 'user_side/order_confirmed.html')


    


@login_required(login_url='login')
def add_item_to_wish_list(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    
    try:
        wishlist_item = WishList.objects.get(user=request.user, product=product)
        wishlist_item.delete()  # Remove the item from the wishlist if it exists
    except WishList.DoesNotExist:
        wishlist_item = WishList(user=request.user, product=product)
        wishlist_item.save()  # Add the item to the wishlist
    
    return redirect(request.META.get('HTTP_REFERER', 'wishlist_page'))



@login_required(login_url='login')
def wishlist_page(request):
    wishlist_items = WishList.objects.filter(user=request.user)
    user_wishlist_products = [item.product for item in wishlist_items]
    
    context = {
        'wishlist_items': wishlist_items,
        'user_wishlist_products': user_wishlist_products,
    }
    return render(request, 'user_side/wishlist_page.html', context)




@login_required(login_url='login')
def download_invoice(request, order_id):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
   

    try:
        order = Order.objects.get(id=order_id, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(id=order.payment.id)

       


        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'subtotal': subtotal,

        }
        return render(request, 'user_side/order_confirmed.html', context)
    
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('index')






@login_required(login_url='login')
def wallet(request):
    cur_user = request.user
    try:
        wallet = Wallet.objects.get(user=cur_user)
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=cur_user, amount=0)
    wallet_amount = wallet.amount

    # Retrieve the referral ID from the user's profile
    user = UserProfile.objects.get(user=cur_user)
    referral_id = user.referral_id
    

    context = {'wallet_amount': wallet_amount, 'referral_id': referral_id}
    return render(request, 'user_side/wallet.html', context)




@login_required(login_url='login')
def pay_from_wallet(request, order_id):
    cur_user = request.user
    order = Order.objects.get(id=order_id)
    try:
        wallet = Wallet.objects.get(user=cur_user)
        
    except:
        wallet = Wallet.objects.create(user=cur_user, amount=0)
        wallet.save()
        
    if wallet.amount>order.order_total:
        payment_id = f'uw{order.order_number}{order_id}'
        payment = Payment.objects.create(user=cur_user, 
                                         payment_method='Wallet',payment_id=payment_id,
                                         amount_paid=order.order_total, status='COMPLETED')

        payment.save()
        order.is_ordered = True
        
        order.payment = payment
        order.save()
        wallet.amount -= order.order_total
        wallet.save()

        cart_items = CartItem.objects.filter(user=request.user)

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.size = item.variations.variation_value
            orderproduct.color = item.variations.variation_value
            orderproduct.save()




        
        cart_items.delete()
        
    else:
        messages.warning(request, 'Not Enough Balance in Wallet')
        return redirect('payment', order_id)
    context = {
        'order': order,
        'order_number': order.order_number,
        'transID': payment.payment_id,
        }
    return render(request, 'user_side/order_confirmed.html', context)





@login_required(login_url='login')
def pay_with_cash_on_delivery(request, order_id):
    cur_user = request.user
    order = Order.objects.get(id=order_id)

    payment_id = f'uw{order.order_number}{order_id}'
    payment = Payment.objects.create(user=cur_user, 
                                        payment_method='Cash on Delivery',payment_id=payment_id,
                                        amount_paid=order.order_total, status='COMPLETED')
    
    payment.save()
    order.is_ordered = True
    order.payment = payment
    order.save()


    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.size = item.variations.variation_value
            orderproduct.color = item.variations.variation_value
            orderproduct.save()


    # Clear the cart (adjust this based on your project structure)
    cart_items.delete()

    tax = 0
    total = 0
    quantity = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax
    print('******grand total*****', grand_total)


    applied_coupon = request.session.get('coupon_code')
    
    if applied_coupon:
        coupon = Coupon.objects.get(coupon_code=applied_coupon)
        print('******coupon*******', coupon)
        
        coupon_discount = coupon.discount_amount
        print('*****coupon_discount*****', coupon_discount, coupon.discount_amount)
    else:
        coupon_discount = 0

    context = {
        'order': order,
        'order_number': order.order_number,
        'transID': payment.payment_id,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
        'coupon_discount':coupon_discount,
        }

    # Redirect to the order confirmed page
    return render(request, 'user_side/order_confirmed.html', context)





@login_required(login_url='login')
def return_order(request, order_id):
    order = Order.objects.get(id=order_id)

    if order.status == 'Delivered':
        user_profile = request.user
        wallet, created = Wallet.objects.get_or_create(user=user_profile)

        # Credit the purchased amount back to the wallet
        wallet.amount += order.order_total
        wallet.amount = round(wallet.amount, 2)
        wallet.save()

        # Update the order status to 'Returned'
        order.status = 'Returned'
        order.save()

    return redirect('order_history')  # Redirect back to the order history page
