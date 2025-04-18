from django.db import models

# Create your models here.
class Module(models.Model):
    """
    Model for the module app
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=20)
    is_installed = models.BooleanField(default=False)
    installed_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    app_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.name} v{self.version} ({'Installed' if self.is_installed else 'Not installed'})"