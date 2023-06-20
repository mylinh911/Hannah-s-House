from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from app.models import Customer, Product, Category, Order, OrderDetail
from django.contrib.auth import get_user_model
from django.test import TestCase
from app.serializers import AcceptOrderSerializer

class CustomerAPITestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse('register-api')

    def test_create_customer_with_valid_data(self):
        data = {
            'user_name': 'john_doe',
            'password': 'password123',
            'email': 'john@example.com',
            'full_name': 'John Doe',
            'address': '123 Main St',
            'phone': '1234567890',
        }

        initial_count = Customer.objects.count()  

        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), initial_count + 1)  
        self.assertEqual(Customer.objects.get().user_name, 'john_doe')

    def test_create_customer_with_duplicate_user_name(self):
        # Create a customer with the same user_name
        Customer.objects.create(
            user_name='john_doe',
            password='password123',
            email='john@example.com',
            full_name='John Doe',
            address='123 Main St',
            phone='1234567890',
        )

        data = {
            'user_name': 'john_doe',
            'password': 'password456',
            'email': 'john456@example.com',
            'full_name': 'John Doe 456',
            'address': '456 Main St',
            'phone': '0987654321',
        }

        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['user_name'][0]), "{'This user_name already exists.'}")
        self.assertEqual(Customer.objects.count(), 1)

class CustomerLoginViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            user_name='testuser',
            password='testpassword',
            email='test@example.com',
            full_name='Test User',
            address='Test Address',
            phone='1234567890'
        )

    def test_successful_login(self):
        data = {
            'user_name': 'testuser',
            'password': 'testpassword'
        }
        url = reverse('login-api')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Đăng nhập thành công.')
        self.assertIn('session_id', response.data)

    def test_invalid_password(self):
        data = {
            'user_name': 'testuser',
            'password': 'wrongpassword'
        }
        url = reverse('login-api')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['message'], 'Mật khẩu không hợp lệ.')

    def test_customer_not_found(self):
        data = {
            'user_name': 'nonexistentuser',
            'password': 'testpassword'
        }
        url = reverse('login-api')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'Khách hàng không tồn tại.')

    def test_missing_required_fields(self):
        data = {
            'user_name': 'testuser'
            # Missing 'password' field
        }
        url = reverse('login-api')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertEqual(response.data['password'][0], 'Trường này là bắt buộc.')

    def test_get_required_fields(self):
        url = reverse('login-api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('required_fields', response.data)
        self.assertListEqual(response.data['required_fields'], ['user_name', 'password'])

class ProductListViewTest(APITestCase):
    def setUp(self):
        category = Category.objects.create(name='Electronics')
        Product.objects.create(
            name='Laptop',
            description='A high-performance laptop',
            price=1500.0,
            featured=True
        ).category.add(category)
        Product.objects.create(
            name='Headphones',
            description='Wireless headphones',
            price=100.0,
            featured=False
        ).category.add(category)

    def test_get_product_list(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Laptop')
        self.assertEqual(response.data[0]['category'][0]['name'], 'Electronics')
        self.assertEqual(response.data[1]['name'], 'Headphones')
        self.assertEqual(response.data[1]['category'][0]['name'], 'Electronics')

    def test_filter_by_category(self):
        url = reverse('product-list')
        category = Category.objects.get(name='Electronics')
        data = {'category': category.id}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_featured_only(self):
        url = reverse('product-list')
        data = {'featured_only': 'true'}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Laptop')

class OrderPlacementAPITestCase(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(user_name='test_user', password='test_password', email='test@example.com', full_name='Test User', address='Test Address', phone='1234567890')

        self.category1 = Category.objects.create(name='Category 1', slug='category-1')
        self.category2 = Category.objects.create(name='Category 2', slug='category-2')

        self.product1 = Product.objects.create(name='Product 1', description='Description 1', price=10.0)
        self.product1.category.add(self.category1)
        self.product2 = Product.objects.create(name='Product 2', description='Description 2', price=20.0)
        self.product2.category.add(self.category2)
        
    def test_get_required_fields(self):
        url = reverse('order-api')  
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_fields = {
            'order_required_fields': ['order_details', 'shipping_address'],
            'order_detail_required_fields': ['product', 'quantity']
        }
        self.assertEqual(response.data, expected_fields)

    def test_create_order(self):
        login_url = reverse('login-api')
        login_data = {
            'user_name': self.customer.user_name,
            'password': self.customer.password
        }
        login_response = self.client.post(login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        initial_order_count = Order.objects.count()
        initial_order_detail_count = OrderDetail.objects.count()

        
        # Retrieve the session ID from the response's cookies
        session_id = login_response.cookies.get('sessionid').value

        # Set the logged-in user as the customer
        customer = self.customer

        # Prepare the data for creating an order
        order_details = [
            {
                'product': 1,
                'quantity': 2
            },
            {
                'product': 2,
                'quantity': 3
            }
        ]
        shipping_address = '123 Main St'

        # Set the request data
        url = reverse('order-api')
        data = {
            'customer': customer.userID,
            'order_details': order_details,
            'shipping_address': shipping_address
        }

        # Set the session ID in the client's credentials
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + session_id)
        self.client.cookies['sessionid'] = session_id

        # Send the POST request to create the order
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Order.objects.count(), initial_order_count + 1)
        self.assertEqual(OrderDetail.objects.count(), initial_order_detail_count + 2)

    def test_create_order_invalid_data(self):
        url = reverse('order-api')  
        order_data = {
            'order_details': [
                {
                    'product': 1,
                    'quantity': 2
                }
            ],
            'shipping_address': '123 Main St'
        }

        response = self.client.post(url, order_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('order_details', response.data)

class AcceptOrderViewTests(APITestCase):
    def setUp(self):
        # Create a test order with status 'pending'
        self.customer = Customer.objects.create(user_name='test_user')

        self.order = Order.objects.create(customer=self.customer,status='pending')
        self.url = reverse('accept-order-api', kwargs={'order_id': self.order.orderID})

    def test_get_order(self):
        response = self.client.get(self.url)
        serializer = AcceptOrderSerializer(self.order)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_put_order_status(self):
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')

    def test_put_order_status_invalid(self):
        # Change the order status to 'shipped' manually
        self.order.status = 'shipped'
        self.order.save()
        
        response = self.client.put(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Order status cannot be changed'})

    def test_put_order_not_found(self):
        invalid_url = reverse('accept-order-api', kwargs={'order_id': 999})
        response = self.client.put(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'message': 'Order not found'})