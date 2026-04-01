"""Chat tools for the azure plugin -- tenants, subscriptions, resource groups."""

import json

from friction_dissolved.core.plugin_spec import ToolDef


def _serialize(obj: object) -> str:
    """Serialize a Pydantic model or list of models to JSON string."""
    if isinstance(obj, list):
        return json.dumps([item.model_dump() for item in obj], default=str)
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump(), default=str)
    return json.dumps(obj, default=str)


# ── Tenant executors ─────────────────────────────────────────────────────────


def _list_tenants(args: dict) -> str:
    from azure import tenants_service
    return _serialize(tenants_service.list_tenants(args["client_slug"]))


def _create_tenant(args: dict) -> str:
    from azure import tenants_service
    from azure.models import TenantCreate
    data = TenantCreate(
        name=args["name"],
        tenant_id=args.get("tenant_id", ""),
        primary_domain=args.get("primary_domain", ""),
        custom_domain=args.get("custom_domain", ""),
        admin_contact=args.get("admin_contact", ""),
    )
    return _serialize(tenants_service.create_tenant(args["client_slug"], data))


# ── Subscription executors ───────────────────────────────────────────────────


def _list_subscriptions(args: dict) -> str:
    from azure import subscriptions_service
    return _serialize(subscriptions_service.list_subscriptions(args["client_slug"]))


def _create_subscription(args: dict) -> str:
    from azure import subscriptions_service
    from azure.models import SubscriptionCreate
    data = SubscriptionCreate(
        name=args["name"],
        subscription_id=args.get("subscription_id", ""),
        tenant_id=args["tenant_id"],
        offer_type=args.get("offer_type", ""),
        owner=args.get("owner", ""),
    )
    return _serialize(
        subscriptions_service.create_subscription(args["client_slug"], data)
    )


# ── Resource group executors ─────────────────────────────────────────────────


def _list_resource_groups(args: dict) -> str:
    from azure import resource_groups_service
    return _serialize(
        resource_groups_service.list_resource_groups(args["client_slug"])
    )


def _create_resource_group(args: dict) -> str:
    from azure import resource_groups_service
    from azure.models import ResourceGroupCreate
    data = ResourceGroupCreate(
        name=args["name"],
        subscription_id=args.get("subscription_id"),
        location=args.get("location", ""),
        purpose=args.get("purpose", ""),
        tags=args.get("tags", ""),
    )
    return _serialize(
        resource_groups_service.create_resource_group(args["client_slug"], data)
    )


# ── Combined TOOLS list ─────────────────────────────────────────────────────


TOOLS: list[ToolDef] = [
    ToolDef(
        spec={
            "type": "function",
            "function": {
                "name": "list_tenants",
                "description": "List tenants for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_slug": {"type": "string"},
                    },
                    "required": ["client_slug"],
                },
            },
        },
        execute=_list_tenants,
    ),
    ToolDef(
        spec={
            "type": "function",
            "function": {
                "name": "create_tenant",
                "description": "Create a tenant for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_slug": {"type": "string"},
                        "name": {"type": "string"},
                        "tenant_id": {
                            "type": "string",
                            "description": "Entra ID tenant GUID",
                        },
                        "primary_domain": {"type": "string"},
                        "custom_domain": {"type": "string"},
                        "admin_contact": {"type": "string"},
                    },
                    "required": ["client_slug", "name"],
                },
            },
        },
        execute=_create_tenant,
    ),
    ToolDef(
        spec={
            "type": "function",
            "function": {
                "name": "list_subscriptions",
                "description": "List subscriptions for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_slug": {"type": "string"},
                    },
                    "required": ["client_slug"],
                },
            },
        },
        execute=_list_subscriptions,
    ),
    ToolDef(
        spec={
            "type": "function",
            "function": {
                "name": "create_subscription",
                "description": "Create a subscription for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_slug": {"type": "string"},
                        "name": {"type": "string"},
                        "subscription_id": {
                            "type": "string",
                            "description": "Azure subscription GUID",
                        },
                        "tenant_id": {
                            "type": "integer",
                            "description": "ID of the tenant (from list_tenants)",
                        },
                        "offer_type": {"type": "string"},
                        "owner": {"type": "string"},
                    },
                    "required": ["client_slug", "name", "tenant_id"],
                },
            },
        },
        execute=_create_subscription,
    ),
    ToolDef(
        spec={
            "type": "function",
            "function": {
                "name": "list_resource_groups",
                "description": "List resource groups for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_slug": {"type": "string"},
                    },
                    "required": ["client_slug"],
                },
            },
        },
        execute=_list_resource_groups,
    ),
    ToolDef(
        spec={
            "type": "function",
            "function": {
                "name": "create_resource_group",
                "description": "Create a resource group for a client",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "client_slug": {"type": "string"},
                        "name": {"type": "string"},
                        "subscription_id": {
                            "type": "integer",
                            "description": "ID of the subscription",
                        },
                        "location": {
                            "type": "string",
                            "description": "Azure region",
                        },
                        "purpose": {"type": "string"},
                        "tags": {"type": "string"},
                    },
                    "required": ["client_slug", "name"],
                },
            },
        },
        execute=_create_resource_group,
    ),
]
