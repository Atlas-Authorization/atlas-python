"""Names the Atlas API accepts in configuration and sends in webhooks."""

from __future__ import annotations

__all__ = [
    "CAPTCHA_PROVIDERS",
    "LINKING_TRUST_LEVELS",
    "BILLING_PROVIDERS",
    "SIGNING_KEY_PROVIDERS",
    "WEBHOOK_EVENT_SESSION_UPDATED",
    "WEBHOOK_EVENT_USER_REACTIVATED",
    "EMAIL_TEMPLATE_ACCOUNT_REACTIVATED",
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
