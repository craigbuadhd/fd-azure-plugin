import logging
import sqlite3

from friction_dissolved.db.engine import db_manager
from azure.models import (
    ResourceGroup,
    ResourceGroupCreate,
    ResourceGroupUpdate,
)
from friction_dissolved.core.soft_delete import (
    has_dependents,
    purge,
    restore,
    soft_delete,
)

logger = logging.getLogger(__name__)

_ALL_COLS = (
    "id, name, subscription_id, location, purpose, tags, "
    "status, notes, created_at, updated_at"
)


def _conn(client_slug: str) -> sqlite3.Connection:
    return db_manager.get_client_connection(client_slug)


def list_resource_groups(
    client_slug: str, include_deleted: bool = False
) -> list[ResourceGroup]:
    where = "" if include_deleted else "WHERE deleted_at IS NULL"
    rows = _conn(client_slug).execute(
        f"SELECT {_ALL_COLS} FROM resource_groups {where} ORDER BY name"
    ).fetchall()
    return [ResourceGroup(**dict(r)) for r in rows]


def get_resource_group(client_slug: str, rg_id: int) -> ResourceGroup | None:
    row = _conn(client_slug).execute(
        f"SELECT {_ALL_COLS} FROM resource_groups WHERE id = ? AND deleted_at IS NULL",
        (rg_id,),
    ).fetchone()
    if row is None:
        return None
    return ResourceGroup(**dict(row))


def create_resource_group(client_slug: str, data: ResourceGroupCreate) -> ResourceGroup:
    conn = _conn(client_slug)

    if data.subscription_id is not None:
        sub = conn.execute(
            "SELECT id FROM subscriptions WHERE id = ? AND deleted_at IS NULL",
            (data.subscription_id,),
        ).fetchone()
        if sub is None:
            raise ValueError(f"Subscription not found: {data.subscription_id}")

    cursor = conn.execute(
        "INSERT INTO resource_groups "
        "(name, subscription_id, location, purpose, tags, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.name, data.subscription_id, data.location,
            data.purpose, data.tags, data.notes,
        ),
    )
    conn.commit()
    logger.info("Created resource group '%s' for client %s", data.name, client_slug)

    rg = get_resource_group(client_slug, cursor.lastrowid)
    if rg is None:
        raise RuntimeError("Resource group was created but could not be retrieved")
    return rg


def update_resource_group(
    client_slug: str, rg_id: int, data: ResourceGroupUpdate
) -> ResourceGroup | None:
    existing = get_resource_group(client_slug, rg_id)
    if existing is None:
        return None

    conn = _conn(client_slug)
    updates: list[str] = []
    params: list[str | int | None] = []

    if data.subscription_id is not None:
        sub = conn.execute(
            "SELECT id FROM subscriptions WHERE id = ? AND deleted_at IS NULL",
            (data.subscription_id,),
        ).fetchone()
        if sub is None:
            raise ValueError(f"Subscription not found: {data.subscription_id}")
        updates.append("subscription_id = ?")
        params.append(data.subscription_id)

    field_map: dict[str, str | None] = {
        "name": data.name,
        "location": data.location,
        "purpose": data.purpose,
        "tags": data.tags,
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
    params.append(rg_id)

    conn.execute(
        f"UPDATE resource_groups SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()
    logger.info("Updated resource group %d for client %s", rg_id, client_slug)
    return get_resource_group(client_slug, rg_id)


def delete_resource_group(client_slug: str, rg_id: int) -> bool:
    if get_resource_group(client_slug, rg_id) is None:
        return False
    return soft_delete(_conn(client_slug), "resource_groups", "id", rg_id)


def restore_resource_group(client_slug: str, rg_id: int) -> bool:
    return restore(_conn(client_slug), "resource_groups", "id", rg_id)


def purge_resource_group(client_slug: str, rg_id: int) -> tuple[bool, str]:
    conn = _conn(client_slug)
    if has_dependents(conn, "capacities", "resource_group_ref", rg_id):
        return False, "Cannot purge: capacities still reference this resource group."
    return purge(conn, "resource_groups", "id", rg_id, "resource_group"), ""
