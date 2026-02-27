"""Organization management API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import require_super_admin
from app.common.exceptions import AppException
from app.common.service import get_org_service
from app.domain.models.user import User
from app.domain.schemas.organization import (
    CreateOrganizationRequest,
    OrganizationDetailResponse,
    OrganizationResponse,
    UpdateOrganizationRequest,
)
from app.services.organization.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


def _to_org_response(organization) -> OrganizationResponse:
    """Map domain Organization to OrganizationResponse."""
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        description=organization.description,
        is_active=organization.is_active,
        created_by=organization.created_by,
        created_at=organization.created_at,
        updated_at=organization.updated_at,
    )


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    request: CreateOrganizationRequest,
    current_user: User = Depends(require_super_admin),
    org_service: OrganizationService = Depends(get_org_service),
) -> OrganizationResponse:
    """Create organization (Super Admin only)."""
    organization = await org_service.create_organization(
        name=request.name,
        description=request.description,
        created_by=current_user.id,
    )
    return _to_org_response(organization)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    is_active: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(require_super_admin),
    org_service: OrganizationService = Depends(get_org_service),
) -> list[OrganizationResponse]:
    """List organizations (Super Admin only)."""
    organizations = await org_service.list_organizations(
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return [_to_org_response(org) for org in organizations]


@router.get("/{org_id}", response_model=OrganizationDetailResponse)
async def get_organization(
    org_id: str,
    current_user: User = Depends(require_super_admin),
    org_service: OrganizationService = Depends(get_org_service),
) -> OrganizationDetailResponse:
    """Get organization details (Super Admin only)."""
    organization = await org_service.get_organization(org_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    members = await org_service.get_organization_members(
        organization_id=org_id,
        actor_user=current_user,
    )

    return OrganizationDetailResponse(
        organization=_to_org_response(organization),
        members=members,
        member_count=len(members),
    )


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    request: UpdateOrganizationRequest,
    _: User = Depends(require_super_admin),
    org_service: OrganizationService = Depends(get_org_service),
) -> OrganizationResponse:
    """Update organization details (Super Admin only)."""
    updated = await org_service.update_organization(
        org_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return _to_org_response(updated)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_organization(
    org_id: str,
    _: User = Depends(require_super_admin),
    org_service: OrganizationService = Depends(get_org_service),
) -> None:
    """Deactivate organization (Super Admin only)."""
    try:
        success = await org_service.deactivate_organization(org_id)
    except AppException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
