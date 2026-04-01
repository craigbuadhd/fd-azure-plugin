from fastapi import APIRouter, HTTPException

from azure.models import (
    ResourceGroup,
    ResourceGroupCreate,
    ResourceGroupUpdate,
)
from azure import resource_groups_service as resource_group_service
from consulting import clients_service as client_service

router = APIRouter(
    prefix="/api/clients/{client_slug}/resource-groups", tags=["resource-groups"]
)


def _require_client(client_slug: str) -> None:
    if client_service.get_client(client_slug) is None:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("", response_model=list[ResourceGroup])
def list_resource_groups(client_slug: str) -> list[ResourceGroup]:
    _require_client(client_slug)
    return resource_group_service.list_resource_groups(client_slug)


@router.get("/{rg_id}", response_model=ResourceGroup)
def get_resource_group(client_slug: str, rg_id: int) -> ResourceGroup:
    _require_client(client_slug)
    rg = resource_group_service.get_resource_group(client_slug, rg_id)
    if rg is None:
        raise HTTPException(status_code=404, detail="Resource group not found")
    return rg


@router.post("", response_model=ResourceGroup, status_code=201)
def create_resource_group(client_slug: str, data: ResourceGroupCreate) -> ResourceGroup:
    _require_client(client_slug)
    try:
        return resource_group_service.create_resource_group(client_slug, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{rg_id}", response_model=ResourceGroup)
def update_resource_group(
    client_slug: str, rg_id: int, data: ResourceGroupUpdate
) -> ResourceGroup:
    _require_client(client_slug)
    try:
        rg = resource_group_service.update_resource_group(client_slug, rg_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if rg is None:
        raise HTTPException(status_code=404, detail="Resource group not found")
    return rg


@router.delete("/{rg_id}", status_code=204)
def delete_resource_group(client_slug: str, rg_id: int) -> None:
    _require_client(client_slug)
    if not resource_group_service.delete_resource_group(client_slug, rg_id):
        raise HTTPException(status_code=404, detail="Resource group not found")
