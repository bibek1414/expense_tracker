# models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#3B82F6')
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='expense')
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Expense(models.Model):
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default='expense')

    def __str__(self):
        return self.title
    
    def abs(self):
        """Return absolute value of amount for display purposes"""
        return abs(self.amount)