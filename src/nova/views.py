import json
from http import HTTPStatus

from django.http import HttpRequest, JsonResponse
from django.views import View

from nova.utils import create_file, google_auth, share_file, validate_request_data


class UploadFile(View):

    async def post(self, request: HttpRequest) -> JsonResponse:
        """
        Asynchronously handles a POST request to upload a file.
        Args:
            request (HttpRequest): The HTTP request object containing the file data and name.
        Returns:
            JsonResponse: A JSON response containing the result of the file upload.
                - If the file data or name is missing in the request, returns a JSON response with an error message and
                    HTTP status code 400.
                - If the file upload fails, returns a JSON response with an error message and HTTP status code 500.
                - If the file upload is successful, returns a JSON response with a success message and
                    HTTP status code 200.
        """
        request_data = json.loads(request.body)
        data = request_data.get("data", "")
        name = request_data.get("name", "")

        result_of_validation = await validate_request_data(data, name)
        if result_of_validation is not None:
            return result_of_validation
        try:
            gauth = await google_auth()
            file = await create_file(gauth, name, data)
            link = await share_file(file, gauth.credentials.access_token)
        except Exception:
            return JsonResponse({"error": "Failed to upload file.", "status": HTTPStatus.INTERNAL_SERVER_ERROR})

        return JsonResponse(
            {
                "message": f"File {name} uploaded successfully. Link: {link}",
                "status": HTTPStatus.OK,
            }
        )
