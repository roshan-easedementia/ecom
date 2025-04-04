from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('admin/dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('add_product/', views.add_product, name='add_product'),
    path('product_list/', views.product_list, name='product_list'),
    path('category_list/', views.category_list, name='category_list'),
    path('user_list/', views.user_list, name='user_list'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('soft_delete_product/<int:product_id>/', views.soft_delete_product, name='soft_delete_product'),
    path('add_variations/<int:product_id>/', views.add_variations, name='add_variations'),
    path('view_variations/<int:product_id>/', views.view_variations, name='view_variations'),
    path('edit_variation/<int:product_id>/<int:variation_id>/', views.edit_variation, name='edit_variation'),
    path('delete_variation/<int:product_id>/<int:variation_id>/', views.delete_variation, name='delete_variation'),
    path('add-stock/<int:product_id>/', views.add_stock, name='add_stock'),
    path('delete-stock/<int:stock_id>/', views.delete_stock, name='delete_stock'),
    path('add_category/', views.add_category, name='add_category'),
    path('edit_category/<str:category_name>/', views.edit_category, name='edit_category'),
    path('delete_category/<str:category_name>/', views.delete_category, name='delete_category'),
    path('block_unblock_user/<int:user_id>/', views.block_unblock_user, name='block_unblock_user'),
    path('brand_list/', views.brand_list, name='brand_list'),
    path('add_brand/', views.add_brand, name='add_brand'),
    path('edit_brand/<str:brand_name>', views.edit_brand, name='edit_brand'),
    path('delete_brand/<str:brand_name>', views.delete_brand, name='delete_brand'),
    path('order_list/', views.order_list, name='order_list'),
    path('ordered_product_details/<int:order_id>/', views.ordered_product_details, name='ordered_product_details'),
    path('update_order_status/<str:order_id>/', views.update_order_status, name='update_order_status'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('coupon_list/', views.coupon_list, name='coupon_list'),
    path('adminpanel/edit_coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('adminpanel/delete_coupon/<int:coupon_id>/', views.delete_coupon, name='delete_coupon'),
    path('add_coupon/', views.add_coupon, name='add_coupon'),
    path('category_offer/', views.category_offer, name='category_offer'),
    path('edit_offer/<int:offer_id>/', views.edit_offer, name='edit_offer'),
    path('delete_offer/<int:offer_id>/', views.delete_offer, name='delete_offer'),


    

   
]