from django.shortcuts import render
from django.http import Http404
from module.models import Module


class ModularURLMiddleware:
    """
    Middleware to dynamically include URLs from installed modules.
    This allows modules to be installed/uninstalled at runtime without restarting the server.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Process the request and dynamically include URLs if needed."""
        
        # Extract the first part of the path to check if it's a module
        path_parts = request.path.strip('/').split('/')
        if path_parts:
            path_prefix = path_parts[0]
            
            # Check if this path prefix corresponds to an installed module
            module = Module.objects.filter(app_name=path_prefix, is_installed=False).first()
            
            if module:
                # Return a 404 response when trying to access an uninstalled module
                raise Http404(f"Module '{path_prefix}' is not installed")


            
        response = self.get_response(request)
        return response