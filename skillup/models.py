import os
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, knox_id, email=None, password=None, department=None, lab_part=None, project=None, **extra_fields):
        if not knox_id:
            raise ValueError('Knox ID must be set')
        email = self.normalize_email(email) if email else None
        extra_fields.setdefault('is_active', True)

        user = self.model(
            knox_id=knox_id,
            email=email,
            department=department,
            lab_part=lab_part,
            project=project,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, knox_id, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(knox_id, email, password, **extra_fields)

class User(AbstractUser):
    knox_id = models.CharField(max_length=50, unique=True)
    username = None

    DEPARTMENT_CHOICES = [
        ('COT', 'COT'),
        ('CST', 'CST'),
        ('CIT', 'CIT'),
        ('NWT', 'NWT'),
    ]

    LAB_PART_CHOICES = [
        ('CO1', 'CO1'),
        ('CO2', 'CO2'),
        ('CO3', 'CO3'),
        ('CO4', 'CO4'),
        ('CML', 'CML'),
    ]

    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    lab_part = models.CharField(max_length=10, choices=LAB_PART_CHOICES, blank=True, null=True)
    project = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'knox_id'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return f'{self.knox_id} - {self.email}'

class MarkdownFile(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='admin_md_files/')
    upload_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ModifiedMarkdownFile(models.Model):
    original_file = models.ForeignKey(MarkdownFile, on_delete=models.CASCADE, related_name='modifications')
    modified_file = models.FileField(upload_to='modified_md_files/', blank=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Modified: {self.original_file} by {self.modified_by.knox_id}'

class SubmittedMarkdownFile(models.Model):
    modified_file = models.OneToOneField(ModifiedMarkdownFile, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Submitted: {self.modified_file.original_file.title}'

class Task(models.Model):
    STATUS_CHOICE = [
        ('assigned', 'Assigned'),
        ('ongoing', 'Ongoing'),
        ('submitted', 'Submitted'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    REVIEW_STATUS_CHOICE = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='assigned')
    submitted_file = models.ForeignKey(
        'SubmittedMarkdownFile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    time_limit_minutes = models.PositiveBigIntegerField(
        default=30,
        help_text='How many minutes the student has to complete this task'
    )

    review_status = models.CharField(
        max_length=10,
        choices=REVIEW_STATUS_CHOICE,
        default='pending',
        help_text='Admin review of the completed task'
    )

    # tracking
    started_at = models.DateTimeField(blank=True, null=True)
    time_taken = models.PositiveIntegerField(blank=True, null=True, help_text="Seconds taken to submit")

    def __str__(self):
        return self.title or 'Untitled Task'

    def get_markdown_content(self):
        if self.submitted_file and self.submitted_file.modified_file:
            final_md = self.submitted_file.modified_file.modified_file
            if final_md:
                with final_md.open('rb') as f:
                    content = f.read()
                return content.decode('utf-8') if isinstance(content, bytes) else content
        return ""

    def start_task(self):
        from django.utils import timezone
        if self.status in ('assigned', 'submitted'):
            self.status = 'ongoing'
            if not self.started_at:
                self.started_at = timezone.now()
            self.save()

    def complete_task(self):
        if self.status in ('ongoing', 'submitted'):
            self.status = 'done'
            self.save()
