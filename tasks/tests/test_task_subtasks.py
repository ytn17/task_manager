
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Task


class TaskSubtaskTests(APITestCase):

    def setUp(self):
        self.parent = Task.objects.create(
            title="Build application",
            description="Build a complete application",
            completed=False,
            priority="high"
        )

        self.subtasks_url = reverse(
            "task-subtasks",
            kwargs={"pk": self.parent.id}
        )

        self.breakdown_url = reverse(
            "task-breakdown",
            kwargs={"pk": self.parent.id}
        )

    def test_create_subtask(self):
        payload = {
            "title": "Create database",
            "description": "Create database schema",
            "completed": False,
            "priority": "medium"
        }

        response = self.client.post(
            self.subtasks_url,
            payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        subtask = Task.objects.get(title="Create database")
        self.assertEqual(subtask.parent, self.parent)

    def test_list_subtasks(self):
        Task.objects.create(
            title="Create database",
            description="Create schema",
            completed=False,
            priority="medium",
            parent=self.parent
        )

        response = self.client.get(self.subtasks_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_breakdown_creates_subtasks(self):
        generated_data = [
            {
                "title": "Create database",
                "description": "Create database schema",
                "completed": False,
                "priority": "medium"
            },
            {
                "title": "Create API",
                "description": "Implement API endpoints",
                "completed": False,
                "priority": "medium"
            }
        ]

        with patch(
            "tasks.views.break_down_task",
            return_value=generated_data
        ):
            response = self.client.post(
                self.breakdown_url,
                {},
                format="json"
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            Task.objects.filter(parent=self.parent).count(),
            2
        )

    def test_subtask_cannot_have_subtasks(self):
        child = Task.objects.create(
            title="Child task",
            description="A subtask",
            completed=False,
            priority="medium",
            parent=self.parent
        )

        url = reverse(
            "task-subtasks",
            kwargs={"pk": child.id}
        )

        response = self.client.post(
            url,
            {
                "title": "Nested task",
                "description": "Should not be allowed",
                "completed": False,
                "priority": "low"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
