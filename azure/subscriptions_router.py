from fastapi import APIRouter, HTTPException

from azure.models import (
    Subscription,
    SubscriptionCreate,
    SubscriptionUpdate,
)
from azure import subscriptions_service as subscription_service
from consulting import clients_service as client_service

router = APIRouter(
    prefix="/api/clients/{client_slug}/subscriptions", tags=["subscriptions"]
)


def _require_client(client_slug: str) -> None:
    if client_service.get_client(client_slug) is None:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("", response_model=list[Subscription])
def list_subscriptions(client_slug: str) -> list[Subscription]:
    _require_client(client_slug)
    return subscription_service.list_subscriptions(client_slug)


@router.get("/{sub_id}", response_model=Subscription)
def get_subscription(client_slug: str, sub_id: int) -> Subscription:
    _require_client(client_slug)
    sub = subscription_service.get_subscription(client_slug, sub_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.post("", response_model=Subscription, status_code=201)
def create_subscription(client_slug: str, data: SubscriptionCreate) -> Subscription:
    _require_client(client_slug)
    try:
        return subscription_service.create_subscription(client_slug, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{sub_id}", response_model=Subscription)
def update_subscription(
    client_slug: str, sub_id: int, data: SubscriptionUpdate
) -> Subscription:
    _require_client(client_slug)
    try:
        sub = subscription_service.update_subscription(client_slug, sub_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if sub is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.delete("/{sub_id}", status_code=204)
def delete_subscription(client_slug: str, sub_id: int) -> None:
    _require_client(client_slug)
    if not subscription_service.delete_subscription(client_slug, sub_id):
        raise HTTPException(status_code=404, detail="Subscription not found")
