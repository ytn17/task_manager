from typing import override

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Task
from .serializers import TaskSerializer
from django.http import Http404
from .responses import error_response, serializer_error_details
from .ai import parse_task_text
from datetime import date
from rest_framework.decorators import action
from .services import break_down_task
from .idempotency import check_idempotency, store_idempotency

# Create your views here.
class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    filterset_fields = ["completed", "priority", "due_date"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "due_date", "priority", "title"]

    @override
    def create(self, request):
        key = request.headers.get("Idempotency-Key")
        result, stored_response = check_idempotency(key, body=request.data)

        if result == 'REPLAY':
            return Response(
            stored_response,
            status=status.HTTP_201_CREATED
        )

        if result == 'CONFLICT':
            return error_response(
                code="IDEMPOTENCY_CONFLICT",
                message="Idempotency key already used with a different request body",
                details=[],
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
    
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Validation failed",
                details=serializer_error_details(serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        response = Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
        store_idempotency(key, request.data, response.data)
        return response

    @override
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        try:
            instance = self.get_object()
        
        except Http404:
            return error_response(
                code="NOT FOUND",
                message="Task not found to update",
                details=[],
                status=status.HTTP_404_NOT_FOUND
                )

        serializer = self.get_serializer(
            instance,
            data = request.data,
            partial = partial
        )

        if not serializer.is_valid():
            return error_response(
                            code="VALIDATION_ERROR",
                            message="Validation failed",
                            details=serializer_error_details(serializer.errors),
                            status=status.HTTP_400_BAD_REQUEST
                        )

        serializer.save()
        return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
        )

    @override
    def retrieve(self, request, pk=None):
        try:
            instance = self.get_object()

        except Http404:
            return error_response(
                    code="NOT FOUND",
                    message="Task not found ",
                    details=[],
                    status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(instance)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @override
    def destroy(self, request, pk=None):
        try:
            instance = self.get_object()
        
        except Http404:
            return error_response(
                code="NOT FOUND",
                message="Task not found ",
                details=[],
                status=status.HTTP_404_NOT_FOUND
            )
        
        instance.delete()
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail = False, methods=['POST'], url_path="from-text")
    def from_text(self, request):
        key = request.headers.get("Idempotency-Key")
        result, stored_response = check_idempotency(key, body=request.data)

        if result == "REPLAY":
            return Response(
                stored_response,
                status=status.HTTP_201_CREATED
            )

        if result == "CONFLICT":
            return error_response(
                code="IDEMPOTENCY_CONFLICT",
                message="Idempotency key already used with a different request body",
                details=[],
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        text = request.data.get("text")

        if not isinstance(text, str) or not text.strip():
            return error_response(
            code="VALIDATION_ERROR",
            message="Text is required",
            details=[
                {
                    "field": "text",
                    "issue": "must not be empty"
                }
            ],
            status=status.HTTP_400_BAD_REQUEST
        )

        try:
            parsed_data = parse_task_text(text, date.today())
        except Exception:
            return error_response(
            code="PARSER_ERROR",
            message="Unable to process task text",
            details=[],
            status=status.HTTP_502_BAD_GATEWAY
            )

        serializer = TaskSerializer(data=parsed_data)
        if not serializer.is_valid():
            return error_response(
            code="PARSER_VALIDATION_ERROR",
            message="Parser returned invalid task data",
            details=serializer_error_details(serializer.errors),
            status=status.HTTP_502_BAD_GATEWAY
            )

        serializer.save()
        response = Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

        store_idempotency(
        key,
        request.data,
        response.data
        )

        return response

    @action(detail=True, methods=["get", "post"])
    def subtasks(self, request, pk=None):

        parent = self.get_object()

        if request.method == "GET":

            subtasks = parent.subtasks.all()

            serializer = TaskSerializer(
                subtasks,
                many=True
            )

            return Response(serializer.data)

        if parent.parent is not None:
            return error_response(
                "INVALID_OPERATION",
                "A subtask cannot have its own subtasks",
                [],
                status.HTTP_400_BAD_REQUEST
            )

        serializer = TaskSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                code="VALIDATION_ERROR",
                message="Validation failed",
                details=serializer_error_details(serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(parent=parent)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def breakdown(self, request, pk=None):
        task = self.get_object()

        key = request.headers.get("Idempotency-Key")
        request_body = {
            "task_id": task.id,
            "body": request.data
        }

        result, stored_response = check_idempotency(
            key,
            body=request_body
        )

        if result == "REPLAY":
            return Response(
                stored_response,
                status=status.HTTP_201_CREATED
            )
        if result == "CONFLICT":
            return error_response(
                code="IDEMPOTENCY_CONFLICT",
                message="Idempotency key already used with a different request body",
                details=[],
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        if task.parent is not None:
            return error_response(
                "INVALID_OPERATION",
                "A subtask cannot be broken down",
                [],
                status.HTTP_400_BAD_REQUEST
            )

        subtask_data = break_down_task(task)

        serializers_list = [
            TaskSerializer(data=item)
            for item in subtask_data
        ]

        errors = []

        for index, serializer in enumerate(serializers_list):

            if not serializer.is_valid():
                errors.append({
                    "field": f"subtasks[{index}]",
                    "issue": str(serializer.errors)
                })

        if errors:
            return error_response(
                "VALIDATION_ERROR",
                "Generated subtasks are invalid",
                errors,
                status.HTTP_400_BAD_REQUEST
            )

        created_subtasks = []

        for serializer in serializers_list:
            created_subtasks.append(
                serializer.save(parent=task)
            )

        response_serializer = TaskSerializer(
            created_subtasks,
            many=True
        )

        store_idempotency(
            key,
            request_body,
            response_serializer.data
        )

        return Response(
            result,
            status=status.HTTP_201_CREATED
        )


        



