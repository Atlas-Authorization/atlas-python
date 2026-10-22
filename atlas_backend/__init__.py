"""atlas-backend — the official Python backend SDK for Atlas.

A typed client over the ``sk_`` Backend API (BAPI) and the ``psk_`` Platform
API, the Python peer of the TypeScript ``@atlas/backend`` SDK.

    from atlas_backend import AtlasClient, AtlasError

    atlas = AtlasClient("sk_live_...")
    user = atlas.users.create({"email_address": "ada@example.com"})
    for org in paginate(atlas.organizations.list):
        print(org["name"])
"""

from __future__ import annotations

from . import models
from ._client import (
    AsyncAtlasClient,
    AsyncAtlasPlatformClient,
    AtlasClient,
    AtlasPlatformClient,
)
from ._errors import AtlasError, ErrorCode, ErrorItem
from ._handshake import (
    HandshakeParams,
    HandshakeSession,
    PKCEPair,
    aredeem_handshake,
    create_pkce_pair,
    read_handshake_params,
    redeem_handshake,
)
from ._logout import (
    BACKCHANNEL_LOGOUT_EVENT,
    LogoutTokenClaims,
    LogoutTokenVerifier,
    logout_token_from_form,
)
from ._pagination import acollect, aiterate, collect, paginate
from ._transport import DEFAULT_BASE_URL, UnknownFieldsHook
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

from ._referrals import (
    REFERRAL_CONNECTION_TEST_REF,
    REFERRAL_OP_ENDPOINTS,
    REFERRAL_PROTOCOL_USER_AGENT,
    REFERRAL_PROTOCOL_VERSION,
    REFERRAL_PROTOCOL_VERSION_HEADER,
    REFERRAL_SIGNAL_TYPES,
    REFERRAL_UPDATED_EVENT,
    ReferralAliasPayload,
    ReferralContext,
    ReferralErasePayload,
    ReferralExportPayload,
    ReferralOp,
    ReferralPartnerPayload,
    ReferralPingPayload,
    ReferralPingResponse,
    ReferralRiskVerdict,
    ReferralSignalPayload,
    ReferralSignupPayload,
    ReferralSignupResponse,
    ReferralUpdatedEvent,
    ReferralUserPayload,
    ReferralVerification,
    SignedReferralEvent,
    referral_op_for_path,
    sign_referral_updated_event,
    verify_referral_request,
)
from ._webhooks import WebhookVerification, verify_webhook

__version__ = "0.11.0"

__all__ = [
    "AtlasClient",
    "AsyncAtlasClient",
    "AtlasPlatformClient",
    "AsyncAtlasPlatformClient",
    "AtlasError",
    "ErrorCode",
    "ErrorItem",
    "DEFAULT_BASE_URL",
    "UnknownFieldsHook",
    "models",
    "LogoutTokenVerifier",
    "LogoutTokenClaims",
    "logout_token_from_form",
    "BACKCHANNEL_LOGOUT_EVENT",
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
    "verify_webhook",
    "WebhookVerification",
    "verify_referral_request",
    "referral_op_for_path",
    "ReferralOp",
    "ReferralExportPayload",
    "REFERRAL_OP_ENDPOINTS",
    "ReferralVerification",
    "ReferralContext",
    "ReferralRiskVerdict",
    "ReferralSignupPayload",
    "ReferralSignupResponse",
    "ReferralErasePayload",
    "ReferralPartnerPayload",
    "ReferralSignalPayload",
    "REFERRAL_CONNECTION_TEST_REF",
    "REFERRAL_PROTOCOL_USER_AGENT",
    "REFERRAL_SIGNAL_TYPES",
    "REFERRAL_PROTOCOL_VERSION",
    "REFERRAL_PROTOCOL_VERSION_HEADER",
    "ReferralAliasPayload",
    "ReferralUserPayload",
    "ReferralPingPayload",
    "ReferralPingResponse",
    "REFERRAL_UPDATED_EVENT",
    "ReferralUpdatedEvent",
    "SignedReferralEvent",
    "sign_referral_updated_event",
    "__version__",
]
