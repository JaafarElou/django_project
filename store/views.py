from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
import datetime
from .forms import UserCreationForm, LoginForm, ProductSearchForm
from .models import *
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})

# login page
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print(f"User is authenticated successfully.")
                return redirect('store')
    else:
        form = LoginForm()
    return render(request, 'store/login.html', {'form': form})

# logout page
def user_logout(request):
    logout(request)
    return redirect('login')


# Add the following import at the beginning of your views.py file
from django.db.models import Q

# Update your store view
def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    # Get the search query from the request GET parameters
    query = request.GET.get('q')

    # Filter products based on the search query
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |  # Search in product name
            Q(description__icontains=query)  # Search in product description
        ).distinct()
    else:
        # If no search query, get all products
        products = Product.objects.all()

    form = ProductSearchForm(request.GET)
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        if search_query:
            products = Product.objects.filter(name__icontains=search_query)

    page = request.GET.get('page', 1)
    paginator = Paginator(products, 3)  # Show 10 products per page

    try:
        paginated_products = paginator.page(page)
    except PageNotAnInteger:
        paginated_products = paginator.page(1)
    except EmptyPage:
        paginated_products = paginator.page(paginator.num_pages)

    context = {'products': paginated_products, 'cartItems': cartItems, 'form': form}
    return render(request, 'store/store.html', context)


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def cart(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)
