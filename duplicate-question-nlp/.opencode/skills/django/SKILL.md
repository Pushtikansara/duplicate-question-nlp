---
name: django
description: Use when building Python web applications with Django. Covers ORM, views, templates, admin, REST framework, and best practices.
---

# Django Skill

## Overview
Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Built by experienced developers, it takes care of much of the hassle of web development, allowing developers to focus on writing their app without needing to reinvent the wheel.

## Instructions
- Follow the model-view-template (MVT) architecture — models define data, views handle logic, templates handle presentation
- Use Django's ORM for database operations; avoid raw SQL unless necessary for complex queries
- Keep business logic in models and services, not in views
- Use class-based views (CBV) for common patterns; use function-based views (FBV) for custom logic
- Use Django REST Framework (DRF) for building RESTful APIs
- Use Django's built-in admin interface for internal data management
- Write tests for models, views, and forms; Django's test client makes integration testing straightforward
- Use `django-debug-toolbar` during development for query optimization and performance analysis
- Configure settings with environment variables using `python-decouple` or `django-environ`
- Use Django's migrations system for database schema changes; never alter the database manually
- Use caching strategically with Redis or Memcached for performance
- Implement proper authentication with Django's built-in auth system or custom backends

## Core Concepts

### Models and ORM
- Each model is a Python class that subclasses `django.db.models.Model`
- Fields: `CharField`, `IntegerField`, `DateField`, `ForeignKey`, `ManyToManyField`, `OneToOneField`
- Field options: `null`, `blank`, `default`, `unique`, `db_index`, `choices`, `verbose_name`
- Meta class: `ordering`, `verbose_name`, `db_table`, `indexes`, `constraints`
- Manager: default `objects`; custom managers for reusable query logic
- QuerySet: lazy, chainable, cacheable; use `select_related` and `prefetch_related` for optimization
- Aggregation: `annotate()`, `aggregate()`, `Count`, `Sum`, `Avg`, `F()`, `Q()` objects
- Signals: `post_save`, `pre_delete` for decoupled side effects (use sparingly)
- Migrations: `python manage.py makemigrations` and `python manage.py migrate`

### Views
- Function-based views: take request, return response (HttpResponse, render, redirect)
- Class-based views: `ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`, `FormView`
- Mixins: `LoginRequiredMixin`, `PermissionRequiredMixin`, `UserPassesTestMixin`
- View decorators: `@login_required`, `@permission_required`, `@require_http_methods`
- `TemplateView` for static pages
- `RedirectView` for redirect logic

### Templates
- Django Template Language (DTL): `{{ variable }}`, `{% tag %}`, `{{ value|filter }}`
- Template inheritance: `{% extends "base.html" %}`, `{% block content %}` / `{% endblock %}`
- Built-in filters: `date`, `default`, `length`, `pluralize`, `linebreaks`, `safe`
- Custom template tags and filters: `templatetags/` directory in app
- `{% static %}` for static files, `{% url %}` for URL reversing
- Context processors for injecting common data into all templates
- Avoid complex logic in templates — keep them presentation-only

### Admin Interface
- Register models with `admin.site.register(Model)` or `@admin.register(Model)`
- Customize with `ModelAdmin`: `list_display`, `list_filter`, `search_fields`, `ordering`, `readonly_fields`
- `InlineModelAdmin` for editing related models on the same page
- `actions` for bulk operations
- Custom admin views for complex administration tasks
- Override admin templates for custom styling

### Forms
- `ModelForm` auto-generates forms from models
- `Form` for custom forms not tied to a model
- Field validation: `clean_<fieldname>()`, `clean()`, custom validators
- Widgets: customize HTML rendering of form fields
- Form rendering: `{{ form }}`, `{{ form.as_p }}`, `{{ form.as_table }}`, `{{ form.as_ul }}`
- CSRF protection: `{% csrf_token %}` in all POST forms
- File uploads: `request.FILES` with `enctype="multipart/form-data"`

### Django REST Framework
- `ModelViewSet` for full CRUD on a model
- Serializers: `ModelSerializer` for model serialization; custom serializers for complex logic
- Permissions: `IsAuthenticated`, `IsAdminUser`, `DjangoModelPermissions`, custom permission classes
- Authentication: `TokenAuthentication`, `SessionAuthentication`, `JWTAuthentication` (via `djangorestframework-simplejwt`)
- Pagination: `PageNumberPagination`, `LimitOffsetPagination`, `CursorPagination`
- Filtering: `django-filter` integration for complex query building
- Versioning: URL namespace versioning or Accept header versioning
- Throttling: rate limiting per user or IP

## Examples

### Model Definition
```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('Tag', related_name='posts')

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'published_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('post_detail', args=[self.slug])
```

### Class-Based View with Mixins
```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Post
from .forms import PostForm

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            status=Post.Status.PUBLISHED
        ).select_related('author').prefetch_related('tags')

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    slug_url_kwarg = 'slug'

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'
    success_url = reverse_lazy('post_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/post_form.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
```

### DRF ViewSets
```python
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Comment
from .serializers import PostSerializer, PostDetailSerializer, CommentSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(status='published')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'tags__name']
    search_fields = ['title', 'content']
    ordering_fields = ['published_at', 'title']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user and not request.user.is_staff:
            return Response({'error': 'Not allowed'}, status=403)
        post.status = 'published'
        post.save()
        return Response({'status': 'published'})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = post.comments.filter(is_approved=True)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
```

### Management Command
```python
# management/commands/publish_scheduled.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from blog.models import Post

class Command(BaseCommand):
    help = 'Publish posts that are scheduled'

    def handle(self, *args, **options):
        now = timezone.now()
        posts = Post.objects.filter(
            status='draft',
            published_at__lte=now,
        )
        count = posts.update(status='published')
        self.stdout.write(self.style.SUCCESS(f'Published {count} posts'))
```

## Best Practices
- Use `select_related()` for ForeignKey relationships and `prefetch_related()` for ManyToMany to prevent N+1 queries
- Keep views thin — move business logic to model methods or service classes
- Use `@transaction.atomic` for operations that need database consistency
- Use `F()` expressions for atomic updates and avoiding race conditions
- Use `Q()` objects for complex query lookups (OR conditions, negations)
- Use `get_object_or_404()` and `get_list_or_404()` for safety
- Override `save()` and `delete()` for model-level business rules
- Use `signals` sparingly — they can make data flow hard to trace
- Always run `makemigrations` and `migrate` after model changes
- Use `python manage.py check --deploy` to verify production readiness

## Common Mistakes
- N+1 query problem: fetching related objects without `select_related`/`prefetch_related`
- Using `ForeignKey` without `on_delete` parameter (required as of Django 2.0)
- Storing files/media without proper configuration for production (using default file storage)
- Exposing sensitive data via the admin interface (use `list_display` carefully)
- Not using database indexes on frequently queried fields (performance issues)
- Putting business logic in views instead of models or services
- Using `filter()` in a loop instead of a single query with `__in` lookup
- Not using `SECRET_KEY` from environment variable in production
- Leaving `DEBUG=True` in production (security + performance issue)
- Using `GenericForeignKey` or `GenericRelation` without careful consideration
- Running heavy tasks synchronously in views (use Celery instead)

## Libraries
- **djangorestframework** — RESTful API framework
- **django-cors-headers** — CORS headers for API
- **django-filter** — advanced filtering for DRF
- **django-debug-toolbar** — development debugging panel
- **django-environ** — environment variable management
- **django-allauth** — authentication with social providers
- **django-celery-beat** — periodic tasks with Celery
- **django-cacheops** — automatic caching for querysets
- **django-storages** — file storage backends (S3, GCS, Azure)
- **django-extensions** — management commands (shell_plus, runserver_plus, graph_models)
- **django-haystack** — full-text search with Elasticsearch
- **django-import-export** — import/export data via admin
- **pytest-django** — pytest integration for Django testing
- **sentry-sdk** — error monitoring

## Design Principles
- **Batteries Included**: Django comes with ORM, admin, auth, forms, templates, sessions, and more
- **DRY (Don't Repeat Yourself)**: Define models in one place; migrations, forms, and admin derive from them
- **Model-View-Template (MVT)**: Clear separation between data, logic, and presentation
- **Reusable Apps**: Django projects are composed of pluggable apps
- **Explicit is Better than Implicit**: Django's configuration is explicit — settings, URLs, and INSTALLED_APPS
- **Security by Default**: CSRF protection, XSS escaping, SQL injection prevention, clickjacking protection

## Coding Standards
- Follow Django's coding style (PEP 8 + Django conventions)
- App naming: plural lowercase (`blog`, `users`, `comments`)
- Class names: PascalCase for models, views, forms (`Post`, `PostListView`, `PostForm`)
- URL namespacing: `app_name:view_name`
- Template directory: `app_name/templates/app_name/template.html`
- Static files: `app_name/static/app_name/`
- Use `get_user_model()` instead of direct `User` import for custom user models
- Use `reverse()` and `reverse_lazy()` instead of hardcoding URLs
- Use `settings.py` per environment: `base.py`, `development.py`, `production.py`
- Define `__str__` on all models for readable admin representation
- Use `Meta` class for model metadata, permissions, and ordering
- Keep migrations in version control; never delete or squash shared migrations without coordination

## Security
- Always use CSRF protection on forms (`{% csrf_token %}`)
- Use `@login_required` or `LoginRequiredMixin` for authenticated views
- Use `@permission_required` for permission checks
- Sanitize user input — Django's ORM prevents SQL injection; form validation handles XSS
- Set `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` in production
- Use `SecurityMiddleware` (included by default) for security headers
- Set `ALLOWED_HOSTS` to prevent HTTP Host header attacks
- Use `django-axes` or `django-ratelimit` for brute-force protection on login
- Use `X-Content-Type-Options: nosniff` via security middleware
- Rotate `SECRET_KEY` periodically; never commit it to version control
- Use password validators: `AUTH_PASSWORD_VALIDATORS`
- Use `hashers` configuration for password hashing (Argon2 recommended)

## Performance
- Use `select_related` and `prefetch_related` for related object queries
- Add database indexes for frequently queried fields
- Use `QuerySet.only()` or `QuerySet.defer()` to load only needed fields
- Use `QuerySet.values()` or `values_list()` for data-only queries (no model instantiation)
- Cache expensive queries with `django.core.cache` (Redis backend)
- Use `{% cache %}` template tag for caching template fragments
- Use `django-compressor` for minifying CSS/JS assets
- Configure database connection pooling (pgBouncer for PostgreSQL)
- Use CDN for static and media files
- Implement database read replicas for read-heavy workloads
- Use `atomic()` for transactional operations; avoid long-running transactions
- Profile database queries with `django-debug-toolbar` or `py-spy`
- Use connection pooling with Django's `CONN_MAX_AGE` setting
- Use `iterator()` for large querysets to reduce memory usage
