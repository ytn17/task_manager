# Task Management API

A RESTful Task Management API built using **Django**, **Django REST Framework (DRF)**, and **PostgreSQL**.

The API allows users to create, retrieve, update, and delete tasks. It also supports natural-language task creation, subtasks, automatic task breakdown, idempotency, filtering, searching, ordering, and pagination.

## Features

- **Task CRUD:** Create, retrieve, update, and delete tasks.
- **Task validation:** Validate task fields, priorities, and parent-child relationships.
- **Natural-language task creation:** Create tasks from plain-text descriptions using a rule-based parser.
- **Subtasks:** Create and retrieve subtasks associated with a parent task.
- **Task breakdown:** Automatically generate subtasks for an existing task.
- **Idempotency:** Prevent duplicate task creation when clients retry requests using an `Idempotency-Key`.
- **Filtering:** Filter tasks by completion status, priority, and due date.
- **Search:** Search tasks by title and description.
- **Ordering:** Sort tasks by supported fields.
- **Pagination:** Return tasks in configurable pages.
- **Consistent error responses:** Use a common error response structure for API failures.

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- django-filter

## Project Structure

```text
task-management-api/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── tasks/
│   ├── migrations/
│   ├── tests/
│   │   ├── test_task_crud.py
│   │   ├── test_task_filters.py
│   │   ├── test_task_idempotency.py
│   │   ├── test_task_subtasks.py
│   │   └── test_task_from_text.py
│   │
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── ai.py
│   ├── services.py
│   ├── idempotency.py
│   └── responses.py
│
├── manage.py
├── requirements.txt
└── README.md
```

## Prerequisites

Make sure you have the following installed:

- Python 3.10+
- PostgreSQL
- pip
- Git

## Installation and Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd task-management-api
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**macOS/Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you don't have a `requirements.txt` yet, generate one using:

```bash
pip freeze > requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database:

```sql
CREATE DATABASE task_management;
```

Configure your database credentials in `config/settings.py` or through environment variables.

Example:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "task_management",
        "USER": "postgres",
        "PASSWORD": "your_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## Task Model

Each task contains the following fields:

| Field | Type | Description |
|---|---|---|
| `id` | Integer | Unique task identifier |
| `title` | String | Task title |
| `description` | Text | Task description |
| `completed` | Boolean | Whether the task is completed |
| `priority` | String | `low`, `medium`, or `high` |
| `due_date` | Date | Optional due date |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |
| `parent` | Foreign Key | Optional reference to the parent task |

A task can have subtasks, but a subtask cannot have its own subtasks.

## API Endpoints

Assuming the task router is registered under `/api/tasks/`:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/tasks/` | List all tasks |
| POST | `/api/tasks/` | Create a task |
| GET | `/api/tasks/{id}/` | Retrieve a task |
| PUT | `/api/tasks/{id}/` | Update a task |
| PATCH | `/api/tasks/{id}/` | Partially update a task |
| DELETE | `/api/tasks/{id}/` | Delete a task |
| POST | `/api/tasks/from-text/` | Create a task from plain text |
| GET | `/api/tasks/{id}/subtasks/` | Retrieve subtasks |
| POST | `/api/tasks/{id}/subtasks/` | Create a subtask |
| POST | `/api/tasks/{id}/breakdown/` | Generate subtasks automatically |

## API Usage Examples

### 1. Create a Task

**POST** `/api/tasks/`

Request:

```json
{
    "title": "Complete Django assignment",
    "description": "Implement task management API",
    "completed": false,
    "priority": "high",
    "due_date": "2026-12-01"
}
```

### 2. Retrieve All Tasks

**GET** `/api/tasks/`

Returns a paginated list of tasks.

### 3. Update a Task

**PATCH** `/api/tasks/1/`

Request:

```json
{
    "completed": true
}
```

### 4. Delete a Task

**DELETE** `/api/tasks/1/`

Returns HTTP `204 No Content` when successful.

### 5. Create a Task from Natural Language

**POST** `/api/tasks/from-text/`

Request:

```json
{
    "text": "Remind me to complete the project report tomorrow with high priority"
}
```

The parser extracts task information such as title, description, priority, and due date.

The natural-language parser is implemented in `tasks/ai.py` and can be replaced with an AI-powered implementation without changing the API endpoint.

### 6. Create a Subtask

**POST** `/api/tasks/1/subtasks/`

Request:

```json
{
    "title": "Write unit tests",
    "description": "Add tests for task CRUD operations",
    "priority": "medium",
    "completed": false
}
```

The parent task is determined by the task ID in the URL.

### 7. Retrieve Subtasks

**GET** `/api/tasks/1/subtasks/`

Returns all subtasks belonging to task `1`.

### 8. Automatically Break Down a Task

**POST** `/api/tasks/1/breakdown/`

Generates subtasks for the specified parent task using the task breakdown service.

## Idempotency

The API supports idempotency for task creation operations.

Clients can provide an `Idempotency-Key` header:

```http
Idempotency-Key: request-123
```

Behavior:

- **New key:** Processes the request and stores the response.
- **Same key + same request body:** Returns the previously stored response without creating duplicate records.
- **Same key + different request body:** Returns HTTP `422 Unprocessable Entity`.

The current implementation uses an in-memory dictionary. Idempotency records are therefore process-local and are lost when the application restarts.

## Filtering, Searching, and Ordering

### Filtering

Filter tasks using query parameters:

```text
GET /api/tasks/?completed=false
GET /api/tasks/?priority=high
GET /api/tasks/?due_date=2026-12-01
```

Filters can be combined:

```text
GET /api/tasks/?completed=false&priority=high
```

### Searching

Search by title or description:

```text
GET /api/tasks/?search=assignment
```

### Ordering

Supported ordering fields:

- `created_at`
- `due_date`
- `priority`
- `title`

Examples:

```text
GET /api/tasks/?ordering=due_date
GET /api/tasks/?ordering=-created_at
GET /api/tasks/?ordering=title
```

Use a minus sign (`-`) for descending order.

### Pagination

The API uses page-number pagination with a default page size of 10.

Examples:

```text
GET /api/tasks/?page=1
GET /api/tasks/?page=2
```

Response structure:

```json
{
    "count": 25,
    "next": "http://127.0.0.1:8000/api/tasks/?page=2",
    "previous": null,
    "results": []
}
```

## Error Handling

API errors use a consistent response structure.

Example:

```json
{
    "code": "VALIDATION_ERROR",
    "message": "Invalid task data",
    "details": [
        {
            "field": "priority",
            "issue": "Invalid choice."
        }
    ]
}
```

Common HTTP status codes:

| Status | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 204 | Resource deleted |
| 400 | Validation error or invalid operation |
| 404 | Task not found |
| 422 | Idempotency conflict |
| 502 | Task parser failure |

## Running Tests

Run the complete test suite:

```bash
python manage.py test
```

Run tests for a specific module:

```bash
python manage.py test tasks.tests.test_task_crud
python manage.py test tasks.tests.test_task_filters
python manage.py test tasks.tests.test_task_idempotency
python manage.py test tasks.tests.test_task_subtasks
python manage.py test tasks.tests.test_task_from_text
```

The test suite covers:

- Task creation, retrieval, updating, and deletion.
- Input validation and error handling.
- Filtering, searching, ordering, and pagination.
- Idempotent request handling.
- Subtask creation and retrieval.
- Natural-language task parsing.

## Future Improvements

- Replace in-memory idempotency storage with Redis or database-backed storage.
- Add authentication and authorization.
- Replace the rule-based parser with an LLM-powered parser.
- Add API documentation using Swagger/OpenAPI.
- Add Docker support and deployment configuration.
- Introduce background processing for complex task breakdown operations.

## License

This project was developed as a learning and backend engineering assignment.