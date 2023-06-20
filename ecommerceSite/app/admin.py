from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Product)
# admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Employee)
# admin.site.register(OrderDetail)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(ImportOrder )
admin.site.register(ImportOrderDetail)
admin.site.register(SaleOrder )
admin.site.register(SaleOrderDetail)
admin.site.register(WorkTime)
admin.site.register(Cost)

class ImportOrderDetailAdmin(admin.ModelAdmin):
    # existing fields...

    def delete_model(self, request, obj):
        product = obj.product
        product.quantity -= obj.quantity
        if product.quantity > 0:
            product.in_price_avg = (product.quantity * product.in_price_avg - obj.quantity * obj.in_price) / product.quantity
        else:
            product.in_price_avg = 0
        product.save()
        super().delete_model(request, obj)

