import logging
import sqlite3

from friction_dissolved.db.engine import db_manager
from azure.models import Tenant, TenantCreate, TenantUpdate
from friction_dissolved.core.soft_delete import (
    has_dependents,
    purge,
    restore,
    soft_delete,
)

logger = logging.getLogger(__name__)

_ALL_COLS = (
    "id, name, tenant_id, primary_domain, custom_domain, "
    "admin_contact, notes, created_at, updated_at"
)


def _conn(client_slug: str) -> sqlite3.Connection:
    return db_manager.get_client_connection(client_slug)


def list_tenants(client_slug: str, include_deleted: bool = False) -> list[Tenant]:
    where = "" if include_deleted else "WHERE deleted_at IS NULL"
    rows = _conn(client_slug).execute(
        f"SELECT {_ALL_COLS} FROM tenants {where} ORDER BY name"
    ).fetchall()
    return [Tenant(**dict(r)) for r in rows]


def get_tenant(client_slug: str, tenant_id: int) -> Tenant | None:
    row = _conn(client_slug).execute(
        f"SELECT {_ALL_COLS} FROM tenants WHERE id = ? AND deleted_at IS NULL",
        (tenant_id,),
    ).fetchone()
    if row is None:
        return None
    return Tenant(**dict(row))


def create_tenant(client_slug: str, data: TenantCreate) -> Tenant:
    conn = _conn(client_slug)
    cursor = conn.execute(
        "INSERT INTO tenants "
        "(name, tenant_id, primary_domain, custom_domain, admin_contact, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            data.name, data.tenant_id, data.primary_domain,
            data.custom_domain, data.admin_contact, data.notes,
        ),
    )
    conn.commit()
    logger.info("Created tenant '%s' for client %s", data.name, client_slug)

    tenant = get_tenant(client_slug, cursor.lastrowid)
    if tenant is None:
        raise RuntimeError("Tenant was created but could not be retrieved")
    return tenant


def update_tenant(
    client_slug: str, tenant_id: int, data: TenantUpdate
) -> Tenant | None:
    existing = get_tenant(client_slug, tenant_id)
    if existing is None:
        return None

    updates: list[str] = []
    params: list[str | int] = []
    field_map = {
        "name": data.name,
        "tenant_id": data.tenant_id,
        "primary_domain": data.primary_domain,
        "custom_domain": data.custom_domain,
        "admin_contact": data.admin_contact,
        "notes": data.notes,
    }
    for col, val in field_map.items():
        if val is not None:
            updates.append(f"{col} = ?")
            params.append(val.strip() if isinstance(val, str) else val)
    if not updates:
        return existing

    updates.append("updated_at = datetime('now')")
    params.append(tenant_id)

    conn = _conn(client_slug)
    conn.execute(
        f"UPDATE tenants SET {', '.join(updates)} WHERE id = ?",
        params,
    )
    conn.commit()
    logger.info("Updated tenant %d for client %s", tenant_id, client_slug)
    return get_tenant(client_slug, tenant_id)


def delete_tenant(client_slug: str, tenant_id: int) -> bool:
    if get_tenant(client_slug, tenant_id) is None:
        return False
    return soft_delete(_conn(client_slug), "tenants", "id", tenant_id)


def restore_tenant(client_slug: str, tenant_id: int) -> bool:
    return restore(_conn(client_slug), "tenants", "id", tenant_id)


def purge_tenant(client_slug: str, tenant_id: int) -> tuple[bool, str]:
    """Purge if no subscriptions depend on this tenant."""
    conn = _conn(client_slug)
    if has_dependents(conn, "subscriptions", "tenant_id", tenant_id):
        return False, "Cannot purge: subscriptions still reference this tenant."
    return purge(conn, "tenants", "id", tenant_id, "tenant"), ""
