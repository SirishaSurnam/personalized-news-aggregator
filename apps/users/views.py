from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'login.html' [cite: 96]
    redirect_authenticated_user = True [cite: 96]

    def get_success_url(self):
        return reverse_lazy('home') [cite: 96] # Redirect to home after successful login

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home') [cite: 96] # Redirect to home after logout

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST) [cite: 97]
        if form.is_valid():
            user = form.save() [cite: 97]
            username = form.cleaned_data.get('username') [cite: 97]
            messages.success(request, f'Account created for {username}!') [cite: 97]
            login(request, user) [cite: 97] # Log the user in after registration
            return redirect('home') [cite: 97] # Redirect to home page
    else:
        form = UserCreationForm() [cite: 97]

    return render(request, 'register.html', {'form': form}) [cite: 97]