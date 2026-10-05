"""atlas-backend — the official Python backend SDK for Atlas.

A typed client over the ``sk_`` Backend API (BAPI), the Python peer of the
TypeScript ``@atlas/backend`` SDK.

    from atlas_backend import AtlasClient, AtlasError

    atlas = AtlasClient("sk_live_...")
    user = atlas.users.create({"email_address": "ada@example.com"})
    for org in paginate(atlas.organizations.list):
        print(org["name"])
"""

from __future__ import annotations

from ._client import AsyncAtlasClient, AtlasClient
from ._errors import AtlasError, ErrorItem
from ._handshake import (
    HandshakeParams,
    HandshakeSession,
    PKCEPair,
    aredeem_handshake,
    create_pkce_pair,
    read_handshake_params,
    redeem_handshake,
)
from ._pagination import acollect, aiterate, collect, paginate
from ._transport import DEFAULT_BASE_URL
from ._types import CursorPage, DeletedObject, ListPage, Metadata
from ._verify import (
    CLOCK_SKEW_SECONDS,
    DEFAULT_TTL_MS,
    REFETCH_INTERVAL_MS,
    ApiKeyVerification,
    ApiKeyVerifier,
    AtlasBackend,
    AtlasUser,
    JwksCache,
    SessionClaims,
    VerificationError,
)

__version__ = "0.1.0"

__all__ = [
    "AtlasClient",
    "AsyncAtlasClient",
    "AtlasError",
    "ErrorItem",
    "DEFAULT_BASE_URL",
    "paginate",
    "collect",
    "aiterate",
    "acollect",
    "CursorPage",
    "ListPage",
    "DeletedObject",
    "Metadata",
    "HandshakeSession",
    "HandshakeParams",
    "PKCEPair",
    "create_pkce_pair",
    "redeem_handshake",
    "aredeem_handshake",
    "read_handshake_params",
    "AtlasBackend",
    "SessionClaims",
    "AtlasUser",
    "VerificationError",
    "JwksCache",
    "ApiKeyVerifier",
    "ApiKeyVerification",
    "CLOCK_SKEW_SECONDS",
    "REFETCH_INTERVAL_MS",
    "DEFAULT_TTL_MS",
    "__version__",
]
