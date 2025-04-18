from django.apps import AppConfig


class ProductConfig(AppConfig):
    """
    Config for the product app
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "product"

    def ready(self):
        """
        Register this module with the module registry.
        This is called when Django starts.
        """
        from module.registry import registry
        # The registry will automatically discover and register this module
