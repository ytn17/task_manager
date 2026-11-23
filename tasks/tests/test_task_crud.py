from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Task


class TaskCRUDTests(APITestCase):

    def setUp(self):
        self.task = Task.objects.create(
        title="Complete assignment",
        description="Complete Django assignment",
        completed=False,
        priority="high"
    )

        self.list_url = reverse("task-list")
        self.detail_url = reverse(
            "task-detail",
            kwargs={"pk": self.task.id}
        )

    def test_create_task(self):
        payload = {
            "title": "Learn Django REST Framework",
            "description": "Build a REST API",
            "completed": False,
            "priority": "high"
        }

        response = self.client.post(
            self.list_url,
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)

    def test_retrieve_task(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["title"],
            "Complete assignment"
        )

    def test_update_task(self):
        payload = {
            "title": "Updated assignment",
            "description": "Updated description",
            "completed": False,
            "priority": "high"
        }

        response = self.client.put(
            self.detail_url,
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.task.refresh_from_db()

        self.assertEqual(self.task.title, "Updated assignment")

    def test_delete_task(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Task.objects.filter(id=self.task.id).exists()
        )

    def test_retrieve_nonexistent_task(self):
        url = reverse("task-detail", kwargs={"pk": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)