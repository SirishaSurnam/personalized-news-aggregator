from django.shortcuts import render, redirect
# authenticate is not used here but often is with custom login logic
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    """
    Custom login view.
    - Sets the template to 'login.html'.
    - Redirects authenticated users if they try to access the login page.
    - Redirects to 'home' upon successful login.
    """
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        # It's good practice to add a success message upon login
        messages.success(self.request, "You have been successfully logged in.")
        return reverse_lazy('home')  # Redirect to home after successful login

    def form_invalid(self, form):
        # Add an error message if login fails
        messages.error(
            self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """
    Custom logout view.
    - Redirects to 'home' after logout.
    """
    # For LogoutView, next_page can be set directly as an attribute
    # or by overriding get_next_page() if more complex logic is needed.
    next_page = reverse_lazy('home')  # Redirect to home after logout

    def dispatch(self, request, *args, **kwargs):
        # Add a success message upon logout
        # dispatch is a good place if you want the message regardless of GET/POST
        # or you can override get_next_page or post
        response = super().dispatch(request, *args, **kwargs)
        # Check if the user was actually logged out before showing the message
        if not request.user.is_authenticated:
            messages.success(request, "You have been successfully logged out.")
        return response


def register(request):
    """
    Handles user registration.
    - If POST request, validates the UserCreationForm.
    - If valid, saves the user, logs them in, shows a success message, and redirects to 'home'.
    - If GET request or form is invalid, displays the registration form.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request, f'Account created for {username}! You are now logged in.')
            # Log the user in automatically after registration
            login(request, user)
            return redirect('home')  # Redirect to home page
        else:
            # Display form errors to the user
            for field in form.errors:
                for error in form.errors[field]:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(
                            request, f"{form.fields[field].label}: {error}")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})
