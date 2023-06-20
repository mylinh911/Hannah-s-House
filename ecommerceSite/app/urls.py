from django.contrib import admin
from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

# API URLs
api_patterns = [
    path('v1/register/', views.CustomerAPIView.as_view(), name='register-api'),
    path('v1/login/', views.CustomerLoginView.as_view(), name='login-api'),
    path('v1/products/', views.ProductListView.as_view(), name='product-list'),
    path('v1/order/', views.OrderPlacementAPIView.as_view(), name='order-api'),
    path('v1/accept-order/<int:order_id>/', views.AcceptOrderView.as_view(), name='accept-order-api'),
]

# Web URLs
web_patterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('import_product/', views.import_product, name='import_product'),
    path('sale/', views.sale, name='sale'),
    path('product_search/', views.product_search, name='product_search'),
    path('summary/', views.summary, name='summary'),
    path('add_product/', views.add_product, name='add_product'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutPage, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('orderlist/', views.orderlist, name='orderlist'),
    path('checkout_demo/', views.checkoutDemo, name='checkout_demo'),
    path('products/', views.productList, name='products'),
    path('cart/', views.cart, name='cart'),
    path('update_item/', views.updateItem, name='update_item'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('get_subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
    path('get_subsubcategories/<int:subcategory_id>/', views.get_subsubcategories, name='get_subsubcategories'),
    path('get_subsubsubcategories/<int:subsubcategory_id>/', views.get_subsubsubcategories, name='get_subsubsubcategories'),
    path('product_info/<int:product_id>/', views.product_info, name='product_info'),
    path('sale_detail/', views.sale_detail, name='sale_detail'),
    path('sale_order_details/', views.sale_order_details, name='sale_order_details'),
    path('import_order_detail/', views.import_order_detail, name='import_order_detail'),
    path('enter_work_time/', views.enter_work_time, name='enter_work_time'),
    path('salary_detail/', views.salary_detail, name='salary_detail'),
    path('add_cost/', views.add_cost, name='add_cost'),
    
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_patterns)),
    path('', include(web_patterns)),
]