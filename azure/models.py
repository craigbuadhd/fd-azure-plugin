from datetime import datetime

from pydantic import BaseModel, field_validator

from friction_dissolved.core.azure_regions import AZURE_REGIONS


# -- Tenants -------------------------------------------------------------------


class TenantCreate(BaseModel):
    name: str
    tenant_id: str = ""
    primary_domain: str = ""
    custom_domain: str = ""
    admin_contact: str = ""
    notes: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v


class TenantUpdate(BaseModel):
    name: str | None = None
    tenant_id: str | None = None
    primary_domain: str | None = None
    custom_domain: str | None = None
    admin_contact: str | None = None
    notes: str | None = None


class Tenant(BaseModel):
    id: int
    name: str
    tenant_id: str
    primary_domain: str
    custom_domain: str
    admin_contact: str
    notes: str
    created_at: datetime
    updated_at: datetime


# -- Subscriptions -------------------------------------------------------------


OFFER_TYPES = [
    "CSP",
    "Enterprise Agreement",
    "Free Trial",
    "MSDN / Visual Studio",
    "Pay-As-You-Go",
    "Sponsorship",
    "Other",
]


class SubscriptionCreate(BaseModel):
    name: str
    subscription_id: str = ""
    tenant_id: int
    offer_type: str = ""
    owner: str = ""
    notes: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v


class SubscriptionUpdate(BaseModel):
    name: str | None = None
    subscription_id: str | None = None
    tenant_id: int | None = None
    offer_type: str | None = None
    owner: str | None = None
    status: str | None = None
    notes: str | None = None


class Subscription(BaseModel):
    id: int
    name: str
    subscription_id: str
    tenant_id: int | None
    offer_type: str
    owner: str
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime


# -- Resource Groups -----------------------------------------------------------


class ResourceGroupCreate(BaseModel):
    name: str
    subscription_id: int | None = None
    location: str = ""
    purpose: str = ""
    tags: str = ""
    notes: str = ""

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        v = v.strip()
        if v and v not in AZURE_REGIONS:
            raise ValueError("Location not recognised. Must be a valid Azure region.")
        return v


class ResourceGroupUpdate(BaseModel):
    name: str | None = None
    subscription_id: int | None = None
    location: str | None = None
    purpose: str | None = None
    tags: str | None = None
    status: str | None = None
    notes: str | None = None


class ResourceGroup(BaseModel):
    id: int
    name: str
    subscription_id: int | None
    location: str
    purpose: str
    tags: str
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime
