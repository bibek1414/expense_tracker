# Generated by Django 5.1.6 on 2025-03-02 15:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0003_alter_category_options_alter_expense_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={},
        ),
        migrations.AlterModelOptions(
            name='expense',
            options={},
        ),
        migrations.RemoveField(
            model_name='expense',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='expense',
            name='updated_at',
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='expense',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='expenses.category'),
        ),
        migrations.AlterField(
            model_name='expense',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='expense',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='expense',
            name='title',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='expense',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
