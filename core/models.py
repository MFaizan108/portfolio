from django.db import models


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    badge = models.CharField(max_length=50, blank=True, help_text='e.g. "Featured Project"')
    short_description = models.TextField()
    tech_stack = models.CharField(max_length=300, help_text="Comma-separated, e.g. Python, Django, PostgreSQL")
    thumbnail = models.ImageField(upload_to="projects/thumbnails/", blank=True, null=True)
    github_url = models.URLField(blank=True)
    live_demo_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    # Case-study fields — only populated for in-depth project pages (e.g. GSMS)
    problem = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    architecture_text = models.CharField(max_length=300, blank=True, help_text="e.g. Frontend -> REST API -> Django Backend -> PostgreSQL")
    result = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    @property
    def tech_list(self):
        return [t.strip() for t in self.tech_stack.split(",") if t.strip()]

    @property
    def has_case_study(self):
        return bool(self.problem or self.solution)


class ProjectFeature(models.Model):
    project = models.ForeignKey(Project, related_name="features", on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class ProjectChallenge(models.Model):
    project = models.ForeignKey(Project, related_name="challenges", on_delete=models.CASCADE)
    challenge = models.CharField(max_length=300)
    solution = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.challenge


class ProjectScreenshot(models.Model):
    project = models.ForeignKey(Project, related_name="screenshots", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="projects/screenshots/")
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.caption or f"Screenshot #{self.pk}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.name}"
