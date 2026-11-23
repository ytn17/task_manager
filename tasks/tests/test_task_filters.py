from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Task


class TaskFilterTests(APITestCase):

    def setUp(self):
        self.url = reverse("task-list")

        Task.objects.create(
            title="Complete assignment",
            description="Django project",
            completed=False,
            priority="high"
        )

        Task.objects.create(
            title="Attend meeting",
            description="Project discussion",
            completed=True,
            priority="medium"
        )

        Task.objects.create(
            title="Prepare documentation",
            description="Write project documentation",
            completed=False,
            priority="low"
        )

    def test_filter_by_completed(self):
        response = self.client.get(
            self.url,
            {"completed": "false"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for task in response.data["results"]:
            self.assertFalse(task["completed"])

    def test_filter_by_priority(self):
        response = self.client.get(
            self.url,
            {"priority": "high"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for task in response.data["results"]:
            self.assertEqual(task["priority"], "high")

    def test_search_by_title(self):
        response = self.client.get(
            self.url,
            {"search": "meeting"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        self.assertEqual(
            response.data["results"][0]["title"],
            "Attend meeting"
        )

    def test_ordering_by_title(self):
        response = self.client.get(
            self.url,
            {"ordering": "title"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        titles = [
            task["title"]
            for task in response.data["results"]
        ]

        self.assertEqual(titles, sorted(titles))

    def test_combined_filters_and_search(self):
        response = self.client.get(
            self.url,
            {
                "completed": "false",
                "priority": "high",
                "search": "assignment"
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_pagination(self):
        response = self.client.get(
            self.url,
            {"page": 1}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)