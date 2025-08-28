import markdown  # type: ignore

from django.contrib.auth import get_user_model, login, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest

from rest_framework.permissions import BasePermission, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView

from rest_framework import permissions, viewsets, status

from .models import Task, MarkdownFile, ModifiedMarkdownFile, SubmittedMarkdownFile
from .serializers import (
    TaskSerializer, UserRegistrationSerializer,
    MarkdownFileSerializer, ModifiedMarkdownFileSerializer, SubmittedMarkdownFileSerializer
)

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class HybridLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        knox_id = request.data.get('knox_id')
        password = request.data.get('password')
        if not knox_id or not password:
            return Response({'detail': 'knox_id and password required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, knox_id=knox_id, password=password)
        if user is None:
            return Response({'detail': 'Invalid Knox ID or Password'}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # simple session auth response
        return Response({'detail': 'Hybrid login successful'}, status=status.HTTP_200_OK)

def login_view(request):
    return render(request, "login.html")

def register_view(request):
    return render(request, "register.html")

def index_view(request):
    return render(request, "index.html")

@login_required
def task_view(request, task_id):
    return render(request, "tasks.html", {"task_id": task_id})

@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, id=pk, assigned_to=request.user)
    is_review = request.GET.get('review') == 'true'
    raw_markdown = task.get_markdown_content() or ""
    render_md = markdown.markdown(raw_markdown)
    if is_review and task.status != 'done':
        return HttpResponseBadRequest("Cannot review a task that isn't done")
    return render(request, 'task_detail.html', {
        'task': task,
        'task_markdown': raw_markdown,
        'render_markdown': render_md,
        'time_limit': task.time_limit_minutes,
        'is_review': is_review
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    return Response({
        'knox_id': user.knox_id,
        'email': user.email,
        'department': user.department,
        'lab_part': user.lab_part,
        'project': user.project
    }, status=status.HTTP_200_OK)

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user.is_staff

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'Error': 'only Admins can assign tasks'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        task = self.get_object()
        if request.user != task.assigned_to:
            return Response({'Error': 'You can only start your own assigned tasks'}, status=status.HTTP_403_FORBIDDEN)
        task.start_task()
        return Response({'message': 'Task started', 'status': task.status}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        task = self.get_object()
        if request.user != task.assigned_to:
            return Response({'Error': 'You can only submit your own assigned tasks'}, status=status.HTTP_403_FORBIDDEN)
        try:
            time_taken = int(request.data.get('time_taken', 0))
        except ValueError:
            return Response({'Error': 'Invalid time_taken value'}, status=status.HTTP_400_BAD_REQUEST)
        task.status = 'submitted'
        task.time_taken = time_taken
        task.save()
        return Response({'message': 'Task Submitted', 'status': task.status, 'time_taken': task.time_taken}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        if request.user != task.assigned_to:
            return Response({'Error': 'you can only complete your own assigned tasks'}, status=status.HTTP_403_FORBIDDEN)
        if task.status not in ('ongoing', 'submitted'):
            return Response({'Error': 'you can only complete tasks that are in progress or submitted'}, status=status.HTTP_403_FORBIDDEN)
        task.complete_task()
        return Response({'message': 'Task marked as done', 'status': task.status}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def fail(self, request, pk=None):
        task = self.get_object()
        if request.user != task.assigned_to:
            return Response({'Error': 'you can only fail your own assigned tasks'}, status=status.HTTP_403_FORBIDDEN)
        task.status = 'failed'
        task.save()
        return Response({'message': 'Task marked as failed', 'status': task.status}, status=status.HTTP_200_OK)

class MarkdownFileViewSet(viewsets.ModelViewSet):
    queryset = MarkdownFile.objects.all()
    serializer_class = MarkdownFileSerializer
    permission_classes = [IsAdminUser]

class ModifiedMarkdownFileViewSet(viewsets.ModelViewSet):
    queryset = ModifiedMarkdownFile.objects.all()
    serializer_class = ModifiedMarkdownFileSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        original_file_id = request.data.get('original_file')
        _ = get_object_or_404(MarkdownFile, id=original_file_id)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubmittedMarkdownFileViewSet(viewsets.ModelViewSet):
    queryset = SubmittedMarkdownFile.objects.all()
    serializer_class = SubmittedMarkdownFileSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        modified_file_id = request.data.get('modified_file')
        modified_file = get_object_or_404(ModifiedMarkdownFile, id=modified_file_id)
        if SubmittedMarkdownFile.objects.filter(modified_file=modified_file).exists():
            return Response({'error': 'File already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        submitted_md = SubmittedMarkdownFile.objects.create(modified_file=modified_file)
        return Response(SubmittedMarkdownFileSerializer(submitted_md).data, status=status.HTTP_201_CREATED)
