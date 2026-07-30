from django.contrib import admin

from .models import (
    ContactMessage,
    Project,
    ProjectChallenge,
    ProjectFeature,
    ProjectScreenshot,
)


class ProjectFeatureInline(admin.TabularInline):
    model = ProjectFeature
    extra = 1


class ProjectChallengeInline(admin.TabularInline):
    model = ProjectChallenge
    extra = 1


class ProjectScreenshotInline(admin.TabularInline):
    model = ProjectScreenshot
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "badge", "is_featured", "order", "has_case_study")
    list_editable = ("order", "is_featured")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProjectFeatureInline, ProjectChallengeInline, ProjectScreenshotInline]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at")
    readonly_fields = ("name", "email", "subject", "message", "created_at")

    def has_add_permission(self, request):
        return False
