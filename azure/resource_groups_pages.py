from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from consulting import clients_service as client_service
from azure import subscriptions_service as subscription_service
from azure import resource_groups_service as resource_group_service
from azure.models import (
    ResourceGroupCreate,
    ResourceGroupUpdate,
)
from friction_dissolved.core.azure_regions import AZURE_REGIONS

from friction_dissolved.core.templates import TEMPLATES_DIR as _TEMPLATES_DIR
router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


def _render(name: str, request: Request, **context: object) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context)


def _rg_form_context(client_slug: str) -> dict:
    return {
        "subscriptions": subscription_service.list_subscriptions(client_slug),
        "regions": AZURE_REGIONS,
    }


@router.get("/clients/{client_slug}/resource-groups", response_class=HTMLResponse)
def resource_group_list_page(
    request: Request, client_slug: str, success: str = ""
) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    rgs = resource_group_service.list_resource_groups(client_slug)
    subs = subscription_service.list_subscriptions(client_slug)
    subscription_map = {s.id: s.name for s in subs}
    return _render(
        "resource_groups/list.html", request,
        client=client, resource_groups=rgs, subscription_map=subscription_map,
        success=success,
    )


@router.get("/clients/{client_slug}/resource-groups/new", response_class=HTMLResponse)
def new_resource_group_form(request: Request, client_slug: str) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return _render(
        "resource_groups/form.html", request,
        client=client, rg=None, error=None,
        **_rg_form_context(client_slug),
    )


@router.post("/clients/{client_slug}/resource-groups/new", response_model=None)
def create_resource_group_page(
    request: Request,
    client_slug: str,
    name: str = Form(""),
    subscription_id: str = Form(""),
    location: str = Form(""),
    purpose: str = Form(""),
    tags: str = Form(""),
    notes: str = Form(""),
) -> Response:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        sub_id = int(subscription_id) if subscription_id else None
        data = ResourceGroupCreate(
            name=name, subscription_id=sub_id, location=location,
            purpose=purpose, tags=tags, notes=notes,
        )
        resource_group_service.create_resource_group(client_slug, data)
        return RedirectResponse(
            url=f"/clients/{client_slug}/resource-groups", status_code=303
        )
    except ValueError as e:
        return _render(
            "resource_groups/form.html", request,
            client=client, error=str(e),
            **_rg_form_context(client_slug),
            rg={
                "name": name, "subscription_id": subscription_id,
                "location": location, "purpose": purpose,
                "tags": tags, "notes": notes,
            },
        )


@router.get("/clients/{client_slug}/resource-groups/{rg_id}", response_class=HTMLResponse)
def resource_group_detail_page(
    request: Request, client_slug: str, rg_id: int
) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    rg = resource_group_service.get_resource_group(client_slug, rg_id)
    if rg is None:
        raise HTTPException(status_code=404, detail="Resource group not found")
    return _render(
        "resource_groups/form.html", request,
        client=client, rg=rg, error=None,
        **_rg_form_context(client_slug),
    )


@router.post("/clients/{client_slug}/resource-groups/{rg_id}", response_model=None)
def update_resource_group_page(
    request: Request,
    client_slug: str,
    rg_id: int,
    name: str = Form(""),
    subscription_id: str = Form(""),
    location: str = Form(""),
    purpose: str = Form(""),
    tags: str = Form(""),
    notes: str = Form(""),
) -> Response:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        sub_id = int(subscription_id) if subscription_id else None
        data = ResourceGroupUpdate(
            name=name, subscription_id=sub_id, location=location,
            purpose=purpose, tags=tags, notes=notes,
        )
        resource_group_service.update_resource_group(client_slug, rg_id, data)
        return RedirectResponse(
            url=f"/clients/{client_slug}/resource-groups", status_code=303
        )
    except ValueError as e:
        rg = resource_group_service.get_resource_group(client_slug, rg_id)
        return _render(
            "resource_groups/form.html", request,
            client=client, rg=rg, error=str(e),
            **_rg_form_context(client_slug),
        )
