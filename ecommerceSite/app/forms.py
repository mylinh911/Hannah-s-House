from django import forms
from django.core.exceptions import ValidationError
from .models import Customer, Product, Category, WorkTime, Cost

class CustomerForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm password')

    def clean_user_name(self):
        user_name = self.cleaned_data.get('user_name')

        if Customer.objects.filter(user_name=user_name).exists():
            raise ValidationError('Username already exists')

        return user_name

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')

        if password and password2 and password != password2:
            raise forms.ValidationError('Passwords do not match')

    class Meta:
        model = Customer
        fields = ['user_name', 'password', 'password2', 'email', 'name', 'address', 'phone']

class ProductSearchForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False, label='Tìm kiếm sản phẩm')

class CustomCategoryModelChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class ProductForm(forms.ModelForm):
    selected_category = forms.CharField(widget=forms.HiddenInput, required=False)
    selected_subcategory = forms.CharField(widget=forms.HiddenInput, required=False)
    selected_subsubcategory = forms.CharField(widget=forms.HiddenInput, required=False)

    # image = forms.ImageField()
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'quantity', 'in_price_near', 'price']

    def clean_name(self):
        name = self.cleaned_data.get('name')

        if Product.objects.filter(name=name).exists():
            raise ValidationError('Sản phẩm đã có trong danh sách')

        return name
    
class WorkTimeForm(forms.ModelForm):
    class Meta:
        model = WorkTime
        fields = ['employee', 'work_date', 'work_time']

class CostForm(forms.ModelForm):
    class Meta:
        model = Cost
        fields = ['expense_date', 'description', 'amount']
    

        
