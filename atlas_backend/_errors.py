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
    #: The body set a field that is not writable on this endpoint (``param`` names it; the
    #: message names the call that changes it).
    READ_ONLY_FIELD = "READ_ONLY_FIELD"
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
    #: The key is valid but lacks a scope the call needs (``meta.required_scope``). Older
    #: servers sent ``SCOPE_MISSING``; :attr:`AtlasError.is_insufficient_scope` accepts both.
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    #: The former spelling of ``INSUFFICIENT_SCOPE``, still accepted.
    SCOPE_MISSING = "SCOPE_MISSING"
    #: A key locked to ``allowed_origins`` was used from another browser origin (403).
    ORIGIN_NOT_ALLOWED = "ORIGIN_NOT_ALLOWED"
    #: No such route; ``did_you_mean`` lists close matches, ``allowed_methods`` the verbs the
    #: path does take.
    ROUTE_NOT_FOUND = "ROUTE_NOT_FOUND"
    #: The call needs a live (production) instance.
    NOT_A_LIVE_INSTANCE = "NOT_A_LIVE_INSTANCE"
    #: The call works on a test-mode instance only.
    TEST_MODE_ONLY = "TEST_MODE_ONLY"
    TESTING_UNAVAILABLE = "TESTING_UNAVAILABLE"
    #: Partner links are not available for this partner or deployment.
    PARTNER_LINK_UNAVAILABLE = "PARTNER_LINK_UNAVAILABLE"
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
    #: Captcha is bring-your-own-keys: turning it on (or switching provider) without a
    #: stored site key and secret for that provider is refused.
    CAPTCHA_KEYS_REQUIRED = "CAPTCHA_KEYS_REQUIRED"
    #: Removing a captcha key a live flow uses was refused (``meta.flows``). Retry with
    #: ``delete_captcha_secret(force=True)`` to remove it and turn those flows off.
    CAPTCHA_IN_USE = "CAPTCHA_IN_USE"
    #: The development email sender is not available on a production instance (409).
    DEVELOPMENT_EMAIL_NOT_ALLOWED = "DEVELOPMENT_EMAIL_NOT_ALLOWED"
    #: The development email sender is not available on this deployment (503).
    DEVELOPMENT_EMAIL_UNAVAILABLE = "DEVELOPMENT_EMAIL_UNAVAILABLE"
    #: The development sender's daily or per-recipient hourly cap is spent (429;
    #: ``meta.window``, ``meta.retry_after_seconds``).
    DEVELOPMENT_EMAIL_LIMIT_REACHED = "DEVELOPMENT_EMAIL_LIMIT_REACHED"
    #: The development sender sends only Atlas's own sign-in emails (422).
    DEVELOPMENT_EMAIL_TEMPLATE_NOT_ALLOWED = "DEVELOPMENT_EMAIL_TEMPLATE_NOT_ALLOWED"
    #: Referrals cannot be enabled until the provider's needs are set (422; ``meta``
    #: names what is missing).
    REFERRALS_NOT_CONFIGURED = "REFERRALS_NOT_CONFIGURED"
    #: Another user on the instance already holds that referral code (409).
    REFERRAL_CODE_TAKEN = "REFERRAL_CODE_TAKEN"
    #: Managed WAF provision or deprovision on an instance with no WAF configuration saved
    #: (422; ``meta.action``).
    MANAGED_WAF_NOT_CONFIGURED = "MANAGED_WAF_NOT_CONFIGURED"
    #: A Sign in with Atlas test or review account used something outside the app(s) it
    #: was made for: another app, the dashboard, account settings (403).
    TEST_ACCOUNT_RESTRICTED = "TEST_ACCOUNT_RESTRICTED"
    #: The account's cap of test and review accounts is reached (409).
    PROVISIONED_ACCOUNT_LIMIT_REACHED = "PROVISIONED_ACCOUNT_LIMIT_REACHED"
    #: A setting or address needs a verified domain the account does not have (422).
    DOMAIN_NOT_VERIFIED = "DOMAIN_NOT_VERIFIED"
    INTERNAL = "INTERNAL"


class ErrorItem(TypedDict, total=False):
    """One entry of the BAPI error envelope."""

    code: str
    message: str
    param: str
    meta: dict[str, Any]
    #: ``ROUTE_NOT_FOUND``: close route matches.
    did_you_mean: list[str]
    #: ``ROUTE_NOT_FOUND``: the HTTP methods the path does accept.
    allowed_methods: list[str]
    #: A link to the error's documentation page.
    docs_url: str


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

    @property
    def is_insufficient_scope(self) -> bool:
        """The key lacks a scope (``INSUFFICIENT_SCOPE``, or the former ``SCOPE_MISSING``)."""
        return self.has_code(ErrorCode.INSUFFICIENT_SCOPE) or self.has_code(ErrorCode.SCOPE_MISSING)

    @property
    def required_scope(self) -> str | None:
        """The scope an ``INSUFFICIENT_SCOPE`` error says is missing (``meta.required_scope``)."""
        for e in self.errors:
            if e.get("code") in (ErrorCode.INSUFFICIENT_SCOPE, ErrorCode.SCOPE_MISSING):
                scope = (e.get("meta") or {}).get("required_scope")
                if isinstance(scope, str):
                    return scope
        return None

    @property
    def is_step_up_required(self) -> bool:
        """The call needs a recent second factor (``STEP_UP_REQUIRED``)."""
        return self.has_code(ErrorCode.STEP_UP_REQUIRED)

    @property
    def is_origin_not_allowed(self) -> bool:
        """The key is locked to other browser origins (``ORIGIN_NOT_ALLOWED``)."""
        return self.has_code(ErrorCode.ORIGIN_NOT_ALLOWED)

    @property
    def did_you_mean(self) -> list[str]:
        """``ROUTE_NOT_FOUND``: close route matches (empty otherwise)."""
        for e in self.errors:
            if e.get("did_you_mean"):
                return list(e["did_you_mean"])
        return []

    @property
    def allowed_methods(self) -> list[str]:
        """``ROUTE_NOT_FOUND``: the HTTP methods the path accepts (empty otherwise)."""
        for e in self.errors:
            if e.get("allowed_methods"):
                return list(e["allowed_methods"])
        return []

    @property
    def docs_url(self) -> str | None:
        """A link to the first error's documentation page, when Atlas sent one."""
        for e in self.errors:
            if e.get("docs_url"):
                return e["docs_url"]
        return None
