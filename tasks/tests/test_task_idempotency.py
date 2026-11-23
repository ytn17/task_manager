from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Task
from tasks.idempotency import idempotency_store


class TaskIdempotencyTests(APITestCase):

    def setUp(self):
        idempotency_store.clear()
        self.url = reverse("task-list")

        self.payload = {
            "title": "Complete assignment",
            "description": "Finish API implementation",
            "status": "pending",
            "priority": "high"
        }

        self.headers = {
            "HTTP_IDEMPOTENCY_KEY": "test-key-123"
        }

    def test_same_request_same_key_returns_original_response(self):

        first_response = self.client.post(
            self.url,
            self.payload,
            format="json",
            **self.headers
        )

        second_response = self.client.post(
            self.url,
            self.payload,
            format="json",
            **self.headers
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            first_response.data["id"],
            second_response.data["id"]
        )

        self.assertEqual(Task.objects.count(), 1)

    def test_same_key_different_request_returns_conflict(self):

        self.client.post(
            self.url,
            self.payload,
            format="json",
            **self.headers
        )

        different_payload = self.payload.copy()
        different_payload["title"] = "Different task"

        response = self.client.post(
            self.url,
            different_payload,
            format="json",
            **self.headers
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )

        self.assertEqual(Task.objects.count(), 1)

    def test_request_without_idempotency_key(self):

        response = self.client.post(
            self.url,
            self.payload,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )