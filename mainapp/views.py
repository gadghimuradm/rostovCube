from django.db import transaction
from django.shortcuts import render
from django.views.generic import DetailView, View
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login


from .models import Category, CartProduct, Customer, Product, Order
from .mixins import CartMixin, CategoryDetailMixin
from .forms import OrderForm, LoginForm, RegistrationForm
from .utils import recalc_cart


class InfoView(CartMixin, DetailView):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        products = Product.objects.all()
        context = {
            'categories': categories,
            'products': products,
            'cart': self.cart
        }
        return render(request, 'info.html', context)


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            categories = Category.objects.all()
            context = {
                'cart': self.cart,
                'categories': categories
            }
            return render(request, 'cart.html', context)
        else:
            messages.add_message(request, messages.INFO, 'Для покупок необходимо создать аккаунт')
            return HttpResponseRedirect('/')


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        products = Product.objects.all()
        context = {
            'categories': categories,
            'products': products,
            'cart': self.cart
        }
        return render(request, 'base.html', context)


class ProductDetailView(CategoryDetailMixin, CartMixin, DetailView):

    model = Product
    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'
    queryset = Product.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context


class CategoryDetailView(CategoryDetailMixin, CartMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.filter(category_id=context['object'].id)
        context['cart'] = self.cart
        context['products'] = products
        return context


class AddToCardView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            product_slug = kwargs.get('slug')
            product = Product.objects.get(slug=product_slug)
            cart_product, created = CartProduct.objects.get_or_create(
                user=self.cart.owner, cart=self.cart, product=product
            )
            if created:
                self.cart.products.add(cart_product)
            recalc_cart(self.cart)
            self.cart.save()
            messages.add_message(request, messages.INFO, 'Товар успешно добавлен')
            return HttpResponseRedirect('/cart/')
        else:
            messages.add_message(request, messages.INFO, 'Для покупок необходимо создать аккаунт')
            return HttpResponseRedirect('/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        cart_product.save()
        recalc_cart(self.cart)
        self.cart.save()
        messages.add_message(request, messages.INFO, 'Количество успешно изменено')
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(
            user=self.cart.owner, cart=self.cart, product=product
        )
        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        self.cart.save()
        messages.add_message(request, messages.INFO, 'Товар успешно удалён')
        return HttpResponseRedirect('/cart/')


class CheckoutView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = OrderForm(request.POST or None)
        context = {
            'form': form,
            'categories': categories,
            'cart': self.cart
        }
        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_date = form.cleaned_data['order_date']
            new_order.comment = form.cleaned_data['comment']
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Спасибо за заказ! Менеджер с вами свяжется')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')


class LoginView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        form = LoginForm(request.POST or None)
        context = {
            'categories': categories,
            'form': form,
            'cart': self.cart
        }
        return render(request, 'login.html', context)

    def post(self, request, *args, **kwargs):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return HttpResponseRedirect('/')

        context = {'form': form, 'cart': self.cart}
        return render(request, 'login.html', context)


class RegistrationView(CategoryDetailMixin, CartMixin, View):

    def get(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        categories = Category.objects.all()
        context = {
            'categories': categories,
            'form': form,
            'cart': self.cart
        }
        return render(request, 'registration.html', context)

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST or None)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.username = form.cleaned_data['username']
            new_user.email = form.cleaned_data['email']
            new_user.first_name = form.cleaned_data['first_name']
            new_user.last_name = form.cleaned_data['last_name']
            new_user.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            Customer.objects.create(
                user=new_user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address']
            )
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            login(request, user)
            return HttpResponseRedirect('/')

        context = {'form': form, 'cart': self.cart}
        return render(request, 'registration.html', context)


class ProfileView(CategoryDetailMixin, CartMixin, View):

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        categories = Category.objects.all()
        context = {
            'categories': categories,
            'orders': orders,
            'cart': self.cart
        }
        return render(request, 'profile.html', context)