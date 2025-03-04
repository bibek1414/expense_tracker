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
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import date   
from django.contrib.auth.forms import UserCreationForm
from .models import Expense, Profile
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
import requests
from urllib.parse import urlencode
from django.conf import settings


def google_login(request):
    """Redirect users to Google's OAuth consent screen."""
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    auth_url = f"{settings.GOOGLE_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)

def google_callback(request):
    """Handle the callback from Google OAuth."""
    code = request.GET.get('code')
    if not code:
        return redirect('login')  # Redirect to login if no code is provided

    # Exchange the authorization code for an access token
    token_data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post(settings.GOOGLE_TOKEN_URL, data=token_data)
    if response.status_code != 200:
        return redirect('login')  # Handle error

    access_token = response.json().get('access_token')

    # Fetch user info using the access token
    user_info_response = requests.get(settings.GOOGLE_USER_INFO_URL, headers={
        'Authorization': f'Bearer {access_token}'
    })
    if user_info_response.status_code != 200:
        return redirect('login')  # Handle error

    user_info = user_info_response.json()
    email = user_info.get('email')
    first_name = user_info.get('given_name', '')
    last_name = user_info.get('family_name', '')

    # Create or get the user
    user, created = User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'first_name': first_name, 'last_name': last_name}
    )

    # Log the user in with the specified backend
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('expenses:dashboard')  # Redirect to your home page

@login_required
def profile_view(request):
    # Calculate financial summary
    income_transactions = Expense.objects.filter(user=request.user, type='income')
    expense_transactions = Expense.objects.filter(user=request.user, type='expense')
    total_income = sum(transaction.amount for transaction in income_transactions)
    total_expenses = sum(transaction.amount for transaction in expense_transactions)
    balance = total_income - total_expenses
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
    }
    
    return render(request, 'expenses/profile.html', context)

@login_required
def profile_update(request):
    if request.method == 'POST':
        # Update User model fields
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Get or create the Profile instance
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Update Profile model fields
        profile.phone = request.POST.get('phone', '')
        profile.bio = request.POST.get('bio', '')
        
        # Handle profile photo upload
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        
        profile.save()
        
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('expenses:profile')
        
    # If not POST, redirect to profile page
    return redirect('expenses:profile')

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
        'balance': balance, 
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
    """View to add a new expense or income"""
    # Calculate balance
    expenses = Expense.objects.filter(user=request.user)
    total_income = expenses.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    if request.method == 'POST':
        # Extract form data
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        date_value = request.POST.get('date')
        description = request.POST.get('description')
        transaction_type = request.POST.get('type')
        
        # Create and save the expense/income
        category = get_object_or_404(Category, id=category_id)
        Expense.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            date=date_value,
            description=description,
            type=transaction_type
        )
        
        # Redirect to dashboard or appropriate page
        return HttpResponseRedirect(reverse('expenses:dashboard'))
    
    # For GET requests, prepare the form
    categories = Category.objects.all()
    categories_json = json.dumps(
        [{'id': category.id, 'name': category.name, 'type': category.type} 
         for category in categories],
        cls=DjangoJSONEncoder
    )
    
    context = {
        'categories': categories,
        'categories_json': categories_json,
        'today': date.today().strftime('%Y-%m-%d'),
        'balance': balance,  
    }
    
    return render(request, 'expenses/add_expense.html', context)

@login_required
def edit_expense(request, expense_id):
    """View to edit an existing expense or income"""
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)

    # Calculate balance
    expenses = Expense.objects.filter(user=request.user)
    total_income = expenses.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expenses.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    if request.method == 'POST':
        # Extract form data
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        date_value = request.POST.get('date')
        description = request.POST.get('description')
        transaction_type = request.POST.get('type')
        
        # Update the expense/income
        expense.title = title
        expense.amount = amount
        expense.category = get_object_or_404(Category, id=category_id)
        expense.date = date_value
        expense.description = description
        expense.type = transaction_type
        expense.save()
        
        # Redirect to dashboard or appropriate page
        return HttpResponseRedirect(reverse('expenses:dashboard'))
    
    # For GET requests, prepare the form with existing data
    categories = Category.objects.all()
    categories_json = json.dumps(
        [{'id': category.id, 'name': category.name, 'type': category.type} 
         for category in categories],
        cls=DjangoJSONEncoder
    )
    
    context = {
        'expense': expense,
        'categories': categories,
        'categories_json': categories_json,
        'balance': balance,  
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

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})