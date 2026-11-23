from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tasks.models import Task
from tasks.idempotency import idempotency_store


class TaskFromTextTests(APITestCase):

    def setUp(self):
        idempotency_store.clear()

        self.url = reverse("task-from-text")

        self.parsed_data = {
            "title": "Complete project",
            "description": "Finish Django API project",
            "status": "pending",
            "priority": "high"
        }

    @patch("tasks.views.parse_task_text")
    def test_create_task_from_text(self, mock_parser):

        mock_parser.return_value = self.parsed_data

        response = self.client.post(
            self.url,
            {
                "text": "Complete project by tomorrow"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(Task.objects.count(), 1)

        self.assertEqual(
            response.data["title"],
            "Complete project"
        )

        mock_parser.assert_called_once()

    def test_empty_text_returns_validation_error(self):

        response = self.client.post(
            self.url,
            {"text": ""},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(Task.objects.count(), 0)

    @patch("tasks.views.parse_task_text")
    def test_parser_failure_returns_502(self, mock_parser):

        mock_parser.side_effect = Exception("Parser failed")

        response = self.client.post(
            self.url,
            {"text": "Create a task"},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY
        )

        self.assertEqual(Task.objects.count(), 0)

    @patch("tasks.views.parse_task_text")
    def test_same_idempotency_key_does_not_create_duplicate(
        self,
        mock_parser
    ):

        mock_parser.return_value = self.parsed_data

        headers = {
            "HTTP_IDEMPOTENCY_KEY": "text-key-123"
        }

        payload = {
            "text": "Complete project by tomorrow"
        }

        first_response = self.client.post(
            self.url,
            payload,
            format="json",
            **headers
        )

        second_response = self.client.post(
            self.url,
            payload,
            format="json",
            **headers
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

        mock_parser.assert_called_once()