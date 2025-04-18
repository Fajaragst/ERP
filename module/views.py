import importlib
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView
from django.contrib import messages
from django.views import View
from django.core.management import call_command
from .models import Module
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .registry import registry


# Create your views here.
@method_decorator(login_required, name="dispatch")
class ModuleListView(ListView):
    model = Module
    template_name = 'module_list.html'
    context_object_name = 'modules'

class InstallModuleView(TemplateView):

    def post(self, request, module_id):
        module = get_object_or_404(Module, pk=module_id)
        
        if not module.is_installed:
            try:
                # Install the module
                importlib.import_module(module.app_name)
                registry.install_module(module.app_name)
                
                call_command('migrate', module.app_name)
                messages.success(request, f"Module '{module.name}' successfully installed.")
            except Exception as e:
                messages.error(request, f"Error installing module: {str(e)}")
        else:
            messages.info(request, f"Module '{module.name}' is already installed.")
            
        return redirect('module:module_list')

class UninstallModuleView(TemplateView):
    def post(self, request, module_id):
        module = get_object_or_404(Module, pk=module_id)
        module.is_installed = False 
        module.save()
        messages.success(request, f"Module '{module.name}' successfully uninstalled.")
        
        return redirect('module:module_list')

class UpgradeModuleView(TemplateView):
    def post(self, request, module_id):
        module = get_object_or_404(Module, pk=module_id)
        call_command('migrate', module.app_name)
        messages.success(request, f"Module '{module.name}' successfully upgraded.")
        
        return redirect('module:module_list')