from django.db import models, transaction
from django.contrib.auth.models import User
from django.contrib.auth.hashers import  check_password, make_password
from django.urls import reverse
from django.utils import timezone
from django.db.models import F


# Create your models here.
class Customer(models.Model):
    userID = models.AutoField(primary_key=True, editable=False)
    user_name = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=10)
    

    def check_password(self, password):
        if (self.password==password):
            return True
        else:
            return False

class Category(models.Model):
    sub_category = models.ForeignKey('self', on_delete=models.CASCADE, related_name='sub_categories', null = True, blank = True)
    is_sub = models.BooleanField(default=False)
    name = models.CharField(max_length=200, null=True)
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    productID = models.AutoField(primary_key=True)
    category = models.ManyToManyField(Category, related_name='product')
    name = models.CharField(max_length=200,null=True)
    description = models.TextField(max_length=2000,null=True,blank=True)
    quantity = models.FloatField(default=0,null=True,blank=True)
    in_price_near = models.FloatField(null=True,blank=True)
    in_price_avg = models.FloatField(null=True,blank=True)
    price = models.FloatField(null=True,blank=True)
    image = models.ImageField(null=True,blank=True)
    featured = models.BooleanField(default=False, null=True, blank=False)
    
    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('product-detail', args=[str(self.productID)])

    @property
    def ImageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('cart', 'Giỏ hàng'),
        ('demo', 'Xem trước'),
        ('pending', 'Đang chờ xử lý'),
        ('shipped', 'Đã gửi hàng'),
        ('delivered', 'Đã giao hàng'),
        ('canceled', 'Đã hủy'),
    ]

    orderID = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=ORDER_STATUS_CHOICES, default='cart') 
    shipping_address = models.CharField(max_length=100, default='')
    canceled_reason = models.CharField(max_length=100, blank=True)

    def cancel_order(self, reason):
        if self.status == 'canceled':
            self.canceled_reason = reason
            self.save()
        else:
            raise ValueError("Cannot cancel an order that is not in 'canceled' status")

    def __str__(self):
        return str(self.pk)

    def ship_order(self):
        self.status = 'shipped'
        self.save()

    @property
    def get_cart_items(self):
        orderitems = self.orderdetail_set.all()
        total = sum([item.quantity for item in orderitems])
        return total
    @property
    def get_cart_total(self):
        orderitems = self.orderdetail_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    def get_absolute_url(self):
        return reverse('order-detail', args=[str(self.orderID)])


class OrderDetail(models.Model):
    product = models.ForeignKey(Product,on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(Order,on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=0,null=True,blank=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

    def __str__(self):
        return str(self.pk)

class Supplier(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class ImportOrder(models.Model):
    import_orderID = models.AutoField(primary_key=True)
    import_date = models.DateField(default=timezone.now)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    total_import = models.FloatField(default=0)

    def __str__(self):
        return f"Import Order #{self.import_orderID}"

class ImportOrderDetail(models.Model):
    import_order = models.ForeignKey(ImportOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField()
    in_price = models.FloatField()

    def __str__(self):
        return f"Import Order Detail #{self.id}"
    
    def delete(self, *args, **kwargs):
        product = self.product
        product.quantity -= self.quantity
        if product.quantity > 0:
            product.in_price_avg = ((product.quantity+self.quantity) * product.in_price_avg - self.quantity * self.in_price) / product.quantity
        else:
            product.in_price_avg = 0
        product.save()
        super().delete(*args, **kwargs)

    

class Employee(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class SaleOrder(models.Model):
    sale_orderID = models.AutoField(primary_key=True)
    sale_date = models.DateField(default=timezone.now)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    total_revenue = models.FloatField(default=0)
    total_interest = models.FloatField(default=0)

    def __str__(self):
        return f"Sale Order #{self.sale_orderID}"

class SaleOrderDetail(models.Model):
    sale_order = models.ForeignKey(SaleOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField()
    sale_price = models.FloatField()
    in_price = models.FloatField(default=0)
    revenue = models.FloatField()
    interest = models.FloatField()
    note = models.CharField(max_length=50, default='')

    def delete(self, *args, **kwargs):
        # Add the quantity of this instance back to the product's quantity
        self.product.quantity = F('quantity') + self.quantity
        self.product.save()

        # Update the total_revenue and total_interest of the related SaleOrder
        self.sale_order.total_revenue = F('total_revenue') - self.revenue
        self.sale_order.total_interest = F('total_interest') - self.interest
        self.sale_order.save()

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.pk:
            # Nếu đây là một bản ghi đã tồn tại
            old_sale_order_detail = SaleOrderDetail.objects.get(pk=self.pk)

            # Kiểm tra xem product có thay đổi hay không
            if old_sale_order_detail.product != self.product:
                # Trừ đi số lượng cũ từ quantity của sản phẩm trước khi sửa
                old_sale_order_detail.product.quantity = F('quantity') + old_sale_order_detail.quantity
                old_sale_order_detail.product.save()

        # Trừ đi số lượng mới từ quantity của sản phẩm sau khi sửa
        self.product.quantity = F('quantity') - self.quantity
        self.product.save()

        self.revenue = self.quantity * self.sale_price
        self.interest = self.quantity * (self.sale_price - (self.product.in_price_avg or self.product.in_price_near))

        # Cập nhật total_revenue và total_interest của SaleOrder liên quan
        self.sale_order.total_revenue = F('total_revenue') + self.revenue - old_sale_order_detail.revenue
        self.sale_order.total_interest = F('total_interest') + self.interest - old_sale_order_detail.interest
        self.sale_order.save()

        super().save(*args, **kwargs)

class WorkTime(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    work_date = models.DateField()
    work_time = models.FloatField(default=0,null=True,blank=True)
    bonus = models.BooleanField(default=False, null=False, blank=False)

class Cost(models.Model):
    expense_date = models.DateField()
    description = models.CharField(max_length=255)
    amount = models.FloatField()


   