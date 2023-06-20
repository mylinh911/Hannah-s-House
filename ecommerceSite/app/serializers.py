from rest_framework import serializers
from .models import Customer, Product, Category, Order, OrderDetail
from django.contrib.sessions.models import Session

class CustomerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'user_name': {'required': True},
            'email': {'required': True},
            'full_name': {'required': True},
            'address': {'required': True},
            'phone': {'required': True},
        }

    def validate_user_name(self, value):
        if self.instance:
            if Customer.objects.filter(user_name=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError({"This user_name already exists."})
        else:
            if Customer.objects.filter(user_name=value).exists():
                raise serializers.ValidationError({"This user_name already exists."})
        return value

class CustomerLoginSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=50, required=True)
    password = serializers.CharField(max_length=50, required=True, write_only=True)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name',)

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=True)

    class Meta:
        model = Product
        fields = ('productID', 'category', 'name', 'description', 'price','featured')

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = ['product', 'quantity']
        extra_kwargs = {
            'product': {'required': True},
            'quantity': {'required': True},
        }

class OrderSerializer(serializers.ModelSerializer):
    order_details = OrderDetailSerializer(many=True, write_only=True)
    customer = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Order
        fields = ['customer', 'order_details', 'shipping_address']
        extra_kwargs = {
            'order_details': {'required': True},
            'shipping_address': {'required': True},
        }

    def create(self, validated_data):
        session = self.context['request'].session
        customer_id = session.get('customer_id')

        try:
            customer = Customer.objects.get(userID=customer_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError({"detail": "Login please"})

        validated_data['customer'] = customer
        order_details_data = validated_data.pop('order_details')
        order = Order.objects.create(**validated_data)

        for order_detail_data in order_details_data:
            OrderDetail.objects.create(order=order, **order_detail_data)

        return order

    def get_required_fields(self):
        order_serializer = OrderSerializer()
        order_detail_serializer = OrderDetailSerializer()

        order_required_fields = [field.field_name for field in order_serializer.fields.values() if field.required]
        order_detail_required_fields = [field.field_name for field in order_detail_serializer.fields.values() if field.required]

        return {
            'order_required_fields': order_required_fields,
            'order_detail_required_fields': order_detail_required_fields,
        }

class AcceptOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'