"""Account related models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any

from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.types import Discriminator


@dataclass(frozen=True, slots=True)
class FullAccount(DataClassORJSONMixin):
    """Full account information."""

    account_id: str
    name: OwnerName
    email: str
    email_verified: bool
    disabled: bool
    locale: str
    referral_link: str
    is_paired: bool
    account_type: AccountType
    root_info: dict[str, str]
    profile_photo_url: str | None = None
    country: str | None = None
    team: dict[str, str] | None = None
    team_member_id: str | None = None

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:
        """Pre deserialize hook."""
        if "account_type" in d:
            d["account_type"] = d["account_type"][".tag"]
        return d


class AccountType(StrEnum):
    """Account type."""

    BASIC = "basic"
    PRO = "pro"
    BUSINESS = "business"


@dataclass(frozen=True, slots=True)
class OwnerName:
    """Name of the owner of the account."""

    given_name: str
    surname: str
    familiar_name: str
    display_name: str
    abbreviated_name: str


@dataclass(frozen=True, slots=True)
class SpaceUsage(DataClassORJSONMixin):
    """Space usage information response."""

    allocation: Annotated[
        IndividualSpaceAllocation | TeamSpaceAllocation,
        Discriminator(include_supertypes=True, variant_tagger_fn=lambda x: x.tag),
    ]
    used: int


@dataclass(frozen=True, slots=True)
class IndividualSpaceAllocation:
    """Individual space allocation."""

    tag = "individual"
    allocated: int


@dataclass(frozen=True, slots=True)
class TeamSpaceAllocation:
    """Team space allocation."""

    tag = "team"
    used: int
    user_within_team_space_allocated: int
    user_within_team_space_used_cached: int
    user_within_team_space_limit_type: dict[str, str]
