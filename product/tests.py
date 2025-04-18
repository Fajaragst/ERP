from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Product

class ProductModelTest(TestCase):
    """Unit tests for the Product model"""
    
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Product",
            barcode="123456789",
            price=99.99,
            stock=100
        )
    
    def test_product_creation(self):
        """Test that a product can be created"""
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.barcode, "123456789")
        self.assertEqual(self.product.price, 99.99)
        self.assertEqual(self.product.stock, 100)
    
    def test_string_representation(self):
        """Test the string representation of a product"""
        self.assertEqual(str(self.product), "Test Product")


class ProductViewsTest(TestCase):
    """Integration tests for the Product views"""
    
    def setUp(self):
        # Create a test user with product permissions
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create a privileged user with all product permissions
        self.privileged = User.objects.create_user(
            username='privileged',
            password='privilegedpass'
        )
        
        # Get content type for product model
        content_type = ContentType.objects.get_for_model(Product)
        
        # Add permissions to privileged user
        add_permission = Permission.objects.get(
            content_type=content_type, codename='add_product')
        change_permission = Permission.objects.get(
            content_type=content_type, codename='change_product')
        delete_permission = Permission.objects.get(
            content_type=content_type, codename='delete_product')
        
        self.privileged.user_permissions.add(add_permission)
        self.privileged.user_permissions.add(change_permission)
        self.privileged.user_permissions.add(delete_permission)
        
        # Create test product
        self.product = Product.objects.create(
            name="Test Product",
            barcode="123456789",
            price=99.99,
            stock=100
        )
        
        # Set up client
        self.client = Client()
    
    def test_product_list_view_requires_login(self):
        """Test that the product list view requires login"""
        response = self.client.get(reverse('product:product_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('login', response.url)
    
    def test_product_list_view_with_login(self):
        """Test that the product list view works with login"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('product:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertContains(response, "123456789")
        self.assertContains(response, "99.99")
    
    def test_product_create_view_requires_permission(self):
        """Test that the product create view requires permission"""
        # Login as regular user without permissions
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('product:product_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to module list
    
    def test_product_create_view_with_permission(self):
        """Test that the product create view works with permission"""
        self.client.login(username='privileged', password='privilegedpass')
        response = self.client.get(reverse('product:product_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Product")
    
    def test_product_update_view_requires_permission(self):
        """Test that the product update view requires permission"""
        # Login as regular user without permissions
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('product:product_update', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to module list
    
    def test_product_update_view_with_permission(self):
        """Test that the product update view works with permission"""
        self.client.login(username='privileged', password='privilegedpass')
        response = self.client.get(
            reverse('product:product_update', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Update Product")
        self.assertContains(response, "Test Product")  # Pre-filled form
    
    def test_product_delete_view_requires_permission(self):
        """Test that the product delete view requires permission"""
        # Login as regular user without permissions
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(
            reverse('product:product_delete', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 302)  # Redirect to module list
    
    def test_product_create_post(self):
        """Test creating a product via POST"""
        self.client.login(username='privileged', password='privilegedpass')
        new_product_data = {
            'name': 'New Product',
            'barcode': '987654321',
            'price': 49.99,
            'stock': 50
        }
        response = self.client.post(
            reverse('product:product_create'),
            new_product_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify the product was created
        self.assertTrue(Product.objects.filter(name='New Product').exists())
        new_product = Product.objects.get(name='New Product')
        self.assertEqual(new_product.barcode, '987654321')
        self.assertEqual(new_product.price, 49.99)
        self.assertEqual(new_product.stock, 50)
    
    def test_product_update_post(self):
        """Test updating a product via POST"""
        self.client.login(username='privileged', password='privilegedpass')
        updated_data = {
            'name': 'Updated Product',
            'barcode': self.product.barcode,
            'price': 129.99,
            'stock': 75
        }
        response = self.client.post(
            reverse('product:product_update', kwargs={'pk': self.product.pk}),
            updated_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product')
        self.assertEqual(self.product.price, 129.99)
        self.assertEqual(self.product.stock, 75)
    
    def test_product_delete_post(self):
        """Test deleting a product via POST"""
        self.client.login(username='privileged', password='privilegedpass')
        response = self.client.post(
            reverse('product:product_delete', kwargs={'pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
    
    def test_context_data_includes_permissions(self):
        """Test that the context includes permission flags"""
        self.client.login(username='privileged', password='privilegedpass')
        response = self.client.get(reverse('product:product_list'))
        self.assertTrue(response.context['can_add'])
        self.assertTrue(response.context['can_edit'])
        self.assertTrue(response.context['can_delete'])
        
        # Test with regular user
        self.client.logout()
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('product:product_list'))
        self.assertFalse(response.context['can_add'])
        self.assertFalse(response.context['can_edit'])
        self.assertFalse(response.context['can_delete'])


class ProductModuleIntegrationTest(TestCase):
    """Tests for the integration between Product app and Module system"""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name="Test Product",
            barcode="123456789",
            price=99.99,
            stock=100
        )
        
        # Set up client
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')
    
    def test_product_module_info(self):
        """Test that the product module info is correctly defined"""
        # Import the module_info
        from .module_info import NAME, DESCRIPTION, VERSION
        
        self.assertEqual(NAME, "Product Management")
        self.assertTrue(len(DESCRIPTION) > 0)  # Description should not be empty
        self.assertTrue(VERSION)  # Version should be defined
