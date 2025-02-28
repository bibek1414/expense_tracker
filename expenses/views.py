from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Expense
from django.db.models import Sum
from datetime import datetime

@login_required
def expense_list(request):
    if request.user.is_authenticated:
        expenses = Expense.objects.filter(user=request.user).order_by('-date')
    else:
        expenses = Expense.objects.all().order_by('-date')
    
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    context = {
        'expenses': expenses,
        'total': total
    }
    return render(request, 'expenses/expense_list.html', context)
@login_required
def add_expense(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to add expenses.')
        return redirect('login')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        date = request.POST.get('date')
        description = request.POST.get('description')

        Expense.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            date=date,
            description=description
        )
        messages.success(request, 'Expense added successfully!')
        return redirect('expenses:expense_list')
    
    return render(request, 'expenses/add_expense.html')
@login_required
def edit_expense(request, pk):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to edit expenses.')
        return redirect('login')
        
    expense = get_object_or_404(Expense, pk=pk)
    if expense.user != request.user:
        messages.error(request, 'You cannot edit this expense.')
        return redirect('expenses:expense_list')
    
    if request.method == 'POST':
        expense.title = request.POST.get('title')
        expense.amount = request.POST.get('amount')
        expense.category = request.POST.get('category')
        expense.date = request.POST.get('date')
        expense.description = request.POST.get('description')
        expense.save()
        
        messages.success(request, 'Expense updated successfully!')
        return redirect('expenses:expense_list')
    
    context = {'expense': expense}
    return render(request, 'expenses/edit_expense.html', context)
@login_required
def delete_expense(request, pk):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to delete expenses.')
        return redirect('login')
        
    expense = get_object_or_404(Expense, pk=pk)
    if expense.user != request.user:
        messages.error(request, 'You cannot delete this expense.')
        return redirect('expenses:expense_list')
        
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expenses:expense_list')
    
    context = {'expense': expense}
    return render(request, 'expenses/delete_expense.html', context)