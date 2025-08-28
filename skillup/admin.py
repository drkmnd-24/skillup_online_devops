from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from django.urls import reverse

from .models import User, Task, MarkdownFile, ModifiedMarkdownFile, SubmittedMarkdownFile
from .admin_forms import ModifiedMarkdownFileForm

admin.site.register(User)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'assigned_to', 'status', 'review_status', 'review_actions')
    list_filter = ('status', 'review_status', 'assigned_to')

    def review_actions(self, obj):
        if obj.status == 'done':
            pass_url = reverse('admin:task_mark_pass', args=[obj.id])
            fail_url = reverse('admin:task_mark_fail', args=[obj.id])
            return format_html(
                '<a class="button" href="{}">Pass</a>'
                '<a class="button" href="{}" style="margin-left: 10px;">Fail</a>',
                pass_url, fail_url
            )
        return 'N/A'
    review_actions.short_description = 'Review'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:task_id>/mark_pass/', self.admin_site.admin_view(self.mark_pass), name='task_mark_pass'),
            path('<int:task_id>/mark_fail/', self.admin_site.admin_view(self.mark_fail), name='task_mark_fail'),
        ]
        return custom_urls + urls

    def mark_pass(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        task.review_status = 'passed'
        task.save()
        self.message_user(request, f'Task {task.title} marked as PASSED')
        return redirect('admin:main_app_task_changelist')

    def mark_fail(self, request, task_id):
        task = get_object_or_404(Task, pk=task_id)
        task.review_status = 'failed'
        task.save()
        self.message_user(request, f'Task {task.title} marked as FAILED')
        return redirect('admin:main_app_task_changelist')

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        submitted_file_id = request.GET.get('submitted_file')
        if submitted_file_id:
            initial['submitted_file'] = submitted_file_id
        return initial

@admin.register(MarkdownFile)
class MarkdownFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'upload_at', 'view_content', 'modify_button')
    search_fields = ('title',)
    list_filter = ('upload_at',)
    readonly_fields = ('upload_at',)

    def view_content(self, obj):
        if obj.file:
            with obj.file.open('r') as f:
                content = f.read()
            return format_html('<pre>{}</pre>', content[:500])
        return 'No content available'

    def modify_button(self, obj):
        url = reverse('admin:main_app_modifiedmarkdownfile_add') + f'?original_file={obj.id}'
        return format_html('<a class="button" href="{}">Modify</a>', url)

    view_content.short_description = 'Markdown Preview'
    modify_button.short_description = 'Modify Markdown'

@admin.register(ModifiedMarkdownFile)
class ModifiedMarkdownFileAdmin(admin.ModelAdmin):
    form = ModifiedMarkdownFileForm
    list_display = ('id', 'original_file', 'modified_by', 'modified_at',
                    'view_modified_content', 'submit_button')
    readonly_fields = ('modified_at', 'modified_file')
    search_fields = ('original_file__title', 'modified_by__knox_id')
    list_filter = ('modified_at',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(submittedmarkdownfile__isnull=False)

    def view_modified_content(self, obj):
        if obj.modified_file:
            with obj.modified_file.open('r') as f:
                content = f.read()
            return format_html('<pre>{}</pre>', content[:500])
        return 'No modified content available'

    def submit_button(self, obj):
        url = reverse('admin:main_app_submittedmarkdownfile_add') + f'?modified_file={obj.id}'
        return format_html('<a class="button" href="{}">Submit</a>', url)

    view_modified_content.short_description = 'Modified Content'
    submit_button.short_description = 'Submit'

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        original_file_id = request.GET.get('original_file')
        if original_file_id:
            initial['original_file'] = original_file_id
        if request.user.is_authenticated:
            initial['modified_by'] = request.user.pk
        return initial

@admin.register(SubmittedMarkdownFile)
class SubmitMarkdownFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'modified_file', 'submitted_at', 'view_submitted_content', 'assigned_button')
    search_fields = ('modified_file__original_file__title',)
    list_filter = ('submitted_at',)
    readonly_fields = ('submitted_at',)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        modified_file_id = request.GET.get('original_file')
        if modified_file_id:
            initial['original_file'] = modified_file_id
        if request.user.is_authenticated:
            initial['modified_by'] = request.user.pk
        return initial

    def view_submitted_content(self, obj):
        if obj.modified_file and obj.modified_file.modified_file:
            with obj.modified_file.modified_file.open('r') as f:
                content = f.read()
            return format_html('<pre>{}</pre>', content[:500])
        return 'No final content available'

    def assigned_button(self, obj):
        url = reverse('admin:main_app_task_add') + f'?submitted_file={obj.id}'
        return format_html('<a href="{}">Assign to Student</a>', url)

    view_submitted_content.short_description = 'Submitted Markdown Preview'
    assigned_button.short_description = 'Assign to Student'
