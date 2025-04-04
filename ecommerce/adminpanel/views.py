from django.shortcuts import render,redirect,HttpResponse,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .models import Product, ProductImage, Variation, Offer, Stock
from .forms import AddProductForm
from .models import Product,ProductImage,Category,Brand
from user.models import UserProfile, Coupon
from django.db.models import Q 
from django.http import HttpResponseBadRequest
from user.models import Order
from django.db.models import Sum, F, Value, Count
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO
from django.core.files.images import ImageFile
from django.http import JsonResponse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.contrib.auth.decorators import login_required




# Create your views here.

@login_required(login_url='adminpanel:admin_login')
def admin_dashboard(request):
    return render(request, 'admin_side/index.html')



def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username,password)
        admin = authenticate(request, username=username, password=password)

        if admin is not None:
            if admin.is_superuser:
                login(request, admin)
                messages.success(request, "Admin login successful!")
                return redirect('adminpanel:admin_dashboard')
        
        messages.error(request, "Invalid admin credentials!")
        return redirect("adminpanel:admin_login")
    else:
        # Clear session and logout message
        request.session.flush()
        # messages.success(request, "Admin logout successful!")
        return render(request, 'admin_side/authentication-login.html')
    


@login_required(login_url='adminpanel:admin_login')
def product_list(request):
    search_query = request.GET.get('search', '')

    # Query the products based on the search query
    if search_query:
        products = Product.objects.filter(product_name__icontains=search_query)
    else:
        products = Product.objects.all()

    context = {
        'products': products
    }

    return render(request, 'admin_side/products.html', context)
    # products = Product.objects.all()
    # return render(request, 'admin_side/products.html', {'products': products})





@login_required(login_url='adminpanel:admin_login')
def add_product(request):
    categories = Category.objects.all()
    brands = Brand.objects.all()
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product_name = request.POST.get('product_name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        brand_id = request.POST.get('brand')
        images = request.FILES.getlist('images[]')
        stock = request.POST.get('stock')

        brand = Brand.objects.get(id=brand_id)


        category = Category.objects.get(pk=category_id)

        # Get the cropped image data as a base64 string
        cropped_image_data = request.POST.get('cropped_image')
        # image_1 = request.POST.get('image_1')

        
        

        product = Product(product_id=product_id,product_name=product_name, category=category,description=description, price=price,brand=brand, rprice=price)
        product.image=images[0]#cropped_image_data#images[0]
        product.save()

       
        for i in range(len(images)):
            prd_image = ProductImage(product=product, image=images[i])
            prd_image.save()

            
            
        return redirect('adminpanel:product_list')
    else:
        form = AddProductForm() 
    
    context = {
        'form': form,
        'categories': categories,
        'brands': brands,
    }
    
    return render(request, 'admin_side/add_product.html', context)


@login_required(login_url='adminpanel:admin_login')
def edit_product(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    categories = Category.objects.all()
    brands = Brand.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product_name = request.POST.get('product_name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        brand_id = request.POST.get('brand')
        image = request.FILES.get('image')
        stock = request.POST.get('stock')

        category = get_object_or_404(Category, pk=category_id)
        brand = Brand.objects.get(id=brand_id)

        product.product_id = product_id
        product.product_name = product_name
        product.category = category
        product.description = description
        product.price = price
        product.brand = brand
        product.stock = stock
        product.rprice = price

        # Only update the image if a new one is provided
        if image:
            product.image = image

        product.save()

        return redirect('adminpanel:product_list')
    else:
        context = {
            'product': product,
            'categories': categories,
            'brands': brands,
        
        }
        # context = {'product_id':product_id}

    return render(request, 'admin_side/edit_product.html', context)




@login_required(login_url='adminpanel:admin_login')
def delete_product(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('adminpanel:product_list')
    return render(request, 'admin_side/delete_product.html', {'product': product})



@login_required(login_url='adminpanel:admin_login')
def soft_delete_product(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        product.is_active = False  # Mark the product as inactive (soft deleted)
        product.save()
        messages.success(request, f"Product '{product.product_name}' has been soft deleted.")
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
   
    return redirect('adminpanel:product_list')





@login_required(login_url='adminpanel:admin_login')
def add_variations(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)  # Corrected field name
    variations = Variation.objects.filter(product=product)  # Fetch existing variations

    if request.method == 'POST':
        variation_id = request.POST.get('variation_id')
        stock = request.POST.get('stock')

        if variation_id and stock:
            variation = get_object_or_404(Variation, id=variation_id, product=product)
            variation.stock = stock  # Update stock
            variation.save()

        return redirect('adminpanel:add_variations', product_id=product_id)

    context = {
        'product_id': product_id,
        'variations': variations,  # Pass variations to the template
    }
    return render(request, 'admin_side/add_variations.html', context)








@login_required(login_url='adminpanel:admin_login')
def view_variations(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    variations = Variation.objects.filter(product=product)
    
    context = {
        'product_id': product_id,
        'variations': variations,
    }
    return render(request, 'admin_side/add_variations.html', context)




@login_required(login_url='adminpanel:admin_login')
def edit_variation(request, product_id, variation_id):
    variation = get_object_or_404(Variation, id=variation_id)
    if request.method == 'POST':
        # Process the form data and update the variation
        variation_category = request.POST.get('variation_category')
        variation_value = request.POST.get('variation_value')
        stock = request.POST.get('stock')
        
        variation.variation_category = variation_category
        variation.variation_value = variation_value
        variation.stock = stock
        variation.save()
        
        return redirect('adminpanel:view_variations', product_id=product_id)
    
    context = {
        'variation': variation,
        'product_id': product_id,
    }
    return render(request, 'admin_side/edit_variations.html', context)





@login_required(login_url='adminpanel:admin_login')
def delete_variation(request, product_id, variation_id):
    variation = get_object_or_404(Variation, id=variation_id)
    
    if request.method == 'POST':
        # Delete the variation
        variation.delete()
        return redirect('adminpanel:view_variations', product_id=product_id)
    
    # If the request method is not POST, redirect to a safe URL
    return redirect('adminpanel:view_variations', product_id=product_id)



@login_required(login_url='adminpanel:admin_login')
def add_stock(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    stocks = Stock.objects.filter(product=product)
    print("Product:", product)
    print("stocks:", stocks)
    if request.method == "POST":
        stock_quantity = request.POST.get("stock", 0)
        stock_obj, created = Stock.objects.get_or_create(product=product)
        stock_obj.stock += int(stock_quantity)  # Update stock
        stock_obj.save()

        return redirect('adminpanel:add_stock', product_id=product_id)

    return render(request, 'admin_side/add_stock.html', {'product': product, 'stocks': stocks})




@login_required(login_url='adminpanel:admin_login')
def delete_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    product_id = stock.product.product_id  # Retrieve product ID before deleting the stock
    stock.delete()
    messages.success(request, "Stock entry deleted successfully.")
    return redirect('adminpanel:add_stock', product_id=product_id)



@login_required(login_url='adminpanel:admin_login')
def category_list(request):
    search_query = request.GET.get('search')
    
    if search_query:
        categories = Category.objects.filter(Q(category_name__icontains=search_query))
    else:
        categories = Category.objects.all()

    return render(request, 'admin_side/category.html', {'categories': categories})



@login_required(login_url='adminpanel:admin_login')
def add_category(request):
    
    if request.method == 'POST':
        category_name = request.POST.get('category_name')

        category = Category(category_name=category_name)
        category.save()
        
        return redirect('adminpanel:category_list')
    
    return render(request, 'admin_side/add_category.html')



@login_required(login_url='adminpanel:admin_login')
def edit_category(request, category_name):
    category = get_object_or_404(Category, category_name=category_name)
    if request.method == 'POST':
        category_name = request.POST.get('category_name')


        category.category_name = category_name
        category.save()

        return redirect('adminpanel:category_list')
    else:
        context = {
            'category':category
        }
    
    return render(request, 'admin_side/edit_category.html', context)




@login_required(login_url='adminpanel:admin_login')
def delete_category(request, category_name):
    category = get_object_or_404(Category, category_name=category_name)
    if request.method == 'POST':
        category.delete()
        return redirect('adminpanel:category_list')
    # return render(request, 'admin_side/category_list.html', {'category': category})
    return redirect('adminpanel:category_list')



@login_required(login_url='adminpanel:admin_login')
def user_list(request):
    
    search_query = request.GET.get('search', '')

    # Query the users based on the search query
    if search_query:
        users = UserProfile.objects.filter(name__icontains=search_query)
    else:
        users = UserProfile.objects.all()

    context = {
        'users': users
    }

    return render(request, 'admin_side/user_list.html', context)
    
    # return render(request, 'admin_side/user_list.html')



@login_required(login_url='adminpanel:admin_login')
def block_unblock_user(request, user_id):
    user = get_object_or_404(UserProfile, user_id=user_id)

    # Toggle the is_blocked status of the user
    user.is_blocked = not user.is_blocked
    user.save()

    if user.is_blocked:
        logout(request)
        print('User is logged out')

    return redirect('adminpanel:user_list')




@login_required(login_url='adminpanel:admin_login')
def brand_list(request):
    search_query = request.GET.get('search')
    
    if search_query:
        brands = Brand.objects.filter(Q(brand_name__icontains=search_query))
    else:
        brands = Brand.objects.all()

    return render(request, 'admin_side/brand.html', {'brands': brands})



@login_required(login_url='adminpanel:admin_login')
def add_brand(request):
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')

        brands = Brand(brand_name=brand_name)
        brands.save()
        
        return redirect('adminpanel:brand_list')
    
    return render(request, 'admin_side/add_brand.html')



@login_required(login_url='adminpanel:admin_login')
def edit_brand(request, brand_name):
    brands = get_object_or_404(Brand, brand_name=brand_name)
    if request.method == 'POST':
        brand_name = request.POST.get('brand_name')


        brands.brand_name = brand_name
        brands.save()

        return redirect('adminpanel:brand_list')
    else:
        context = {
            'brands':brands
        }
    
    return render(request, 'admin_side/edit_brand.html', context)



@login_required(login_url='adminpanel:admin_login')
def delete_brand(request, brand_name):
    brands = get_object_or_404(Brand, brand_name=brand_name)
    if request.method == 'POST':
        brands.delete()
        return redirect('adminpanel:brand_list')
    # return render(request, 'admin_side/category_list.html', {'category': category})
    return redirect('adminpanel:brand_list')



from user.models import Order,OrderProduct
@login_required(login_url='adminpanel:admin_login')
def order_list(request):
    orders = Order.objects.all().order_by('-created_at')  # Fetch all orders from the Order model
    context = {'orders': orders}
    return render(request, 'admin_side/order_list.html', context)



@login_required(login_url='adminpanel:admin_login')
def ordered_product_details(request, order_id):
    order = Order.objects.get(id=order_id)
    ordered_products = OrderProduct.objects.filter(order=order)
    context = {
        'order': order,
        'ordered_products': ordered_products,
    }
    return render(request, 'admin_side/ordered_product_details.html', context)




@login_required(login_url='adminpanel:admin_login')
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=int(order_id))
        status = request.POST['status']
        order.status = status
        order.save()
        return redirect('adminpanel:order_list')
    else:
        return HttpResponseBadRequest("Bad request.")
    


@login_required(login_url='adminpanel:admin_login')
def sales_report(request):
    if request.method == 'POST':
        from_date = request.POST.get('fromDate')
        to_date = request.POST.get('toDate')
        time_period = request.POST.get('timePeriod')

        # Check for empty or missing dates
        if not from_date or not to_date:
            return HttpResponseBadRequest("Please provide valid date values.")

        # Convert date strings to datetime objects
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
        except ValueError:
            return HttpResponseBadRequest("Invalid date format.")

        # Calculate sales data based on time period
        if time_period == 'all':
            sales_data = Order.objects.filter(created_at__range=[from_date, to_date]).values('created_at__date') \
            .annotate(total_orders=Count('id'), total_revenue=Sum('order_total'))
        elif time_period == 'daily':
            sales_data = Order.objects.filter(created_at__date__range=[from_date, to_date]).values('created_at__date') \
            .annotate(total_orders=Count('id'), total_revenue=Sum('order_total'))
        elif time_period == 'weekly':
            sales_data = Order.objects.filter(created_at__range=[from_date, to_date]) \
                .extra({'week': "date_trunc('week', created_at)"}).values('week') \
                .annotate(total_orders=Count('id'), total_revenue=Sum('order_total'))
        elif time_period == 'monthly':
            sales_data = Order.objects.filter(created_at__range=[from_date, to_date]) \
                .extra({'month': "date_trunc('month', created_at)"}).values('month') \
                .annotate(total_orders=Count('id'), total_revenue=Sum('order_total'))
        elif time_period == 'yearly':
            sales_data = Order.objects.filter(created_at__range=[from_date, to_date]) \
                .extra({'year': "date_trunc('year', created_at)"}).values('year') \
                .annotate(total_orders=Count('id'), total_revenue=Sum('order_total'))

        # Define the dateWise queryset for daily sales data
        dateWise = Order.objects.filter(created_at__date__range=[from_date, to_date]) \
        .values('created_at__date') \
        .annotate(total_orders=Count('id'), total_revenue=Sum('order_total'))

        

        # Calculate Total Users
        total_users = Order.objects.filter(is_ordered=True).values('user').distinct().count()

        # Calculate Total Products
        total_products = OrderProduct.objects.filter(order__is_ordered=True).values('product').distinct().count()

        # Calculate Total Orders
        total_orders = Order.objects.filter(is_ordered=True).count()

        # Calculate Total Revenue
        total_revenue = Order.objects.filter(is_ordered=True).aggregate(total_revenue=Sum('order_total'))['total_revenue']

        context = {
            'sales_data': sales_data,
            'from_date': from_date,
            'to_date': to_date,
            'report_type': time_period,
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'dateWise': dateWise, 
        }

        return render(request, 'admin_side/sales_report.html', context)

    return render(request, 'admin_side/sales_report.html')




@login_required(login_url='adminpanel:admin_login')
def coupon_list(request):
    coupons = Coupon.objects.all()
    context = {
        'coupons': coupons
    }
    return render(request, 'admin_side/coupon_list.html', context)



@login_required(login_url='adminpanel:admin_login')
def add_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        discount_amount = request.POST.get('discount_amount')
        minimum_amount = request.POST.get('minimum_amount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')

        coupon = Coupon(
            coupon_code=coupon_code,
            discount_amount=discount_amount,
            minimum_amount=minimum_amount,
            valid_from=valid_from,
            valid_to=valid_to
        )
        coupon.save()

        return redirect('adminpanel:coupon_list')

    return render(request, 'admin_side/add_coupon.html')





@login_required(login_url='adminpanel:admin_login')
def edit_coupon(request, coupon_id):
    try:
        # Get the coupon instance by its ID
        coupon = Coupon.objects.get(pk=coupon_id)

        # Check if the request method is POST (form submission)
        if request.method == 'POST':
            # Retrieve the data from the POST request
            coupon_code = request.POST.get('coupon_code')
            discount_amount = request.POST.get('discount_amount')
            minimum_amount = request.POST.get('minimum_amount')
            valid_from = request.POST.get('valid_from')
            valid_to = request.POST.get('valid_to')

            # Update the coupon instance with the new data
            coupon.coupon_code = coupon_code
            coupon.discount_amount = discount_amount
            coupon.minimum_amount = minimum_amount
            coupon.valid_from = valid_from
            coupon.valid_to = valid_to

            # Save the updated coupon instance
            coupon.save()

            return redirect('adminpanel:coupon_list')  # Redirect to the coupon list view after editing

        return render(request, 'admin_side/edit_coupon.html', {'coupon': coupon})
    
    except Coupon.DoesNotExist:
        return HttpResponseBadRequest("Coupon does not exist")
    


@login_required(login_url='adminpanel:admin_login')
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        coupon.delete()
        return redirect('adminpanel:coupon_list')

    return redirect('adminpanel:coupon_list')


@login_required(login_url='adminpanel:admin_login')
def category_offer(request):
    if request.method == 'POST':

        category_id = request.POST.get('category')
        discount = float(request.POST.get('discount'))
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        category = Category.objects.get(id=category_id)
        if Offer.objects.filter(category=category).exists():
            messages.warning(request, "There is Already One Discount offer on this product")
            return redirect('adminpanel:category_offer')
        # if len(str(discount)) <= 2 or discount == 100:
        print(category_id, discount, start_date, end_date)
        discount = int(discount) / 100
        category = Category.objects.get(id=category_id)
        dis = Offer(discount=(discount * 100), category=category, start_date=start_date, end_date=end_date)
        dis.save()
        product_list = Product.objects.filter(category=category)
        for product in product_list:
            product.discount = discount*100
            # product.rprice = product.price
            product.price = product.rprice - round(product.rprice*discount,2)
            product.save()
            
            
        messages.success(request, f'{discount*100}% Discount Added for all Products under {category.category_name}')
        return redirect('adminpanel:category_offer')



        # offer = Offer.objects.create(category=category, discount_percentage=discount_percentage, start_date=start_date, end_date=end_date)
        # offer.save()

        # Redirect to the same page to show the updated offers
        return redirect('adminpanel:category_offer')

    categories = Category.objects.all()
    added_offers = Offer.objects.all()

    context = {'categories': categories, 'added_offers': added_offers,}
    return render(request, 'admin_side/category_offer.html', context)



@login_required(login_url='adminpanel:admin_login')
def admin_discount_add(request):
    if request.method == 'POST':
        discount = request.POST.get('discount')
        category_id = request.POST.get('category')
        category = Category.objects.get(uid=category_id)
        if Offer.objects.filter(category=category).exists():
            messages.warning(request, "There is Already One Discount offer on this product")
            return redirect('admin_manage_offers')
        if len(str(discount)) <=2 or discount == 100:
            discount = int(discount) / 100
            category = Category.objects.get(uid=category_id)
            dis = Offer(discount=(discount * 100), category=category)
            dis.save()
            product_list = Product.objects.filter(category=category)
            for product in product_list:
                product.discount = discount*100
                product.price = product.rprice - round(product.rprice*discount,2)
                product.save()
                variant_list = Variation.objects.filter(product_id=product)
                for var in variant_list:
                    var.price = round(var.rprice*discount,2)
                    var.save()

            messages.success(request, f'{discount*100}% Discount Added for all Products under {category.category_name}')
        return redirect('admin_manage_offers')




@login_required(login_url='adminpanel:admin_login')
def edit_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)

    if request.method == 'POST':
        # Process the form data to update the offer
        offer.discount_percentage = float(request.POST.get('discount_percentage'))
        offer.start_date = request.POST.get('start_date')
        offer.end_date = request.POST.get('end_date')
        offer.save()
        return redirect('adminpanel:category_offer')
    
    categories = Category.objects.all()

    context = {
        'offer': offer,
        'categories':categories,
               }
    return render(request, 'admin_side/edit_offer.html', context)



@login_required(login_url='adminpanel:admin_login')
def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)

    if request.method == 'POST':
        product_list = Product.objects.filter(category=offer.category)
        for product in product_list:
            product.discount = 0
            product.price = product.rprice
            product.save()
        offer.delete()
        return redirect('adminpanel:category_offer')  # Redirect back to the offers list

    return redirect('adminpanel:category_offer')



