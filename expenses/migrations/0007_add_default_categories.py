# Generated by Django 5.1.6 on 2025-03-03 13:12
from django.db import migrations

def add_default_categories(apps, schema_editor):
    Category = apps.get_model('expenses', 'Category')
    # Income categories
    income_categories = [
        {'name': 'Salary', 'color': '#4CAF50', 'type': 'income'},
        {'name': 'Interest', 'color': '#8BC34A', 'type': 'income'},
        {'name': 'Business', 'color': '#009688', 'type': 'income'},
        {'name': 'Extra Income', 'color': '#00BCD4', 'type': 'income'}
    ]
    # Expense categories
    expense_categories = [
        {'name': 'Food', 'color': '#F44336', 'type': 'expense'},
        {'name': 'Entertainment', 'color': '#E91E63', 'type': 'expense'},
        {'name': 'Housing', 'color': '#9C27B0', 'type': 'expense'},
        {'name': 'Transportation', 'color': '#673AB7', 'type': 'expense'},
        {'name': 'Utilities', 'color': '#3F51B5', 'type': 'expense'},
        {'name': 'Healthcare', 'color': '#2196F3', 'type': 'expense'},
        {'name': 'Shopping', 'color': '#FF9800', 'type': 'expense'},
        {'name': 'Other', 'color': '#795548', 'type': 'expense'}
    ]
    # Create all categories
    for category_data in income_categories + expense_categories:
        Category.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'color': category_data['color'],
                'type': category_data['type']
            }
        )

def remove_default_categories(apps, schema_editor):
    # This is optional - only if you want to reverse the migration
    Category = apps.get_model('expenses', 'Category')
    income_names = ['Salary', 'Interest', 'Business', 'Extra Income']
    expense_names = ['Food', 'Entertainment', 'Housing', 'Transportation', 'Utilities', 'Healthcare', 'Shopping', 'Other']
    Category.objects.filter(name__in=income_names + expense_names).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('expenses', '0006_category_type'),
    ]
    operations = [
        migrations.RunPython(add_default_categories, remove_default_categories),
    ]