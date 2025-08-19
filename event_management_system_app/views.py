from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Category, Event, EventWishlist, EventAttendance
from django.shortcuts import render, redirect
from django.urls import reverse
from django import forms


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned


from django.contrib.auth.tokens import default_token_generator as account_activation_token


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user: User = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate your account'
            message = render_to_string('registration/activation_email.txt', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email]).send()
            return render(request, 'registration/activation_sent.html')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'registration/activation_complete.html')
    else:
        return render(request, 'registration/activation_invalid.html')


def delete_event(request, event_id):
    if request.method == 'POST':
        event = Event.objects.get(id=event_id)
        event.delete()
    return redirect(reverse('category_list'))


def create_event(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        priority = request.POST.get('priority')
        description = request.POST.get('description')
        location = request.POST.get('location')
        organizer = request.POST.get('organizer')
        latitude = request.POST.get('latitude') or None
        longitude = request.POST.get('longitude') or None

        category = Category.objects.get(pk=category_id)

        Event.objects.create(
            name=name,
            category=category,
            start_date=start_date,
            end_date=end_date,
            priority=priority,
            description=description,
            location=location,
            organizer=organizer,
            latitude=latitude,
            longitude=longitude,
        )
        return redirect('category_list')
    else:
        categories = Category.objects.all()
        return render(request, 'event/create_event.html', {'categories': categories})


def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.method == 'POST':
        # Update event fields based on form data
        event.name = request.POST.get('name')
        event.start_date = request.POST.get('start_date')
        event.end_date = request.POST.get('end_date')
        event.priority = request.POST.get('priority')
        event.description = request.POST.get('description')
        event.location = request.POST.get('location')
        event.organizer = request.POST.get('organizer')
        event.latitude = request.POST.get('latitude') or None
        event.longitude = request.POST.get('longitude') or None
        event.save()
        return redirect('category_list')
    else:
        # Render update event page with event data
        return render(request, 'event/update_event.html', {'event': event})

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'event/category_list.html', {'categories': categories})

def create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        Category.objects.create(name=name)
        return redirect('category_list')
    return render(request, 'event/create_category.html')


def delete_category(request, category_id):
    category = Category.objects.get(pk=category_id)
    if category.event_set.exists(): # type: ignore
        messages.error(
            request, "You cannot delete this category as it contains events.")
    else:
        category.delete()
        messages.success(request, "Category deleted successfully.")
    return redirect('category_list')

def category_events(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    events = category.events.all()
    return render(request, 'event/category_events.html', {'category': category, 'events': events})

def event_chart(request):
    categories = Category.objects.all()
    pending_counts = {}
    for category in categories:
        pending_counts[category.name] = Event.objects.filter(category=category, start_date__gt=timezone.now()).count()
    return render(request, 'event/event_chart.html', {'pending_counts': pending_counts})


def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    is_wishlisted = False
    is_joined = False
    if request.user.is_authenticated:
        is_wishlisted = EventWishlist.objects.filter(user=request.user, event=event).exists()
        is_joined = EventAttendance.objects.filter(user=request.user, event=event).exists()
    return render(request, 'event/event_detail.html', {
        'event': event,
        'is_wishlisted': is_wishlisted,
        'is_joined': is_joined,
        'mapbox_token': settings.MAPBOX_TOKEN,
    })


@login_required
def toggle_wishlist(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    wishlist, created = EventWishlist.objects.get_or_create(user=request.user, event=event)
    if not created:
        wishlist.delete()
    return redirect('event_detail', event_id=event.id)


@login_required
def join_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    attendance, created = EventAttendance.objects.get_or_create(user=request.user, event=event)
    if not created:
        attendance.delete()
    return redirect('event_detail', event_id=event.id)


@login_required
def my_wishlist(request):
    wishlists = EventWishlist.objects.filter(user=request.user).select_related('event')
    return render(request, 'event/my_wishlist.html', {'wishlists': wishlists})