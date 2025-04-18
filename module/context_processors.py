from .models import Module

def modules_processor(request):
    """
    Context processor that adds modules to all templates
    """
    modules = Module.objects.filter(is_installed=True).order_by('name')
    return {
        'active_modules': modules
    } 