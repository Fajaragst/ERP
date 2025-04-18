"""
Models for the product app
"""
from django.db import models

class Product(models.Model):
    """
    Model for the product app
    """
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=200, unique=True)
    price = models.FloatField()
    stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
