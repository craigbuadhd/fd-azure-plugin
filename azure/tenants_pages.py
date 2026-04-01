from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from consulting import clients_service as client_service
from azure import tenants_service as tenant_service
from azure import subscriptions_service as subscription_service
from azure.models import TenantCreate, TenantUpdate

from friction_dissolved.core.templates import TEMPLATES_DIR as _TEMPLATES_DIR
router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=_TEMPLATES_DIR)


def _render(name: str, request: Request, **context: object) -> HTMLResponse:
    return templates.TemplateResponse(request, name, context)


@router.get("/clients/{client_slug}/tenants", response_class=HTMLResponse)
def tenant_list_page(request: Request, client_slug: str, success: str = "") -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    tenants = tenant_service.list_tenants(client_slug)
    subs = subscription_service.list_subscriptions(client_slug)
    sub_counts = {}
    for s in subs:
        sub_counts[s.tenant_id] = sub_counts.get(s.tenant_id, 0) + 1
    return _render(
        "tenants/list.html", request,
        client=client, tenants=tenants, sub_counts=sub_counts, success=success,
    )


@router.get("/clients/{client_slug}/tenants/new", response_class=HTMLResponse)
def new_tenant_form(request: Request, client_slug: str) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return _render("tenants/form.html", request, client=client, tenant=None, error=None)


@router.post("/clients/{client_slug}/tenants/new", response_model=None)
def create_tenant_page(
    request: Request,
    client_slug: str,
    name: str = Form(""),
    tenant_id: str = Form(""),
    primary_domain: str = Form(""),
    custom_domain: str = Form(""),
    admin_contact: str = Form(""),
    notes: str = Form(""),
) -> Response:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        data = TenantCreate(
            name=name, tenant_id=tenant_id, primary_domain=primary_domain,
            custom_domain=custom_domain, admin_contact=admin_contact, notes=notes,
        )
        tenant_service.create_tenant(client_slug, data)
        return RedirectResponse(
            url=f"/clients/{client_slug}/tenants", status_code=303
        )
    except ValueError as e:
        return _render(
            "tenants/form.html", request,
            client=client, error=str(e),
            tenant={
                "name": name, "tenant_id": tenant_id,
                "primary_domain": primary_domain, "custom_domain": custom_domain,
                "admin_contact": admin_contact, "notes": notes,
            },
        )


@router.get("/clients/{client_slug}/tenants/{tid}", response_class=HTMLResponse)
def tenant_detail_page(request: Request, client_slug: str, tid: int) -> HTMLResponse:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    tenant = tenant_service.get_tenant(client_slug, tid)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    subs = [s for s in subscription_service.list_subscriptions(client_slug) if s.tenant_id == tid]
    return _render(
        "tenants/form.html", request,
        client=client, tenant=tenant, error=None, child_subscriptions=subs,
    )


@router.post("/clients/{client_slug}/tenants/{tid}", response_model=None)
def update_tenant_page(
    request: Request,
    client_slug: str,
    tid: int,
    name: str = Form(""),
    tenant_id: str = Form(""),
    primary_domain: str = Form(""),
    custom_domain: str = Form(""),
    admin_contact: str = Form(""),
    notes: str = Form(""),
) -> Response:
    client = client_service.get_client(client_slug)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        data = TenantUpdate(
            name=name, tenant_id=tenant_id, primary_domain=primary_domain,
            custom_domain=custom_domain, admin_contact=admin_contact, notes=notes,
        )
        tenant_service.update_tenant(client_slug, tid, data)
        return RedirectResponse(
            url=f"/clients/{client_slug}/tenants", status_code=303
        )
    except ValueError as e:
        tenant = tenant_service.get_tenant(client_slug, tid)
        return _render(
            "tenants/form.html", request,
            client=client, tenant=tenant, error=str(e),
        )
