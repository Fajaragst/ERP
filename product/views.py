"""
Views for the product app
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required
from django.urls import reverse_lazy
from product.form import ProductForm
from .models import Product

@method_decorator(login_required, name="dispatch")
class ProductListView(ListView):
    """
    View to list all products
    """
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_add'] = self.request.user.has_perm('product.add_product')
        context['can_edit'] = self.request.user.has_perm('product.change_product')
        context['can_delete'] = self.request.user.has_perm('product.delete_product')
        
        return context

@method_decorator(permission_required('product.add_product', login_url=reverse_lazy('module:module_list')), name="dispatch")
class ProductCreateView(CreateView):
    """
    View to create a new product
    """
    model = Product
    template_name = 'product_form.html'
    form_class = ProductForm
    success_url = reverse_lazy('product:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['title'] = 'Create Product'
        context['button_text'] = 'Create'
        return context

@method_decorator(permission_required('product.change_product', login_url=reverse_lazy('module:module_list')), name="dispatch")
class ProductUpdateView(UpdateView):
    """
    View to update a product
    """
    model = Product
    template_name = 'product_form.html'
    form_class = ProductForm
    success_url = reverse_lazy('product:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Product'
        context['button_text'] = 'Update'
        return context

@method_decorator(permission_required('product.delete_product', login_url=reverse_lazy('module:module_list')), name="dispatch")
class ProductDeleteView(DeleteView):
    """
    View to delete a product
    """
    model = Product
    success_url = reverse_lazy('product:product_list')
