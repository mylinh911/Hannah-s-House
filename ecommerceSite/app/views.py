from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import *
from django.db.models import Q
import json
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomerForm, ProductForm, ProductSearchForm, WorkTimeForm, CostForm
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.utils.translation import get_language, activate, gettext
from django.views import generic
from django.contrib.auth.models import User
# from ecommerceSite.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string
import smtplib
from django.contrib.sessions.backends.db import SessionStore
from django.views.decorators.http import require_GET
from PIL import Image

from django.db.models import F, Value
from django.db.models.functions import Concat

from itertools import groupby
from operator import itemgetter

from datetime import datetime

# for API 
from django.core.serializers import serialize
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import CustomerSerializer, CustomerLoginSerializer, ProductSerializer, OrderDetailSerializer, OrderSerializer, AcceptOrderSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.sessions.models import Session

class CustomerAPIView(APIView):
    def get_required_fields(self):
        serializer = CustomerSerializer()
        required_fields = [field.field_name for field in serializer.fields.values() if field.required]
        return required_fields

    def post(self, request, *args, **kwargs):
        serializer = CustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        required_fields = self.get_required_fields()
        return Response({'required_fields': required_fields})

class CustomerLoginView(APIView):
    def get_required_fields(self):
        serializer = CustomerLoginSerializer()
        required_fields = [field.field_name for field in serializer.fields.values() if field.required]
        return required_fields

    def get(self, request, *args, **kwargs):
        required_fields = self.get_required_fields()
        return Response({'required_fields': required_fields})

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_name = serializer.validated_data['user_name']
        password = serializer.validated_data['password']
        
        user = authenticate(request, user_name=user_name, password=password)
        
        if user is not None:
            login(request, user)
            session = SessionStore()
            session.create()
            session['customer_id'] = user.customer.userID
            session.save()
            return Response({'message': 'Đăng nhập thành công.', 'session_id': session.session_key})

        try:
            customer = Customer.objects.get(user_name=user_name)
            if customer.check_password(password):
                request.session['customer_id'] = customer.userID
                return Response({'message': 'Đăng nhập thành công.', 'session_id': request.session.session_key})
            else:
                return Response({'message': 'Mật khẩu không hợp lệ.'}, status=status.HTTP_401_UNAUTHORIZED)
        except Customer.DoesNotExist:
            return Response({'message': 'Khách hàng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

class ProductListView(APIView):
    def get(self, request):
        category_id = request.GET.get('category')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        featured_only = request.GET.get('featured_only')

        products = Product.objects.all()

        if category_id:
            products = products.filter(category__id=category_id)


        if featured_only:
            products = products.filter(featured=True)

        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)

class OrderPlacementAPIView(APIView):
    def get(self, request):
        serializer = OrderSerializer()
        required_fields = serializer.get_required_fields()
        return Response(required_fields, status=status.HTTP_200_OK)
        
    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()

            order.status = 'pending'  
            order.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class AcceptOrderView(APIView):
    def get(self, request, order_id):
        try:
            order = Order.objects.get(orderID=order_id)
            serializer = AcceptOrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, order_id):
        try:
            order = Order.objects.get(orderID=order_id)
        except Order.DoesNotExist:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if order.status != 'pending':
            return Response({'message': 'Order status cannot be changed'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'shipped'
        order.save()
        
        return Response({'message': 'Order status updated to shipped'}, status=status.HTTP_200_OK)
        
def check_user_id_in_session(request):
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    
    for value in session_values:
        if value in customer_ids:
            return True
    
    return False

def register(request):
    user_not_login = "hidden"
    user_login = "hidden"
    
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomerForm()
    return render(request, 'app/register.html', {'form': form, 'user_not_login':user_not_login, 'user_login':user_login})

def home(request, language = None):
    Order.objects.filter(status='demo').delete()
    cur_language = language or request.LANGUAGE_CODE
    activate(cur_language)
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    products = Product.objects.filter(featured=True)
    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            user_not_login = "hidden"
            user_login = "show"
            order, created = Order.objects.get_or_create(customer = customer, status ='cart')
            cartItems = order.get_cart_items
            context = { 'cartItems': cartItems,'products': products,'user_name':customer.name, 'user_not_login':user_not_login, 'user_login':user_login}
            return render(request,'app/home.html',context)

    if request.user.is_authenticated:
        user_not_login = "hidden"
        user_login = "show"
        context = { 'products': products,'user_name':request.user.last_name, 'user_not_login':user_not_login, 'user_login':user_login}
        return render(request,'app/home.html',context)
    
    user_not_login = "show"
    user_login = "hidden"
    context = {'products': products,'user_not_login':user_not_login, 'user_login':user_login}
    return render(request,'app/home.html',context)

def loginPage(request):
    Order.objects.filter(status='demo').delete()
    user_not_login = "hidden"
    user_login = "hidden"
    
    if request.method =="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        try:
            customer = Customer.objects.get(user_name=username)
            if customer.check_password(password):
                request.session['customer_id'] = customer.userID
                
                return redirect('home')  
            else:
                error_message = 'Invalid password'
        except Customer.DoesNotExist:
            error_message = 'Customer does not exist'
        return render(request, 'app/login.html', {'error_message': error_message, 'user_not_login':user_not_login, 'user_login':user_login})
    else:
        return render(request, 'app/login.html', { 'user_not_login':user_not_login, 'user_login':user_login})

def logoutPage(request):
    Order.objects.filter(status='demo').delete()
    if request.user.is_authenticated:
        logout(request)
        return redirect('login')

    if 'customer_id' in request.session:
        del request.session['customer_id']
    return redirect('login')

def productList(request):
    categories = Category.objects.filter(is_sub=False)
    search_query = request.GET.get('search_query', '')
    category_filter = request.GET.get('category', '')

    # Bộ lọc theo tên sản phẩm
    name_filter = Q()
    if search_query:
        search_terms = search_query.split()
        for term in search_terms:
            name_filter &= Q(name__icontains=term)

    # Bộ lọc theo danh mục
    category_products = Product.objects.all()
    if category_filter:
        category_products = category_products.filter(category__id=category_filter)

    # Kết hợp các bộ lọc
    products = Product.objects.filter(name_filter, productID__in=category_products.values('productID'))

    Order.objects.filter(status='demo').delete()
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()

    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            user_not_login = "hidden"
            user_login = "show"
            order, created = Order.objects.get_or_create(customer=customer, status='cart')
            cartItems = order.get_cart_items
            context = {'cartItems': cartItems, 'products': products, 'user_name': customer.name,
                       'user_not_login': user_not_login, 'user_login': user_login, 'categories': categories }
            return render(request, 'app/product.html', context)
    
    user_not_login = "show"
    user_login = "hidden"
    context = {'products': products,'user_not_login':user_not_login, 'user_login':user_login, 'categories': categories}
    return render(request,'app/product.html',context)

# def product_detail_view(request, primary_key):
#     product = get_object_or_404(Product, pk=primary_key)
#     return render(request, 'app/product_detail.html', context={'product': product})

class ProductDetailView(generic.DetailView):
    Order.objects.filter(status='demo').delete()

    model = Product

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request  # Access the request object

        customer_ids = Customer.objects.values_list('userID', flat=True)
        session_values = request.session.values()

        for value in session_values:
            if value in customer_ids:
                customer = Customer.objects.get(userID=value)
                user_not_login = "hidden"
                user_login = "show"
                context['user_name'] = customer.name
                context['user_not_login'] = user_not_login
                context['user_login'] = user_login
                order, created = Order.objects.get_or_create(customer = customer, status ='cart')
                cartItems = order.get_cart_items
                context ['cartItems']= cartItems
                return context

        user_not_login = "show"
        user_login = "hidden"
        context ['cartItems']=0
        context['user_not_login'] = user_not_login
        context['user_login'] = user_login
        return context

def cart(request):
    Order.objects.filter(status='demo').delete()
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            order, created = Order.objects.get_or_create(customer=customer, status='cart')
            items = order.orderdetail_set.all()
            user_not_login = "hidden"
            user_login = "show"
            cartItems = order.get_cart_items
            context = {
                'cartItems': cartItems,
                'items': items,
                'order': order,
                'user_name': customer.name,
                'user_not_login': user_not_login,
                'user_login': user_login
            }
            return render(request, 'app/cart.html', context)

    user_not_login = "show"
    user_login = "hidden"
    items = []
    order = []
    cartItems = []
    context = {
        'items': items,
        'cartItems': cartItems,
        'user_not_login': user_not_login,
        'user_login': user_login
    }
    return render(request, 'app/cart.html', context)

def updateItem(request):
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            break
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    quantity = int(data.get('quantity', 0))
    product = Product.objects.get(productID=productId)
    order, created = Order.objects.get_or_create(customer=customer, status ='cart')
    orderItem, created = OrderDetail.objects.get_or_create(order=order, product=product)
    if action == 'add':
        orderItem.quantity += quantity
    elif action == 'remove':
        orderItem.quantity -= 1
    orderItem.save()
    if action == 'delete':
        orderItem.delete()
    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse({'status': 'success'})

def checkoutDemo(request):
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            break
    data = json.loads(request.body)
    orderQuantityList = data['orderQuantityList']
    orderProductList = data['orderProductList']

    order = Order.objects.create(customer=customer, status='demo')

    for i in range(len(orderQuantityList)):
        product = Product.objects.get(productID=orderProductList[i])
        quantity = orderQuantityList[i]
        OrderDetail.objects.create(order=order, product=product, quantity=quantity)

    return JsonResponse({'status': 'success'})

def checkout(request):
    user_not_login = "hidden"
    user_login = "show"
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    
    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            if request.method == 'POST':
                province = request.POST.get('province')
                district = request.POST.get('district')
                commune = request.POST.get('commune')
                house_number = request.POST.get('house_number')

                information = house_number + ', ' + commune + ', ' + district + ', ' + province

                order = Order.objects.filter(customer=customer, status='demo').order_by('-order_date').first()
                cart = Order.objects.get(customer=customer, status='cart')
                cart_items = cart.orderdetail_set.all()
                pending_order = order.orderdetail_set.all()
                for cart_item in cart_items:
                    if pending_order.filter(product=cart_item.product).exists():
                        cart_item.delete()
                order.shipping_address = information
                print(information)
                order.status ='pending'
                order.save()

                staff_users = User.objects.filter(is_staff=True)
                staff_emails = [user.email for user in staff_users]
                email='linhttm193303@gmail.com'
                password = 'xxxxxx'
                email_sents = [customer.email]
                email_sents.extend(staff_emails)

                session = smtplib.SMTP('smtp.gmail.com', 587)
                session.starttls()
                session.login(email, password)

                subject = "ecommerce shop"

                customer_mail_content = f"Subject: {subject}\n\nBạn đã đặt hàng thành công".encode('utf-8')
                staff_mail_content = f"Subject: {subject}\n\nCó đơn đặt hàng mới".encode('utf-8')

                for recipient_email in email_sents:
                    if recipient_email == customer.email:
                        mail_content = customer_mail_content
                    else:
                        mail_content = staff_mail_content

                    session.sendmail(email, recipient_email, mail_content)

                session.quit()
                print('mail sent')
                return redirect('home')
            order = Order.objects.filter(customer=customer, status='demo').order_by('-order_date').first()

            items = order.orderdetail_set.all()
            user_not_login = "hidden"
            user_login = "show"
            cartItems = order.get_cart_items
            context = { 'cartItems': cartItems,'items':items, 'order': order, 'user_name':customer.name, 'user_not_login':user_not_login, 'user_login':user_login}
            return render(request,'app/checkout.html',context)

    
    items = []
    order = {'get_cart_items':0, 'get_cart_total':0}
    cartItems = order['get_cart_items']
    context = {'items': items, 'cartItems':cartItems , 'user_not_login':user_not_login, 'user_login':user_login  }
    return render(request,'app/checkout.html',context)

def orderlist(request, language = None):
    Order.objects.filter(status='demo').delete()
    cur_language = language or request.LANGUAGE_CODE
    activate(cur_language)
    customer_ids = Customer.objects.values_list('userID', flat=True)
    session_values = request.session.values()
    for value in session_values:
        if value in customer_ids:
            customer = Customer.objects.get(userID=value)
            user_not_login = "hidden"
            user_login = "show"
            orders = Order.objects.filter(customer=customer).exclude(status__in=['demo', 'cart'])
            order, created = Order.objects.get_or_create(customer = customer, status ='cart')
            if order is None:
                cartItems = '0'
            else:
                cartItems = order.get_cart_items
            is_staff = "hidden"
            context = { 'is_staff': is_staff,'cartItems': cartItems,'orders': orders,'user_name':customer.name, 'user_not_login':user_not_login, 'user_login':user_login}
            return render(request,'app/orderlist.html',context)

    if request.user.is_authenticated:
        if request.method == 'POST':
            order_id = request.POST.get('order_id')
            order = Order.objects.get(pk=order_id)
            order.status = 'shipped'
            order.save()
        user_not_login = "hidden"
        user_login = "show"
        orders = Order.objects.exclude(status__in=['demo', 'cart'])
        cartItems = '0'
        is_staff = "show"
        context = { 'is_staff': is_staff, 'cartItems': cartItems,'orders': orders,'user_name':request.user.last_name, 'user_not_login':user_not_login, 'user_login':user_login}
        return render(request,'app/orderlist.html',context)


    
    user_not_login = "show"
    user_login = "hidden"
    context = {'user_not_login':user_not_login, 'user_login':user_login}
    return render(request,'app/orderlist.html',context)
    
class OrderDetailView(generic.DetailView):
    Order.objects.filter(status='demo').delete()

    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request  # Access the request object

        customer_ids = Customer.objects.values_list('userID', flat=True)
        session_values = request.session.values()

        for value in session_values:
            if value in customer_ids:
                customer = Customer.objects.get(userID=value)
                user_not_login = "hidden"
                user_login = "show"
                context['user_name'] = customer.name
                context['user_not_login'] = user_not_login
                context['user_login'] = user_login
                return context

        user_not_login = "show"
        user_login = "hidden"
        context['user_not_login'] = user_not_login
        context['user_login'] = user_login
        return context

    def post(self, request, *args, **kwargs):
        order = self.get_object()

        if 'cancel_order' in request.POST:
            reason = request.POST.get('reason')
            order.status = 'canceled'
            order.cancel_order(reason)

            order.save(update_fields=['status'])

        Order.objects.filter(status='demo').delete()
        customer_ids = Customer.objects.values_list('userID', flat=True)
        session_values = request.session.values()
        for value in session_values:
            if value in customer_ids:
                customer = Customer.objects.get(userID=value)
                user_not_login = "hidden"
                user_login = "show"
                orders = Order.objects.filter(customer=customer).exclude(status__in=['demo', 'cart'])
                context = { 'orders': orders,'user_name':customer.name, 'user_not_login':user_not_login, 'user_login':user_login}
                return render(request,'app/orderlist.html',context)

def add_product(request):
    products = Product.objects.all()

    # Tính tổng vốn
    total_cost = calculate_total_cost(products)

    categories = Category.objects.filter(is_sub=False)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Lấy thông tin từ form
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            quantity = form.cleaned_data['quantity']
            in_price_near = form.cleaned_data['in_price_near']
            price = form.cleaned_data['price']
            # image = form.cleaned_data['image']

            # Lấy category, subcategory và subsubcategory từ request.POST
            category_id = request.POST.get('selected_category', None)
            subcategory_id = request.POST.get('selected_subcategory', None)
            subsubcategory_id = request.POST.get('selected_subsubcategory', None)

            # Tạo đối tượng Product
            product = Product(
                name=name,
                description=description,
                quantity=quantity,
                in_price_near=in_price_near,
                price=price,
                # image=image
            )
            product.save()
            # Lưu category cho product
            if category_id:
                category = Category.objects.get(id=category_id)
                product.category.add(category)

            # Lưu subcategory cho product
            if subcategory_id:
                subcategory = Category.objects.get(id=subcategory_id)
                product.category.add(subcategory)

            # Lưu subsubcategory cho product
            if subsubcategory_id:
                subsubcategory = Category.objects.get(id=subsubcategory_id)
                product.category.add(subsubcategory)

            # Lưu product vào cơ sở dữ liệu
            product.save()
        return redirect('add_product')
    else:
        form = ProductForm()
    return render(request, 'app/add_product.html', {'form': form, 'total_cost': total_cost, 'categories': categories})

def get_subcategories(request, category_id):
    category = Category.objects.get(id=category_id)
    subcategories = category.sub_categories.all()

    subcategories_list = [{'id': subcategory.id, 'name': subcategory.name} for subcategory in subcategories]

    return JsonResponse(subcategories_list, safe=False)

def get_subsubcategories(request, subcategory_id):
    subcategory = Category.objects.get(id=subcategory_id)
    subsubcategories = subcategory.sub_categories.all()

    subsubcategories_list = [{'id': subsubcategory.id, 'name': subsubcategory.name} for subsubcategory in subsubcategories]

    return JsonResponse(subsubcategories_list, safe=False)

def get_subsubsubcategories(request, subsubcategory_id):
    subsubcategory = Category.objects.get(id=subsubcategory_id)
    subsubsubcategories = subsubcategory.sub_categories.all()

    subsubsubcategories_list = [{'id': subsubsubcategory.id, 'name': subsubsubcategory.name} for subsubsubcategory in subsubsubcategories]

    return JsonResponse(subsubsubcategories_list, safe=False)

def calculate_total_cost(products):
    total_cost = sum(product.quantity * (product.in_price_avg or product.in_price_near or 0) for product in products)
    return total_cost


def summary(request):
    # Truy vấn tất cả sản phẩm từ cơ sở dữ liệu và loại bỏ các sản phẩm trùng lặp dựa trên trường 'category'
    products = Product.objects.all().order_by('name')

    # Tính tổng vốn
    total_cost = calculate_total_cost(products)

    # Truyền danh sách sản phẩm và tổng vốn vào template
    return render(request, 'app/summary.html', {'products': products, 'total_cost': total_cost})

def import_product(request):
    products = Product.objects.all()
    categories = Category.objects.filter(is_sub=False)

    # Tính tổng vốn
    total_cost = calculate_total_cost(products)
    import_cost = total_cost-368941.78401807696
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        supplier = Supplier.objects.get(name=supplier_name)
        import_date = request.POST.get('import_date')
        import_order = ImportOrder.objects.create(supplier=supplier, import_date=import_date)

        i = 1
        total_import = 0 
        while f'product_{i}' in request.POST:
            product_id = request.POST.get(f'product_{i}')
            quantity = float(request.POST.get(f'quantity_{i}'))
            in_price = float(request.POST.get(f'in_price_{i}'))
            category_id = request.POST.get(f'selected_category_{i}', None)
            subcategory_id = request.POST.get(f'selected_subcategory_{i}', None)
            subsubcategory_id = request.POST.get(f'selected_subsubcategory_{i}', None)

            if product_id == '777':
                product_name = request.POST.get(f'newProductName_{i}')
                product = Product.objects.create(name=product_name, quantity=quantity, in_price_near=in_price)
                if category_id:
                    category = Category.objects.get(id=category_id)
                    product.category.add(category)

                # Lưu subcategory cho product
                if subcategory_id:
                    subcategory = Category.objects.get(id=subcategory_id)
                    product.category.add(subcategory)

                # Lưu subsubcategory cho product
                if subsubcategory_id:
                    subsubcategory = Category.objects.get(id=subsubcategory_id)
                    product.category.add(subsubcategory)
            else:
                product = Product.objects.get(productID=product_id)
                ImportOrderDetail.objects.create(import_order=import_order, product=product, quantity=quantity, in_price=in_price)
                # Update Product information
                
                if product.in_price_avg is None:
                    product.in_price_avg = product.in_price_near
                product.in_price_near = in_price
                product.in_price_avg = (product.quantity * product.in_price_avg + quantity * in_price) / (product.quantity + quantity)
                product.quantity += quantity
                product.save()
            print("Name of product: ", product.name) 
            print("Quantity: ", quantity)
            print("In price: ", in_price)
            print("Category main id: ", category_id)
            print("Category sub id: ", subcategory_id)
            print("Category subsub id: ", subsubcategory_id)

            total_import += in_price * quantity

            i += 1
    
        import_order.total_import = total_import
        import_order.save()

        return redirect('import_product')  # Redirect to a success page or another view

    products = Product.objects.all()
    suppliers = Supplier.objects.all()

    return render(request, 'app/import_product.html', {'products': products, 'suppliers': suppliers, 'categories': categories, 'import_cost': import_cost})

def sale(request):
    products = Product.objects.all()
    employee = Employee.objects.all()
    customers = Customer.objects.all()

    # Tính tổng vốn
    total_cost = calculate_total_cost(products)
    sale_cost = 597470.914018077-total_cost
    total_in_price = 0
    sale_orders = SaleOrder.objects.all()
    # for sale_order in sale_orders:
    #     if sale_order.sale_orderID > :
    #         total_in_price += total_in_price + s
            
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer = Customer.objects.get(name=customer_name)
        employee_name = request.POST.get('employee_name')
        employee = Employee.objects.get(name=employee_name)
        sale_date = request.POST.get('sale_date')
        sale_order = SaleOrder.objects.create(customer=customer, employee=employee, sale_date=sale_date)

        i = 1
        total_revenue = 0 
        total_interest = 0 
        while f'product_{i}' in request.POST:
            product_id = request.POST.get(f'product_{i}')
            quantity = float(request.POST.get(f'quantity_{i}'))
            note = request.POST.get(f'note_{i}')
            sale_price = float(request.POST.get(f'sale_price_{i}'))
           
            product = Product.objects.get(productID=product_id)
            revenue = quantity * sale_price
            if product.in_price_avg is None:
                product.in_price_avg = product.in_price_near
            interest = revenue - quantity * product.in_price_avg
            SaleOrderDetail.objects.create(sale_order=sale_order, product=product, quantity=quantity, sale_price=sale_price, note = note)
            # Update Product information
            
            product.quantity = product.quantity-quantity
            product.save()
            print("Name of product: ", product.name) 
            print("Quantity: ", quantity)
            print("Sale price: ", sale_price)
            print("Revenue: ", quantity * sale_price)
            total_revenue += revenue
            total_interest += interest

            i += 1
    
        sale_order.total_revenue = total_revenue
        sale_order.total_interest = total_interest
        sale_order.save()

        return redirect('sale')  # Redirect to a success page or another view

    products = Product.objects.all()
    employees = Employee.objects.all()
    customers = Customer.objects.all()

    return render(request, 'app/sale.html', {'products': products, 'employees': employees, 'customers': customers, 'sale_cost': sale_cost})

@require_GET
def product_search(request):
    search_query = request.GET.get('search_query', '')
    name_filter = Q()
    if search_query:
        search_terms = search_query.split()
        for term in search_terms:
            name_filter &= Q(name__icontains=term)
    products = Product.objects.filter(name_filter).values('productID', 'name')
    return JsonResponse({'products': list(products)})

def product_info(request, product_id):
    try:
        product = Product.objects.get(productID=product_id)
        product_data = serialize('json', [product])

        return JsonResponse({'product': product_data}, safe=False)

    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
def sale_detail(request):
    sale_orders = SaleOrder.objects.all()
    for sale_order in sale_orders:
        sale_order_details = SaleOrderDetail.objects.filter(sale_order=sale_order)
        for sale_order_detail in sale_order_details:
            sale_order_detail.in_price = (sale_order_detail.revenue - sale_order_detail.interest)/sale_order_detail.quantity
    costs = Cost.objects.all()

    # Get the filters from the request
    sale_date_start = request.GET.get('sale_date_start')
    sale_date_end = request.GET.get('sale_date_end')
    employee_id = request.GET.get('employee')
    customer_id = request.GET.get('customer')

    # Apply the filters
    if sale_date_start:
        sale_date_start = datetime.strptime(sale_date_start, '%Y-%m-%d').date()
    if sale_date_end:
        sale_date_end = datetime.strptime(sale_date_end, '%Y-%m-%d').date()

    # Apply the filters
    if sale_date_start and sale_date_end:
        # Use __range for date range filtering
        sale_orders = sale_orders.filter(sale_date__range=(sale_date_start, sale_date_end))
        costs = costs.filter(expense_date__range=(sale_date_start, sale_date_end))
    if employee_id:
        sale_orders = sale_orders.filter(employee_id=employee_id)
    if customer_id:
        sale_orders = sale_orders.filter(customer_id=customer_id)

    total_cost = 0
    expense_cost = 0
    sum_revenue = 0
    sum_interest = 0


    sale_order_details = SaleOrderDetail.objects.filter(sale_order__in=sale_orders)
    for sale_order in sale_orders:
        check_revenue = 0
        check_interest = 0
        total_revenue = sale_order.total_revenue
        total_interest = sale_order.total_interest
        list_sale_order_details = SaleOrderDetail.objects.filter(sale_order=sale_order)
        for detail in list_sale_order_details:
            check_revenue += detail.revenue
            check_interest += detail.interest
        if check_revenue != total_revenue:
            print("Revenue is not correct")
            print("Sale order id: ", sale_order.total_revenue)
            sale_order.total_revenue = check_revenue
            sale_order.save()
        else:
            if check_interest != total_interest:
                print("Interest is not correct")
                print("Sale order id: ", sale_order.total_interest)
                sale_order.total_interest = check_interest
                sale_order.save()
        sum_revenue += sale_order.total_revenue
        sum_interest += sale_order.total_interest  # Retrieve the related SaleOrderDetail objects

    for detail in sale_order_details:
        total_cost += detail.revenue - detail.interest
        if detail.product.in_price_avg is None:
            detail.product.in_price_avg = detail.product.in_price_near

    for cost in costs:
        expense_cost += cost.amount

    profit = sum_revenue - total_cost - expense_cost
    hanh = profit * 0.8
    linh = profit * 0.2

    context = {
        'sale_orders': sale_orders,
        'employees': Employee.objects.all(),
        'customers': Customer.objects.all(),
        'total_cost': total_cost,
        'sum_revenue': sum_revenue,
        'sum_interest': sum_interest,
        'costs': costs,
        'expense_cost': expense_cost,
        'profit': profit,
        'hanh': hanh,
        'linh': linh,
    }
    return render(request, 'app/sale_detail.html', context)

def sale_order_details(request):
    # Lấy các Sale Order Detail và sắp xếp theo thứ tự interest (mặc định là tăng dần)
    sale_order_details = SaleOrderDetail.objects.all().order_by('interest')

    # Kiểm tra nếu có yêu cầu sắp xếp giảm dần
    if request.GET.get('order_by_interest') == 'desc':
        sale_order_details = sale_order_details.reverse()

    context = {
        'sale_order_details': sale_order_details,
    }

    return render(request, 'app/sale_order_details.html', context)

def enter_work_time(request):
    employees = Employee.objects.all()
    if request.method == 'POST':
        employee_name = request.POST.get('employee_name')
        employee = Employee.objects.get(name=employee_name)
        work_date = request.POST.get('work_date')
        work_time = request.POST.get('work_time')
        time = WorkTime.objects.create(employee=employee, work_time=work_time, work_date=work_date)
        time.save()
        return redirect('enter_work_time')

    return render(request, 'app/enter_work_time.html', {'employees': employees})

def salary_detail(request):
    sale_orders = SaleOrder.objects.all()
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        month_year_str = request.POST.get('month')  # Đây là chuỗi ngày/tháng/năm từ request

        # Chuyển đổi chuỗi thành đối tượng datetime
        month_year_date = datetime.strptime(month_year_str, '%Y-%m')

        # Lấy tháng và năm từ đối tượng datetime
        month = month_year_date.month
        year = month_year_date.year
  
        employee = Employee.objects.get(id=employee_id)
        work_times = WorkTime.objects.filter(employee_id=employee_id, work_date__month=month_year_date.month, work_date__year=month_year_date.year)

        print(employee.name)
        print(month)
        print(year)
        print(work_times.count)

        if month:
            sale_orders = sale_orders.filter(sale_date__month=month)
        if year:
            sale_orders = sale_orders.filter(sale_date__year=year)
        if employee_id:
            sale_orders = sale_orders.filter(employee_id=employee_id)

        sale_orders = SaleOrder.objects.filter(employee_id=employee_id, sale_date__month=month_year_date.month, sale_date__year=month_year_date.year).order_by('sale_date')
        sum_revenue = 0
        sum_interest = 0
        for sale_order in sale_orders:
            sum_revenue += sale_order.total_revenue
            sum_interest += sale_order.total_interest  # Retrieve the related SaleOrderDetail objects

        # Tính tổng số giờ làm trong tháng
        total_work_hours = WorkTime.objects.filter(employee=employee, work_date__month=month, work_date__year=year).aggregate(total_work_hours=models.Sum('work_time'))['total_work_hours'] or 0

        # Tiền lương theo giờ
        hourly_salary = total_work_hours * 15

        # Tính số ngày làm từ 12 tiếng trở lên và từ 7 đến 12 tiếng
        days_above_12_hours = WorkTime.objects.filter(employee=employee, work_date__month=month, work_date__year=year, work_time__gte=12).count()
        days_7_to_12_hours = WorkTime.objects.filter(employee=employee, work_date__month=month, work_date__year=year, work_time__gte=7, work_time__lt=12).count()

        # Phụ cấp ăn trưa
        meal_allowance = (30 * days_above_12_hours) + (15 * days_7_to_12_hours)

        # Phụ cấp xăng xe
        fuel_allowance = 200

        # Lấy thông tin doanh số nhân viên đó bán được trong tháng
        total_sales = SaleOrder.objects.filter(employee=employee, sale_date__month=month, sale_date__year=year).aggregate(total_sales=models.Sum('total_revenue'))['total_sales'] or 0

        # Tiền hoa hồng
        commission = total_sales * 0.01

        # Số giờ làm có thưởng
        bonus_hours = WorkTime.objects.filter(employee=employee, work_date__month=month, work_date__year=year, bonus=True).aggregate(total_bonus_hours=models.Sum('work_time'))['total_bonus_hours'] or 0

        # Lương thưởng
        bonus_salary = bonus_hours * 15

        #Lương chuyên cần
        bonus_full_time = 240

        # Tổng lương
        total_salary = hourly_salary + meal_allowance + fuel_allowance + commission + bonus_salary + bonus_full_time

        context = {
            'employee': employee,
            'work_times': work_times,
            'employees': Employee.objects.all(),
            'hourly_salary': hourly_salary,
            'meal_allowance': meal_allowance,
            'fuel_allowance': fuel_allowance,
            'commission': commission,
            'bonus_salary': bonus_salary,
            'bonus_full_time': bonus_full_time,
            'total_salary': total_salary,
            'total_work_hours' : total_work_hours,
            'sale_orders': sale_orders,
            'sum_revenue': sum_revenue,
            'sum_interest': sum_interest
        }

        return render(request, 'app/salary_detail.html', context)
    
    return render(request, 'app/salary_detail.html', {'employees': Employee.objects.all()})

def add_cost(request):
    if request.method == 'POST':
        expense_date = request.POST.get('expense_date')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        cost = Cost.objects.create(expense_date=expense_date, description=description, amount=amount)
        cost.save()
        return redirect('add_cost')

    return render(request, 'app/add_cost.html')

def import_order_detail(request):
    import_orders = ImportOrder.objects.all()
    # import_order_details = ImportOrderDetail.objects.filter(import_order=import_order)

    return render(request, 'app/import_order_detail.html', {'import_orders': import_orders})

