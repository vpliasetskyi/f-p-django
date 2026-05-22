from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm

class CustomLoginView(LoginView):
    template_name = "registration/login.html"

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
