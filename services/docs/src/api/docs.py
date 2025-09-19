from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from httpx import AsyncClient

from core.configs.base import settings
from core.security import basic_auth
from schemas import Service

router = APIRouter(dependencies=[Depends(basic_auth)])


SERVICES = [Service(name=service) for service in settings.SERVICES]


async def fetch_service_openapi(service_name: str) -> dict[str, Any]:
    """Fetch service openapi.json from kubernetes cluster."""
    # noinspection HttpUrlsUsage
    url = f"http://{service_name}.{settings.NAMESPACE}.svc.cluster.local/openapi.json"

    async with AsyncClient(auth=(settings.BASIC_AUTH_USER, settings.BASIC_AUTH_PASS)) as client:
        result = await client.get(url)

        if result.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=result.status_code)

        data: dict[str, Any] = result.json()
        return data


@router.get("/openapi/{service_name}.json")
async def proxy_openapi(service_name: str) -> dict[str, Any]:
    """Proxy for fetching service openapi.json."""
    service = service_name.replace("-service", "")

    if service not in settings.SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    return await fetch_service_openapi(service_name)


@router.get("/docs")
async def custom_swagger_ui() -> HTMLResponse:
    """Loads custom swagger ui with multiple services."""
    html = get_swagger_ui_html(
        openapi_url="",
        title=settings.SERVICE_TITLE,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.27.1/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.27.1/swagger-ui.css",
        swagger_ui_parameters={
            "urls": [s.swagger_data for s in SERVICES],
            "layout": "StandaloneLayout",
        },
    )

    standalone_preset = "https://unpkg.com/swagger-ui-dist@5.27.1/swagger-ui-standalone-preset.js"
    standalone_script = f'<script src="{standalone_preset}"></script>'

    # update body
    html.body = (
        bytes(html.body)
        # --------------
        .decode("utf-8")
        .replace("<!-- `SwaggerUIBundle` is now available on the page -->", standalone_script)
        .replace("SwaggerUIBundle.SwaggerUIStandalonePreset", "SwaggerUIStandalonePreset")
        .encode("utf-8")
    )

    # update content length
    content_length = str(len(html.body)).encode("utf-8")
    html.raw_headers[0] = (b"content-length", content_length)

    return html
