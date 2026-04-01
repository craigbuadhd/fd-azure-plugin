import logging
import sqlite3

from friction_dissolved.db.engine import db_manager
from azure.models import (
    Subscription,
    SubscriptionCreate,
    SubscriptionUpdate,
)
from friction_dissolved.core.soft_delete import (
    has_dependents,
    purge,
    restore,
    soft_delete,
)

logger = logging.getLogger(__name__)

_ALL_COLS = (
    "id, name, subscription_id, tenant_id, offer_type, "
    "owner, status, notes, created_at, updated_at"
)


def _conn(client_slug: str) -> sqlite3.Connection:
    return db_manager.get_client_connection(client_slug)


def list_subscriptions(client_slug: str, include_deleted: bool = False) -> list[Subscription]:
    where = "" if include_deleted else "WHERE deleted_at IS NULL"
    rows = _conn(client_slug).execute(
        f"SELECT {_ALL_COLS} FROM subscriptions {where} ORDER BY name"
    ).fetchall()
    return [Subscription(**dict(r)) for r in rows]


def get_subscription(client_slug: str, sub_id: int) -> Subscription | None:
    row = _conn(client_slug).execute(
        f"SELECT {_ALL_COLS} FROM subscriptions WHERE id = ? AND deleted_at IS NULL",
        (sub_id,),
    ).fetchone()
    if row is None:
        return None
    return Subscription(**dict(row))


def create_subscription(client_slug: str, data: SubscriptionCreate) -> Subscription:
    conn = _conn(client_slug)

    if data.tenant_id is not None:
        tenant = conn.execute(
            "SELECT id FROM tenants WHERE id = ? AND deleted_at IS NULL",
            (data.tenant_id,),
        ).fetchone()
        if tenant is None:
            raise ValueError(f"Tenant not found: {data.tenant_id}")

    cursor = conn.execute(
        "INSERT INTO subscriptions "
        "(name, subscription_id, tenant_id, offer_type, owner, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.name, data.subscription_id, data.tenant_id,
            data.offer_type, data.owner, data.notes,
        ),
    )
    conn.commit()
    logger.info("Created subscription '%s' for client %s", data.name, client_slug)

    sub = get_subscription(client_slug, cursor.lastrowid)
    if sub is None:
        raise RuntimeError("Subscription was created but could not be retrieved")
    return sub


def update_subscription(
    client_slug: str, sub_id: int, data: SubscriptionUpdate
) -> Subscription | None:
    existing = get_subscription(client_slug, sub_id)
    if existing is None:
        return None

    conn = _conn(client_slug)
    updates: list[str] = []
    params: list[str | int | None] = []

    if data.tenant_id is not None:
        tenant = conn.execute(
            "SELECT id FROM tenants WHERE id = ? AND deleted_at IS NULL",
            (data.tenant_id,),
        ).fetchone()
        if tenant is None:
            raise ValueError(f"Tenant not found: {data.tenant_id}")
        updates.append("tenant_id = ?")
        params.append(data.tenant_id)

    field_map: dict[str, str | None] = {
        "name": data.name,
        "subscription_id": data.subscription_id,
        "offer_type": data.offer_type,
        "owner": data.owner,
        "status": data.status,
        "notes": data.notes,
    }
    for col, val in field_map.items():
        if val is not None:
            updates.append(f"{col} = ?")
            params.append(val.strip() if col == "name" else val)
    if not updates:
        return existing

    updates.append("updated_at = datetime('now')")
    params.append(sub_id)

    conn.execute(
        f"UPDATE subscriptions SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()
    logger.info("Updated subscription %d for client %s", sub_id, client_slug)
    return get_subscription(client_slug, sub_id)


def delete_subscription(client_slug: str, sub_id: int) -> bool:
    if get_subscription(client_slug, sub_id) is None:
        return False
    return soft_delete(_conn(client_slug), "subscriptions", "id", sub_id)


def restore_subscription(client_slug: str, sub_id: int) -> bool:
    return restore(_conn(client_slug), "subscriptions", "id", sub_id)


def purge_subscription(client_slug: str, sub_id: int) -> tuple[bool, str]:
    """Purge if no capacities depend on this subscription."""
    conn = _conn(client_slug)
    if has_dependents(conn, "capacities", "subscription_ref", sub_id):
        return False, "Cannot purge: capacities still reference this subscription."
    return purge(conn, "subscriptions", "id", sub_id, "subscription"), ""
