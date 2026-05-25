from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CustomUser, Profile
from .forms import ProfileUpdateForm

class CustomLoginView(LoginView):
    template_name = "registration/login.html"

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("login")

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"



class ProfileDetailView(DetailView):
    model = CustomUser
    template_name = "users/profile.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        if user.profile.is_public or (self.request.user.is_authenticated and self.request.user == user):
            from apps.lists.models import WatchItem
            from django.db.models import Avg
            qs = WatchItem.objects.filter(user=user).select_related('contnt_item').order_by('-updated_at')
            context['watch_items'] = qs
            context['watched_count'] = qs.filter(status='completed').count()
            context['plan_count'] = qs.filter(status='plan_to_watch').count()
            avg = qs.filter(rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
            context['avg_rating'] = round(avg, 1) if avg else None
        else:
            context['watch_items'] = None
            context['is_private'] = True
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = "users/profile_edit.html"

    def get_object(self):
        return self.request.user.profile

    def get_success_url(self):
        return reverse_lazy('profile', kwargs={'username': self.request.user.username})
