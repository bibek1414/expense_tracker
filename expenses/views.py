from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Expense, Category
import json
from datetime import timedelta
from collections import defaultdict
from decimal import Decimal

@login_required
def transactions(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    
    # Calculate balance
    total_income = expenses.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    paginator = Paginator(expenses, 10)  # Show 10 expenses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    is_paginated = paginator.num_pages > 1

    context = {
        'expenses': page_obj,
        'is_paginated': is_paginated,
        'page_obj': page_obj,
        'balance': balance,  # Pass balance to the template
    }
    return render(request, 'expenses/transactions.html', context)
@login_required
def dashboard(request):
    period = request.GET.get('period', 'monthly')
    date_str = request.GET.get('date')
    
    if date_str:
        try:
            current_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()
    
    # Calculate date ranges based on period
    if (period == 'daily'):
        start_date = current_date
        end_date = current_date
        prev_start_date = start_date - timedelta(days=1)
        prev_end_date = prev_start_date
        next_date = start_date + timedelta(days=1)
        prev_date = start_date - timedelta(days=1)
    elif (period == 'weekly'):
        start_date = current_date - timedelta(days=current_date.weekday())
        end_date = start_date + timedelta(days=6)
        prev_start_date = start_date - timedelta(days=7)
        prev_end_date = prev_start_date + timedelta(days=6)
        next_date = end_date + timedelta(days=1)
        prev_date = start_date - timedelta(days=1)
    elif (period == 'monthly'):
        start_date = current_date.replace(day=1)
        # Last day of current month
        if (start_date.month == 12):
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
        # Previous month
        if (start_date.month == 1):
            prev_start_date = start_date.replace(year=start_date.year - 1, month=12, day=1)
        else:
            prev_start_date = start_date.replace(month=start_date.month - 1, day=1)
        # Last day of previous month
        prev_end_date = start_date - timedelta(days=1)
        next_date = end_date + timedelta(days=1)
        prev_date = start_date - timedelta(days=1)
    elif (period == 'yearly'):
        start_date = current_date.replace(month=1, day=1)
        end_date = current_date.replace(month=12, day=31)
        prev_start_date = start_date.replace(year=start_date.year - 1)
        prev_end_date = end_date.replace(year=end_date.year - 1)
        next_date = start_date.replace(year=start_date.year + 1)
        prev_date = start_date.replace(year=start_date.year - 1)
    else:  # all time
        start_date = None
        end_date = None
        prev_start_date = None
        prev_end_date = None
        next_date = None
        prev_date = None
    
    # Get expenses and income for current period
    transactions = Expense.objects.filter(user=request.user)
    if (start_date and end_date):
        transactions = transactions.filter(date__range=(start_date, end_date))
    
    # Separate income and expenses
    expenses = transactions.filter(type='expense')
    income = transactions.filter(type='income')
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = income.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate balance
    balance = total_income - total_expenses  # Expenses are negative, so this works
    
    # Calculate totals for current period
    total_amount = total_expenses + total_income
    transaction_count = transactions.count()
    
    # Calculate daily average
    if (start_date and end_date):
        days_in_period = (end_date - start_date).days + 1
        daily_average = float(total_amount) / days_in_period if (days_in_period > 0) else 0
    else:
        daily_average = 0
    
    # Get previous period data for comparison
    prev_transactions = Expense.objects.filter(user=request.user)
    if (prev_start_date and prev_end_date):
        prev_transactions = prev_transactions.filter(date__range=(prev_start_date, prev_end_date))
    
    prev_expenses = prev_transactions.filter(type='expense')
    prev_income = prev_transactions.filter(type='income')
    
    prev_total_expenses = prev_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    prev_total_income = prev_income.aggregate(Sum('amount'))['amount__sum'] or 0
    prev_total = prev_total_expenses + prev_total_income
    
    # Calculate percent change
    if (prev_total > 0):
        percent_change = ((float(total_amount) - float(prev_total)) / float(prev_total)) * 100
    else:
        percent_change = 0
    
    # Get expenses by category
    category_data = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calculate top category
    top_category = None
    if (category_data):
        top_category_id = category_data[0]['category']
        top_category = Category.objects.get(id=top_category_id)
        top_category.total = float(category_data[0]['total'])
        top_category.percentage = (top_category.total / float(total_expenses)) * 100 if (total_expenses > 0) else 0
    
    # Prepare data for charts
    category_chart_data = []
    for cat in category_data:
        category = Category.objects.get(id=cat['category'])
        percentage = (float(cat['total']) / float(total_expenses)) * 100 if (total_expenses > 0) else 0
        category_chart_data.append({
            'name': category.name,
            'value': float(cat['total']),  # Convert Decimal to float
            'percentage': percentage,
            'color': category.color
        })
    
    # Prepare data for line chart (daily expenses)
    line_chart_data = []
    if (start_date and end_date):
        date_range = (end_date - start_date).days + 1
        
        # Create date range dictionary
        date_expenses = defaultdict(float)
        
        # Group expenses by date
        for expense in expenses:
            date_key = expense.date.strftime('%Y-%m-%d')
            date_expenses[date_key] += float(expense.amount)  # Convert Decimal to float
        
        # Fill in the chart data
        current = start_date
        for _ in range(date_range):
            date_key = current.strftime('%Y-%m-%d')
            date_label = current.strftime('%b %d')
            
            line_chart_data.append({
                'date': date_label,
                'amount': float(date_expenses.get(date_key, 0))  # Convert Decimal to float
            })
            
            current += timedelta(days=1)
    
    # Pagination for transactions
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Determine if pagination is needed
    is_paginated = len(transactions) > 10
    
    # Convert data to JSON for JavaScript
    category_chart_json = json.dumps(category_chart_data)
    line_chart_json = json.dumps(line_chart_data)
    
    context = {
        'period': period,
        'current_date': current_date,
        'start_date': start_date,
        'end_date': end_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'today': timezone.now().date(),
        'transactions': page_obj if is_paginated else transactions,
        'is_paginated': is_paginated,
        'page_obj': page_obj if is_paginated else None,
        'paginator': paginator if is_paginated else None,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'total_amount': total_amount,
        'transaction_count': transaction_count,
        'daily_average': daily_average,
        'percent_change': percent_change,
        'top_category': top_category,
        'category_chart_data': category_chart_json,
        'line_chart_data': line_chart_json,
    }
    
    return render(request, 'expenses/dashboard.html', context)
@login_required
def add_expense(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        type = request.POST.get('type')

        if not all([title, amount, date, category_id, type]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('expenses:add_expense')

        try:
            amount = Decimal(amount)
            if type == 'expense':
                amount = -amount  # Subtract for expenses
            category = get_object_or_404(Category, id=category_id)
            Expense.objects.create(
                user=request.user,
                title=title,
                amount=amount,
                date=date,
                category=category,
                description=description,
                type=type
            )
            messages.success(request, 'Transaction added successfully!')
            return redirect('expenses:dashboard')
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
            return redirect('expenses:add_expense')

    categories = Category.objects.all()
    today = timezone.now().date().strftime('%Y-%m-%d')
    context = {
        'categories': categories,
        'today': today
    }
    return render(request, 'expenses/add_expense.html', context)

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        category_id = request.POST.get('category')
        description = request.POST.get('description', '')
        
        # Validate required fields
        if not all([title, amount, date, category_id]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('expenses:edit_expense', expense_id=expense_id)
        
        try:
            # Convert amount to Decimal
            amount = Decimal(amount)
            
            # Get category
            category = get_object_or_404(Category, id=category_id)
            
            # Update expense
            expense.title = title
            expense.amount = amount
            expense.date = date
            expense.category = category
            expense.description = description
            expense.save()
            
            messages.success(request, 'Expense updated successfully!')
            return redirect('expenses:dashboard')
            
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid amount.')
            return redirect('expenses:edit_expense', expense_id=expense_id)
    
    # GET request
    categories = Category.objects.all()
    
    context = {
        'expense': expense,
        'categories': categories
    }
    
    return render(request, 'expenses/edit_expense.html', context)

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
    
    return redirect('expenses:dashboard')

@login_required
def expense_categories(request):
    categories = Category.objects.all()
    
    context = {
        'categories': categories
    }
    
    return render(request, 'expenses/categories.html', context)

@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color', '#3B82F6')  # Default to blue if no color is provided
        
        if not name:
            messages.error(request, 'Please provide a category name.')
            return redirect('expenses:add_category')
        
        Category.objects.create(name=name, color=color)
        messages.success(request, 'Category added successfully!')
        return redirect('expenses:expense_categories')
    
    return render(request, 'expenses/add_category.html')

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        
        if not name:
            messages.error(request, 'Please provide a category name.')
            return redirect('expenses:edit_category', category_id=category_id)
        
        category.name = name
        if color:
            category.color = color
        category.save()
        
        messages.success(request, 'Category updated successfully!')
        return redirect('expenses:expense_categories')
    
    context = {
        'category': category
    }
    
    return render(request, 'expenses/edit_category.html', context)

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    # Check if the category is used by any expenses
    if Expense.objects.filter(category=category).exists():
        messages.error(request, 'Cannot delete category as it is used by one or more expenses.')
        return redirect('expenses:expense_categories')
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
    
    return redirect('expenses:expense_categories')

