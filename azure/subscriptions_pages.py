from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from consulting import clients_service as client_service
from azure import tenants_service as tenant_service
from azure import subscriptions_service as subscription_service
from azure import resource_groups_service
from azure.models import (
    OFFER_TYPES,
    SubscriptionCreate,
    SubscriptionUpdate,
)

from friction_dissolved.core.templates import TEMPLATES_DIR as _TEMPLATES_DIR
router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


def _render(name: str, request: Request, **context: object) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context)


@router.get("/clients/{client_slug}/subscriptions", response_class=HTMLResponse)
def subscription_list_page(
    request: Request, client_slug: str, success: str = ""
) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    subs = subscription_service.list_subscriptions(client_slug)
    tenants = tenant_service.list_tenants(client_slug)
    tenant_map = {t.id: t.name for t in tenants}
    return _render(
        "subscriptions/list.html", request,
        client=client, subscriptions=subs, tenant_map=tenant_map,
        success=success,
    )


@router.get("/clients/{client_slug}/subscriptions/new", response_class=HTMLResponse)
def new_subscription_form(request: Request, client_slug: str) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    tenants = tenant_service.list_tenants(client_slug)
    return _render(
        "subscriptions/form.html", request,
        client=client, subscription=None, error=None,
        tenants=tenants, offer_types=OFFER_TYPES,
    )


@router.post("/clients/{client_slug}/subscriptions/new", response_model=None)
def create_subscription_page(
    request: Request,
    client_slug: str,
    name: str = Form(""),
    subscription_id: str = Form(""),
    tenant_id: str = Form(""),
    offer_type: str = Form(""),
    owner: str = Form(""),
    notes: str = Form(""),
) -> Response:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        t_id = int(tenant_id) if tenant_id else None
        data = SubscriptionCreate(
            name=name, subscription_id=subscription_id, tenant_id=t_id,
            offer_type=offer_type, owner=owner, notes=notes,
        )
        subscription_service.create_subscription(client_slug, data)
        return RedirectResponse(
            url=f"/clients/{client_slug}/subscriptions", status_code=303
        )
    except ValueError as e:
        tenants = tenant_service.list_tenants(client_slug)
        return _render(
            "subscriptions/form.html", request,
            client=client, error=str(e),
            tenants=tenants, offer_types=OFFER_TYPES,
            subscription={
                "name": name, "subscription_id": subscription_id,
                "tenant_id": tenant_id, "offer_type": offer_type,
                "owner": owner, "notes": notes,
            },
        )


@router.get("/clients/{client_slug}/subscriptions/{sid}", response_class=HTMLResponse)
def subscription_detail_page(
    request: Request, client_slug: str, sid: int
) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    sub = subscription_service.get_subscription(client_slug, sid)
    if sub is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    tenants = tenant_service.list_tenants(client_slug)
    rgs = [rg for rg in resource_groups_service.list_resource_groups(client_slug) if rg.subscription_id == sid]
    parent_tenant = next((t for t in tenants if t.id == sub.tenant_id), None)
    return _render(
        "subscriptions/form.html", request,
        client=client, subscription=sub, error=None,
        tenants=tenants, offer_types=OFFER_TYPES,
        child_resource_groups=rgs, parent_tenant=parent_tenant,
    )


@router.post("/clients/{client_slug}/subscriptions/{sid}", response_model=None)
def update_subscription_page(
    request: Request,
    client_slug: str,
    sid: int,
    name: str = Form(""),
    subscription_id: str = Form(""),
    tenant_id: str = Form(""),
    offer_type: str = Form(""),
    owner: str = Form(""),
    notes: str = Form(""),
) -> Response:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        t_id = int(tenant_id) if tenant_id else None
        data = SubscriptionUpdate(
            name=name, subscription_id=subscription_id, tenant_id=t_id,
            offer_type=offer_type, owner=owner, notes=notes,
        )
        subscription_service.update_subscription(client_slug, sid, data)
        return RedirectResponse(
            url=f"/clients/{client_slug}/subscriptions", status_code=303
        )
    except ValueError as e:
        sub = subscription_service.get_subscription(client_slug, sid)
        tenants = tenant_service.list_tenants(client_slug)
        return _render(
            "subscriptions/form.html", request,
            client=client, subscription=sub, error=str(e),
            tenants=tenants, offer_types=OFFER_TYPES,
        )
