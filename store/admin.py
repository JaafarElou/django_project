from django.contrib import admin

from .models import *

class ProductInline(admin.TabularInline):
    model = Product
    extra = 0  # Show existing products without the option to add more

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('cate_name', 'product_count')

    def product_count(self, obj):
        return obj.product_set.count()

    product_count.short_description = 'Number of Products'

    inlines = [ProductInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # Show existing order items without the option to add more

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'date_ordered', 'complete', 'transaction_id']
    inlines = [OrderItemInline]

admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
admin.site.register(Category, CategoryAdmin)
