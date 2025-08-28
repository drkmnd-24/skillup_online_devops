from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Task, MarkdownFile, ModifiedMarkdownFile, SubmittedMarkdownFile

User = get_user_model()


class UserLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "knox_id", "email", "department", "lab_part", "project")


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "knox_id", "email", "password", "department", "lab_part", "project")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MarkdownFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarkdownFile
        fields = "__all__"


class ModifiedMarkdownFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifiedMarkdownFile
        fields = "__all__"


class SubmittedMarkdownFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmittedMarkdownFile
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserLiteSerializer(read_only=True)
    submitted_file = SubmittedMarkdownFileSerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            "id", "title", "description", "assigned_to", "status",
            "submitted_file", "created_at", "updated_at",
            "time_limit_minutes", "review_status", "started_at", "time_taken"
        )
