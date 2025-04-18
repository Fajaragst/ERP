import importlib
import os
import pkgutil
from django.apps import apps
from django.conf import settings
from django.urls import clear_url_caches, path, include
from .models import Module

class ModuleRegistry:
    """
    Registry for managing modules in the ERP system.
    Handles discovery, registration, and status tracking of modules.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModuleRegistry, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize the registry"""
        self.modules = {}
        self.discover_modules()
        self.sync_with_database()
    
    def discover_modules(self):
        """
        Discover available modules by scanning the project directory
        and looking for apps that have a module_info.py file
        """
        # Convert BASE_DIR to string if it's a Path object
        base_dir = str(settings.BASE_DIR)
        
        # Get all installed apps
        for app_config in apps.get_app_configs():
            # Skip Django's built-in apps and third-party apps
            if not str(app_config.path).startswith(base_dir):
                continue
                
            # Check if this app has module_info.py
            module_info_path = os.path.join(app_config.path, 'module_info.py')

            if os.path.exists(module_info_path):
                try:
                    # Import the module_info
                    module_info = importlib.import_module(f"{app_config.name}.module_info")
                    # Register this module
                    self.register_module(
                        name=getattr(module_info, 'NAME', app_config.name),
                        app_name=app_config.name,
                        description=getattr(module_info, 'DESCRIPTION', ''),
                        version=getattr(module_info, 'VERSION', '1.0.0'),
                    )
                except ImportError:
                    # Skip if module_info can't be imported
                    pass
    
    def register_module(self, name, app_name, description='', version='1.0.0'):
        """
        Register a module with the registry and update the database
        """
            
        # Store in memory registry
        self.modules[app_name] = {
            'name': name,
            'description': description,
            'version': version,
        }

        # Update or create in database
        try:
            module, created = Module.objects.get_or_create(
                app_name=app_name,
                defaults={
                    'name': name,
                    'description': description,
                    'version': version,
                    'is_installed': False
                }
            )
            
            # Update if module exists but info has changed
            if not created:
                update_fields = []
                if module.name != name:
                    module.name = name
                    update_fields.append('name')
                if module.description != description:
                    module.description = description
                    update_fields.append('description')
                if module.version != version:
                    module.version = version
                    update_fields.append('version')
                
                if update_fields:
                    module.save(update_fields=update_fields)
                    
        except Exception as e:
            # This will happen during initial migrations when Module table doesn't exist yet
            pass
    
    def get_module(self, app_name):
        """Get module info from registry"""
        return self.modules.get(app_name)
    
    def get_all_modules(self):
        """Get all registered modules"""
        return self.modules
    
    def is_module_installed(self, app_name):
        """Check if a module is installed"""
        try:
            module = Module.objects.get(app_name=app_name, is_installed=True)
            return module.is_installed
        except Module.DoesNotExist:
            return False
    
    def install_module(self, app_name):
        """Install a module"""
        try:
            module = Module.objects.get(app_name=app_name)
            module.is_installed = True
            module.save()
            self.reload_urlconf()
            return True
        except Module.DoesNotExist:
            return False
    
    def uninstall_module(self, app_name):
        """Uninstall a module"""
        try:
            module = Module.objects.get(app_name=app_name)
            module.is_installed = False
            module.save()
            self.reload_urlconf()
            
            # Mark as missing if it's not in the filesystem
            if app_name in self.modules:
                if self.modules[app_name].get('missing', False):
                    # This module is missing from filesystem, consider removing it
                    # from database if it's been uninstalled
                    if not module.is_installed:
                        print(f"Removing module '{module.name}' from database as it's uninstalled and missing from filesystem")
                        module.delete()
                        # Also remove from in-memory registry
                        del self.modules[app_name]
            
            return True
        except Module.DoesNotExist:
            return False
    
    def sync_with_database(self):
        """
        Sync registry with database:
        1. Add modules that exist in database but not in registry
        2. Remove modules from database that no longer exist in the filesystem
        """
        try:
            # Get all modules from database
            db_modules = Module.objects.all()
            
            # Add modules that exist in database but not in registry
            for db_module in db_modules:
                if db_module.app_name not in self.modules:
                    # Module exists in database but not in filesystem
                    # Keep it in registry for reference
                    self.modules[db_module.app_name] = {
                        'name': db_module.name,
                        'description': db_module.description,
                        'version': db_module.version,
                        'missing': True  # Mark as missing from filesystem
                    }
                    
                    print(f"Warning: Module '{db_module.name}' exists in database but not in filesystem")
                    
                    # Delete module from database if it doesn't exist in filesystem
                    if not db_module.is_installed:
                        print(f"Removing module '{db_module.name}' from database as it's not installed and missing from filesystem")
                        db_module.delete()
        except Exception as e:
            # This will happen during initial migrations when Module table doesn't exist yet
            pass

    def get_urlpatterns(self):
        urlpatterns = []
        print('apply again')
        modules = Module.objects.filter(is_installed=True)
        for module in modules:
            urlpatterns.append(
                path(f'{module.app_name}/', include(f'{module.app_name}.urls'))
            )
        print(urlpatterns)
        return urlpatterns

    def reload_urlconf(self):
        clear_url_caches()
        importlib.reload(importlib.import_module(settings.ROOT_URLCONF))
    
# Singleton instance
registry = ModuleRegistry() 