"""The single error type every Backend API call raises on a non-2xx.

Atlas answers a failed BAPI call with the §9.1 envelope::

    { "errors": [ { "code", "message", "param?", "meta?" } ] }

``code`` is the stable, machine-readable part of that contract — integrators
branch on it (``LAST_ADMIN``, ``NOT_FOUND``, ``SCOPE_MISSING``, ...) — so it is
surfaced first-class here rather than buried in a parsed body. The raw
``errors`` list and the HTTP ``status`` are both kept so a caller can inspect
``param``/``meta`` (e.g. a rate limit's ``retry_after``) when they need to.
"""

from __future__ import annotations

from typing import Any, TypedDict


class ErrorCode:
    """The stable error codes the API returns in ``errors[].code``.

    Compare against these instead of string literals::

        except AtlasError as err:
            if err.has_code(ErrorCode.UNKNOWN_FIELD):
                ...

    New codes may appear over time; treat an unknown code as a generic failure.
    """

    VALIDATION_FAILED = "VALIDATION_FAILED"
    #: A strict write named a body field the endpoint does not accept.
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    #: An idempotency key was reused with a different request (e.g. another unit or amount).
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    #: A usage debit would exceed an API key's spend cap. ``api_keys.record_usage``
    #: reports it as ``code`` on the debit (``allowed`` is ``False``), not as an error.
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    #: The session has ended (signed out, timed out from inactivity, or past its
    #: absolute expiry) and cannot be kept alive.
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_IDLE_EXPIRED = "SESSION_IDLE_EXPIRED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    #: The key is unknown, revoked or malformed.
    INVALID_KEY = "INVALID_KEY"
    #: The key is valid but for another surface (e.g. a platform key on an instance route).
    WRONG_KEY_SURFACE = "WRONG_KEY_SURFACE"
    FORBIDDEN = "FORBIDDEN"
    SCOPE_MISSING = "SCOPE_MISSING"
    IDENTIFIER_EXISTS = "IDENTIFIER_EXISTS"
    IDENTIFIER_NOT_FOUND = "IDENTIFIER_NOT_FOUND"
    VERIFICATION_EXPIRED = "VERIFICATION_EXPIRED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"
    TOO_MANY_ATTEMPTS = "TOO_MANY_ATTEMPTS"
    PASSWORD_BREACHED = "PASSWORD_BREACHED"
    PASSWORD_POLICY = "PASSWORD_POLICY"
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"
    LOCKED = "LOCKED"
    BANNED = "BANNED"
    DELETED = "DELETED"
    MFA_REQUIRED = "MFA_REQUIRED"
    MFA_ALREADY_ENROLLED = "MFA_ALREADY_ENROLLED"
    MFA_NOT_ENROLLED = "MFA_NOT_ENROLLED"
    STEP_UP_REQUIRED = "STEP_UP_REQUIRED"
    LAST_EMAIL = "LAST_EMAIL"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    TOKEN_REUSE_DETECTED = "TOKEN_REUSE_DETECTED"
    SESSION_REVOKED = "SESSION_REVOKED"
    SESSION_IDLE_EXPIRED = "SESSION_IDLE_EXPIRED"
    REFRESH_REUSE_DETECTED = "REFRESH_REUSE_DETECTED"
    OAUTH_STATE_INVALID = "OAUTH_STATE_INVALID"
    PROVIDER_TOKEN_UNAVAILABLE = "PROVIDER_TOKEN_UNAVAILABLE"
    OAUTH_EXCHANGE_FAILED = "OAUTH_EXCHANGE_FAILED"
    LAST_AUTH_METHOD = "LAST_AUTH_METHOD"
    IDENTITY_ALREADY_LINKED = "IDENTITY_ALREADY_LINKED"
    ACCOUNT_EXISTS = "ACCOUNT_EXISTS"
    WALLET_GATE_UNMET = "WALLET_GATE_UNMET"
    LAST_ADMIN = "LAST_ADMIN"
    ALREADY_MEMBER = "ALREADY_MEMBER"
    ROLE_IN_USE = "ROLE_IN_USE"
    #: A billing plan cannot be deleted while subscriptions use it.
    PLAN_IN_USE = "PLAN_IN_USE"
    CONFLICT = "CONFLICT"
    MEMBERSHIP_LIMIT_REACHED = "MEMBERSHIP_LIMIT_REACHED"
    STRATEGY_DISABLED = "STRATEGY_DISABLED"
    SIGN_UP_RESTRICTED = "SIGN_UP_RESTRICTED"
    WAITLISTED = "WAITLISTED"
    IDENTIFIER_NOT_ALLOWED = "IDENTIFIER_NOT_ALLOWED"
    DISPOSABLE_EMAIL_BLOCKED = "DISPOSABLE_EMAIL_BLOCKED"
    SMS_REGION_BLOCKED = "SMS_REGION_BLOCKED"
    AUTHENTICATOR_NOT_ALLOWED = "AUTHENTICATOR_NOT_ALLOWED"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    CAPTCHA_FAILED = "CAPTCHA_FAILED"
    CHALLENGE_UNAVAILABLE = "CHALLENGE_UNAVAILABLE"
    READ_ONLY_MODE = "READ_ONLY_MODE"
    SIGN_UPS_DISABLED = "SIGN_UPS_DISABLED"
    SIGN_INS_DISABLED = "SIGN_INS_DISABLED"
    PROVIDER_DISABLED = "PROVIDER_DISABLED"
    PROVIDER_SIGN_UP_DISABLED = "PROVIDER_SIGN_UP_DISABLED"
    PROVIDER_SIGN_IN_DISABLED = "PROVIDER_SIGN_IN_DISABLED"
    IP_NOT_ALLOWED = "IP_NOT_ALLOWED"
    SSO_REQUIRED = "SSO_REQUIRED"
    ORG_METHOD_NOT_ALLOWED = "ORG_METHOD_NOT_ALLOWED"
    SETTINGS_INVALID = "SETTINGS_INVALID"
    ACTION_BLOCKED = "ACTION_BLOCKED"
    HIGH_RISK_BLOCKED = "HIGH_RISK_BLOCKED"
    ENROLMENT_TOKEN_INVALID = "ENROLMENT_TOKEN_INVALID"
    ENROLMENT_TOKEN_EXPIRED = "ENROLMENT_TOKEN_EXPIRED"
    ENROLMENT_TOKEN_EXHAUSTED = "ENROLMENT_TOKEN_EXHAUSTED"
    #: The instance has no working email provider for this send.
    EMAIL_DELIVERY_NOT_CONFIGURED = "EMAIL_DELIVERY_NOT_CONFIGURED"
    #: Turning this setting on needs an email provider configured first.
    EMAIL_PROVIDER_REQUIRED = "EMAIL_PROVIDER_REQUIRED"
    #: Removing the email provider was refused: email-dependent features are on
    #: (listed in ``meta.features``) and nothing else would deliver email. Retry with
    #: ``messaging_providers.delete("email", force=True)`` to remove it anyway.
    EMAIL_PROVIDER_IN_USE = "EMAIL_PROVIDER_IN_USE"
    INTERNAL = "INTERNAL"


class ErrorItem(TypedDict, total=False):
    """One entry of the BAPI error envelope."""

    code: str
    message: str
    param: str
    meta: dict[str, Any]


class AtlasError(Exception):
    """Raised on any non-2xx response from the Backend API.

    Carries the HTTP ``status`` and the full parsed ``errors`` envelope. Branch
    on :attr:`code` (the first error's stable code) or use :meth:`has_code`.
    """

    status: int
    errors: list[ErrorItem]

    def __init__(
        self,
        status: int,
        errors: list[ErrorItem],
        message: str | None = None,
    ) -> None:
        first_message = errors[0].get("message") if errors else None
        super().__init__(
            message or first_message or f"Atlas API request failed with status {status}"
        )
        self.status = status
        self.errors = errors

    @property
    def code(self) -> str | None:
        """The first error's stable code, the field callers branch on most."""
        if not self.errors:
            return None
        return self.errors[0].get("code")

    def has_code(self, code: str) -> bool:
        """True when any error in the envelope carries the given stable code."""
        return any(e.get("code") == code for e in self.errors)
