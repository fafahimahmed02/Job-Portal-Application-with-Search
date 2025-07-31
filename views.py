from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Job, Application
from .forms import JobForm, ApplicationForm
from django.contrib.auth.models import User, Group

def home(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Employer').exists():
            return redirect('employer_dashboard')
        elif request.user.groups.filter(name='Applicant').exists():
            return redirect('applicant_dashboard')
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        user = User.objects.create_user(username=username, password=password)
        if role == 'employer':
            user.groups.add(Group.objects.get(name='Employer'))
        else:
            user.groups.add(Group.objects.get(name='Applicant'))
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('home')
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')

@login_required
def employer_dashboard(request):
    if not request.user.groups.filter(name='Employer').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    jobs = Job.objects.filter(posted_by=request.user)
    return render(request, 'employer_dashboard.html', {'jobs': jobs})

@login_required
def applicant_dashboard(request):
    if not request.user.groups.filter(name='Applicant').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    return render(request, 'applicant_dashboard.html')

def job_list(request):
    query = request.GET.get('q', '')
    jobs = Job.objects.all()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        )
    return render(request, 'job_list.html', {'jobs': jobs, 'query': query})

def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'job_detail.html', {'job': job})

@login_required
def job_create(request):
    if not request.user.groups.filter(name='Employer').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            messages.success(request, 'Job posted successfully.')
            return redirect('employer_dashboard')
    else:
        form = JobForm()
    return render(request, 'job_form.html', {'form': form})

@login_required
def apply_job(request, pk):
    if not request.user.groups.filter(name='Applicant').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(request, 'Application submitted successfully.')
            return redirect('applicant_dashboard')
    else:
        form = ApplicationForm()
    return render(request, 'application_form.html', {'form': form, 'job': job})

@login_required
def job_applicants(request, pk):
    if not request.user.groups.filter(name='Employer').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    applications = Application.objects.filter(job=job)
    return render(request, 'applications_list.html', {'job': job, 'applications': applications})

@login_required
def my_applications(request):
    if not request.user.groups.filter(name='Applicant').exists():
        messages.error(request, 'Access denied.')
        return redirect('home')
    applications = Application.objects.filter(applicant=request.user)
    return render(request, 'my_applications.html', {'applications': applications})
