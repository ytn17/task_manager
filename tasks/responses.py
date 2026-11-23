from rest_framework.response import Response

def error_response(code, message, details, status):
    return Response(
        {
            "error": {
                "code": str(code),
                "message": str(message),
                "details": details
            }
        },
        status = status
    )

def serializer_error_details(errors):
    details = []

    for field, messages in errors.items():
        for message in messages:
            details.append({
                "field": str(field),
                "issue": str(message)
            })

    return details