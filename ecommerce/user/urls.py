from django.urls import path 
from django.contrib.auth import views as auth_views
from . import views




urlpatterns = [
    path('',views.index, name='index'),
    path('index',views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='user_side/login.html'), name='login'),
    path('verify_otp/<str:email>/', views.verify_otp, name='verify_otp'),
    path('signup/', views.register_user, name='signup'),
    path('signup/verify-otp/', views.verify_otp, name='verify_signup_otp'),
    path('login_with_email_and_otp', views.login_with_email_and_otp, name='login_with_email_and_otp'),
    path('login_with_email_and_otp/verify-otp/', views.verify_otp_login, name='verify_login_otp'),
    path('verify_otp_login/<str:email>/', views.verify_otp_login, name='verify_otp_login'),
    path('logout/', views.logout_view, name='logout'),

    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('send_otp_forgot_password/', views.send_otp_forgot_password, name='send_otp_forgot_password'),
    path('verify_otp_reset_password/<str:email>/', views.verify_otp_reset_password, name='verify_otp_reset_password'),
    path('set_new_password/<str:email>/', views.set_new_password, name='set_new_password'),

    



    
    path('product-detail/<int:product_id>/', views.product_detail, name='product_detail'),

    path('shoping_cart/', views.cart, name='shopping_cart'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('add_quantity_to_cart/<int:product_id>/<int:cart_item_id>/', views.add_quantity_to_cart, name='add_quantity_to_cart'),
    path('remove_cart/<int:product_id>/<int:cart_item_id>/', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:product_id>/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'),

    path('user_profile/', views.user_profile, name='user_profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('address/', views.address_page, name='address_page'),
    path('add_address/', views.add_address, name='add_address'),
    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('change_password/', views.change_password, name='change_password'),
    path('wallet/', views.wallet, name='wallet'),
    path('order_history/', views.order_history, name='order_history'),
    path('ordered_product_details/<int:order_id>', views.ordered_product_details, name='ordered_product_details'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('download_invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),



    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('order_confirmed/', views.order_confirmed, name='order_confirmed'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('set_default_address/<int:address_id>/', views.set_default_address, name='set_default_address'),

    path('wishlist/', views.wishlist_page, name='wishlist_page'),
    path('add_item_to_wish_list/<int:product_id>/', views.add_item_to_wish_list, name='add_item_to_wish_list'),


    path('category/jersey/', views.jersey_category, name='jersey_category'),
    path('category/boot', views.boot_category, name='boot_category'),
    path('category/equipments', views.equipments_category, name='equipments_category'),
    path('category/accessories', views.accessories_category, name='accessories_category'),

    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path('payment/<order_id>/', views.payment, name='payment'),

    path('pay_from_wallet/<int:order_id>/', views.pay_from_wallet, name='pay_from_wallet'),
    path('return_order/<int:order_id>/', views.return_order, name='return_order'),
    path('pay_with_cash_on_delivery/<int:order_id>/', views.pay_with_cash_on_delivery, name='pay_with_cash_on_delivery'),

   



    

]