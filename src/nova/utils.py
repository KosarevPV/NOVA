""""""

import json
import re
from http import HTTPStatus
from typing import Any, Dict, Optional

from django.conf import settings
from django.http import JsonResponse
from httpx import AsyncClient, Response
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile


async def validate_request_data(data: str, name: str) -> Optional[JsonResponse]:
    """
    Validates the request data for uploading a file.

    Args:
        data (str): The data to be uploaded.
        name (str): The name of the file.
    Returns:
        JsonResponse: A JSON response indicating the validation result.
            - If the data parameter is empty or only contains whitespace characters,
              returns a JSON response with an error message and HTTP status code 400.
            - If the data parameter exceeds the maximum allowed length,
              returns a JSON response with an error message and HTTP status code 400.
            - If the name parameter is empty or does not match the required format,
              returns a JSON response with an error message and HTTP status code 400.
            - Otherwise, returns None.
    """
    if not data:
        return JsonResponse(
            {"error": "Data parameter is required."},
            status=HTTPStatus.BAD_REQUEST,
        )
    if not data.strip(" \n\t\r"):
        return JsonResponse(
            {"error": "Data parameter is not allowed to be empty."},
            status=HTTPStatus.BAD_REQUEST,
        )
    if len(data) > settings.MAX_DATA_LEN:
        return JsonResponse(
            {"error": f"Data parameter is too large. Maximum allowed count of symbols is {settings.MAX_DATA_LEN}."},
            status=HTTPStatus.BAD_REQUEST,
        )
    if not name:
        return JsonResponse(
            {"error": "Name parameter is required."},
            status=HTTPStatus.BAD_REQUEST,
        )

    if not re.match(r"^[a-zA-Z0-9_]{1,50}.[a-zA-Z]{2,4}$", name):
        return JsonResponse(
            {"error": "Invalid file name format."},
            status=HTTPStatus.BAD_REQUEST,
        )

    return None


async def async_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = 5,
    client_params: Optional[Dict[str, Any]] = None,
) -> Response:
    """
    Asynchronous request function.

    Args:
        method (str): The HTTP method to use for the request.
        url (str): The URL to send the request to.
        headers (Optional[Dict[str, Any]]): Optional headers to include in the request.
        data (Optional[Dict[str, Any]]): Optional data to include in the request body.
        timeout (Optional[int]): Optional timeout value in seconds for the request.
        client_params (Optional[Dict[str, Any]]): Optional parameters to pass to the AsyncClient constructor.
    Returns:
        Response: The response object representing the result of the request.
    """
    async with AsyncClient(**(client_params or {})) as client:
        return await client.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            timeout=timeout,
        )


# TODO: rewrite asynchronous
async def google_auth() -> GoogleAuth:
    """
    Asynchronously authenticates with Google using the provided settings.

    Returns:
        GoogleAuth: An instance of the GoogleAuth class representing the authenticated session.
    """
    settings = {
        "client_config_backend": "service",
        "service_config": {"client_json_file_path": "nova.json"},
    }
    # Create instance of GoogleAuth
    gauth = GoogleAuth(settings=settings)
    # Authenticate
    gauth.ServiceAuth()
    return gauth


# TODO: rewrite asynchronous
async def create_file(gauth: GoogleAuth, name: str, data: str) -> GoogleDriveFile:
    """
    Creates a file on Google Drive using the provided authentication and file data.

    Args:
        gauth (GoogleAuth): An instance of the GoogleAuth class for authentication.
        name (str): The name of the file to be created.
        data (str): The content of the file to be created.
    Returns:
        GoogleDriveFile: The created file on Google Drive.
    """
    drive = GoogleDrive(gauth)
    my_file = drive.CreateFile(
        {
            "title": name,
            "parents": [{"id": settings.FOLDER_ID}]
        }
    )

    my_file.SetContentString(data)
    my_file.Upload()
    return my_file


async def share_file(my_file: GoogleDriveFile, access_token: str):
    """
    Share a Google Drive file with anyone who has the link.

    Args:
        my_file (GoogleDriveFile): The file to be shared.
        access_token (str): The access token for authentication.
    Returns:
        str: The link to the shared file.
    """
    file_id = my_file["id"]
    url = "https://www.googleapis.com/drive/v3/files/" + file_id + "/permissions?supportsAllDrives=true"
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
    }
    payload = {"type": "anyone", "value": "anyone", "role": "reader"}
    await async_request("POST", url, headers=headers, data=payload)
    return my_file["alternateLink"]
