from django.apps import AppConfig


class AnotherExampleAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "another_example_app"

    def ready(self):
        """
        Register this module with the module registry.
        This is called when Django starts.
        """
        from module.registry import registry
