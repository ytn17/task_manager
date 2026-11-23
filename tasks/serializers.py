from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Task
        fields = '__all__'

    def validate_parent(self, value):

        if value and value.parent is not None:
            raise serializers.ValidationError(
                "A subtask cannot have its own subtasks."
            )

        return value