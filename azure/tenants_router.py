from fastapi import APIRouter, HTTPException

from azure.models import Tenant, TenantCreate, TenantUpdate
from azure import tenants_service as tenant_service
from consulting import clients_service as client_service

router = APIRouter(prefix="/api/clients/{client_slug}/tenants", tags=["tenants"])


def _require_client(client_slug: str) -> None:
    if client_service.get_client(client_slug) is None:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("", response_model=list[Tenant])
def list_tenants(client_slug: str) -> list[Tenant]:
    _require_client(client_slug)
    return tenant_service.list_tenants(client_slug)


@router.get("/{tenant_id}", response_model=Tenant)
def get_tenant(client_slug: str, tenant_id: int) -> Tenant:
    _require_client(client_slug)
    tenant = tenant_service.get_tenant(client_slug, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.post("", response_model=Tenant, status_code=201)
def create_tenant(client_slug: str, data: TenantCreate) -> Tenant:
    _require_client(client_slug)
    return tenant_service.create_tenant(client_slug, data)


@router.patch("/{tenant_id}", response_model=Tenant)
def update_tenant(client_slug: str, tenant_id: int, data: TenantUpdate) -> Tenant:
    _require_client(client_slug)
    tenant = tenant_service.update_tenant(client_slug, tenant_id, data)
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(client_slug: str, tenant_id: int) -> None:
    _require_client(client_slug)
    if not tenant_service.delete_tenant(client_slug, tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
