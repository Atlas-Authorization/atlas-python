"""Names the Atlas API accepts in configuration and sends in webhooks."""

from __future__ import annotations

__all__ = [
    "CAPTCHA_PROVIDERS",
    "LINKING_TRUST_LEVELS",
    "BILLING_PROVIDERS",
    "SIGNING_KEY_PROVIDERS",
    "WEBHOOK_EVENT_SESSION_UPDATED",
    "WEBHOOK_EVENT_USER_REACTIVATED",
    "WEBHOOK_EVENT_USER_POLICY_ACCEPTED",
    "WEBHOOK_EVENT_POLICY_VERSION_PUBLISHED",
    "EMAIL_TEMPLATE_ACCOUNT_REACTIVATED",
    "WEBHOOK_EVENT_PRIVACY_REQUEST_UPDATED",
    "WEBHOOK_EVENT_PRIVACY_REQUEST_COMPLETED",
    "WEBHOOK_EVENT_USER_DELETION_SCHEDULED",
    "WEBHOOK_EVENT_USER_DELETION_CANCELED",
    "WEBHOOK_EVENT_SECRET_KEY_EXPIRING",
    "WEBHOOK_EVENT_SECRET_KEY_REVOKED",
    "WEBHOOK_EVENT_ENDPOINT_FAILING",
    "WEBHOOK_EVENT_ENDPOINT_DISABLED",
    "WEBHOOK_EVENT_ENDPOINT_RECOVERED",
    "WEBHOOK_EVENT_DELIVERY_TARGET_FAILING",
    "WEBHOOK_EVENT_DELIVERY_TARGET_DISABLED",
    "WEBHOOK_EVENT_DELIVERY_TARGET_RECOVERED",
    "WEBHOOK_EVENT_TEST",
    "WEBHOOK_EVENT_STATUS_INCIDENT_CREATED",
    "WEBHOOK_EVENT_STATUS_INCIDENT_UPDATED",
    "WEBHOOK_EVENT_STATUS_INCIDENT_RESOLVED",
    "WEBHOOK_EVENT_NAMING",
    "WEBHOOK_SIGNATURE_VERSIONS",
    "REFERRAL_PROVIDER_REFERALLI",
    "REFERRAL_PROVIDER_ALIASES",
    "PREFLIGHT_CODES",
]

#: Captcha providers (``auth_config.captcha.provider``). Captcha is bring-your-own-keys:
#: store the secret with ``instance.set_captcha_secret`` first. ``vercel_botid`` is
#: secret-only: set ``attestationUrl`` instead of a site key.
CAPTCHA_PROVIDERS = (
    "none",
    "atlas",
    "hcaptcha",
    "turnstile",
    "recaptcha",
    "recaptcha_v3",
    "recaptcha_enterprise",
    "funcaptcha",
    "friendly",
    "yandex",
    "geetest",
    "mcaptcha",
    "capy",
    "seon",
    "awswaf",
    "perimeterx",
    "akamai",
    "kasada",
    "incapsula",
    "captchafox",
    "vercel_botid",
)

#: ``auth_config.accountLinkingTrust`` values.
LINKING_TRUST_LEVELS = ("always", "verified", "never")

#: Billing providers an instance can sell end-user plans through (bring your own key).
BILLING_PROVIDERS = ("stripe", "polar", "dodo", "creem", "chargebee", "autumn", "commet")

#: Where the token-signing key can live.
SIGNING_KEY_PROVIDERS = ("local", "aws_kms", "gcp_kms", "azure_key_vault")

#: A session's custom data changed.
WEBHOOK_EVENT_SESSION_UPDATED = "session.updated"
#: A dormant account signed in again.
WEBHOOK_EVENT_USER_REACTIVATED = "user.reactivated"
#: The security notice sent when a dormant account signs in again.
EMAIL_TEMPLATE_ACCOUNT_REACTIVATED = "account_reactivated"

#: A user accepted a policy version (payload: ``policy_acceptance`` with its evidence).
WEBHOOK_EVENT_USER_POLICY_ACCEPTED = "user.policy_accepted"
#: A policy version was published.
WEBHOOK_EVENT_POLICY_VERSION_PUBLISHED = "policy.version_published"

# Webhook event names added with the integrator platform. Endpoints with ``event_naming``
# ``canonical`` / ``both`` receive the canonical names; the aliases stay valid for
# ``legacy`` / ``both`` (see ``canonical_webhook_event``).
WEBHOOK_EVENT_PRIVACY_REQUEST_UPDATED = "privacy_request.updated"
WEBHOOK_EVENT_PRIVACY_REQUEST_COMPLETED = "privacy_request.completed"
WEBHOOK_EVENT_USER_DELETION_SCHEDULED = "user.deletion_scheduled"
WEBHOOK_EVENT_USER_DELETION_CANCELED = "user.deletion_canceled"
WEBHOOK_EVENT_SECRET_KEY_EXPIRING = "secret_key.expiring"
WEBHOOK_EVENT_SECRET_KEY_REVOKED = "secret_key.revoked"
WEBHOOK_EVENT_ENDPOINT_FAILING = "webhook_endpoint.failing"
WEBHOOK_EVENT_ENDPOINT_DISABLED = "webhook_endpoint.disabled"
WEBHOOK_EVENT_ENDPOINT_RECOVERED = "webhook_endpoint.recovered"
WEBHOOK_EVENT_DELIVERY_TARGET_FAILING = "delivery_target.failing"
WEBHOOK_EVENT_DELIVERY_TARGET_DISABLED = "delivery_target.disabled"
WEBHOOK_EVENT_DELIVERY_TARGET_RECOVERED = "delivery_target.recovered"
WEBHOOK_EVENT_TEST = "webhook.test"
WEBHOOK_EVENT_STATUS_INCIDENT_CREATED = "status.incident.created"
WEBHOOK_EVENT_STATUS_INCIDENT_UPDATED = "status.incident.updated"
WEBHOOK_EVENT_STATUS_INCIDENT_RESOLVED = "status.incident.resolved"

#: ``event_naming`` values on a webhook endpoint.
WEBHOOK_EVENT_NAMING = ("canonical", "legacy", "both")
#: ``signature_versions`` values on a webhook endpoint.
WEBHOOK_SIGNATURE_VERSIONS = ("v1", "v2")

#: Referral provider id. ``referally`` is the former id of ``referalli``; both are accepted.
REFERRAL_PROVIDER_REFERALLI = "referalli"
REFERRAL_PROVIDER_ALIASES = {"referally": "referalli"}

#: Preflight finding codes added with the integrator platform.
PREFLIGHT_CODES = (
    "oauth_client_no_backchannel_logout_uri",
    "pkce_not_required",
    "passkey_without_uv",
    "auto_link_unverified",
    "integration_enabled_never_minted",
    "integration_verify_errors",
    "integration_receiver_failing",
    "cookie_consent_not_enabled",
    "status_dependency_unreachable",
    "status_dependency_outage",
    "secret_key_expiring",
)
