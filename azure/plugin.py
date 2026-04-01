"""Azure plugin -- tenants, subscriptions, resource groups."""

from pathlib import Path

from fastapi import APIRouter

from friction_dissolved.core.plugin_spec import (
    ArchiveConfig,
    BulkDeleteConfig,
    CascadeRule,
    PluginSpec,
    PurgeCheck,
)
from azure.tools import TOOLS
from azure.tenants_router import router as tenants_api
from azure.subscriptions_router import router as subs_api
from azure.resource_groups_router import router as rg_api
from azure.tenants_pages import router as tenants_pages
from azure.subscriptions_pages import router as subs_pages
from azure.resource_groups_pages import router as rg_pages

_DIR = Path(__file__).resolve().parent

api_router = APIRouter()
api_router.include_router(tenants_api)
api_router.include_router(subs_api)
api_router.include_router(rg_api)

page_router = APIRouter()
page_router.include_router(tenants_pages)
page_router.include_router(subs_pages)
page_router.include_router(rg_pages)


def _lazy_tenant_svc():
    from azure import tenants_service
    return tenants_service


def _lazy_sub_svc():
    from azure import subscriptions_service
    return subscriptions_service


def _lazy_rg_svc():
    from azure import resource_groups_service
    return resource_groups_service


spec = PluginSpec(
    name="azure",
    version="0.1.0",
    description="Azure infrastructure: tenants, subscriptions, resource groups",
    hard_deps=["consulting"],
    api_router=api_router,
    page_router=page_router,
    client_migrations_dir=str(_DIR / "migrations" / "client"),
    tools=TOOLS,
    cascade_rules=[
        CascadeRule(
            source_table="tenants",
            target_table="subscriptions",
            fk_column="tenant_id",
        ),
        CascadeRule(
            source_table="subscriptions",
            target_table="resource_groups",
            fk_column="subscription_id",
        ),
        CascadeRule(
            source_table="subscriptions",
            target_table="capacities",
            fk_column="subscription_ref",
        ),
    ],
    purge_checks=[
        PurgeCheck(
            table="tenants",
            fk_table="subscriptions",
            fk_column="tenant_id",
            message="Cannot purge: subscriptions still reference this tenant.",
        ),
        PurgeCheck(
            table="subscriptions",
            fk_table="resource_groups",
            fk_column="subscription_id",
            message="Cannot purge: resource groups still reference this subscription.",
        ),
        PurgeCheck(
            table="subscriptions",
            fk_table="capacities",
            fk_column="subscription_ref",
            message="Cannot purge: capacities still reference this subscription.",
        ),
        PurgeCheck(
            table="resource_groups",
            fk_table="capacities",
            fk_column="resource_group_ref",
            message="Cannot purge: capacities still reference this resource group.",
        ),
    ],
    archive_configs=[
        ArchiveConfig(
            entity_type="tenants",
            label="Tenant",
            list_deleted=lambda slug: _lazy_tenant_svc().list_tenants(
                slug, include_deleted=True
            ),
            list_active=lambda slug: _lazy_tenant_svc().list_tenants(slug),
            restore=lambda slug, id: _lazy_tenant_svc().restore_tenant(slug, id),
            purge=lambda slug, id: _lazy_tenant_svc().purge_tenant(slug, id),
        ),
        ArchiveConfig(
            entity_type="subscriptions",
            label="Subscription",
            list_deleted=lambda slug: _lazy_sub_svc().list_subscriptions(
                slug, include_deleted=True
            ),
            list_active=lambda slug: _lazy_sub_svc().list_subscriptions(slug),
            restore=lambda slug, id: _lazy_sub_svc().restore_subscription(slug, id),
            purge=lambda slug, id: _lazy_sub_svc().purge_subscription(slug, id),
        ),
        ArchiveConfig(
            entity_type="resource_groups",
            label="Resource Group",
            list_deleted=lambda slug: _lazy_rg_svc().list_resource_groups(
                slug, include_deleted=True
            ),
            list_active=lambda slug: _lazy_rg_svc().list_resource_groups(slug),
            restore=lambda slug, id: _lazy_rg_svc().restore_resource_group(slug, id),
            purge=lambda slug, id: _lazy_rg_svc().purge_resource_group(slug, id),
        ),
    ],
)
