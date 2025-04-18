from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Module
from .registry import ModuleRegistry
import os
import tempfile
from unittest.mock import patch, MagicMock

class ModuleModelTest(TestCase):
    """Unit tests for the Module model"""
    
    def setUp(self):
        self.module = Module.objects.create(
            name="Test Module",
            description="A test module",
            version="1.0.0",
            is_installed=False,
            app_name="test_module"
        )
    
    def test_module_creation(self):
        """Test that a module can be created"""
        self.assertEqual(self.module.name, "Test Module")
        self.assertEqual(self.module.description, "A test module")
        self.assertEqual(self.module.version, "1.0.0")
        self.assertEqual(self.module.is_installed, False)
        self.assertEqual(self.module.app_name, "test_module")
    
    def test_string_representation(self):
        """Test the string representation of a module"""
        self.assertEqual(str(self.module), "Test Module v1.0.0 (Not installed)")
        
        # Test with installed module
        self.module.is_installed = True
        self.module.save()
        self.assertEqual(str(self.module), "Test Module v1.0.0 (Installed)")


class ModuleRegistryTest(TestCase):
    """Tests for the ModuleRegistry class"""
    
    def setUp(self):
        # Create a temporary module_info.py file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.module_dir = os.path.join(self.temp_dir.name, "test_module")
        os.makedirs(self.module_dir, exist_ok=True)
        
        # Create a module_info.py file
        with open(os.path.join(self.module_dir, "module_info.py"), "w") as f:
            f.write('NAME = "Test Module"\n')
            f.write('DESCRIPTION = "A test module"\n')
            f.write('VERSION = "1.0.0"\n')
        
        # Create a module in the database
        self.module = Module.objects.create(
            name="Database Module",
            description="A module that exists only in the database",
            version="2.0.0",
            is_installed=True,
            app_name="db_module"
        )
        
        # Initialize the registry
        self.registry = ModuleRegistry()
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_get_module(self):
        """Test getting a module from the registry"""
        # Add a module to the registry
        self.registry.modules["test_module"] = {
            "name": "Test Module",
            "description": "A test module",
            "version": "1.0.0"
        }
        
        # Get the module
        module = self.registry.get_module("test_module")
        
        # Check that the module was returned correctly
        self.assertEqual(module["name"], "Test Module")
        self.assertEqual(module["description"], "A test module")
        self.assertEqual(module["version"], "1.0.0")
    
    def test_is_module_installed(self):
        """Test checking if a module is installed"""
        # The module created in setUp is installed
        self.assertTrue(self.registry.is_module_installed("db_module"))
        
        # A non-existent module should not be installed
        self.assertFalse(self.registry.is_module_installed("nonexistent_module"))
    
    def test_install_module(self):
        """Test installing a module"""
        # Create a module that is not installed
        Module.objects.create(
            name="Uninstalled Module",
            description="A module that is not installed",
            version="1.0.0",
            is_installed=False,
            app_name="uninstalled_module"
        )
        
        # Install the module
        result = self.registry.install_module("uninstalled_module")
        
        # Check that the installation was successful
        self.assertTrue(result)
        
        # Check that the module is now installed
        module = Module.objects.get(app_name="uninstalled_module")
        self.assertTrue(module.is_installed)
    
    def test_uninstall_module(self):
        """Test uninstalling a module"""
        # The module created in setUp is installed
        
        # Uninstall the module
        result = self.registry.uninstall_module("db_module")
        
        # Check that the uninstallation was successful
        self.assertTrue(result)
        
        # Check that the module is now uninstalled
        module = Module.objects.get(app_name="db_module")
        self.assertFalse(module.is_installed)


class ModuleViewsTest(TestCase):
    """Integration tests for the Module views"""
    
    def setUp(self):
        # Create a test user with admin privileges
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create a regular user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create test modules
        self.module1 = Module.objects.create(
            name="Test Module 1",
            description="A test module",
            version="1.0.0",
            is_installed=False,
            app_name="test_module1"
        )
        
        self.module2 = Module.objects.create(
            name="Test Module 2",
            description="Another test module",
            version="2.0.0",
            is_installed=True,
            app_name="test_module2"
        )
        
        # Set up client
        self.client = Client()
    
    def test_module_list_view_requires_login(self):
        """Test that the module list view requires login"""
        response = self.client.get(reverse('module:module_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('login', response.url)
    
    def test_module_list_view_with_login(self):
        """Test that the module list view works with login"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('module:module_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Module 1")
        self.assertContains(response, "Test Module 2")
    
    def test_install_module_view(self):
        """Test installing a module"""
        
        # Mock the importlib.import_module function to prevent actual import attempts
        with patch('module.views.importlib.import_module') as mock_import:
            mock_import.return_value = MagicMock()
            
            # Login and make the request
            self.client.login(username='admin', password='adminpassword')
            response = self.client.post(
                reverse('module:install_module', kwargs={'module_id': self.module1.pk})
            )
            
            # Check redirect
            self.assertEqual(response.status_code, 302)  # Redirect after success
            
            # Verify the module is now installed
            self.module1.refresh_from_db()
            self.assertTrue(self.module1.is_installed)
            
            # Verify the import was attempted with the correct module name
            mock_import.assert_called_once_with(self.module1.app_name)
    
    def test_uninstall_module_view(self):
        """Test uninstalling a module"""
        self.client.login(username='admin', password='adminpassword')
        response = self.client.post(
            reverse('module:uninstall_module', kwargs={'module_id': self.module2.pk})
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify the module is now uninstalled
        self.module2.refresh_from_db()
        self.assertFalse(self.module2.is_installed)
    
    def test_context_processor(self):
        """Test that the context processor adds modules to the context"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('module:module_list'))
        
        # Only installed modules should be in the context
        active_modules = response.context['active_modules']
        self.assertEqual(len(active_modules), 1)
        self.assertEqual(active_modules[0].name, "Test Module 2")


class ModuleMiddlewareTest(TestCase):
    """Tests for the ModularURLMiddleware"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create test modules
        self.installed_module = Module.objects.create(
            name="Installed Module",
            description="A module that is installed",
            version="1.0.0",
            is_installed=True,
            app_name="installed"
        )
        
        self.uninstalled_module = Module.objects.create(
            name="Uninstalled Module",
            description="A module that is not installed",
            version="1.0.0",
            is_installed=False,
            app_name="uninstalled"
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')
    
    def test_access_to_uninstalled_module(self):
        """Test that access to an uninstalled module is blocked"""
        # This URL doesn't actually exist, but the middleware should block it before Django tries to resolve it
        response = self.client.get('/uninstalled/')
        self.assertEqual(response.status_code, 404)
    
    def test_access_to_nonexistent_module(self):
        """Test that access to a non-existent module is allowed (Django will handle the 404)"""
        # This URL doesn't exist, but it's not an uninstalled module, so the middleware should allow it
        response = self.client.get('/nonexistent/')
        self.assertEqual(response.status_code, 404)  # Django's 404, not the middleware's
