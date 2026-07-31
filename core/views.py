from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from . import data
from .forms import ContactForm
from .models import Project


def home(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            send_mail(
                subject=f"Portfolio contact: {contact_message.subject}",
                message=(
                    f"From: {contact_message.name} <{contact_message.email}>\n\n"
                    f"{contact_message.message}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_RECIPIENT_EMAIL],
                fail_silently=True,
            )
            messages.success(request, "Thanks for reaching out! I'll get back to you soon.")
            return redirect("/#contact")
        messages.error(request, "Please fix the errors below and try again.")
    else:
        form = ContactForm()

    projects = Project.objects.filter(is_featured=True).prefetch_related("features")
    gsms = projects.filter(slug="gsms").first()
    other_projects = projects.exclude(slug="gsms")

    context = {
        "gsms": gsms,
        "other_projects": other_projects,
        "skill_categories": data.SKILL_CATEGORIES,
        "quick_facts": data.QUICK_FACTS,
        "experience": data.EXPERIENCE,
        "education": data.EDUCATION,
        "social": data.SOCIAL_LINKS,
        "github_username": data.GITHUB_USERNAME,
        "hero_photo_url": data.HERO_PHOTO_URL,
        "featured_repos": data.FEATURED_REPOS,
        "form": form,
    }
    return render(request, "core/home.html", context)


def project_detail(request, slug):
    project = get_object_or_404(
        Project.objects.prefetch_related("features", "challenges", "screenshots"),
        slug=slug,
    )
    return render(request, "core/project_detail.html", {"project": project, "social": data.SOCIAL_LINKS})
