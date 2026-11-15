"""Generated Backend API / Platform API operations (do not edit).

Produced by ``scripts/gen_catalog.py`` from the OpenAPI snapshot; the async mirror is
``_acatalog.py``. Hand-written resources inherit the class of the same name here.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

from . import catalog_models as cm
from ._transport import _SyncTransport
from ._util import _enc, _qd


class Abac:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def authorize_token(
        self,
        body: cm.PostAbacAuthorizeTokenBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Decide for the principal an access token stands for. The token is verified first (an
        active Atlas session token, or a token from a trusted issuer); its claims map to the
        principal and parents per the token mapping. An invalid token is a 401, not a deny.
        """
        return self._t.request(
            method="POST",
            path="/v1/abac/authorize_token",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def export_cedar(
        self,
        body: cm.PostAbacCedarExportBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Convert Cedar policy text to the Cedar JSON policy format (annotations, decimal and ip
        extension calls included).
        """
        return self._t.request(
            method="POST",
            path="/v1/abac/cedar/export",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def import_cedar(
        self,
        body: cm.PostAbacCedarImportBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Convert Cedar JSON policies to policy text. With `name`, also create the policy from
        them.
        """
        return self._t.request(
            method="POST",
            path="/v1/abac/cedar/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_token_mapping(
        self,
    ) -> dict[str, Any]:
        """How access-token claims become a policy principal and its parents, and which extra token
        issuers are trusted.
        """
        return self._t.request(
            method="GET",
            path="/v1/abac/token_mapping",
        )

    def set_token_mapping(
        self,
        body: cm.PutAbacTokenMappingBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Set the claim mapping used by `authorize_token`: the principal type and id claim, claims
        that become parent entities (org, role, groups), claims copied as attributes, and
        trusted issuers with their JWKS URLs.
        """
        return self._t.request(
            method="PUT",
            path="/v1/abac/token_mapping",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AbacPolicies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_cedar_json(
        self,
        abac_policy_id: str,
    ) -> dict[str, Any]:
        """The current version of a stored policy as Cedar JSON."""
        return self._t.request(
            method="GET",
            path=f"/v1/abac_policies/{_enc(abac_policy_id)}/cedar_json",
        )


class AbuseSignals:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        kind: Literal['sign_up', 'recovery'] | None = None,
        outcome: Literal['allowed', 'scored', 'blocked'] | None = None,
        attempt_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAbuseSignalsResponse:
        """The sign-up and recovery requests abuse protection looked at, newest first: outcome,
        network address and ASN, risk score and reasons. Never an email address.
        """
        return self._t.request(
            method="GET",
            path="/v1/abuse_signals",
            query=_qd({'kind': kind, 'outcome': outcome, 'attempt_id': attempt_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        kind: Literal['sign_up', 'recovery'] | None = None,
        outcome: Literal['allowed', 'scored', 'blocked'] | None = None,
        attempt_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetAbuseSignalsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(kind=kind, outcome=outcome, attempt_id=attempt_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_summary(
        self,
        *,
        days: int | None = None,
    ) -> cm.GetAbuseSignalsSummaryResponse:
        """Counts of abuse signals by kind and outcome over the last N days."""
        return self._t.request(
            method="GET",
            path="/v1/abuse_signals/summary",
            query=_qd({'days': days}),
        )


class AccessPolicies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def impact(
        self,
        body: cm.PostAccessPoliciesImpactBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.AccessPolicyImpact:
        """Impact preview: replay a draft policy (`draft`: conditions, grants, stages, targets)
        against the sampled sign-ins of the last `days` (1-30, default 7) and get how many would
        have been allowed, stepped up or blocked, plus the affected users. Nothing is stored or
        enforced.
        """
        return self._t.request(
            method="POST",
            path="/v1/access_policies/impact",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_insights(
        self,
        *,
        days: int | None = None,
    ) -> cm.AccessPolicyInsights:
        """Report-only insights: how often `report_only` policies would have blocked or stepped up
        a request in the last `days`, per policy and per day.
        """
        return self._t.request(
            method="GET",
            path="/v1/access_policies/insights",
            query=_qd({'days': days}),
        )


class Actions:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def rollback(
        self,
        action_id: str,
        body: cm.PostActionsByIdRollbackBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostActionsByIdRollbackResponse:
        """Put an earlier version's code and target back live, as a NEW version (history stays
        linear). Also ends any staged rollout. 404 for a version that is not kept.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/actions/{_enc(action_id)}/rollback",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def update_rollout(
        self,
        action_id: str,
        body: cm.PatchActionsByIdRolloutBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.Action:
        """Move a staged rollout: 1-99 changes its share, 100 promotes the staged version to
        current, 0 aborts it and drops it. 409 when the Action has no staged version.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/actions/{_enc(action_id)}/rollout",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_versions(
        self,
        action_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetActionsByIdVersionsResponse:
        """Every kept version of an Action (up to 50, newest first), with which one is live and
        which one is staged. Each is an immutable snapshot of the code (or HTTP target); the
        first change to an Action that predates versions snapshots what it was.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/actions/{_enc(action_id)}/versions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_versions(
        self,
        action_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetActionsByIdVersionsResponseDataItem]:
        """Every item of :meth:`list_versions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_versions(action_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_version(
        self,
        action_id: str,
        body: cm.PostActionsByIdVersionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostActionsByIdRollbackResponse:
        """Publish new code (or a new HTTP target) as the next version. By default it goes live at
        once. With `rollout_percent` from 1 to 99 it is staged: that share of executions runs it
        (one user always lands on the same side), the rest keep the current version, until you
        move or end the rollout with PATCH /v1/actions/{id}/rollout. 409 while another rollout
        is in progress. Writes an audit row naming the versions.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/actions/{_enc(action_id)}/versions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_version(
        self,
        action_id: str,
        version: str,
    ) -> cm.GetActionsByIdVersionsResponseDataItem:
        """One version of an Action, with its code."""
        return self._t.request(
            method="GET",
            path=f"/v1/actions/{_enc(action_id)}/versions/{_enc(version)}",
        )


class AdministrativeUnits:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAdministrativeUnitsResponse:
        """List administrative units: named sets of users that a scoped organization administrator
        may manage.
        """
        return self._t.request(
            method="GET",
            path="/v1/administrative_units",
            query=_qd({'organization_id': organization_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetAdministrativeUnitsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(organization_id=organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostAdministrativeUnitsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAdministrativeUnitsResponseDataItem:
        """Create an administrative unit. Without a `filter` it is static and you list its members;
        with one it is dynamic and its members are whoever match.
        """
        return self._t.request(
            method="POST",
            path="/v1/administrative_units",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        administrative_unit_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAdministrativeUnitsByIdResponse:
        """Delete a unit. A membership scope that named it stops reaching those people."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        administrative_unit_id: str,
    ) -> cm.GetAdministrativeUnitsResponseDataItem:
        """Read one unit by id or key."""
        return self._t.request(
            method="GET",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}",
        )

    def update(
        self,
        administrative_unit_id: str,
        body: cm.PatchAdministrativeUnitsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAdministrativeUnitsResponseDataItem:
        """Change a unit's name, description or filter."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_members(
        self,
        administrative_unit_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAdministrativeUnitsByIdMembersResponse:
        """The listed members of a static unit (409 for a dynamic unit)."""
        return self._t.request(
            method="GET",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}/members",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_members(
        self,
        administrative_unit_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetAdministrativeUnitsByIdMembersResponseDataItem]:
        """Every item of :meth:`list_members`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_members(administrative_unit_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_member(
        self,
        administrative_unit_id: str,
        body: cm.PostAdministrativeUnitsByIdMembersBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAdministrativeUnitsByIdMembersResponse:
        """Add and remove people on a static unit."""
        return self._t.request(
            method="POST",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}/members",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AgentAccessReviews:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAgentAccessReviewsResponse:
        """The agent access reviews, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/agent_access_reviews",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetAgentAccessReviewsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostAgentAccessReviewsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentAccessReviewsResponseDataItem:
        """Start an access review of agents' live grants: one item per grant, assigned to the
        agent's sponsor (else its owner), who certifies or revokes it.
        """
        return self._t.request(
            method="POST",
            path="/v1/agent_access_reviews",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        agent_access_review_id: str,
        *,
        decision: str | None = None,
        reviewer_user_id: str | None = None,
    ) -> cm.GetAgentAccessReviewsByIdResponse:
        """One review with its items; filter by decision or reviewer."""
        return self._t.request(
            method="GET",
            path=f"/v1/agent_access_reviews/{_enc(agent_access_review_id)}",
            query=_qd({'decision': decision, 'reviewer_user_id': reviewer_user_id}),
        )

    def close(
        self,
        agent_access_review_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentAccessReviewsResponseDataItem:
        """Close a review; no further decisions are accepted."""
        return self._t.request(
            method="POST",
            path=f"/v1/agent_access_reviews/{_enc(agent_access_review_id)}/close",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def decide_item(
        self,
        agent_access_review_id: str,
        item_id: str,
        body: cm.PostAgentAccessReviewsByIdItemsByItemIdDecideBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentAccessReviewsByIdResponseItemsItem:
        """Certify or revoke one item. A revoke ends that grant immediately."""
        return self._t.request(
            method="POST",
            path=f"/v1/agent_access_reviews/{_enc(agent_access_review_id)}/items/{_enc(item_id)}/decide",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AgentDelegations:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        machine_id: str | None = None,
        delegator_user_id: str | None = None,
        root_id: str | None = None,
        status: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAgentDelegationsResponse:
        """List delegations, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/agent_delegations",
            query=_qd({'machine_id': machine_id, 'delegator_user_id': delegator_user_id, 'root_id': root_id, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        machine_id: str | None = None,
        delegator_user_id: str | None = None,
        root_id: str | None = None,
        status: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetAgentDelegationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(machine_id=machine_id, delegator_user_id=delegator_user_id, root_id=root_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostAgentDelegationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentDelegationsResponseDataItem:
        """Delegate authority to an agent. A root delegation (delegator_user_id) lets the agent act
        for that user; a child (parent_delegation_id) lets an agent pass part of what it holds
        to a sub-agent. A child can only narrow its parent: its scopes must be a subset, its
        lifetime ends no later, and the chain is limited by the instance's maxDelegationDepth.
        Loops are refused. The agent's tokens then carry delegation and act claims, are narrowed
        to the delegated scopes, and stop verifying when the delegation is revoked. Needs a
        recent MFA sign-in. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/agent_delegations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke_for_user(
        self,
        body: cm.PostAgentDelegationsRevokeForUserBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAgentDelegationsRevokeForUserResponse:
        """Revoke every delegation a user made (and everything below them), for example when they
        leave or are suspected compromised.
        """
        return self._t.request(
            method="POST",
            path="/v1/agent_delegations/revoke_for_user",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        agent_delegation_id: str,
    ) -> cm.GetAgentDelegationsByIdResponse:
        """One delegation with its last evaluations."""
        return self._t.request(
            method="GET",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}",
        )

    def evaluate(
        self,
        agent_delegation_id: str,
        body: cm.PostAgentDelegationsByIdEvaluateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAgentDelegationsByIdEvaluateResponse:
        """Continuous access evaluation: may this agent still act? Checks the delegation and its
        ancestors (revoked, expired) and the delegator's live posture (account state; with the
        instance policy on, MFA freshness, risk and device). Returns allow, deny or revoked, the
        reasons, the posture, and how long an allow may be cached (valid_for_seconds). With
        enforce: true (needs machines:write) a failed evaluation applies the instance's policy,
        as the worker's sweep does.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}/evaluate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_graph(
        self,
        agent_delegation_id: str,
    ) -> cm.GetAgentDelegationsByIdGraphResponse:
        """The delegation graph around one delegation: the chain above it and every delegation
        below it, with the edges between them.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}/graph",
        )

    def revoke(
        self,
        agent_delegation_id: str,
        body: cm.PostAgentDelegationsByIdRevokeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAgentDelegationsRevokeForUserResponse:
        """Revoke a delegation and every delegation below it in one step. Tokens already minted
        under them stop verifying at POST /v1/m2m_tokens/verify at once and live out at most
        their short lifetime elsewhere; the agents can mint no new ones. With disable_agents,
        agents left with no live delegation are revoked as machines too. Emits
        agent.delegation_revoked.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Agents:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def verify_request(
        self,
        body: cm.PostAgentsVerifyRequestBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAgentsVerifyRequestResponse:
        """Check a signed bot request (Web Bot Auth, RFC 9421 HTTP Message Signatures, Ed25519, tag
        web-bot-auth). Send the method, the absolute URL and the headers your server received.
        Atlas reads the Signature-Agent header, fetches the bot's key directory from <Signature-
        Agent>/.well-known/http-message-signatures-directory (cached, over a transport that
        refuses private addresses), checks the keyid against the keys' JWK thumbprints, verifies
        the signature and its created/expires window, then applies your allow and block lists.
        decision is allow, block or unknown; only a verified request is ever allowed or blocked.
        The decision is written to the audit log (agent.web_bot_auth_decision). 600 calls per
        minute.
        """
        return self._t.request(
            method="POST",
            path="/v1/agents/verify_request",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_activity(
        self,
        agent_id: str,
        *,
        since: str | None = None,
        before: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAgentsByIdActivityResponse:
        """Everything an agent did, newest first: audit entries about it and entries it caused
        (gateway tool calls with their outcome, connection tokens and actions, access
        decisions). Defaults to the last 30 days.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/agents/{_enc(agent_id)}/activity",
            query=_qd({'since': since, 'before': before, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_activity(
        self,
        agent_id: str,
        *,
        since: str | None = None,
        before: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetAgentsByIdActivityResponseDataItem]:
        """Every item of :meth:`list_activity`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_activity(agent_id, since=since, before=before, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_lifecycle(
        self,
        agent_id: str,
    ) -> cm.GetAgentsByIdLifecycleResponse:
        """An agent's sponsor, backup sponsor and expiry."""
        return self._t.request(
            method="GET",
            path=f"/v1/agents/{_enc(agent_id)}/lifecycle",
        )

    def set_lifecycle(
        self,
        agent_id: str,
        body: cm.PutAgentsByIdLifecycleBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentsByIdLifecycleResponse:
        """Set an agent's sponsor, backup sponsor and expiry (omitted fields keep their value; null
        clears). Emits agent.sponsor_changed. When the sponsor's account is gone, banned or
        locked the backup is promoted automatically; at the expiry the agent's grants are
        revoked and the agent is revoked, after an agent.expiring warning 14 days ahead.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/agents/{_enc(agent_id)}/lifecycle",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def renew(
        self,
        agent_id: str,
        body: cm.PostAgentsByIdRenewBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentsByIdLifecycleResponse:
        """Extend an agent's registration by extend_days (1 to 365) from its current expiry (or
        now, when that has passed). A revoked agent cannot be renewed.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/agents/{_enc(agent_id)}/renew",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AllowlistIdentifiers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAllowlistIdentifiersResponse:
        """List allowlist identifiers (emails, @domains, phones) permitted in allow-list-only mode."""
        return self._t.request(
            method="GET",
            path="/v1/allowlist_identifiers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.AllowlistIdentifier]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostAllowlistIdentifiersBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.AllowlistIdentifier:
        """Add an allowlist identifier: an exact email, an @domain, or an E.164 phone."""
        return self._t.request(
            method="POST",
            path="/v1/allowlist_identifiers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        allowlist_identifier_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAllowlistIdentifiersByIdResponse:
        """Remove an allowlist identifier. Another instance id is 404, never 403."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/allowlist_identifiers/{_enc(allowlist_identifier_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class ApiKeys:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_posture(
        self,
        *,
        issue: str | None = None,
        stale_days: str | None = None,
        never_used_days: str | None = None,
        max_scopes: str | None = None,
        starting_after: str | None = None,
        limit: int | None = None,
    ) -> cm.GetApiKeysPostureResponse:
        """The key posture report: live end-user API keys that are never used, stale, over-scoped,
        without an expiry or without a network allowlist.
        """
        return self._t.request(
            method="GET",
            path="/v1/api_keys/posture",
            query=_qd({'issue': issue, 'stale_days': stale_days, 'never_used_days': never_used_days, 'max_scopes': max_scopes, 'starting_after': starting_after, 'limit': limit}),
        )

    def iter_list_posture(
        self,
        *,
        issue: str | None = None,
        stale_days: str | None = None,
        never_used_days: str | None = None,
        max_scopes: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetApiKeysPostureResponseDataItem]:
        """Every item of :meth:`list_posture`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_posture(issue=issue, stale_days=stale_days, never_used_days=never_used_days, max_scopes=max_scopes, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_callers(
        self,
        api_key_id: str,
        *,
        window_days: str | None = None,
        limit: int | None = None,
    ) -> cm.GetApiKeysByIdCallersResponse:
        """Who uses a key: the busiest caller addresses, user agents and route buckets over the
        last days.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/api_keys/{_enc(api_key_id)}/callers",
            query=_qd({'window_days': window_days, 'limit': limit}),
        )

    def rotate(
        self,
        api_key_id: str,
        body: cm.PostApiKeysByIdRotateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostApiKeysByIdRotateResponse:
        """Rotate an end-user API key with an overlap: mint its successor and keep the old key
        working until the overlap ends.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/api_keys/{_enc(api_key_id)}/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AppCatalog:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_custom_presets(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAppCatalogCustomPresetsResponse:
        """List this instance's private SAML presets, in the portable form POST
        /v1/app_catalog/custom_presets accepts, so a preset can be moved between environments.
        """
        return self._t.request(
            method="GET",
            path="/v1/app_catalog/custom_presets",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_custom_presets(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetAppCatalogCustomPresetsResponseDataItem]:
        """Every item of :meth:`list_custom_presets`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_custom_presets(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_custom_preset(
        self,
        body: cm.PostAppCatalogCustomPresetsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Save a private SAML preset for apps that are not in the catalog (an id, name,
        entityIdTemplate and acsUrlTemplate using {param} placeholders, params with a kind of
        slug, host, https_url or entity, and an attribute map). It then appears in GET
        /v1/app_catalog (custom: true, never verified) and installs like any preset. Saving an
        existing id replaces it.
        """
        return self._t.request(
            method="POST",
            path="/v1/app_catalog/custom_presets",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_custom_preset(
        self,
        custom_preset_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a private preset. Apps already installed from it keep working."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/app_catalog/custom_presets/{_enc(custom_preset_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAppCatalogRequestsResponse:
        """The queue of apps people asked for, most wanted first. Filter with status (open,
        building, available, declined).
        """
        return self._t.request(
            method="GET",
            path="/v1/app_catalog/requests",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetAppCatalogRequestsResponseDataItem]:
        """Every item of :meth:`list_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_requests(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_request(
        self,
        body: cm.PostAppCatalogRequestsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Ask for an app that is not in the catalog (name, protocol, docs_url, note). Asking again
        for an app already open counts as the requester’s vote (once) instead of a duplicate
        (200); a new request is 201; an app already in the catalog is 409.
        """
        return self._t.request(
            method="POST",
            path="/v1/app_catalog/requests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_request(
        self,
        request_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove an app catalog request."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/app_catalog/requests/{_enc(request_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def update_request(
        self,
        request_id: str,
        body: cm.PatchAppCatalogRequestsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Move a request along: status open, building, available or declined, and a note."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/app_catalog/requests/{_enc(request_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def vote_request(
        self,
        request_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAppCatalogRequestsResponseDataItem:
        """Add one vote to an open or in-progress app request (409 when it is available or
        declined, 404 when unknown). One vote per person or key: a repeat vote changes nothing.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/app_catalog/requests/{_enc(request_id)}/vote",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class ApprovalRequests:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        approver_user_id: str | None = None,
        reference: str | None = None,
        created_after: int | None = None,
        created_before: int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetApprovalRequestsResponse:
        """List approval requests, newest first. Filters: `status` (pending, approved, denied,
        expired, cancelled; a pending request past its lifetime counts as expired), `user_id`,
        `approver_user_id`, `reference`, `created_after` and `created_before` (epoch ms). Pages
        with `limit` (1 to 100, default 25) and `starting_after`. Needs `approvals:read`
        (`users:read` keeps working).
        """
        return self._t.request(
            method="GET",
            path="/v1/approval_requests",
            query=_qd({'status': status, 'user_id': user_id, 'approver_user_id': approver_user_id, 'reference': reference, 'created_after': created_after, 'created_before': created_before, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        approver_user_id: str | None = None,
        reference: str | None = None,
        created_after: int | None = None,
        created_before: int | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsersByIdApprovalRequestsByApprovalIdResponse]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(status=status, user_id=user_id, approver_user_id=approver_user_id, reference=reference, created_after=created_after, created_before=created_before, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostApprovalRequestsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersByIdApprovalRequestsResponse:
        """Create an approval request with the subject in the body (`user_id`). Same options as the
        per-user route: a caller-chosen lifetime, an N-of-M approver set (named users or an
        organization role) and a signed receipt. The request is rendered into a canonical text
        whose SHA-256 is its `digest`; approvers sign that digest with a registered device key
        or a passkey, and once enough approve, Atlas signs a receipt (a compact JWS, typ `atlas-
        approval-receipt+jws`) that verifies offline against the instance JWKS. Accepts
        Idempotency-Key. → 201.
        """
        return self._t.request(
            method="POST",
            path="/v1/approval_requests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        approval_request_id: str,
        *,
        wait_seconds: int | None = None,
    ) -> cm.GetUsersByIdApprovalRequestsByApprovalIdResponse:
        """Read one approval request with its decisions and, once approved, the signed receipt.
        `wait_seconds` (0 to 25) holds the call open until the request leaves pending, so an
        agent can wait for a human without a tight polling loop. Needs `approvals:read`.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/approval_requests/{_enc(approval_request_id)}",
            query=_qd({'wait_seconds': wait_seconds}),
        )

    def cancel(
        self,
        approval_request_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersByIdApprovalRequestsByApprovalIdResponse:
        """Withdraw a pending approval request by id, without naming the user. 409 once it is
        approved, denied, expired or already cancelled. Emits approval_request.cancelled. Needs
        `approvals:write`.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/approval_requests/{_enc(approval_request_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def consume(
        self,
        approval_request_id: str,
        body: cm.PostApprovalRequestsByIdConsumeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersByIdApprovalRequestsByApprovalIdResponse:
        """Spend an approved request once. Returns the request with its signed receipt; a second
        call is a 409, as is a request that is not approved. When the request was created with a
        `binding`, send the same `binding` or the call is refused, so a receipt for one action
        can never authorize another. Accepts Idempotency-Key (a retry with the same key returns
        the first answer). Needs `approvals:write`.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/approval_requests/{_enc(approval_request_id)}/consume",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AtlasIdApps:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def adopt(
        self,
        body: cm.PostAtlasIdAppsAdoptBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Adopt an account-level Sign in with Atlas app with the one-time code its owner issued,
        using this instance's own secret key.
        """
        return self._t.request(
            method="POST",
            path="/v1/atlas_id_apps/adopt",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def release(
        self,
        atlas_id_app_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAtlasIdAppsByIdReleaseResponse:
        """Hand an adopted app back to its owner. The instance stops managing its grants."""
        return self._t.request(
            method="POST",
            path=f"/v1/atlas_id_apps/{_enc(atlas_id_app_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Audit:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_chain(
        self,
    ) -> cm.GetAuditChainResponse:
        """The audit chain: whether it is on, its head, its last checkpoint and how many rows are
        not chained yet.
        """
        return self._t.request(
            method="GET",
            path="/v1/audit/chain",
        )

    def set_chain(
        self,
        body: cm.PutAuditChainBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAuditChainResponse:
        """Turn the tamper-evident audit chain on. From then on every audit row is hashed and
        chained to the one before (by the worker, about a minute after it is written) and signed
        checkpoints pin the head. A chain that is on cannot be turned off: its links are the
        evidence. Needs a recent MFA sign-in. Idempotent; call again to change
        checkpoint_interval_seconds.
        """
        return self._t.request(
            method="PUT",
            path="/v1/audit/chain",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_chain_checkpoints(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuditChainCheckpointsResponse:
        """Signed checkpoints, oldest first. Each is a JWS the instance's signing key made; verify
        it against jwks_uri.
        """
        return self._t.request(
            method="GET",
            path="/v1/audit/chain/checkpoints",
            query=_qd({'after_seq': after_seq, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_chain_checkpoints(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetAuditChainCheckpointsResponseDataItem]:
        """Every item of :meth:`list_chain_checkpoints`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_chain_checkpoints(after_seq=after_seq, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_chain_checkpoint(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAuditChainCheckpointsResponseDataItem:
        """Sign a checkpoint of the chain head now (the worker does it on its interval). Refused
        with 409 when the chain does not verify. Returns the existing checkpoint when the head
        is already pinned.
        """
        return self._t.request(
            method="POST",
            path="/v1/audit/chain/checkpoints",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_chain_links(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuditChainLinksResponse:
        """Chain links with the audit rows they cover, oldest first, for an independent verifier
        (`atlas audit verify`).
        """
        return self._t.request(
            method="GET",
            path="/v1/audit/chain/links",
            query=_qd({'after_seq': after_seq, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_chain_links(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetAuditChainLinksResponseDataItem]:
        """Every item of :meth:`list_chain_links`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_chain_links(after_seq=after_seq, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def verify_chain(
        self,
        body: cm.PostAuditChainVerifyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAuditChainVerifyResponse:
        """Recompute the chain from the stored audit rows and check every checkpoint. Read-only.
        Large chains are checked in pages: pass the returned next_seq as from_seq until done is
        true.
        """
        return self._t.request(
            method="POST",
            path="/v1/audit/chain/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AuditRetention:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> dict[str, Any]:
        """How long the instance audit log is kept: the effective days, whether it is configured,
        and the allowed range (30 to 3,650; the default is 365).
        """
        return self._t.request(
            method="GET",
            path="/v1/audit_retention",
        )

    def set(
        self,
        body: cm.PutAuditRetentionBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Set audit log retention in days (`null` returns to the default). Entries older than the
        retention are deleted by an hourly sweep, so shortening it needs `confirm_deletion:
        true`.
        """
        return self._t.request(
            method="PUT",
            path="/v1/audit_retention",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AuthenticatorPolicies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthenticatorPoliciesResponse:
        """List the group-targeted authenticator policies."""
        return self._t.request(
            method="GET",
            path="/v1/authenticator_policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetAuthenticatorPoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostAuthenticatorPoliciesBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAuthenticatorPoliciesResponseDataItem:
        """Create an authenticator policy for a group: `required_factors` (members must pass a
        second factor, or enrol one), `grace_until` (members with no factor may still sign in
        until then), and a `passkey` profile (user verification, attestation, attachment, AAGUID
        allow / block lists) applied when members register passkeys. Policies only add
        protection to the instance settings; several policies combine to the strictest result.
        """
        return self._t.request(
            method="POST",
            path="/v1/authenticator_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_effective(
        self,
        user_id: str,
    ) -> cm.GetAuthenticatorPoliciesEffectiveByUserIdResponse:
        """The combined authenticator rules that apply to one user through their groups."""
        return self._t.request(
            method="GET",
            path=f"/v1/authenticator_policies/effective/{_enc(user_id)}",
        )

    def delete(
        self,
        authenticator_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAuthenticatorPoliciesByIdResponse:
        """Delete an authenticator policy."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/authenticator_policies/{_enc(authenticator_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        authenticator_policy_id: str,
    ) -> cm.GetAuthenticatorPoliciesResponseDataItem:
        """Read one authenticator policy."""
        return self._t.request(
            method="GET",
            path=f"/v1/authenticator_policies/{_enc(authenticator_policy_id)}",
        )

    def update(
        self,
        authenticator_policy_id: str,
        body: cm.PatchAuthenticatorPoliciesByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAuthenticatorPoliciesResponseDataItem:
        """Update an authenticator policy."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/authenticator_policies/{_enc(authenticator_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Authz:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_events(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        store_id: str | None = None,
        kinds: str | None = None,
        wait_ms: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthzEventsResponse:
        """The authorization event feed: tuple writes and deletes (by API call and by the sync),
        new model versions and sync runs, in order. Pass the last `seq` you processed as `after`
        (or `latest` to start from now). `wait_ms` (up to 25000) holds the request open until
        something newer appears, so a local policy decision point can refresh the moment a tuple
        changes. At-least-once: drop an entry whose `id` you have seen. Entries are kept 7 days.
        Needs an API key that is not limited to organizations.
        """
        return self._t.request(
            method="GET",
            path="/v1/authz/events",
            query=_qd({'after': after, 'limit': limit, 'store_id': store_id, 'kinds': kinds, 'wait_ms': wait_ms, 'starting_after': starting_after}),
        )

    def iter_list_events(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        store_id: str | None = None,
        kinds: str | None = None,
        wait_ms: int | None = None,
    ) -> Iterator[cm.GetAuthzEventsResponseDataItem]:
        """Every item of :meth:`list_events`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_events(after=after, limit=limit, store_id=store_id, kinds=kinds, wait_ms=wait_ms, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def explain(
        self,
        body: cm.PostAuthzExplainBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAuthzExplainResponse:
        """Why does this subject have, or not have, this access? Asks RBAC (organization roles,
        member permissions, app roles), delegated org roles, groups, resource roles, ABAC,
        access policies and FGA the same question and returns each rule that contributed, with
        the reason it applied or not and an overall decision. Layers without enough input are
        `skipped` and say what is missing; a failing layer is `error` and never decides alone.
        Read-only. Needs an API key that is not limited to organizations.
        """
        return self._t.request(
            method="POST",
            path="/v1/authz/explain",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def check_rbac(
        self,
        body: cm.PostAuthzRbacCheckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAuthzRbacCheckResponse:
        """A role-based permission check: does this user hold the permission through an
        organization role, a per-member permission, an app role, a delegated role or a group?
        Answered like the role layers of `POST /v1/authz/explain`, and written to the decision
        log (source `rbac`) with the roles the user holds, so `POST /v1/authz/what_if` can later
        replay it against a role change.
        """
        return self._t.request(
            method="POST",
            path="/v1/authz/rbac/check",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_what_if(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthzWhatIfResponse:
        """Saved what-if runs, newest first, with their summaries."""
        return self._t.request(
            method="GET",
            path="/v1/authz/what_if",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_what_if(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetAuthzWhatIfResponseDataItem]:
        """Every item of :meth:`list_what_if`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_what_if(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def what_if(
        self,
        body: cm.PostAuthzWhatIfBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAuthzWhatIfResponse:
        """What would have happened if? Replay the decisions the log recorded over a window (newest
        first, up to `limit`) with a candidate change applied, and report which would have
        flipped between allow and deny. Candidates: ABAC policies to add, replace or remove;
        role permission edits; FGA tuples to write or delete; an access-policy draft (replayed
        against sampled evaluations). Decisions recorded with `input_mode: full` replay exactly;
        with `ids`, attributes a policy reads are missing, so each replay first re-decides under
        the current policies and counts disagreements as `baseline_mismatch`. Nothing is
        changed. Saved by default; 201 when saved. Needs the decision log on (`PUT
        /v1/authz_decision_settings`) and an API key that is not limited to organizations.
        """
        return self._t.request(
            method="POST",
            path="/v1/authz/what_if",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_what_if(
        self,
        what_if_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAuthzWhatIfByIdResponse:
        """Delete a saved what-if run."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/authz/what_if/{_enc(what_if_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_what_if(
        self,
        what_if_id: str,
    ) -> cm.GetAuthzWhatIfResponseDataItem:
        """One saved what-if run with its full result."""
        return self._t.request(
            method="GET",
            path=f"/v1/authz/what_if/{_enc(what_if_id)}",
        )


class AuthzDecisions:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def ingest(
        self,
        body: cm.PostAuthzDecisionsIngestBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAuthzDecisionsIngestResponse:
        """A local policy decision point ships a batch of up to 500 of its decisions and checks in
        with its id and the bundle revision it runs. Decisions are sampled and redacted by the
        instance decision-log settings, exactly like server-side decisions; nothing is stored
        while capture is off.
        """
        return self._t.request(
            method="POST",
            path="/v1/authz_decisions/ingest",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AuthzPdps:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthzPdpsResponse:
        """The fleet of local policy decision points that have checked in: the bundle revision each
        is on, when it was last seen and how many decisions it has shipped.
        """
        return self._t.request(
            method="GET",
            path="/v1/authz_pdps",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.PostAuthzDecisionsIngestResponsePdp]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete(
        self,
        authz_pdp_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAuthzPdpsByIdResponse:
        """Forget a local policy decision point (it reappears if it checks in again)."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/authz_pdps/{_enc(authz_pdp_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Billing:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_connect_accounts(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingConnectAccountsResponse:
        """List the connected accounts, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/billing/connect/accounts",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_connect_accounts(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetBillingConnectAccountsResponseDataItem]:
        """Every item of :meth:`list_connect_accounts`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_connect_accounts(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_connect_account(
        self,
        body: cm.PostBillingConnectAccountsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingConnectAccountsResponseDataItem:
        """Create the Stripe Connect (Express) account a user or organization is paid out to, on
        YOUR Stripe account. One account per subject: a second call returns it (200). Idempotent
        on `idempotency_key`. Send the person to a link from `POST
        /v1/billing/connect/accounts/{id}/onboarding_link` to finish Stripe's onboarding.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/connect/accounts",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_connect_account(
        self,
        account_id: str,
    ) -> cm.GetBillingConnectAccountsResponseDataItem:
        """Read one connected account as Atlas last saw it. `POST .../refresh` re-reads it from
        Stripe.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/billing/connect/accounts/{_enc(account_id)}",
        )

    def onboarding_link_account_connect(
        self,
        account_id: str,
        body: cm.PostBillingConnectAccountsByIdOnboardingLinkBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostBillingConnectAccountsByIdOnboardingLinkResponse:
        """A one-time Stripe-hosted link where the account holder completes onboarding (`type:
        onboarding`, default) or edits their details (`update`). Both URLs must be https and,
        when your app lists allowed origins, on one of them. The link expires quickly and works
        once: mint a new one on `refresh_url`.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/billing/connect/accounts/{_enc(account_id)}/onboarding_link",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def refresh_account_connect(
        self,
        account_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingConnectAccountsResponseDataItem:
        """Re-read the account's onboarding and payout readiness from Stripe and store it."""
        return self._t.request(
            method="POST",
            path=f"/v1/billing/connect/accounts/{_enc(account_id)}/refresh",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_connect_transfers(
        self,
        *,
        account_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingConnectTransfersResponse:
        """The transfer ledger, newest first, optionally for one account."""
        return self._t.request(
            method="GET",
            path="/v1/billing/connect/transfers",
            query=_qd({'account_id': account_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_connect_transfers(
        self,
        *,
        account_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetBillingConnectTransfersResponseDataItem]:
        """Every item of :meth:`list_connect_transfers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_connect_transfers(account_id=account_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_connect_transfer(
        self,
        body: cm.PostBillingConnectTransfersBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingConnectTransfersResponseDataItem:
        """Pay a connected account from your Stripe balance. Atlas re-reads the account first and
        refuses (409) until Stripe reports payouts enabled. Idempotent on `idempotency_key`: a
        retry returns the first transfer, and Stripe is called with the same key, so money moves
        once. The same key with a different account or amount is a 409. Emits
        `billing_transfer.created`.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/connect/transfers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_connect_transfer(
        self,
        transfer_id: str,
    ) -> cm.GetBillingConnectTransfersResponseDataItem:
        """Read one Connect transfer by id: its amount, destination account and status."""
        return self._t.request(
            method="GET",
            path=f"/v1/billing/connect/transfers/{_enc(transfer_id)}",
        )

    def list_coupons(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingCouponsResponse:
        """List the discount codes you offer."""
        return self._t.request(
            method="GET",
            path="/v1/billing/coupons",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_coupons(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetBillingCouponsResponseDataItem]:
        """Every item of :meth:`list_coupons`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_coupons(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_coupon(
        self,
        body: cm.PostBillingCouponsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingCouponsResponseDataItem:
        """Create a discount code. Set exactly one of `percent_off` or `amount_off` (+ `currency`).
        It is created on your own Stripe account as a coupon and promotion code, so Stripe
        enforces and applies it; a provider without discount support refuses with 422.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/coupons",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def validate_coupon(
        self,
        body: cm.PostBillingCouponsValidateBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Would this code work for this subject and plan? `reason`: unknown, inactive, expired,
        exhausted, plan_not_eligible, first_time_only or already_used.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/coupons/validate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_coupon(
        self,
        coupon_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteBillingCouponsByIdResponse:
        """Delete a code and stop it being used. Subscriptions that already have the discount keep
        it.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/billing/coupons/{_enc(coupon_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_coupon(
        self,
        coupon_id: str,
    ) -> cm.GetBillingCouponsResponseDataItem:
        """Read one discount code."""
        return self._t.request(
            method="GET",
            path=f"/v1/billing/coupons/{_enc(coupon_id)}",
        )

    def update_coupon(
        self,
        coupon_id: str,
        body: cm.PatchBillingCouponsByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingCouponsResponseDataItem:
        """Deactivate or reactivate a code, rename it, or change its redemption cap, expiry
        (`expires_at`, null removes it), eligible plans (`plan_ids`, null means every plan) or
        first-time-only rule. The discount itself cannot change; create a new code for that.
        Atlas enforces these when it validates a code at checkout; the promotion code on your
        payment provider keeps the limits it was created with, so the provider's own hosted page
        is still bound by those.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/billing/coupons/{_enc(coupon_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_credits(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingCreditsResponse:
        """A subject's account-credit ledger and its balance per currency."""
        return self._t.request(
            method="GET",
            path="/v1/billing/credits",
            query=_qd({'subject_type': subject_type, 'subject_id': subject_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_credits(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetBillingCreditsResponseDataItem]:
        """Every item of :meth:`list_credits`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_credits(subject_type=subject_type, subject_id=subject_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_credit(
        self,
        body: cm.PostBillingCreditsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingCreditsResponseDataItem:
        """Post account credit (or a negative adjustment) to a subject. Idempotent on
        `idempotency_key`. Once the subject has a customer on the provider the credit lands on
        their balance and is applied to their next invoices; before that it waits for their
        first completed checkout.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/credits",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_invoices(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        status: Literal['draft', 'open', 'paid', 'uncollectible', 'void'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingInvoicesResponse:
        """List the invoices recorded for the plans you sell, newest first, optionally for one
        subject or status. Invoices arrive from your payment provider's signed webhooks, so a
        very new invoice appears once the webhook has been delivered.
        """
        return self._t.request(
            method="GET",
            path="/v1/billing/invoices",
            query=_qd({'subject_type': subject_type, 'subject_id': subject_id, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_invoices(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        status: Literal['draft', 'open', 'paid', 'uncollectible', 'void'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetBillingInvoicesResponseDataItem]:
        """Every item of :meth:`list_invoices`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_invoices(subject_type=subject_type, subject_id=subject_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_invoice(
        self,
        invoice_id: str,
    ) -> cm.GetBillingInvoicesByIdResponse:
        """Read one invoice, with the refunds made against it."""
        return self._t.request(
            method="GET",
            path=f"/v1/billing/invoices/{_enc(invoice_id)}",
        )

    def refund_invoice(
        self,
        invoice_id: str,
        body: cm.PostBillingInvoicesByIdRefundBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingInvoicesByIdResponseRefundsItem:
        """Refund all or part of a paid invoice on the payment provider that issued it (Stripe
        today; other providers answer 422 `unsupported`). `amount` is in minor units and
        defaults to what is left; the refunded total can never pass what was paid. A refund
        returns money only: it does not cancel the subscription or change an entitlement.
        `idempotency_key` is required: a retry with the same key returns the first refund (200)
        instead of making a second. Emits billing_refund.created.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/billing/invoices/{_enc(invoice_id)}/refund",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def create_store_link(
        self,
        body: cm.PostBillingStoreLinksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostBillingStoreLinksResponse:
        """Mint (or read back) the link token for an app-store subscription: pass `token` to the
        store when the person buys (StoreKit `appAccountToken`, Play Billing
        `obfuscatedExternalAccountId`) and the signed store notification is filed under this
        subject and plan. The same subject and plan always get the same token. `plan_id` must be
        an active plan sold through `appstore` or `googleplay` for this kind of subject. 201 on
        first mint, 200 after.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/store_links",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def extend_trial_subscription(
        self,
        subscription_id: str,
        body: cm.PostBillingSubscriptionsByIdExtendTrialBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostBillingSubscriptionsByIdExtendTrialResponse:
        """Move a trialing subscription's trial end later, on the payment provider (Stripe today;
        others answer 422 `unsupported`). Send exactly one of `days` (added to the current trial
        end) or `trial_end` (an absolute time, epoch ms or ISO). A trial can be extended by at
        most 365 days in total. Only a `trialing` subscription qualifies (409 otherwise).
        `idempotency_key` is required: a retry returns the first extension. Emits
        billing_trial.extended.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{_enc(subscription_id)}/extend_trial",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_usage(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        feature: str | None = None,
        since: str | None = None,
        until: str | None = None,
        period: Literal['current'] | None = None,
        events: Literal['true', 'false'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingUsageResponse:
        """Read back the usage Atlas recorded for a subject: the total and the total per feature
        over a time range, and with `events=true` the individual events (keyset-paged).
        `period=current` counts from the start of the subject's current billing period. Usage
        that only your payment provider holds is not here; ask the provider with POST
        /v1/billing/check.
        """
        return self._t.request(
            method="GET",
            path="/v1/billing/usage",
            query=_qd({'subject_type': subject_type, 'subject_id': subject_id, 'feature': feature, 'since': since, 'until': until, 'period': period, 'events': events, 'limit': limit, 'starting_after': starting_after}),
        )

    def batch_usage(
        self,
        body: cm.PostBillingUsageBatchBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostBillingUsageBatchResponse:
        """Report up to 100 usage events in one call. Each event is its own idempotent report with
        the fields of POST /v1/billing/usage, so a retried batch records only what is missing.
        The batch is not all-or-nothing: each result says `recorded`, `duplicate` or `failed`
        (with the error). The response is 200 whenever the batch itself was well formed.
        """
        return self._t.request(
            method="POST",
            path="/v1/billing/usage/batch",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class BlocklistIdentifiers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBlocklistIdentifiersResponse:
        """List blocklist identifiers that cannot sign up or sign in."""
        return self._t.request(
            method="GET",
            path="/v1/blocklist_identifiers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.BlocklistIdentifier]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostAllowlistIdentifiersBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.BlocklistIdentifier:
        """Block an identifier (email, @domain, or E.164 phone) from signing up and signing in."""
        return self._t.request(
            method="POST",
            path="/v1/blocklist_identifiers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        blocklist_identifier_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteBlocklistIdentifiersByIdResponse:
        """Remove a blocklist identifier. Another instance id is 404, never 403."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/blocklist_identifiers/{_enc(blocklist_identifier_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Changes:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        after: int | None = None,
        types: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChangesResponse:
        """Read the change feed: which resources changed since `after`, oldest first, in commit
        order. Each entry names the resource and what happened (`create`, `update`, `delete`)
        and carries `data`, the resource as it is now, in the same shape the webhooks use
        (private metadata is never included). `data` is null for a delete and for a resource
        that is gone by the time you read. `version` equals `seq`: drop an entry whose version
        is not higher than the one you hold for that resource. Changes to fields that only
        record activity (last sign-in, last use of a key, counters) do not create entries. 410
        `RESYNC_REQUIRED` when `after` is older than `retention_floor_seq`: read a snapshot
        instead. Entries are kept 30 days by default (`auth_config.changeFeed.retentionDays`).
        Needs an API key that is not limited to some organizations.
        """
        return self._t.request(
            method="GET",
            path="/v1/changes",
            query=_qd({'after': after, 'types': types, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        after: int | None = None,
        types: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetChangesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(after=after, types=types, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def list_consumers(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChangesConsumersResponse:
        """Every named consumer of the instance, across API keys: its name, the key that owns it
        (`key_id`), the position it acknowledged, when that last moved, and its lag behind the
        feed head. Behind-most first, up to 200. Use it to spot a reader that stopped, before
        its position falls behind the retention floor. Needs an API key that is not limited to
        some organizations.
        """
        return self._t.request(
            method="GET",
            path="/v1/changes/consumers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_consumers(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetChangesConsumersResponseDataItem]:
        """Every item of :meth:`list_consumers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_consumers(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_consumer(
        self,
        name: str,
    ) -> cm.GetChangesConsumersByNameResponse:
        """Where a named consumer has read up to, and how far behind it is. The position is held on
        the server so a restarted reader resumes where it left off. Positions belong to the API
        key that wrote them.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/changes/consumers/{_enc(name)}",
        )

    def set_consumers_ack(
        self,
        name: str,
        body: cm.PutChangesConsumersByNameAckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetChangesConsumersByNameResponse:
        """Acknowledge that a consumer has processed the feed up to `seq`. The position only moves
        forward: a lower or equal `seq` is accepted and changes nothing, so a retry is safe. A
        `seq` beyond `head_seq` is a 400. Consumer name: 1-64 characters from letters, digits,
        dot, dash and underscore. Names belong to the API key that uses them, so two keys can
        use the same name without sharing a position.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/changes/consumers/{_enc(name)}/ack",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_snapshot(
        self,
        resource_type: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChangesSnapshotByResourceTypeResponse:
        """A paginated, full list of the live resources of one type, in id order, pinned to the
        feed position it was taken at. Walk every page, then follow `GET
        /v1/changes?after={snapshot_seq}`: no change between the snapshot and the feed is
        missed, and an entry already reflected in a page is applied again harmlessly (apply by
        version). `next_cursor` carries the pin, so every page of one walk reports the same
        `snapshot_seq`. 410 `RESYNC_REQUIRED` when the pinned position has since been trimmed.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/changes/snapshot/{_enc(resource_type)}",
            query=_qd({'cursor': cursor, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_get_snapshot(
        self,
        resource_type: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Every item of :meth:`get_snapshot`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.get_snapshot(resource_type, cursor=cursor, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class ChatIntegrations:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChatIntegrationsResponse:
        """List chat integrations (Slack workspaces and Teams bots)."""
        return self._t.request(
            method="GET",
            path="/v1/chat_integrations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetChatIntegrationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostChatIntegrationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetChatIntegrationsResponseDataItem:
        """Connect a Slack workspace or a Teams bot using your own app. Slack credentials are
        checked with the workspace before saving.
        """
        return self._t.request(
            method="POST",
            path="/v1/chat_integrations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        chat_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteChatIntegrationsByIdResponse:
        """Remove an integration and its stored credentials."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        chat_integration_id: str,
    ) -> cm.GetChatIntegrationsResponseDataItem:
        """Read one chat integration."""
        return self._t.request(
            method="GET",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}",
        )

    def update(
        self,
        chat_integration_id: str,
        body: cm.PatchChatIntegrationsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetChatIntegrationsResponseDataItem:
        """Turn an integration on or off, change its routing, settings or credentials.
        `config.agent_approver_user_ids` lists who may decide agent access requests from chat.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_interactions(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChatIntegrationsByIdInteractionsResponse:
        """The latest button clicks and what became of them (applied, refused, unlinked, stale)."""
        return self._t.request(
            method="GET",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/interactions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_interactions(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetChatIntegrationsByIdInteractionsResponseDataItem]:
        """Every item of :meth:`list_interactions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_interactions(chat_integration_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def test(
        self,
        chat_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostChatIntegrationsByIdTestResponse:
        """Post a harmless test message to the default channel or conversation."""
        return self._t.request(
            method="POST",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_user_links(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChatIntegrationsByIdUserLinksResponse:
        """Chat users linked to Atlas users. A link is made automatically on first click when the
        chat profile email matches a verified email.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/user_links",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_user_links(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetChatIntegrationsByIdUserLinksResponseDataItem]:
        """Every item of :meth:`list_user_links`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_user_links(chat_integration_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_user_link(
        self,
        chat_integration_id: str,
        body: cm.PostChatIntegrationsByIdUserLinksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetChatIntegrationsByIdUserLinksResponseDataItem:
        """Link a chat user to an Atlas user by hand."""
        return self._t.request(
            method="POST",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/user_links",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_user_link(
        self,
        chat_integration_id: str,
        link_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteChatIntegrationsByIdResponse:
        """Remove the link between a chat user and an Atlas user."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/user_links/{_enc(link_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class CloudAccess:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_targets(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetCloudAccessTargetsResponse:
        """List the cloud access targets: AWS account and role tiles, Google Cloud workforce-pool
        tiles and Azure trust recipes.
        """
        return self._t.request(
            method="GET",
            path="/v1/cloud_access/targets",
            query=_qd({'provider': provider, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_targets(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetCloudAccessTargetsResponseDataItem]:
        """Every item of :meth:`list_targets`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_targets(provider=provider, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_target(
        self,
        body: cm.PostCloudAccessTargetsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetCloudAccessTargetsResponseDataItem:
        """Add a cloud access target. An AWS or Google Cloud target becomes a launcher tile that
        signs people in to that account and role (AWS: the Role, RoleSessionName,
        SessionDuration and PrincipalTag attributes) or workforce pool; assignment limits who
        sees it. Azure stores a federated-credential trust recipe. Config: aws: account_id (12
        digits), role_name, saml_provider_name, session_duration (900-43200 s), session_tags
        {tag key: user field}, transitive_tag_keys, partition (aws, aws-us-gov, aws-cn). gcp:
        pool_id, provider_id (a Workforce Identity Federation SAML provider). azure:
        app_object_id, subject, credential_name.
        """
        return self._t.request(
            method="POST",
            path="/v1/cloud_access/targets",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_target(
        self,
        target_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a target and its launcher tile."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_target(
        self,
        target_id: str,
    ) -> cm.GetCloudAccessTargetsResponseDataItem:
        """Read one cloud access target with its launch URL and assignment."""
        return self._t.request(
            method="GET",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}",
        )

    def update_target(
        self,
        target_id: str,
        body: cm.PatchCloudAccessTargetsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetCloudAccessTargetsResponseDataItem:
        """Change a target's name, config or assignment. The provider cannot change."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_targets_setup(
        self,
        target_id: str,
    ) -> cm.GetCloudAccessTargetsByIdSetupResponse:
        """What to configure on the cloud side for this target, with ready-to-run snippets: the AWS
        CLI command and role trust policy, the gcloud command for the workforce pool provider,
        or the Azure federated credential.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}/setup",
        )


class Compliance:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_inactive_users_preview(
        self,
        *,
        limit: int | None = None,
    ) -> cm.GetComplianceInactiveUsersPreviewResponse:
        """A dry run of the inactive-user policy: who would be warned and who acted on right now,
        without doing anything. Works with the policy off, to size it before turning it on.
        """
        return self._t.request(
            method="GET",
            path="/v1/compliance/inactive_users/preview",
            query=_qd({'limit': limit}),
        )

    def get_posture(
        self,
    ) -> cm.GetCompliancePostureResponse:
        """The live compliance posture: which controls the configuration turns on (data rights
        deadline, erasure window, ownership hand-over, policy acceptance, cookie consent store,
        age gating, inactive-user policy, record of processing, downstream erasure) and counts
        of data rights work. Configuration and counts only: no user data and no secrets.
        """
        return self._t.request(
            method="GET",
            path="/v1/compliance/posture",
        )

    def list_reports(
        self,
        *,
        kind: Literal['posture', 'ropa'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetComplianceReportsResponse:
        """The kept reports, newest first (claims only; fetch one for its signed form)."""
        return self._t.request(
            method="GET",
            path="/v1/compliance/reports",
            query=_qd({'kind': kind, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_reports(
        self,
        *,
        kind: Literal['posture', 'ropa'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetComplianceReportsResponseDataItem]:
        """Every item of :meth:`list_reports`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_reports(kind=kind, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_report(
        self,
        body: cm.PostComplianceReportsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetComplianceReportsResponseDataItem:
        """Generate a posture or record-of-processing report, sign it with the instance key and
        keep it. An auditor can check the signed report against the instance's public keys
        (jwks_uri) later. Emits compliance.report_generated. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/compliance/reports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_report(
        self,
        report_id: str,
    ) -> cm.GetComplianceReportsResponseDataItem:
        """One kept report with its signed form (report), key id and jwks_uri."""
        return self._t.request(
            method="GET",
            path=f"/v1/compliance/reports/{_enc(report_id)}",
        )

    def get_ropa(
        self,
    ) -> cm.GetComplianceRopaResponse:
        """The live record of processing built from compliance.dataPolicy: the controller, each
        processing activity (purpose, legal basis, data categories, subjects, recipients,
        transfers, retention), retention windows, Atlas's sub-processors, and findings (a
        consent basis with nothing to record it, an activity with no retention, a transfer with
        no recipient).
        """
        return self._t.request(
            method="GET",
            path="/v1/compliance/ropa",
        )


class Config:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_limits(
        self,
    ) -> cm.GetConfigLimitsResponse:
        """The limits the write routes enforce that a config tool can check up front: roles per
        resource type, permissions per app role, implied permissions per permission, key
        patterns and text lengths. `atlas plan` validates a file against these before it writes
        anything.
        """
        return self._t.request(
            method="GET",
            path="/v1/config/limits",
        )


class ConnectionActions:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionActionsResponse:
        """The action catalog: typed operations per provider (GitHub, Slack, Notion, HubSpot,
        Google and more), first-party and your own definitions.
        """
        return self._t.request(
            method="GET",
            path="/v1/connection_actions",
            query=_qd({'provider': provider, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetConnectionActionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(provider=provider, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_types(
        self,
        *,
        provider: str | None = None,
    ) -> cm.GetConnectionActionsTypesResponse:
        """TypeScript declarations for the action catalog (every provider, or one with `provider`):
        `ConnectionActionCatalog[provider][action] = { input, output }`, generated from the same
        schemas Atlas validates with, plus `ConnectionActionInput` and `ConnectionActionOutput`
        helpers. Save `source` to a .ts file to type `connections.runAction` end to end.
        """
        return self._t.request(
            method="GET",
            path="/v1/connection_actions/types",
            query=_qd({'provider': provider}),
        )

    def delete(
        self,
        provider: str,
        name: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a custom action definition (a first-party action of the same name comes back)."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/connection_actions/{_enc(provider)}/{_enc(name)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        provider: str,
        name: str,
    ) -> cm.GetConnectionActionsResponseDataItem:
        """One action with its input schema."""
        return self._t.request(
            method="GET",
            path=f"/v1/connection_actions/{_enc(provider)}/{_enc(name)}",
        )

    def set(
        self,
        provider: str,
        name: str,
        body: cm.PutConnectionActionsByProviderByNameBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionActionsResponseDataItem:
        """Define or replace a custom action: data only (an input schema, a request template, a
        response mapping), never code. A definition with a first-party action's name replaces it
        for this instance.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/connection_actions/{_enc(provider)}/{_enc(name)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ConnectionProviderChanges:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        provider: str | None = None,
        status: Literal['open', 'acknowledged', 'resolved', 'all'] | None = None,
        kind: Literal['output_drift', 'deprecation', 'endpoint_gone'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionProviderChangesResponse:
        """The provider change radar: what providers changed under your actions (a response that no
        longer matches the declared output, a deprecation or sunset notice, an endpoint that is
        gone), newest first. Open changes by default. A change is announced once with the
        `connection.provider_change` webhook.
        """
        return self._t.request(
            method="GET",
            path="/v1/connection_provider_changes",
            query=_qd({'provider': provider, 'status': status, 'kind': kind, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        provider: str | None = None,
        status: Literal['open', 'acknowledged', 'resolved', 'all'] | None = None,
        kind: Literal['output_drift', 'deprecation', 'endpoint_gone'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetConnectionProviderChangesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(provider=provider, status=status, kind=kind, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get(
        self,
        connection_provider_change_id: str,
    ) -> cm.GetConnectionProviderChangesResponseDataItem:
        """Read one provider change."""
        return self._t.request(
            method="GET",
            path=f"/v1/connection_provider_changes/{_enc(connection_provider_change_id)}",
        )

    def acknowledge(
        self,
        connection_provider_change_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderChangesResponseDataItem:
        """Mark a change as seen. It stays listed under acknowledged and reopens only if you mark
        it resolved and it happens again.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connection_provider_changes/{_enc(connection_provider_change_id)}/acknowledge",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def resolve(
        self,
        connection_provider_change_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderChangesResponseDataItem:
        """Mark a change as dealt with. If the provider does it again the change reopens."""
        return self._t.request(
            method="POST",
            path=f"/v1/connection_provider_changes/{_enc(connection_provider_change_id)}/resolve",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class ConnectionProviderEventLog:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        topic: str | None = None,
        kind: Literal['lifecycle', 'business'] | None = None,
    ) -> cm.GetConnectionProviderEventLogResponse:
        """The persisted provider events of every connection in the instance, newest first, without
        payloads: the place to look after your webhook endpoint was down. Page with
        `starting_after` and replay what was missed with POST
        /v1/connections/{id}/provider_events/{eventId}/replay.
        """
        return self._t.request(
            method="GET",
            path="/v1/connection_provider_event_log",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'topic': topic, 'kind': kind}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
        topic: str | None = None,
        kind: Literal['lifecycle', 'business'] | None = None,
    ) -> Iterator[cm.GetConnectionProviderEventLogResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, topic=topic, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class ConnectionProviderTopics:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetConnectionProviderTopicsResponse:
        """The business topics this instance subscribes provider connections to (Shopify
        orders/create, products/update; eBay ItemSold and Commerce Notification topics).
        Deliveries of these topics arrive as connection.provider_event with kind business.
        """
        return self._t.request(
            method="GET",
            path="/v1/connection_provider_topics",
        )

    def set(
        self,
        body: cm.PutConnectionProviderTopicsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderTopicsResponse:
        """Replace the instance's business topics: { topics: { shopify: [...], ebay: [...] } }, up
        to 50 per provider, spelled as the provider spells them (Shopify orders/create; eBay
        Trading events such as ItemSold, or Commerce Notification topic ids in
        UPPER_SNAKE_CASE). Connections made afterwards subscribe automatically; call POST
        /v1/connections/{id}/provider_subscriptions/sync for existing ones. A topic not listed
        here is acknowledged and ignored on delivery.
        """
        return self._t.request(
            method="PUT",
            path="/v1/connection_provider_topics",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ConnectionProviders:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def delete_policy(
        self,
        provider: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove the instance policy for a provider (back to the defaults)."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/connection_providers/{_enc(provider)}/policy",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_policy(
        self,
        provider: str,
    ) -> cm.GetConnectionProvidersByProviderPolicyResponse:
        """Read the instance policy for one provider's connections: unique_external_id, whether a
        webhook secret is stored, and the one ingress URL (events_url) for that provider's
        uninstall and revocation notices (shopify, bigcommerce, wix, square, ebay).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/connection_providers/{_enc(provider)}/policy",
        )

    def set_policy(
        self,
        provider: str,
        body: cm.PutConnectionProvidersByProviderPolicyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProvidersByProviderPolicyResponse:
        """Set the instance policy for one provider's connections. unique_external_id: true makes a
        connect or import answer 409 external_id_taken (with the other connection's id) when
        another owner already holds that provider account (a revoked connection does not count).
        webhook_secret is the secret the provider's uninstall ingress verifies with where it is
        not the app's client secret: eBay verification token, Square signature key, Wix public
        key (PEM), Etsy webhook signing secret; null clears it. Write-only.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/connection_providers/{_enc(provider)}/policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ConnectionReconnectSettings:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetConnectionReconnectSettingsResponse:
        """The hosted-reconnect settings: whether Atlas emails the owner a reconnect link when a
        connection needs authorization again, how long the link works, where the browser returns
        afterwards and which providers send the email.
        """
        return self._t.request(
            method="GET",
            path="/v1/connection_reconnect_settings",
        )

    def set(
        self,
        body: cm.PutConnectionReconnectSettingsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionReconnectSettingsResponse:
        """Replace the hosted-reconnect settings (a field left out returns to its default). With
        enabled true, the owner of an oauth connection that needs authorization again (a user,
        or an organization's technical contacts) gets one email per episode through the
        instance's own mail provider, never an Atlas key, with a link to a hosted page that
        restarts the provider consent. Nothing is sent while enabled is false, which is the
        default.
        """
        return self._t.request(
            method="PUT",
            path="/v1/connection_reconnect_settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Connections:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def complete_oauth(
        self,
        body: cm.PostConnectionsOauthCompleteBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsOauthCompleteResponse:
        """Finish a connect whose OAuth client has its own `redirect_uri`: your page received the
        provider's redirect (code and state) and forwards both here. The state is bound to the
        client it was started with, so a code forwarded against another client, another
        instance, or a `redirect_uri` that is not exactly the client's registered value is
        refused (400 OAUTH_STATE_INVALID or a validation error), and a state is single use and
        expires 15 minutes after the connect started. Atlas exchanges the code with the client's
        credentials and the same redirect URI the authorize call carried, and stores the token
        on the connection. Optional `query` carries other provider parameters from the redirect
        (a Shopify hmac). The browser alternative needs no API call: 302 the browser to the
        client's `forward_url` with the same query.
        """
        return self._t.request(
            method="POST",
            path="/v1/connections/oauth/complete",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def register_oauth_client(
        self,
        body: cm.PostConnectionsOauthClientsRegisterBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Create the OAuth client at the provider instead of by hand (dynamic client registration,
        RFC 7591). Atlas registers a web client whose redirect URI is the callback shown in the
        answer (or your `redirect_uri`), stores the returned credentials sealed, and records the
        registration. `token_endpoint_auth_method`: client_secret_basic (default),
        client_secret_post or private_key_jwt (Atlas generates the key and registers its public
        half). The endpoint must be https and public. An owner that already has a client for the
        provider and environment gets 409: delete it first. The secret, the registration token
        and any initial access token are never returned or logged.
        """
        return self._t.request(
            method="POST",
            path="/v1/connections/oauth_clients/register",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_relay_limits(
        self,
    ) -> cm.GetConnectionsRelayLimitsResponse:
        """The relay size limits of this instance: the largest request body and response body, in
        bytes. Defaults are 256 KiB and 1 MiB.
        """
        return self._t.request(
            method="GET",
            path="/v1/connections/relay_limits",
        )

    def set_relay_limits(
        self,
        body: cm.PutConnectionsRelayLimitsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsRelayLimitsResponse:
        """Raise the relay size limits of this instance, up to 25 MiB (26214400 bytes) each:
        request_bytes for the body or multipart sent through POST /v1/connections/{id}/relay,
        response_bytes for what comes back. The relay never reads more than the limit into
        memory, and a response over it is cut with truncated true. Values below the defaults
        (256 KiB, 1 MiB) are refused.
        """
        return self._t.request(
            method="PUT",
            path="/v1/connections/relay_limits",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_token_limits(
        self,
    ) -> cm.GetConnectionsTokenLimitsResponse:
        """The connection-token rate limits of this instance (requests per minute on GET
        /v1/connections/{id}/token, POST /v1/connections/{id}/token/refresh and POST
        /v1/connections/tokens/batch) and how much of the current one-minute window is used:
        per_key (the calling secret key, all connections; default 6,000), per_connection (one
        connection, per key; default 300; no usage shown) per_app (one provider app client: the
        instance client shared by every owner, or an owner's own client; no limit unless you set
        one) and providers (one provider across all of the instance's keys; no limit unless you
        set one). With per_app set, token reads carry x-app-ratelimit-limit, x-app-ratelimit-
        remaining and x-app-ratelimit-reset (seconds) for the app client the connection runs
        under. Conditional reads (If-None-Match) get ten times the per-key and per-connection
        budgets and do not count against provider limits.
        """
        return self._t.request(
            method="GET",
            path="/v1/connections/token_limits",
        )

    def set_token_limits(
        self,
        body: cm.PutConnectionsTokenLimitsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsTokenLimitsResponse:
        """Set this instance's connection-token rate limits, in requests per minute. per_key goes
        up to 60,000 and per_connection up to 3,000 (ten times the defaults); null restores the
        default. per_app (up to 60,000; null removes it) is one shared budget per provider app
        client, on top of the per-key and per-connection ones, answered with 429 and Retry-After
        when spent. providers maps a provider id to an instance-wide limit for that provider's
        connections (up to 60,000; null removes one; up to 100 providers) and merges into the
        stored map; providers null clears them all. Takes effect at once. Over a provider limit,
        the token routes answer 429 with Retry-After and the batch route marks those ids
        rate_limited / provider_limit.
        """
        return self._t.request(
            method="PUT",
            path="/v1/connections/token_limits",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_access_rules(
        self,
        connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove every access rule: the connection is open again."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/connections/{_enc(connection_id)}/access_rules",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_access_rules(
        self,
        connection_id: str,
    ) -> cm.GetConnectionsByIdAccessRulesResponse:
        """Who may use this connection's credential. No rule means open to every key that has the
        route's scope; one rule or more restricts the connection to the principals the rules
        name.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/access_rules",
        )

    def set_access_rules(
        self,
        connection_id: str,
        body: cm.PutConnectionsByIdAccessRulesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsByIdAccessRulesResponse:
        """Replace the connection's access rules (at most 100; an empty list opens the connection
        again). Rules gate credential use: `read_token` (token reads and refreshes), `relay`,
        `run_actions` and `sign`; a key that no rule names gets 403 with reason
        `connection_access_denied`. Managing the connection and its rules stays under
        organizations:read and organizations:write.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/connections/{_enc(connection_id)}/access_rules",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_actions(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionActionsResponse:
        """The actions available on a connection (its provider's catalog)."""
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/actions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_actions(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetConnectionActionsResponseDataItem]:
        """Every item of :meth:`list_actions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_actions(connection_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_action(
        self,
        connection_id: str,
        name: str,
        body: cm.PostConnectionsByIdActionsByNameBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsByIdActionsByNameResponse:
        """Run an action on a connection: the input is validated against the action's schema, the
        connection's granted scopes are checked, and the call goes through the relay (host
        allow-list, credential, one refresh, retry on 429). `dry_run` returns the request
        without sending it; `all_pages` walks the action's pagination. The audit log records the
        action, provider and status, never the input.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/actions/{_enc(name)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_activity(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        kind: Literal['relay', 'token_read', 'token_refresh', 'token_exchange', 'status', 'provider_event', 'reconnect_email', 'reconnect_started'] | None = None,
        outcome: Literal['ok', 'error'] | None = None,
        since: str | None = None,
    ) -> cm.GetConnectionsByIdActivityResponse:
        """The connection's activity log, newest first: relay calls (method, host, status,
        duration, attempts: never the path, query, headers or body), sampled token reads,
        refreshes, status transitions (needs reauthorization, recovered, revoked), provider
        events and the reconnect flow. Kept 30 days. Use it to answer "why did this connection
        stop working" without the provider's dashboard.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/activity",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'kind': kind, 'outcome': outcome, 'since': since}),
        )

    def iter_list_activity(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        kind: Literal['relay', 'token_read', 'token_refresh', 'token_exchange', 'status', 'provider_event', 'reconnect_email', 'reconnect_started'] | None = None,
        outcome: Literal['ok', 'error'] | None = None,
        since: str | None = None,
    ) -> Iterator[cm.GetConnectionsByIdActivityResponseDataItem]:
        """Every item of :meth:`list_activity`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_activity(connection_id, limit=limit, kind=kind, outcome=outcome, since=since, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def list_provider_events(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        topic: str | None = None,
        kind: Literal['lifecycle', 'business'] | None = None,
    ) -> cm.GetConnectionProviderEventLogResponse:
        """The verified provider events kept for this connection (uninstall and revocation notices,
        the business topics the instance subscribed to), newest first, without payloads. Kept 30
        days. Read one with GET /v1/connections/{id}/provider_events/{eventId}; announce it
        again with POST .../replay.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/provider_events",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'topic': topic, 'kind': kind}),
        )

    def iter_list_provider_events(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        topic: str | None = None,
        kind: Literal['lifecycle', 'business'] | None = None,
    ) -> Iterator[cm.GetConnectionProviderEventLogResponseDataItem]:
        """Every item of :meth:`list_provider_events`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_provider_events(connection_id, limit=limit, topic=topic, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_provider_event(
        self,
        connection_id: str,
        event_id: str,
    ) -> cm.GetConnectionProviderEventLogResponseDataItem:
        """One persisted provider event with its payload (business topics; absent when it was over
        256 KB).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/provider_events/{_enc(event_id)}",
        )

    def replay_provider_event(
        self,
        connection_id: str,
        event_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderEventLogResponseDataItem:
        """Announce a stored provider event again as a connection.provider_event webhook, with
        `replayed: true`, the same `delivery_id` and `event_id`, so a receiver that deduplicates
        on the delivery id can tell. It only re-announces: a replayed uninstall does not revoke
        the connection a second time. Audited as connection.provider_event_replayed.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/provider_events/{_enc(event_id)}/replay",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_provider_subscriptions(
        self,
        connection_id: str,
    ) -> cm.GetConnectionsByIdProviderSubscriptionsResponse:
        """What was last subscribed at the provider for this connection, per topic, with the
        provider's own error when a subscription failed (for example Shopify refusing orders
        topics until the app is approved for protected customer data).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/provider_subscriptions",
        )

    def sync_provider_subscription(
        self,
        connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsByIdProviderSubscriptionsResponse:
        """Register the instance's configured business topics for this connection at the provider
        (Shopify webhookSubscriptionCreate per topic; eBay SetNotificationPreferences for
        Trading events and Commerce Notification subscriptions for topic ids) pointing at the
        provider's ingress URL, and return the outcome per topic. Idempotent. A provider refusal
        is reported per topic, not as an error status.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/provider_subscriptions/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def reconnect_link(
        self,
        connection_id: str,
        body: cm.PostConnectionsByIdReconnectLinkBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsByIdReconnectLinkResponse:
        """Mint a hosted reconnect link for an oauth connection (not a revoked one), to send
        through your own channel, or set `send_email` to have Atlas email it to the owner
        through the instance's own mail provider. The URL is returned once. Opening it spends
        nothing; the page's button restarts the provider consent. Honours Idempotency-Key.
        Audited as connection.reconnect_link_issued.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/reconnect_link",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def create_scoped_token(
        self,
        connection_id: str,
        body: cm.PostConnectionsByIdScopedTokensBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsByIdScopedTokensResponse:
        """Mint a scoped relay token: a signed credential for ONE connection that only works
        through POST /v1/connection_relay/scoped, for the listed HTTP methods and https URL
        prefixes, and expires within the hour. It narrows what a caller can do with the
        connection without touching the stored provider token (which stays in the vault).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/scoped_tokens",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def sign(
        self,
        connection_id: str,
        body: cm.PostConnectionsByIdSignBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsByIdSignResponse:
        """Sign a request you send yourself with the connection's `config.signing` preset
        (tiktok_shop, kaufland, walmart_marketplace, poizon, or a generic hmac template with an
        algorithm, a canonical string template and a header or query placement). Describe the
        request (method, https url on an allowed host, optional query, headers and body); the
        answer holds the headers and query parameters to add and the final url. The secret never
        leaves Atlas. Headers that carry the access token (TikTok Shop `x-tts-access-token`,
        Walmart `WM_SEC.ACCESS_TOKEN`) are returned only to a key that also has
        oauth_tokens:read. Needs connections:sign.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/sign",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def downscope_token(
        self,
        connection_id: str,
        body: cm.PostConnectionsByIdTokenDownscopeBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """A short-lived access token limited to a subset of the scopes the connection was granted,
        to hand to a less-trusted caller (an agent, a plugin). The provider mints it from the
        stored refresh token with the scope narrowed; the connection itself is unchanged. 422
        `invalid_scope` when a scope was not granted; 422 `downscope_unsupported` when the
        provider cannot issue a narrower token (Microsoft identity platform v2.0 can).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/token/downscope",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def exchange_token(
        self,
        connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsByIdTokenExchangeResponse:
        """Swap a connection's non-expiring token for an expiring access token and a refresh token,
        so Atlas can refresh it from then on (Shopify offline tokens issued before expiring
        tokens existed). Needs connections:token and organizations:write. 409 when the
        connection already has an expiring token or is not connected; 422 OAUTH_EXCHANGE_FAILED
        with the provider's error when Shopify refuses, and the connection keeps the token it
        had. Audited as connection.token_exchanged.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/token/exchange",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def transfer(
        self,
        connection_id: str,
        body: cm.PostConnectionsByIdTransferBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsResponseDataItem:
        """Transfer a connection to another organization, user or external owner without
        reconnecting: the stored tokens move with it. Audited as connection.owner_changed and
        announced with the connection.owner_changed webhook (`owner` the new owner,
        `previous_owner` the old one). 404 for an unknown new owner. Moving it to its current
        owner changes nothing.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/transfer",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_triggers(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionsByIdTriggersResponse:
        """The triggers of a connection."""
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/triggers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_triggers(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetConnectionsByIdTriggersResponseDataItem]:
        """Every item of :meth:`list_triggers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_triggers(connection_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_trigger(
        self,
        connection_id: str,
        body: cm.PostConnectionsByIdTriggersBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsByIdTriggersResponseDataItem:
        """Subscribe to provider events. webhook: Atlas creates a verified ingress endpoint and,
        for providers whose API allows it (GitHub), registers the webhook there (filter: owner,
        repo); verified deliveries are forwarded to target_url. Other providers get an
        ingress_url to paste into the provider and need `scheme`. poll: a read-only catalog
        action runs on an interval and each new item becomes a `connection.trigger_fired` event.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/triggers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_trigger(
        self,
        connection_id: str,
        trigger_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteConnectionsByIdTriggersByTriggerIdResponse:
        """Remove a trigger: the provider webhook is deleted first when Atlas registered it
        (`provider_unregistered` says what happened; the connection must allow DELETE for that),
        then the ingress endpoint.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/connections/{_enc(connection_id)}/triggers/{_enc(trigger_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_trigger(
        self,
        connection_id: str,
        trigger_id: str,
    ) -> cm.GetConnectionsByIdTriggersResponseDataItem:
        """Read one trigger of a connection."""
        return self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/triggers/{_enc(trigger_id)}",
        )

    def update_trigger(
        self,
        connection_id: str,
        trigger_id: str,
        body: cm.PatchConnectionsByIdTriggersByTriggerIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsByIdTriggersResponseDataItem:
        """Pause or resume a trigger."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/connections/{_enc(connection_id)}/triggers/{_enc(trigger_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Containments:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetContainmentsResponse:
        """Containment records, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/containments",
            query=_qd({'user_id': user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetContainmentsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(user_id=user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class CookieConsents:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        user_id: str | None = None,
        subject: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetCookieConsentsResponse:
        """The cookie consent ledger, newest first, with the visitor id. Filter by user_id or
        subject.
        """
        return self._t.request(
            method="GET",
            path="/v1/cookie_consents",
            query=_qd({'user_id': user_id, 'subject': subject, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        user_id: str | None = None,
        subject: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetCookieConsentsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(user_id=user_id, subject=subject, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_subject(
        self,
        subject: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteCookieConsentsSubjectsBySubjectResponse:
        """Erase one visitor's records (an erasure request from someone who is not a user).
        Audited.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/cookie_consents/subjects/{_enc(subject)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_subject(
        self,
        subject: str,
    ) -> cm.GetCookieConsentsSubjectsBySubjectResponse:
        """One visitor's current choice and history. 404 when nothing is recorded."""
        return self._t.request(
            method="GET",
            path=f"/v1/cookie_consents/subjects/{_enc(subject)}",
        )

    def get_summary(
        self,
        *,
        days: int | None = None,
    ) -> cm.GetCookieConsentsSummaryResponse:
        """Choices recorded in the last days (default 30): distinct visitors, how many sent a
        Global Privacy Control signal, and how many allow each category.
        """
        return self._t.request(
            method="GET",
            path="/v1/cookie_consents/summary",
            query=_qd({'days': days}),
        )


class DataSubjectRequests:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_downstream(
        self,
        data_subject_request_id: str,
    ) -> cm.GetDataSubjectRequestsByIdDownstreamResponse:
        """What each enabled downstream erasure connector has done for this request: pending, done
        (acknowledged by the system or marked by an operator) or not applicable. complete is
        true when every enabled connector is done or not applicable.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/downstream",
        )

    def create_downstream(
        self,
        data_subject_request_id: str,
        connector_id: str,
        body: cm.PostDataSubjectRequestsByIdDownstreamByConnectorIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDataSubjectRequestsByIdDownstreamResponse:
        """Mark a manual erasure connector done (or not_applicable) for this request. An ack
        connector confirms itself and is refused (400). Marking twice keeps the first answer.
        Audited. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/downstream/{_enc(connector_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def run_downstream(
        self,
        data_subject_request_id: str,
        connector_id: str,
        body: cm.PostDataSubjectRequestsByIdDownstreamByConnectorIdRunBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostDataSubjectRequestsByIdDownstreamByConnectorIdRunResponse:
        """Run (or retry) an automatic (mode api) erasure connector for this erasure request, for
        example after a failed run. With dry_run true it only proves the key works and says what
        would be looked up; nothing is deleted. A connector that already finished is skipped.
        Audited. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/downstream/{_enc(connector_id)}/run",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def extend(
        self,
        data_subject_request_id: str,
        body: cm.PostDataSubjectRequestsByIdExtendBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DataSubjectRequest:
        """Move the response deadline of an open data subject request later, with the reason
        recorded on it. due_at must be after the current deadline and within three years of the
        request. Re-arms dsr.overdue for the new date. Audited. 409 when the request is already
        finished.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/extend",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_notes(
        self,
        data_subject_request_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDataSubjectRequestsByIdNotesResponse:
        """Internal notes on a request, oldest first. Never shown to the data subject."""
        return self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/notes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_notes(
        self,
        data_subject_request_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetDataSubjectRequestsByIdNotesResponseDataItem]:
        """Every item of :meth:`list_notes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_notes(data_subject_request_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_note(
        self,
        data_subject_request_id: str,
        body: cm.PostDataSubjectRequestsByIdNotesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDataSubjectRequestsByIdNotesResponseDataItem:
        """Add an internal note to a request (at most 4000 characters). Honours Idempotency-Key."""
        return self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/notes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_receipt(
        self,
        data_subject_request_id: str,
    ) -> cm.GetDataSubjectRequestsByIdReceiptResponse:
        """The signed deletion receipt of a completed erasure: proof, signed with the instance key,
        that it ran. The claims carry ids and dates only (instance, request, subject id,
        requested/erased/scrub dates, steps, retention); verify the JWS in `receipt` with the
        keys at `jwks_uri`. Issued the first time it is asked for and stored, so asking again
        returns the same receipt. 409 for a request that is not a completed erasure.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/receipt",
        )

    def update_triage(
        self,
        data_subject_request_id: str,
        body: cm.PatchDataSubjectRequestsByIdTriageBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Triage a request: who works it, how urgent it is, free labels. Only what is sent
        changes; send at least one. Audited.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/triage",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class DesktopMfa:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_devices_passkeys(
        self,
        device_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDesktopMfaDevicesByIdPasskeysResponse:
        """List the passkeys registered through a workstation."""
        return self._t.request(
            method="GET",
            path=f"/v1/desktop_mfa/devices/{_enc(device_id)}/passkeys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_devices_passkeys(
        self,
        device_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetDesktopMfaDevicesByIdPasskeysResponseDataItem]:
        """Every item of :meth:`list_devices_passkeys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_devices_passkeys(device_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_devices_passkey(
        self,
        device_id: str,
        passkey_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDesktopMfaDevicesByIdPasskeysByPasskeyIdResponse:
        """Remove a passkey registered through a workstation. It stops answering the passkey factor
        at once.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/desktop_mfa/devices/{_enc(device_id)}/passkeys/{_enc(passkey_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Dev:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def delete_emails(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDevEmailsResponse:
        """Empty the development email inbox (development instances only). Refused on a production
        instance (422 TEST_MODE_ONLY).
        """
        return self._t.request(
            method="DELETE",
            path="/v1/dev/emails",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_emails(
        self,
        *,
        to: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDevEmailsResponse:
        """Read the development email inbox (development instances only), newest first. A
        development instance with no email provider stores the end-user mail it would have sent
        (verification codes, password reset, magic links) here instead of failing with
        EMAIL_DELIVERY_NOT_CONFIGURED; nothing is delivered. Messages are kept for 24 hours, at
        most 200 per instance. Filter with `to`. Refused on a production instance (422
        TEST_MODE_ONLY), which keeps failing with EMAIL_DELIVERY_NOT_CONFIGURED when it has no
        provider.
        """
        return self._t.request(
            method="GET",
            path="/v1/dev/emails",
            query=_qd({'to': to, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_emails(
        self,
        *,
        to: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetDevEmailsResponseDataItem]:
        """Every item of :meth:`list_emails`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_emails(to=to, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class DeviceAssurancePolicies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDeviceAssurancePoliciesResponse:
        """List the device assurance policies."""
        return self._t.request(
            method="GET",
            path="/v1/device_assurance_policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetDeviceAssurancePoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostDeviceAssurancePoliciesBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceAssurancePoliciesResponseDataItem:
        """Create a device assurance policy: per-platform minimum OS version (or "newest major
        minus N"), disk encryption, screen lock, secure hardware, jailbreak/root, firewall and
        EDR checks, and a grace period. A device must pass every enabled policy for its
        platform; its `compliant` flag, and so the `deviceTrust` access-policy condition,
        follows the verdict. Existing devices are re-evaluated.
        """
        return self._t.request(
            method="POST",
            path="/v1/device_assurance_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def evaluate(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostDeviceAssurancePoliciesEvaluateResponse:
        """Re-evaluate every device against the current assurance policies."""
        return self._t.request(
            method="POST",
            path="/v1/device_assurance_policies/evaluate",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        device_assurance_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDeviceAssurancePoliciesByIdResponse:
        """Delete a device assurance policy. Devices are re-evaluated."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/device_assurance_policies/{_enc(device_assurance_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        device_assurance_policy_id: str,
    ) -> cm.GetDeviceAssurancePoliciesResponseDataItem:
        """Read one device assurance policy."""
        return self._t.request(
            method="GET",
            path=f"/v1/device_assurance_policies/{_enc(device_assurance_policy_id)}",
        )

    def update(
        self,
        device_assurance_policy_id: str,
        body: cm.PatchDeviceAssurancePoliciesByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceAssurancePoliciesResponseDataItem:
        """Update a device assurance policy. Devices are re-evaluated."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/device_assurance_policies/{_enc(device_assurance_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class DeviceIntegrations:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDeviceIntegrationsResponse:
        """List the device pull integrations. Credentials are never returned."""
        return self._t.request(
            method="GET",
            path="/v1/device_integrations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetDeviceIntegrationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostDeviceIntegrationsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceIntegrationsResponseDataItem:
        """Connect a device source that Atlas pulls on a schedule: Microsoft Intune (Graph,
        `tenantId` + app client credentials with DeviceManagementManagedDevices.Read.All), Jamf
        Pro (`baseUrl` + API client), CrowdStrike Falcon (`cloud` + API client with Zero Trust
        Assessment and Hosts read; `minZtaScore`, `userEmailDomain`), Fleet (`baseUrl` + API
        token) or Google Chrome / ChromeOS (service account with domain-wide delegation).
        Credentials are write-only.
        """
        return self._t.request(
            method="POST",
            path="/v1/device_integrations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        device_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDeviceIntegrationsByIdResponse:
        """Delete a device integration. Devices already pulled stay in the registry."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        device_integration_id: str,
    ) -> cm.GetDeviceIntegrationsResponseDataItem:
        """Read one device integration and its last sync result."""
        return self._t.request(
            method="GET",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}",
        )

    def update(
        self,
        device_integration_id: str,
        body: cm.PatchDeviceIntegrationsByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceIntegrationsResponseDataItem:
        """Change a device integration (name, config, credentials, interval, paused or active)."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def sync(
        self,
        device_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostDeviceIntegrationsByIdSyncResponse:
        """Pull the integration now."""
        return self._t.request(
            method="POST",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class DeviceSso:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_registrations(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDeviceSsoRegistrationsResponse:
        """List devices registered for device-bound SSO, optionally for one `user_id`."""
        return self._t.request(
            method="GET",
            path="/v1/device_sso/registrations",
            query=_qd({'user_id': user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_registrations(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetDeviceSsoRegistrationsResponseDataItem]:
        """Every item of :meth:`list_registrations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_registrations(user_id=user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_registration(
        self,
        registration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDeviceSsoRegistrationsByIdResponse:
        """Delete a device registration and its sessions."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/device_sso/registrations/{_enc(registration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_registration(
        self,
        registration_id: str,
    ) -> cm.GetDeviceSsoRegistrationsResponseDataItem:
        """Read one device registration."""
        return self._t.request(
            method="GET",
            path=f"/v1/device_sso/registrations/{_enc(registration_id)}",
        )

    def revoke_registration(
        self,
        registration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceSsoRegistrationsResponseDataItem:
        """Revoke a device registration. Every refresh token it holds stops working at once and its
        next call is refused.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/device_sso/registrations/{_enc(registration_id)}/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Devices:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_compliance_history(
        self,
        device_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDevicesByIdComplianceHistoryResponse:
        """The compliance transitions of one device, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/devices/{_enc(device_id)}/compliance_history",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_compliance_history(
        self,
        device_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetDevicesByIdComplianceHistoryResponseDataItem]:
        """Every item of :meth:`list_compliance_history`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_compliance_history(device_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class Diagnostics:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_traces(
        self,
        *,
        user_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        code: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDiagnosticsTracesResponse:
        """Search refusal traces of the last 7 days, newest first. Filters: `user_id`, `since` and
        `until` (epoch milliseconds or ISO 8601), `code` (an error code). Paged with `limit` and
        `starting_after` like every list. Each item is the same object GET
        /v1/diagnostics/traces/{id} returns. Needs diagnostics:read.
        """
        return self._t.request(
            method="GET",
            path="/v1/diagnostics/traces",
            query=_qd({'user_id': user_id, 'since': since, 'until': until, 'code': code, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_traces(
        self,
        *,
        user_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        code: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetDiagnosticsTracesResponseDataItem]:
        """Every item of :meth:`list_traces`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_traces(user_id=user_id, since=since, until=until, code=code, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_trace(
        self,
        trace_id: str,
    ) -> cm.GetDiagnosticsTracesResponseDataItem:
        """Explain a refusal. Every error response carries a `trace_id` (and an `Atlas-Trace-Id`
        header); this returns the decision chain behind it: the request, the credential, the
        checks it passed and the one that refused (`decided_by`: captcha, policy, risk,
        rate_limit, scope, step_up, access_policy, verification or validation), with the error
        `code`, `reason`, a plain `explanation` and safe details such as the limit or the
        missing scope. Traces name the user when the request acted for one. Kept 7 days; rate-
        limit refusals are sampled (one per route per 10 seconds). Another instance trace is
        404. Needs diagnostics:read.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/diagnostics/traces/{_enc(trace_id)}",
        )


class DsrConsole:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_requests(
        self,
        *,
        status: str | None = None,
        type: str | None = None,
        assignee: str | None = None,
        unassigned: bool | None = None,
        priority: Literal['low', 'normal', 'high', 'urgent'] | None = None,
        label: str | None = None,
        overdue: bool | None = None,
        due_within_days: int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDsrConsoleRequestsResponse:
        """Data subject requests with triage filters, newest first. A request carries assignee,
        priority and labels next to its deadline and overdue flag.
        """
        return self._t.request(
            method="GET",
            path="/v1/dsr_console/requests",
            query=_qd({'status': status, 'type': type, 'assignee': assignee, 'unassigned': unassigned, 'priority': priority, 'label': label, 'overdue': overdue, 'due_within_days': due_within_days, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_requests(
        self,
        *,
        status: str | None = None,
        type: str | None = None,
        assignee: str | None = None,
        unassigned: bool | None = None,
        priority: Literal['low', 'normal', 'high', 'urgent'] | None = None,
        label: str | None = None,
        overdue: bool | None = None,
        due_within_days: int | None = None,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Every item of :meth:`list_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_requests(status=status, type=type, assignee=assignee, unassigned=unassigned, priority=priority, label=label, overdue=overdue, due_within_days=due_within_days, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_summary(
        self,
    ) -> cm.GetDsrConsoleSummaryResponse:
        """The data rights board in one call: open, overdue, due within 7 days, unassigned, and
        counts by status, type and assignee.
        """
        return self._t.request(
            method="GET",
            path="/v1/dsr_console/summary",
        )


class Entitlements:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def consume(
        self,
        body: cm.PostEntitlementsConsumeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostEntitlementsConsumeResponse:
        """Spend units of a plan feature for a user or organization, atomically and exactly once
        per `idempotency_key`. The answer is the decision (200 whether allowed or not; `reason`
        is `not_entitled` or `limit_reached`); a retry with the same key replays it and never
        spends twice. Who counts: when the subject's live subscription is on an entitlement
        provider (Autumn, Commet) that provider owns the balance and `source` is `provider`;
        otherwise Atlas counts (`source` `atlas`) against the plan's numeric limit for the
        feature (`-1` or no limit is unlimited) in the current billing period, or the UTC
        calendar month when there is no period. For `atlas` the limit check and the write are
        one transaction, so concurrent consumes can never pass the limit. A consume does not
        bill: report billable usage with POST /v1/billing/usage. Emits entitlement.limit_reached
        once, when a consume takes the window to its limit.
        """
        return self._t.request(
            method="POST",
            path="/v1/entitlements/consume",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def refund_consume(
        self,
        body: cm.PostEntitlementsConsumeRefundBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostEntitlementsConsumeRefundResponse:
        """Give back all or part of an earlier Atlas-counted consume (an operation that failed
        after it took its units). Never more than that consume took (409 with `refundable`).
        Idempotent on `idempotency_key`. A subject whose balances are held by its billing
        provider cannot be refunded here (422).
        """
        return self._t.request(
            method="POST",
            path="/v1/entitlements/consume/refund",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ErasureConnectorCatalog:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetErasureConnectorCatalogResponse:
        """The catalog of downstream systems that commonly hold copies of an account's personal
        data (payments, email, SMS, analytics, support, CRM, storage, monitoring, warehouse),
        with how a copy is erased and what it usually holds.
        """
        return self._t.request(
            method="GET",
            path="/v1/erasure_connector_catalog",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetErasureConnectorCatalogResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class ErasureConnectors:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetErasureConnectorsResponse:
        """The downstream systems this application tracks for erasure."""
        return self._t.request(
            method="GET",
            path="/v1/erasure_connectors",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetErasureConnectorsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostErasureConnectorsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetErasureConnectorsResponseDataItem:
        """Track a downstream system. Send catalog_id to take a catalog entry, or key and name for
        your own. mode ack (default): the system acknowledges through POST
        /v1/users/{id}/erasure_acks under ack_source. manual: an operator marks it done on each
        request. api: Atlas calls the vendor's deletion API (stripe, hubspot, mailchimp,
        segment, intercom, zendesk, brevo, customerio) with your own key (credential, sealed,
        never returned) for every address of the person when an erasure request is carried out;
        the result is recorded per request. 409 when the key exists. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/erasure_connectors",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        erasure_connector_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Stop tracking a downstream system. Past request records of it are removed with it. 204."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        erasure_connector_id: str,
    ) -> cm.GetErasureConnectorsResponseDataItem:
        """One erasure connector."""
        return self._t.request(
            method="GET",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}",
        )

    def update(
        self,
        erasure_connector_id: str,
        body: cm.PatchErasureConnectorsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetErasureConnectorsResponseDataItem:
        """Change a connector's name, mode, ack_source, enabled or notes. The key cannot change."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def probe(
        self,
        erasure_connector_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostErasureConnectorsByIdProbeResponse:
        """A read-only call to the vendor that proves the connector's saved key works. Nothing is
        deleted. Audited.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}/probe",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Federation:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetFederationResponse:
        """The OpenID Federation configuration of this instance: entity identifier, authority
        hints, trust anchors, subordinates and registration modes.
        """
        return self._t.request(
            method="GET",
            path="/v1/federation",
        )

    def resolve(
        self,
        body: cm.PostFederationResolveBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Resolve and validate the trust chain of an entity against the configured trust anchors
        and return the resolved metadata, or why the chain is invalid. Nothing is registered.
        """
        return self._t.request(
            method="POST",
            path="/v1/federation/resolve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Fga:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def transform_model(
        self,
        body: cm.PostFgaModelsTransformBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Validate an authorization model and convert it: DSL (or modular DSL files) to canonical
        JSON, and JSON to DSL.
        """
        return self._t.request(
            method="POST",
            path="/v1/fga/models/transform",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_settings(
        self,
    ) -> cm.FgaSettings:
        """How this instance runs fine-grained authorization reads: the result-cache TTL, the
        consistency mode applied to reads that name none, and how long the tuple change log is
        kept.
        """
        return self._t.request(
            method="GET",
            path="/v1/fga/settings",
        )

    def set_settings(
        self,
        body: cm.PutFgaSettingsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.FgaSettings:
        """Change the instance FGA settings. Fields you omit keep their value. `cache_ttl_ms` null
        uses the platform default and 0 turns the result cache off; a request that carries its
        own `consistency` always wins over `default_consistency`; `changelog_retention_days`
        null keeps the whole tuple change log, otherwise older changes are removed in the
        background.
        """
        return self._t.request(
            method="PUT",
            path="/v1/fga/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def run_assertion_stores_authorization_models(
        self,
        store_id: str,
        mid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Run the stored assertions of a model version against the real store tuples."""
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/authorization-models/{_enc(mid)}/assertions/run",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_stores_authorization_models_diff(
        self,
        store_id: str,
        mid: str,
        *,
        against: str | None = None,
    ) -> dict[str, Any]:
        """What changed between a model version and the one before it (or `against`): types,
        relations, conditions, and whether the change can alter who has access.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/authorization-models/{_enc(mid)}/diff",
            query=_qd({'against': against}),
        )

    def get_stores_authorization_models_graph(
        self,
        store_id: str,
        mid: str,
    ) -> dict[str, Any]:
        """The nodes and edges of an authorization model, for a visualizer."""
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/authorization-models/{_enc(mid)}/graph",
        )

    def get_stores_export(
        self,
        store_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """Export the store tuples as NDJSON (one tuple per line), paged: pass the `atlas-next-
        cursor` response header back as `cursor`.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/export",
            query=_qd({'cursor': cursor, 'limit': limit}),
        )

    def import_store(
        self,
        store_id: str,
        body: cm.PostFgaStoresByIdImportBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Bulk-import up to 20,000 tuples. Idempotent: an existing tuple is untouched, a changed
        condition or expiry updates it. Validated against the latest model; `dry_run` reports
        how many are new without writing.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_stores_materializations(
        self,
        store_id: str,
    ) -> dict[str, Any]:
        """The materialized permission sets of a store: which (object type, relation, user type)
        answers are precomputed, their status, the revision they were built at and when a tuple
        expiry will next invalidate them.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations",
        )

    def create_stores_materialization(
        self,
        store_id: str,
        body: cm.PostFgaStoresByIdMaterializationsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Precompute list-objects for every user of `user_type` on `object_type#relation`, so a
        huge list question is one indexed read. The first build runs now; the worker rebuilds
        after tuple writes. A stored answer is served only while it is current for the store
        revision and model, before any tuple expiry, and for a plain `type:id` user with no
        request context or contextual tuples; otherwise list-objects is answered live. A model
        that uses conditions cannot be materialized.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_stores_materialization(
        self,
        store_id: str,
        mid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Remove a materialization; list-objects is then always computed live."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations/{_enc(mid)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def rebuild_materialization_stores(
        self,
        store_id: str,
        mid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Rebuild one materialization now."""
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations/{_enc(mid)}/rebuild",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_stores_snapshot(
        self,
        store_id: str,
        *,
        since: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """What a local policy decision point syncs: the latest model and the store tuples. Without
        `since`, a page of tuples (`full: true`, follow `next_cursor`); with `since=<revision>`,
        only the tuple changes after that revision. Tuples carry `expires_at`; expired tuples
        are never listed.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/snapshot",
            query=_qd({'since': since, 'cursor': cursor, 'limit': limit}),
        )

    def create_stores_test(
        self,
        store_id: str,
        body: cm.PostFgaStoresByIdTestsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Run an FGA test suite in memory: a model (DSL, modules, a version id or the latest),
        suite tuples and tests with check, list_objects and list_users assertions. Returns per-
        test results and relation coverage. The store tuples are never read.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/tests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_stores_watch(
        self,
        store_id: str,
        *,
        since: str | None = None,
        type: str | None = None,
    ) -> str:
        """Server-sent stream of the store tuple changes after `since` (or `Last-Event-ID`). Ends
        after about a minute; reconnect with the last event id.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/watch",
            query=_qd({'since': since, 'type': type}),
        )

    def get_sync(
        self,
    ) -> cm.GetFgaSyncResponse:
        """The managed FGA sync: its settings, how many tuples it owns by kind, the backfill in
        flight and the last run. Needs an API key that is not limited to organizations.
        """
        return self._t.request(
            method="GET",
            path="/v1/fga/sync",
        )

    def set_sync(
        self,
        body: cm.PutFgaSyncBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFgaSyncResponse:
        """Configure the managed sync that turns organization memberships, org roles and groups
        into FGA tuples, so a model can say `viewer: member from organization` without mirroring
        anything by hand. Opt-in per instance; nothing is written until `enabled` is true with a
        `store_id`. Enabling starts from the current end of the change feed and queues a
        backfill. The sync only ever removes tuples it wrote; a tuple that existed first is left
        alone. Tuples the store's model has no relation for are skipped and counted. A store or
        a tuple name cannot change while the sync owns tuples (409): disable it and `POST
        /v1/fga/sync/purge` first. Emits nothing itself; its writes emit fga.tuple_written and
        fga.tuple_deleted.
        """
        return self._t.request(
            method="PUT",
            path="/v1/fga/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def backfill_sync(
        self,
        body: cm.PostFgaSyncBackfillBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFgaSyncResponseBackfill:
        """Queue a backfill: walk every membership, group member and group and write the tuples
        that are missing, then remove owned tuples whose source is gone. `repair: true` rewrites
        every desired tuple, healing tuples someone deleted by hand. Resumable and processed by
        the worker; read the run to follow it. One backfill runs at a time: asking again returns
        the one in flight (200). Honours Idempotency-Key. Emits fga_sync.completed or
        fga_sync.failed when it ends.
        """
        return self._t.request(
            method="POST",
            path="/v1/fga/sync/backfill",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def purge_sync(
        self,
        body: cm.PostFgaSyncPurgeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostFgaSyncPurgeResponse:
        """Remove the tuples the sync wrote (never one that existed before it) and forget them. The
        sync must be disabled (409 otherwise). Send `confirm: true`.
        """
        return self._t.request(
            method="POST",
            path="/v1/fga/sync/purge",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_sync_runs(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFgaSyncRunsResponse:
        """Sync runs, newest first: backfills, and the incremental passes that changed something."""
        return self._t.request(
            method="GET",
            path="/v1/fga/sync/runs",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_sync_runs(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetFgaSyncResponseBackfill]:
        """Every item of :meth:`list_sync_runs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_sync_runs(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_sync_run(
        self,
        run_id: str,
    ) -> cm.GetFgaSyncResponseBackfill:
        """One sync run with its counts and any error."""
        return self._t.request(
            method="GET",
            path=f"/v1/fga/sync/runs/{_enc(run_id)}",
        )

    def create_test(
        self,
        body: cm.PostFgaStoresByIdTestsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Run an FGA test suite with no store: the model comes from `dsl` or `modules`. Returns
        per-test results and relation coverage. For CI.
        """
        return self._t.request(
            method="POST",
            path="/v1/fga/tests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Flows:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_experiments(
        self,
        flow_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFlowsByIdExperimentsResponse:
        """A journey's A/B experiments, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/experiments",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_experiments(
        self,
        flow_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetFlowsByIdExperimentsResponseDataItem]:
        """Every item of :meth:`list_experiments`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_experiments(flow_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_experiment(
        self,
        flow_id: str,
        body: cm.PostFlowsByIdExperimentsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFlowsByIdExperimentsResponseDataItem:
        """Create a draft A/B experiment on a journey. Each variant runs one saved version of the
        journey (the first variant is the control); weights are whole percents adding up to 100.
        Nothing changes for users until it is started. → 201.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/experiments",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_experiment(
        self,
        flow_id: str,
        experiment_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a draft or stopped experiment and its assignments. Stop a running one first."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_experiment(
        self,
        flow_id: str,
        experiment_id: str,
    ) -> cm.GetFlowsByIdExperimentsResponseDataItem:
        """Get one journey experiment with its variants and results."""
        return self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}",
        )

    def update_experiment(
        self,
        flow_id: str,
        experiment_id: str,
        body: cm.PatchFlowsByIdExperimentsByExperimentIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFlowsByIdExperimentsResponseDataItem:
        """Change a draft experiment (name, hypothesis, variants). A started experiment keeps its
        variants so nobody is moved: 409.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_experiments_readout(
        self,
        flow_id: str,
        experiment_id: str,
    ) -> cm.GetFlowsByIdExperimentsByExperimentIdReadoutResponse:
        """Results per variant. Users are counted from when they were assigned: assigned (reached
        the journey), started (a run began, meaning the journey held them), completed,
        abandoned, in progress, completion and abandon rates, the 95% interval of the completion
        rate, average time to complete, and against the first variant the relative lift and a
        two-sided p-value (two-proportion z-test) with significant at 0.05. A difference is only
        worth acting on when significant is true and the sample is large enough.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}/readout",
        )

    def start_experiment(
        self,
        flow_id: str,
        experiment_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFlowsByIdExperimentsResponseDataItem:
        """Start a draft experiment. From now on each user who reaches the journey gets a variant
        (by weight, from a hash of the experiment and the user, stored on first use so it never
        changes) and runs that variant's version. One experiment runs per journey at a time
        (409); the journey must be enabled with an active version. Sends
        journey.experiment_started. Audited.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}/start",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def stop_experiment(
        self,
        flow_id: str,
        experiment_id: str,
        body: cm.PostFlowsByIdExperimentsByExperimentIdStopBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFlowsByIdExperimentsResponseDataItem:
        """Stop a running experiment: users go back to the journey's active version.
        promote_variant makes that variant's version the journey's active one. Sends
        journey.experiment_stopped. Audited.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}/stop",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_messages(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        user_id: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFlowsByIdMessagesResponse:
        """Messages the journey's send_message steps scheduled, newest first (50 by default, at
        most 200). Filter by status and user_id. The text is not returned.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/messages",
            query=_qd({'status': status, 'user_id': user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_messages(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        user_id: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetFlowsByIdMessagesResponseDataItem]:
        """Every item of :meth:`list_messages`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_messages(flow_id, status=status, user_id=user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def cancel_message(
        self,
        flow_id: str,
        message_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFlowsByIdMessagesResponseDataItem:
        """Cancel a message that has not gone out (pending, or failed). 409 once it is sending,
        sent or canceled. Audited.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/messages/{_enc(message_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_runs(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFlowsByIdRunsResponse:
        """Users' runs through one journey, newest first (20 by default, at most 200): started when
        a step was first held for them, completed when every held step was finished, abandoned
        when untouched past the journey's window. Filter with status. Saved answers are not
        included; read them per user.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/runs",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_runs(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetFlowsByIdRunsResponseDataItem]:
        """Every item of :meth:`list_runs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_runs(flow_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class Fraud:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def email_risk(
        self,
        body: cm.PostFraudEmailRiskBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostFraudEmailRiskResponse:
        """Email risk for one address: syntax, disposable domain, role account, MX (with the
        implicit-MX fallback), the suppression list and, when configured or `verify_mailbox` is
        true, a mailbox verdict from your own ZeroBounce or Kickbox account. Returns a score and
        an allow / review / block verdict.
        """
        return self._t.request(
            method="POST",
            path="/v1/fraud/email_risk",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_email_risk_settings(
        self,
    ) -> cm.GetFraudEmailRiskSettingsResponse:
        """Email risk settings: mode, provider, blocking policy and the sign-up gate."""
        return self._t.request(
            method="GET",
            path="/v1/fraud/email_risk/settings",
        )

    def set_email_risk_settings(
        self,
        body: cm.PutFraudEmailRiskSettingsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFraudEmailRiskSettingsResponse:
        """Change email risk settings. `mode`: off, mx or provider (your own verification account;
        the key is write-only). With `gate_sign_up` a `block` verdict refuses the sign-up.
        """
        return self._t.request(
            method="PUT",
            path="/v1/fraud/email_risk/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Grants:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def consume(
        self,
        grant_type: str,
        grant_id: str,
        body: cm.PostGrantsByGrantTypeByIdConsumeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostGrantsByGrantTypeByIdConsumeResponse:
        """Take an amount from one of a grant's counters, atomically. A denial is a 200 decision
        with `allowed: false`.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/consume",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def release_lease(
        self,
        grant_type: str,
        grant_id: str,
        lease_id: str,
        body: cm.PostGrantsByGrantTypeByIdLeasesByLeaseIdReleaseBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostGrantsByGrantTypeByIdLeasesByLeaseIdReleaseResponse:
        """Hand a lease back. What was not consumed returns to the counter. Safe to repeat."""
        return self._t.request(
            method="POST",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/leases/{_enc(lease_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def refund(
        self,
        grant_type: str,
        grant_id: str,
        body: cm.PostGrantsByGrantTypeByIdRefundBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostGrantsByGrantTypeByIdRefundResponse:
        """Give back all or part of one earlier consume. Never more than that consume took."""
        return self._t.request(
            method="POST",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/refund",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_usage(
        self,
        grant_type: str,
        grant_id: str,
    ) -> cm.GetGrantsByGrantTypeByIdUsageResponse:
        """The current window of every counter a grant defines, and the leases still holding an
        amount.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/usage",
        )


class Iga:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_activations(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaActivationsResponse:
        """The activation history, newest first, with each activation's live status."""
        return self._t.request(
            method="GET",
            path="/v1/iga/activations",
            query=_qd({'user_id': user_id, 'entitlement': entitlement, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_activations(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetIgaActivationsResponseDataItem]:
        """Every item of :meth:`list_activations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_activations(user_id=user_id, entitlement=entitlement, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_activation(
        self,
        body: cm.PostIgaActivationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaActivationsResponseDataItem:
        """Activate eligible access for a person as an administrator (the MFA the entitlement asks
        for is waived and the activation is marked `admin`). Justification, ticket and duration
        limits still apply. With `require_approval` the entitlement's approval steps run first
        and the status is `pending_approval`.
        """
        return self._t.request(
            method="POST",
            path="/v1/iga/activations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def end_activation(
        self,
        activation_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaActivationsResponseDataItem:
        """End an activation now: closes the grant, or cancels the pending approval."""
        return self._t.request(
            method="POST",
            path=f"/v1/iga/activations/{_enc(activation_id)}/end",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_bundles(
        self,
        *,
        catalog: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaBundlesResponse:
        """List access bundles (packages of entitlements requested together)."""
        return self._t.request(
            method="GET",
            path="/v1/iga/bundles",
            query=_qd({'catalog': catalog, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_bundles(
        self,
        *,
        catalog: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetIgaBundlesResponseDataItem]:
        """Every item of :meth:`list_bundles`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_bundles(catalog=catalog, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_bundle(
        self,
        body: cm.PostIgaBundlesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaBundlesResponseDataItem:
        """Create a bundle: several catalog entitlements, request form fields, and a policy (who
        may ask, guest expiry).
        """
        return self._t.request(
            method="POST",
            path="/v1/iga/bundles",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_bundle(
        self,
        bundle_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteIgaBundlesByIdResponse:
        """Delete a bundle (access already granted stays)."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_bundle(
        self,
        bundle_id: str,
    ) -> cm.GetIgaBundlesResponseDataItem:
        """Read one bundle by id or key."""
        return self._t.request(
            method="GET",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}",
        )

    def update_bundle(
        self,
        bundle_id: str,
        body: cm.PatchIgaBundlesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaBundlesResponseDataItem:
        """Change an access bundle, its entitlements, form fields or policy."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def request_bundle(
        self,
        bundle_id: str,
        body: cm.PostIgaBundlesByIdRequestBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostIgaBundlesByIdRequestResponse:
        """Request every entitlement of a bundle for a person. Each one follows its own approval
        steps and separation-of-duties rules; the response says which were requested, skipped
        (already held or pending) or failed.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}/request",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_campaign_templates(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaCampaignTemplatesResponse:
        """Ready-made access reviews: inactive users, guest and contractor access, and a quarterly
        two-stage review.
        """
        return self._t.request(
            method="GET",
            path="/v1/iga/campaign_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_campaign_templates(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetIgaCampaignTemplatesResponseDataItem]:
        """Every item of :meth:`list_campaign_templates`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_campaign_templates(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def from_template_campaign(
        self,
        body: cm.PostIgaCampaignsFromTemplateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaCampaignsResponseDataItem:
        """Create a campaign from a template. `parameters` fill the template (inactive_days;
        company_domains).
        """
        return self._t.request(
            method="POST",
            path="/v1/iga/campaigns/from_template",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_campaigns_recommendations(
        self,
        campaign_id: str,
        *,
        reviewer_user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaCampaignsByIdRecommendationsResponse:
        """The open review items with advice for the reviewer: revoke (no sign-in for 90 days, or
        none since the access was granted), review (held by few of the manager's other reports)
        or certify. Advice only.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/iga/campaigns/{_enc(campaign_id)}/recommendations",
            query=_qd({'reviewer_user_id': reviewer_user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_campaigns_recommendations(
        self,
        campaign_id: str,
        *,
        reviewer_user_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetIgaCampaignsByIdRecommendationsResponseDataItem]:
        """Every item of :meth:`list_campaigns_recommendations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_campaigns_recommendations(campaign_id, reviewer_user_id=reviewer_user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def run_now_campaign(
        self,
        campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaCampaignsResponseDataItem:
        """Start a copy of a recurring campaign now, outside its schedule."""
        return self._t.request(
            method="POST",
            path=f"/v1/iga/campaigns/{_enc(campaign_id)}/run_now",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def stop_recurrence_campaign(
        self,
        campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaCampaignsResponseDataItem:
        """Stop a recurring campaign. Copies already started are unaffected."""
        return self._t.request(
            method="POST",
            path=f"/v1/iga/campaigns/{_enc(campaign_id)}/stop_recurrence",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_eligibilities(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaEligibilitiesResponse:
        """People who may activate an entitlement (eligible assignments)."""
        return self._t.request(
            method="GET",
            path="/v1/iga/eligibilities",
            query=_qd({'user_id': user_id, 'entitlement': entitlement, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_eligibilities(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetIgaEligibilitiesResponseDataItem]:
        """Every item of :meth:`list_eligibilities`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_eligibilities(user_id=user_id, entitlement=entitlement, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_eligibility(
        self,
        body: cm.PostIgaEligibilitiesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaEligibilitiesResponseDataItem:
        """Make a person eligible for an entitlement: they hold nothing until they activate it. The
        entitlement needs `activation_rules`. `expires_at` ends the eligibility.
        """
        return self._t.request(
            method="POST",
            path="/v1/iga/eligibilities",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_eligibility(
        self,
        eligibility_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteIgaEligibilitiesByIdResponse:
        """Remove an eligibility. Access already activated stays until it ends."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/iga/eligibilities/{_enc(eligibility_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def import_entitlement(
        self,
        body: cm.PostIgaEntitlementsImportBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostIgaEntitlementsImportResponse:
        """Add catalog entitlements (not requestable, no approval steps) for the groups or app
        roles that exist but are not in the catalog yet.
        """
        return self._t.request(
            method="POST",
            path="/v1/iga/entitlements/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Impersonations:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create(
        self,
        body: cm.PostImpersonationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Start a support impersonation: a session for `user_id` whose token carries `act.sub` =
        `staff_user_id`. The instance policy (GET /v1/instance/impersonation_policy) decides the
        rules: `reason` (max 500 characters) is required unless the policy turns that off,
        `reason_code` must be one of the policy's codes when it lists any, the session lasts at
        most the policy's limit (`max_duration_seconds` can only shorten it; never more than 1
        hour), and `read_only` (default from the policy) makes the session refuse every change
        on the Frontend API and puts `ro: true` in its token. When the policy requires approval
        the call answers 202 with a pending `impersonation_request`; a second staff member
        decides it with POST /v1/impersonations/requests/{id}/approve or /deny. Optional
        `require_staff_org_id` and `require_staff_mfa` apply to the staff user (and to the
        approver). Refused for banned, deleted and impersonation-protected users. Emits
        `impersonation.started` (and the older `session.impersonation_started`); the user is
        emailed when the policy says so and sees the session at GET /v1/client/me/staff_access.
        To export the trail, use GET
        /v1/audit_logs?action=session.impersonation_started&format=jsonl.
        """
        return self._t.request(
            method="POST",
            path="/v1/impersonations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetImpersonationsRequestsResponse:
        """List impersonation requests held for approval, newest first. `status`: pending,
        approved, denied or expired.
        """
        return self._t.request(
            method="GET",
            path="/v1/impersonations/requests",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetImpersonationsRequestsResponseDataItem]:
        """Every item of :meth:`list_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_requests(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_request(
        self,
        request_id: str,
    ) -> cm.GetImpersonationsRequestsResponseDataItem:
        """Read one impersonation request: its status, who asked, who decided, and when it expires."""
        return self._t.request(
            method="GET",
            path=f"/v1/impersonations/requests/{_enc(request_id)}",
        )

    def approve_request(
        self,
        request_id: str,
        body: cm.PostImpersonationsRequestsByIdApproveBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Approve a pending impersonation as a second staff member (`approver_user_id`, never the
        requester). Starts the session and returns it with the request; the decision and the
        approver are audited on the impersonated user. A request expires after 30 minutes.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/impersonations/requests/{_enc(request_id)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def deny_request(
        self,
        request_id: str,
        body: cm.PostImpersonationsRequestsByIdApproveBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Deny a pending impersonation as a second staff member. Audited; no session is created."""
        return self._t.request(
            method="POST",
            path=f"/v1/impersonations/requests/{_enc(request_id)}/deny",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def end(
        self,
        impersonation_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostImpersonationsByIdEndResponse:
        """End an impersonation started with POST /v1/impersonations (`id` is the returned
        impersonation id): revokes the session, audits it on the impersonated user and emits
        `impersonation.ended` (and the older `session.impersonation_ended`).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/impersonations/{_enc(impersonation_id)}/end",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Instance:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_app_event_types(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationsByIdAppEventTypesResponse:
        """The event types third-party apps can subscribe to, each with the scope a user must have
        granted the app.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/app_event_types",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_app_event_types(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOrganizationsByIdAppEventTypesResponseDataItem]:
        """Every item of :meth:`list_app_event_types`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_app_event_types(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def set_app_event_types(
        self,
        body: list[cm.PutInstanceAppEventTypesBodyItem],
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationsByIdAppEventTypesResponse:
        """Replace the event types third-party apps can subscribe to (send an array, or { types:
        [...] }). Each has a type (lowercase dotted, not an Atlas event name), an optional
        description and schema, and a required_scope that must exist in the scope catalogue.
        Publish with POST /v1/app_events { user_id }; subscribe a client with PUT
        /v1/oauth_clients/{id}/webhook.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/app_event_types",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_config_snapshots(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        source: Literal['manual', 'auto', 'pre_restore', 'cli', 'clone'] | None = None,
    ) -> cm.GetInstanceConfigSnapshotsResponse:
        """The configuration snapshots of the instance, newest first. Filter by source: manual,
        auto, pre_restore (saved before a restore), cli, clone.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/config_snapshots",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'source': source}),
        )

    def iter_list_config_snapshots(
        self,
        *,
        limit: int | None = None,
        source: Literal['manual', 'auto', 'pre_restore', 'cli', 'clone'] | None = None,
    ) -> Iterator[cm.GetInstanceConfigSnapshotsResponseDataItem]:
        """Every item of :meth:`list_config_snapshots`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_config_snapshots(limit=limit, source=source, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_config_snapshot(
        self,
        body: cm.PostInstanceConfigSnapshotsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceConfigSnapshotsResponseDataItem:
        """Save the instance's configuration as it is now, with an optional label. Secrets are
        removed from the copy (their paths are listed in redacted_paths). The worker also saves
        a snapshot automatically after configuration changes, so you can go back to a state you
        never named. Needs instance:write. Honours Idempotency-Key. Audited.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/config_snapshots",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_config_snapshots_diff(
        self,
        *,
        from_: str,
        to: str | None = None,
    ) -> cm.GetInstanceConfigSnapshotsDiffResponse:
        """What changed between two configurations, as a list of paths with the value before and
        after. `from` and `to` are snapshot ids, or `current` for the live configuration (to
        defaults to current). Secrets never appear; allowed origins are reported separately.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/config_snapshots/diff",
            query=_qd({'from': from_, 'to': to}),
        )

    def delete_config_snapshot(
        self,
        config_snapshot_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceConfigSnapshotsByIdResponse:
        """Delete one snapshot. Audited."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/instance/config_snapshots/{_enc(config_snapshot_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_config_snapshot(
        self,
        config_snapshot_id: str,
    ) -> cm.GetInstanceConfigSnapshotsResponseDataItem:
        """One snapshot with its configuration (auth_config and allowed_origins). Secrets are never
        in it.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/instance/config_snapshots/{_enc(config_snapshot_id)}",
        )

    def restore_config_snapshot(
        self,
        config_snapshot_id: str,
        body: cm.PostInstanceConfigSnapshotsByIdRestoreBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstanceConfigSnapshotsByIdRestoreResponse:
        """Put a snapshot back: the configuration returns to what it was, the secrets the instance
        holds today stay, and the state being replaced is first saved as a pre_restore snapshot
        so the restore can be undone the same way. dry_run: true returns the changes and writes
        nothing; send its current_sha256 as expected_sha256 to apply exactly what you saw (409
        if the configuration moved). Allowed origins are left alone unless
        include_allowed_origins is true. The restored configuration must pass the same checks as
        any configuration write (422 otherwise). Needs instance:write. Honours Idempotency-Key.
        Audited. Emits config_snapshot.restored.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/instance/config_snapshots/{_enc(config_snapshot_id)}/restore",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_data_key_provider(
        self,
        body: cm.DeleteInstanceDataKeyProviderBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Remove customer-managed encryption by deleting the wrapped data keys. This crypto-shreds
        everything encrypted under them and cannot be undone; send { "confirm": "shred" }.
        """
        return self._t.request(
            method="DELETE",
            path="/v1/instance/data_key_provider",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_data_key_provider(
        self,
    ) -> dict[str, Any]:
        """Customer-managed encryption status: whether it is on, the key provider, the data key
        versions, the last health check and how long a revoked key keeps working before Atlas
        fails closed.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/data_key_provider",
        )

    def data_key_provider(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Turn on customer-managed encryption. A random data key is created, wrapped by the KMS
        key set with PUT /v1/vault/key_provider (AWS KMS, Google Cloud KMS or Azure Key Vault)
        and proved by an unwrap before anything depends on it. From then on everything Atlas
        encrypts for the instance depends on that KMS key; values written earlier stay readable
        until the re-encryption sweep has moved them. If the key is later disabled, deleted or
        its access removed, requests that need the instance data fail with 503
        CUSTOMER_KEY_UNAVAILABLE within five minutes; nothing falls back to a platform key.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set_data_key_provider(
        self,
        body: cm.PutInstanceDataKeyProviderBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Set the cache window: how long Atlas may use a loaded data key without your KMS
        confirming it, which is how long a revoked key keeps working (60 to 3,600 seconds,
        default 300). Shorter revokes faster but depends on the KMS being reachable more
        tightly: Atlas re-confirms every 20 seconds, so a KMS outage longer than the window
        takes the instance down.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/data_key_provider",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def check_data_key_provider(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Check the customer key now: wrap and unwrap a random key through it and open the current
        data keys. `reason` names a failure: key_disabled, key_not_found, access_denied,
        unreachable or invalid_config.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/check",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def rewrap_data_key_provider(
        self,
        body: cm.PostInstanceDataKeyProviderRewrapBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Re-wrap data keys and vault versions wrapped by an earlier KMS key under the provider as
        configured now. Pass `previous` (provider, config, credentials) when the old key is no
        longer the configured one. Only small keys are unwrapped and wrapped again; no data is
        re-encrypted, and it is safe to repeat.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/rewrap",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def rotate_data_key_provider(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Create a new data key version. New data uses it; earlier versions stay until a re-
        encryption sweep reports none left on them.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def rotation_drill_data_key_provider(
        self,
        body: cm.PostInstanceDataKeyProviderRewrapBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstanceDataKeyProviderRotationDrillResponse:
        """A rotation drill: the re-wrap as a dry run. Every data key and vault version that would
        move is opened with the key that holds it, wrapped under the key as configured now and
        opened again; nothing is written. A KMS failure is reported as `ok: false` with its
        reason, not as an error. Sends data_key_provider.drill_completed.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/rotation_drill",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_data_key_provider_rotation_drills(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceDataKeyProviderRotationDrillsResponse:
        """The last 20 rotation drills, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/instance/data_key_provider/rotation_drills",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_data_key_provider_rotation_drills(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.PostInstanceDataKeyProviderRotationDrillResponse]:
        """Every item of :meth:`list_data_key_provider_rotation_drills`, following the cursor page
        by page.
        """
        cursor: str | None = None
        while True:
            page = self.list_data_key_provider_rotation_drills(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_data_key_provider_rotation_drill(
        self,
        rotation_drill_id: str,
    ) -> cm.PostInstanceDataKeyProviderRotationDrillResponse:
        """Read one key rotation drill: its outcome and what it checked."""
        return self._t.request(
            method="GET",
            path=f"/v1/instance/data_key_provider/rotation_drills/{_enc(rotation_drill_id)}",
        )

    def list_deprecations(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceDeprecationsResponse:
        """The deprecation list, each entry saying whether this instance still calls the deprecated
        route or sends the deprecated field (`in_use`, `first_seen_at`).
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/deprecations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_deprecations(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstanceDeprecationsResponseDataItem]:
        """Every item of :meth:`list_deprecations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_deprecations(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def list_exports(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceExportsResponse:
        """The tenant exports of the instance, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/instance/exports",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_exports(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstanceExportsResponseDataItem]:
        """Every item of :meth:`list_exports`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_exports(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_export(
        self,
        body: cm.PostInstanceExportsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """Start a whole-instance export: configuration, roles, organizations, memberships, users
        (profile, metadata, addresses, linked identities), and the non-secret facts about API
        keys, provider connections and webhook endpoints. Never in it: password hashes, MFA
        secrets, recovery codes, API key hashes, provider tokens, signing keys, webhook secrets,
        or any string in the configuration that looks like a secret (their paths are listed in
        redacted_paths). Runs as a job (202); the bundle is kept for expires_in_hours (default
        24, at most 168). Needs instance:write and users:read. A section of more than 100000
        rows fails the job; leave it out of sections and page it with POST
        /v1/users/search/export. Honours Idempotency-Key. Emits instance_export.completed or
        .failed.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/exports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_export(
        self,
        export_id: str,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """One export: status, row counts per section, the bundle digest and signature. The bundle
        itself is not in this body.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/instance/exports/{_enc(export_id)}",
        )

    def get_exports_bundle(
        self,
        export_id: str,
    ) -> dict[str, Any]:
        """Download the bundle (canonical JSON: keys sorted, so its SHA-256 holds for the bytes you
        receive). Headers x-atlas-bundle-sha256 and x-atlas-bundle-signature carry the digest
        and the JWS. Needs instance:read and users:read; audited. 409 until the export finished,
        and after it expired.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/instance/exports/{_enc(export_id)}/bundle",
        )

    def download_url_export(
        self,
        export_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstanceExportsByIdDownloadUrlResponse:
        """A signed link to the bundle that works for 15 minutes without a key (hand it to a person
        or a job that should not hold your secret key). Needs instance:read and users:read;
        audited.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/instance/exports/{_enc(export_id)}/download_url",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def create_exports_revoke_link(
        self,
        export_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """Invalidate every signed download link handed out for this export."""
        return self._t.request(
            method="POST",
            path=f"/v1/instance/exports/{_enc(export_id)}/revoke_links",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_impersonation_policy(
        self,
    ) -> cm.GetInstanceImpersonationPolicyResponse:
        """The instance's staff impersonation policy: require_reason, reason_codes,
        max_duration_seconds, require_approval, read_only_default and notify_user.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/impersonation_policy",
        )

    def set_impersonation_policy(
        self,
        body: cm.PutInstanceImpersonationPolicyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Change the staff impersonation policy. Send only the fields to change; unknown fields
        are refused. Audited.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/impersonation_policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_imports(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceExportsResponse:
        """The tenant imports of the instance, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/instance/imports",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_imports(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstanceExportsResponseDataItem]:
        """Every item of :meth:`list_imports`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_imports(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_import(
        self,
        body: cm.PostInstanceImportsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """Load an export bundle into THIS instance (meant to be a new one). Runs as a job (202),
        in dependency order: configuration (validated like an ordinary config patch), roles,
        organizations, then users with their memberships. Additive and safe to repeat: what
        exists is left as it is. Users come in without passwords or second factors (they use
        password reset or another sign-in); webhook endpoints are created switched OFF with a
        new signing secret nobody has seen (rotate it, then enable); API keys and provider
        connections are never created (mint and connect them here). sha256, if sent, must match
        the bundle. Needs instance:write and users:write. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/imports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_import(
        self,
        import_id: str,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """One import: status, what was created / already existed / failed per section, and what
        could not be placed.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/instance/imports/{_enc(import_id)}",
        )

    def list_integrations_mints(
        self,
        product: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceIntegrationsByProductMintsResponse:
        """The integration's mint log: every getToken({ for }) attempt, from the browser and from
        the server call, newest first, with its outcome (ok, or refused with the reason code),
        the route kind and the user id. No tokens are stored. Kept 7 days. Use it when
        health.last_minted_at stays null: an empty log means nothing is calling Atlas, a refused
        row says why.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/instance/integrations/{_enc(product)}/mints",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_integrations_mints(
        self,
        product: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstanceIntegrationsByProductMintsResponseDataItem]:
        """Every item of :meth:`list_integrations_mints`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_integrations_mints(product, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def test_integration(
        self,
        product: str,
        *,
        wait: str | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostWebhookEndpointsByIdTestResponse1 | cm.PostWebhookEndpointsByIdTestResponse2:
        """Send a signed webhook.test event to the integration's event receiver only, with its
        current signing secret, exactly like a real delivery. Use it to confirm a receiver after
        fixing it, without waiting for a real event. Without ?wait the delivery is queued (201,
        object webhook_delivery); with ?wait=10s the attempt is made now and the result returned
        (200, object webhook_test_result: status success | failed, http_status, latency_ms,
        response_snippet, error_kind, signature_header_sent). A failed attempt is still 200:
        read status. Audited. 404 when the integration has no event receiver.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/instance/integrations/{_enc(product)}/test",
            query=_qd({'wait': wait, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_op_keys(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceOpKeysResponse:
        """The OpenID provider keys beyond the instance signing key: PS256, ES384 and EdDSA signing
        keys and the RSA-OAEP-256 / ECDH-ES keys request objects are encrypted to, with their
        status.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/op_keys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_op_keys(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstanceOpKeysResponseDataItem]:
        """Every item of :meth:`list_op_keys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_op_keys(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def rotate_op_key(
        self,
        body: cm.PostInstanceOpKeysRotateBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Rotate the key of one algorithm (`alg`). The previous public key stays published for
        `grace_period_seconds` (default 24 h) so tokens it signed keep verifying.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/op_keys/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_org_departure_policy(
        self,
    ) -> cm.GetInstanceOrgDeparturePolicyResponse:
        """What happens to the organization connections a departing member authorized: oldest_admin
        (default), a fixed user, or none.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/org_departure_policy",
        )

    def set_org_departure_policy(
        self,
        body: cm.PutInstanceOrgDeparturePolicyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Set the departure policy. `transfer_to`: oldest_admin, user (needs `user_id`, who must
        still be a member) or none.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/org_departure_policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_org_role_entitlements(
        self,
    ) -> cm.GetInstanceOrgRoleEntitlementsResponse:
        """The map of organization role key to the feature keys a seat in that role grants. Those
        features join the token's `fea` claim for a member whose active organization role
        matches, on top of (or without) a plan.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/org_role_entitlements",
        )

    def set_org_role_entitlements(
        self,
        body: cm.PutInstanceOrgRoleEntitlementsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Replace the role to features map. A role left out grants nothing. Takes effect on the
        next token.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/org_role_entitlements",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def create_preflight_ack(
        self,
        body: cm.PostInstancePreflightAcksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstancePreflightAcksResponseDataItem:
        """Acknowledge a preflight finding by code, in the body: the same as PUT
        /v1/instance/preflight/acks/{code}, with the reason optional. An acknowledged finding
        stays listed with acknowledged_at and acknowledged, drops out of the failing count, and
        GET /v1/integration-health reports it as a note (ok stays true when only notes and
        acknowledged findings remain). subject narrows it to one subject of the finding;
        expires_at makes it lapse. Errors cannot be acknowledged (422). Audited
        (preflight_ack.saved).
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/preflight/acks",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_privacy_orchestrator_cases(
        self,
        *,
        status: Literal['open', 'pending', 'failed', 'cancelled', 'cancel_pending', 'abandoned'] | None = None,
        dismissed: bool | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstancePrivacyOrchestratorCasesResponse:
        """The data-rights cases Atlas opened (or tried to) at the orchestrator, newest first,
        paged like every list (`limit` 1-100, `starting_after` = a request id, `has_more`).
        `status` filters (`abandoned` = given up, `failed` = still being retried, `open`,
        `pending`, `cancel_pending`, `cancelled`). A case dismissed by an operator is left out
        unless `dismissed=true`. `reason_code: email_unverified` marks a case deliberately not
        filed because the account's primary email address is not verified. Each `id` is the
        Atlas request id.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/privacy_orchestrator/cases",
            query=_qd({'status': status, 'dismissed': dismissed, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_privacy_orchestrator_cases(
        self,
        *,
        status: Literal['open', 'pending', 'failed', 'cancelled', 'cancel_pending', 'abandoned'] | None = None,
        dismissed: bool | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstancePrivacyOrchestratorCasesResponseDataItem]:
        """Every item of :meth:`list_privacy_orchestrator_cases`, following the cursor page by
        page.
        """
        cursor: str | None = None
        while True:
            page = self.list_privacy_orchestrator_cases(status=status, dismissed=dismissed, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def dismiss_case_privacy_orchestrator(
        self,
        body: cm.PostInstancePrivacyOrchestratorCasesDismissBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstancePrivacyOrchestratorCasesDismissResponse:
        """Dismiss every open case that was deliberately not filed because the account's primary
        email is not verified (`reason_code: email_unverified`), in one call; this clears the
        `privacy_orchestrator.cases_unverified_email` integration-health note. `reason` is
        optional (a default is recorded). Returns how many were dismissed (0 when none). Each is
        audited (privacy_orchestrator.case_dismissed). The requests themselves are untouched.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/privacy_orchestrator/cases/dismiss",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def dismiss_case_privacy_orchestrator_2(
        self,
        case_id: str,
        body: cm.PostInstancePrivacyOrchestratorCasesByIdDismissBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstancePrivacyOrchestratorCasesResponseDataItem:
        """Settle a failed or abandoned case without filing it: it leaves the integration-health
        problem count and the default case list. The `reason` is required and audited
        (privacy_orchestrator.case_dismissed). The request itself is untouched (an account
        deletion still runs on schedule).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/instance/privacy_orchestrator/cases/{_enc(case_id)}/dismiss",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def retry_case_privacy_orchestrator(
        self,
        case_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstancePrivacyOrchestratorCasesResponseDataItem:
        """Open a failed or abandoned case again now: its attempts reset and Atlas sends it to the
        orchestrator immediately; the answer is the case as it stands afterwards. 422 for a case
        that is not failed or abandoned, 404 for an unknown request. Audited
        (privacy_orchestrator.case_retried). A case skipped because the primary email is not
        verified is skipped again until the address is verified.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/instance/privacy_orchestrator/cases/{_enc(case_id)}/retry",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_scopes(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceScopesResponse:
        """The scope catalogue: the scopes your product defines, with consent-screen text per
        locale, `sensitive` and `requires_verified_client`.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/scopes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_scopes(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetInstanceScopesResponseDataItem]:
        """Every item of :meth:`list_scopes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_scopes(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def set_scopes(
        self,
        body: cm.PutInstanceScopesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Replace the scope catalogue. Each scope has a `name`, a `label` and a `description` per
        locale ({ "en": "…", "es": "…" }), `sensitive`, and `requires_verified_client`. The
        consent screen shows the label and description in the user's language (falling back to
        its base language, then `en`). A scope with `requires_verified_client` is refused at
        /oauth2/authorize with `invalid_scope` unless the app's status is `approved` or that
        scope is in the client's `approved_scopes` (per-scope review). The owner and testers of
        a client still in development may request it too. A client still needs the scope in its
        allowed scopes to request it.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/scopes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_secret_keys(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSecretKeysResponse:
        """Alias of GET /v1/secret_keys. List this instance's secret keys with scopes, owner,
        expiry, last use, last-used IP and provisioning tags. Revoked keys stay listed. Filter
        by tag with ?metadata[key]=value.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/secret_keys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_secret_keys(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetSecretKeysResponseDataItem]:
        """Every item of :meth:`list_secret_keys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_secret_keys(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_secret_key(
        self,
        body: cm.PostSecretKeysBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetSecretKeysResponseDataItem:
        """Alias of POST /v1/secret_keys. Create a scoped secret key: `name`, `scopes[]` (refused
        when unknown, or when the calling key does not hold them; presets `read_only`,
        `privacy:execute`, `privacy:grants:revoke`; or `preset: "app-runtime"` for an app server
        runtime key), `expires_at` (at most a year; default one year; "never" is refused),
        `allowed_ips` (CIDRs), `allowed_origins` (browser origins; a request with another Origin
        gets 403 ORIGIN_NOT_ALLOWED), `owner` (default: the creating person or key),
        `external_ref` (idempotent create: a repeat returns the existing key, 200,
        idempotent_replay, no secret), `metadata` (tags; filter the list with
        ?metadata[key]=value) and `key_format` (`atlas`, the default `atlas_<env>_sk_…`, or
        `legacy` `sk_<env>_…`). The secret is returned once. Minting with an operator token
        needs multi-factor sign-in within 5 minutes (403 STEP_UP_REQUIRED). Send `X-Secret-
        Recipient: x25519:<public key>` to receive the secret sealed (libsodium sealed box) as
        `sealed_secret` instead of in plaintext. Example: a data-rights tool's key, { "name":
        "DSAR executor", "scopes": ["privacy:execute", "privacy:grants:revoke"], "expires_at":
        "2027-04-01" }.
        """
        return self._t.request(
            method="POST",
            path="/v1/instance/secret_keys",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_signing_key_schedule(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceSigningKeyScheduleResponse:
        """Turn scheduled rotation off. Keys already published stay as they are."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/signing_key_schedule",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_signing_key_schedule(
        self,
    ) -> cm.GetInstanceSigningKeyScheduleResponse:
        """Read the signing-key rotation schedule."""
        return self._t.request(
            method="GET",
            path="/v1/instance/signing_key_schedule",
        )

    def set_signing_key_schedule(
        self,
        body: cm.PutInstanceSigningKeyScheduleBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceSigningKeyScheduleResponse:
        """Rotate the instance signing key automatically. Every interval_days the worker publishes
        a new key (prepublish_hours before it signs), switches to it, and keeps the previous key
        published until every token it signed has expired: at least the longest token lifetime
        the instance uses plus the key set cache, never under 24 hours, and never dropped while
        one of its tokens can still be presented. Keys in a cloud KMS rotate at the scheduled
        time (they cannot be held back) and are limited to RS256 and ES256. An earlier rotation
        still inside its grace window postpones the next one. Needs a recent MFA sign-in.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/signing_key_schedule",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_user_traits_schema(
        self,
    ) -> cm.UserTraitsSchema:
        """The instance user traits schema: a JSON Schema per metadata bag (public, unsafe and
        private user metadata; public and private organization metadata) and how strictly it
        applies. enforcement is off (the default and what an instance without a schema reports),
        warn or enforce. version is 0 until a schema is stored, then counts up on every change.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/user_traits_schema",
        )

    def set_user_traits_schema(
        self,
        body: cm.PutInstanceUserTraitsSchemaBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.UserTraitsSchema:
        """Store the user traits schema and/or change its enforcement. Omit schemas or enforcement
        to keep the stored one. Each schema is checked before it is stored (a 422 names the
        offending path): a subset of JSON Schema 2020-12 with type, properties, required, enum,
        default, items, maxLength, pattern, description and additionalProperties (true or
        false); any other keyword is refused, a root must have type "object", patterns that
        repeat a repeated group are refused, and a default must satisfy its own schema (it is
        documentation, never written into metadata). Enforcement: off checks nothing; warn lets
        every write through and records each violation in the audit log (field paths and
        messages, never values); enforce answers 422 with one error per field path on a write
        that breaks the schema. It applies to backend (secret key) writes, the dashboard and a
        signed-in user writing their own unsafe_metadata. Imports, migrations, SCIM provisioning
        and other Atlas-internal writes are never checked, so a bulk job is never stopped
        halfway. Existing metadata is not re-validated. Send version (the one you last read) to
        refuse a concurrent change with 409; sending the same content again changes nothing.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/user_traits_schema",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_write_budget(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceWriteBudgetResponse:
        """Back to the platform defaults in observe mode."""
        return self._t.request(
            method="DELETE",
            path="/v1/instance/write_budget",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_write_budget(
        self,
    ) -> cm.DeleteInstanceWriteBudgetResponse:
        """The instance write budgets: writes (mutating Backend API requests), counter_writes
        (grant consume, refund and lease release), events and webhook_fanout, each per 60-second
        window, the mode (observe or enforce), and when a budget was last exceeded.
        """
        return self._t.request(
            method="GET",
            path="/v1/instance/write_budget",
        )

    def set_write_budget(
        self,
        body: cm.PutInstanceWriteBudgetBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceWriteBudgetResponse:
        """Set the write-budget mode and any limit. A limit is an integer from 1 to 10,000,000 per
        minute; null returns one to its default. Unknown fields are refused.
        """
        return self._t.request(
            method="PUT",
            path="/v1/instance/write_budget",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class LegalHolds:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetLegalHoldsResponse:
        """Every active legal hold of the instance, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/legal_holds",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetLegalHoldsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class Localizations:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def check(
        self,
        body: cm.PostLocalizationsCheckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostLocalizationsCheckResponse:
        """Validate translations without saving (a CI step): the checks a save runs, plus empty
        strings, unknown keys and placeholders that differ from an approved translation of the
        same resource in another language. With require_approved, a translation that is not
        stored, not approved, or changed since approval fails too. Never writes. 1 to 500 items.
        """
        return self._t.request(
            method="POST",
            path="/v1/localizations/check",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_review_summary(
        self,
    ) -> cm.GetLocalizationsReviewSummaryResponse:
        """Translations per review status, the review queue (in review and changes requested), and
        approved translations whose text changed after approval.
        """
        return self._t.request(
            method="GET",
            path="/v1/localizations/review_summary",
        )

    def review(
        self,
        localization_id: str,
        body: cm.PostLocalizationsByIdReviewBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetLocalizationsReviewSummaryResponseQueueItem:
        """Move a translation through review: submit (draft or changes_requested to in_review),
        approve (in_review to approved; records who and the hash of the approved text),
        request_changes (in_review to changes_requested; note required), reopen (back to draft).
        Any other move is 409. With localization.requireFourEyes on, approve by the person who
        last wrote the text is 403. Editing an approved text sends it back to draft. With
        localization.requireReview on, only approved translations are served. Emits
        localization.review_decided.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/localizations/{_enc(localization_id)}/review",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_reviews(
        self,
        localization_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetLocalizationsByIdReviewsResponse:
        """The review decisions on a translation, newest first."""
        return self._t.request(
            method="GET",
            path=f"/v1/localizations/{_enc(localization_id)}/reviews",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_reviews(
        self,
        localization_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetLocalizationsByIdReviewsResponseDataItem]:
        """Every item of :meth:`list_reviews`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_reviews(localization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class MachineTrustPolicies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        machine_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMachineTrustPoliciesResponse:
        """List workload trust policies, optionally for one machine."""
        return self._t.request(
            method="GET",
            path="/v1/machine_trust_policies",
            query=_qd({'machine_id': machine_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        machine_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetMachineTrustPoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(machine_id=machine_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostMachineTrustPoliciesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMachineTrustPoliciesResponseDataItem:
        """Create a trust policy: let a token from an external workload platform (GitHub Actions,
        Kubernetes, AWS, GCP or any OIDC issuer) be exchanged for a machine token of one
        machine, with no stored secret. The external token must verify against the issuer, carry
        the audience, and its subject and claims must satisfy the policy. A machine holds at
        most 20. Names are unique per machine (409). Needs a recent MFA sign-in (it widens what
        can act as the machine). Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/machine_trust_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        machine_trust_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMachineTrustPoliciesByIdResponse:
        """Delete a trust policy. Tokens already minted through it live out their lifetime (at most
        max_ttl_seconds).
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        machine_trust_policy_id: str,
    ) -> cm.GetMachineTrustPoliciesResponseDataItem:
        """Fetch one trust policy."""
        return self._t.request(
            method="GET",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}",
        )

    def update(
        self,
        machine_trust_policy_id: str,
        body: cm.PatchMachineTrustPoliciesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMachineTrustPoliciesResponseDataItem:
        """Change a trust policy. kind and machine_id cannot change. Needs a recent MFA sign-in."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def test(
        self,
        machine_trust_policy_id: str,
        body: cm.PostMachineTrustPoliciesByIdTestBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostMachineTrustPoliciesByIdTestResponse:
        """Dry run: would this external token (or signed AWS request) be accepted by this policy?
        Returns the subject and claims it saw, or the reasons it was refused. Mints nothing and
        spends nothing, and works on a disabled policy.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Machines:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def update_grant(
        self,
        machine_id: str,
        grant_id: str,
        body: cm.PatchMachinesByIdGrantsByGrantIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Change a machine's grant in place: scopes, constraints or expiry. 409 once the grant has
        expired.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/machines/{_enc(machine_id)}/grants/{_enc(grant_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Mcp:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create_elevation(
        self,
        body: cm.PostMcpElevationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostMcpElevationsResponse:
        """Give another API key a short write elevation over the admin MCP server. A key with the
        mcp:read_only_default scope can only use read tools until it presents the returned token
        in the X-Atlas-MCP-Elevation header. Needs the mcp:elevate scope, which belongs on a key
        a person holds, not on the agent. The token is bound to that one key and expires by
        itself (at most 15 minutes).
        """
        return self._t.request(
            method="POST",
            path="/v1/mcp/elevations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class McpGateways:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_packs(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPacksResponse:
        """The tool packs of a gateway: named tool sets assigned to agents, organizations or
        groups.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_packs(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMcpGatewaysByIdPacksResponseDataItem]:
        """Every item of :meth:`list_packs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_packs(mcp_gateway_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_pack(
        self,
        mcp_gateway_id: str,
        body: cm.PostMcpGatewaysByIdPacksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPacksResponseDataItem:
        """Create a tool pack. With the gateway's `packs_enforced` on, a caller sees and may call
        only the tools of packs assigned to them.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_pack(
        self,
        mcp_gateway_id: str,
        pack_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMcpGatewaysByIdPacksByPackIdResponse:
        """Delete a tool pack from an MCP gateway."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs/{_enc(pack_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_pack(
        self,
        mcp_gateway_id: str,
        pack_id: str,
    ) -> cm.GetMcpGatewaysByIdPacksResponseDataItem:
        """Read one tool pack of an MCP gateway."""
        return self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs/{_enc(pack_id)}",
        )

    def update_pack(
        self,
        mcp_gateway_id: str,
        pack_id: str,
        body: cm.PatchMcpGatewaysByIdPacksByPackIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPacksResponseDataItem:
        """Change a tool pack; omitted fields keep their value."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs/{_enc(pack_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_pins(
        self,
        mcp_gateway_id: str,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPinsResponse:
        """The pinned tool definitions of a gateway with `guard.pin_tools` on: each tool's
        description and schema is hashed when first seen; a changed definition is blocked
        (status changed) until approved.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/pins",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_pins(
        self,
        mcp_gateway_id: str,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetMcpGatewaysByIdPinsResponseDataItem]:
        """Every item of :meth:`list_pins`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_pins(mcp_gateway_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_pin(
        self,
        mcp_gateway_id: str,
        tool: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Forget a pin; the next tools/list pins whatever the upstream serves then."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/pins/{_enc(tool)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def approve_pin(
        self,
        mcp_gateway_id: str,
        tool: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPinsResponseDataItem:
        """Accept the definition the upstream serves now for a tool whose definition changed.
        Unblocks the tool.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/pins/{_enc(tool)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_upstreams(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpGatewaysByIdUpstreamsResponse:
        """The upstreams of a gateway: MCP servers and OpenAPI-described APIs, each exposed under
        its namespace.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_upstreams(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMcpGatewaysByIdUpstreamsResponseDataItem]:
        """Every item of :meth:`list_upstreams`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_upstreams(mcp_gateway_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_upstream(
        self,
        mcp_gateway_id: str,
        body: cm.PostMcpGatewaysByIdUpstreamsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpGatewaysByIdUpstreamsResponseDataItem:
        """Add an upstream. An mcp upstream's tools are re-served as `<namespace>__<tool>`; an
        openapi upstream turns each operation of the document into a tool and calls the API
        itself (through a connection's relay when auth_kind is connection). At most 20 per
        gateway.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_upstream(
        self,
        mcp_gateway_id: str,
        upstream_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMcpGatewaysByIdUpstreamsByUpstreamIdResponse:
        """Remove an upstream and its tools from the gateway."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_upstream(
        self,
        mcp_gateway_id: str,
        upstream_id: str,
    ) -> cm.GetMcpGatewaysByIdUpstreamsResponseDataItem:
        """Read one upstream of an MCP gateway."""
        return self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}",
        )

    def update_upstream(
        self,
        mcp_gateway_id: str,
        upstream_id: str,
        body: cm.PatchMcpGatewaysByIdUpstreamsByUpstreamIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpGatewaysByIdUpstreamsResponseDataItem:
        """Change an upstream. Omitted fields keep their value; sending `openapi` recompiles the
        tools.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def test_upstream(
        self,
        mcp_gateway_id: str,
        upstream_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostMcpGatewaysByIdUpstreamsByUpstreamIdTestResponse:
        """Reach the upstream with its own auth and list the tools it would add to the gateway.
        Never fails the request: `ok` is false with an `error` instead.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class McpRegistry:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpRegistryResponse:
        """The instance registry of upstream MCP servers: approved ones, and requests waiting for
        review. A gateway with `registry_only` accepts only approved URLs.
        """
        return self._t.request(
            method="GET",
            path="/v1/mcp_registry",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetMcpRegistryResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostMcpRegistryBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpRegistryResponseDataItem:
        """Add a server to the registry as approved (default), or file it as pending for review."""
        return self._t.request(
            method="POST",
            path="/v1/mcp_registry",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        mcp_registry_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMcpRegistryByIdResponse:
        """Remove a registry entry."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/mcp_registry/{_enc(mcp_registry_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def decide(
        self,
        mcp_registry_id: str,
        body: cm.PostMcpRegistryByIdDecideBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpRegistryResponseDataItem:
        """Approve or reject a registry entry."""
        return self._t.request(
            method="POST",
            path=f"/v1/mcp_registry/{_enc(mcp_registry_id)}/decide",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class MessageReceivers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessageReceiversResponse:
        """Where your providers report delivery: for each supported provider (SES, Brevo, Mailgun,
        SMTP2GO, Postmark, SendGrid, Resend, Twilio, Vonage, MessageBird, Plivo) the URL to
        register on your own provider account, how Atlas verifies the callbacks, whether the
        verification secret is set and when a callback last arrived. Callbacks move ledger
        statuses, suppress hard bounces and complaints and send email.delivered, email.bounced,
        email.complained and sms.delivered events. A key with only messaging:read sees the URLs
        without their tokens.
        """
        return self._t.request(
            method="GET",
            path="/v1/message_receivers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMessageReceiversResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete(
        self,
        provider: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessageReceiversByProviderResponse:
        """Forget the stored verification secret of a provider."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/message_receivers/{_enc(provider)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set(
        self,
        provider: str,
        body: cm.PutMessageReceiversByProviderBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessageReceiversResponseDataItem:
        """Store the secret Atlas verifies this provider's callbacks with (your Mailgun webhook
        signing key, SendGrid public key, Resend webhook secret, Vonage signature secret,
        MessageBird signing key, or the SNS topic ARNs to accept). Write-only: it is never
        returned. Twilio needs none (it uses the auth token of your SMS provider).
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/message_receivers/{_enc(provider)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Messages:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        status: Literal['queued', 'sent', 'delivered', 'bounced', 'complained', 'failed', 'suppressed', 'blocked'] | None = None,
        template: str | None = None,
        provider: str | None = None,
        recipient: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessagesResponse:
        """The message ledger: every email, SMS, WhatsApp, voice and push message sent through your
        own providers, newest first, with its status timeline (queued, sent, delivered, bounced,
        complained, failed, suppressed, blocked), the provider that took it and the id the
        provider gave it. Recipients are shown masked and as a keyed hash; the address is not
        stored. A provider's status callbacks (see GET /v1/message_receivers) move the status
        on. Kept for ledger_retention_days (default 90).
        """
        return self._t.request(
            method="GET",
            path="/v1/messages",
            query=_qd({'channel': channel, 'status': status, 'template': template, 'provider': provider, 'recipient': recipient, 'since': since, 'until': until, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        status: Literal['queued', 'sent', 'delivered', 'bounced', 'complained', 'failed', 'suppressed', 'blocked'] | None = None,
        template: str | None = None,
        provider: str | None = None,
        recipient: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetMessagesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(channel=channel, status=status, template=template, provider=provider, recipient=recipient, since=since, until=until, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_summary(
        self,
        *,
        hours: int | None = None,
    ) -> cm.GetMessagesSummaryResponse:
        """How many messages are in each status over the last `hours` (default 24, up to 720)."""
        return self._t.request(
            method="GET",
            path="/v1/messages/summary",
            query=_qd({'hours': hours}),
        )

    def get(
        self,
        message_id: str,
    ) -> cm.GetMessagesResponseDataItem:
        """One message with its full status timeline and the providers tried."""
        return self._t.request(
            method="GET",
            path=f"/v1/messages/{_enc(message_id)}",
        )


class Messaging:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_country_routes(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessagingCountryRoutesResponse:
        """Per-country SMS routes: numbers in a country go through the named provider (your SMS
        provider or one of its fallbacks) first.
        """
        return self._t.request(
            method="GET",
            path="/v1/messaging/country_routes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_country_routes(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMessagingCountryRoutesResponseDataItem]:
        """Every item of :meth:`list_country_routes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_country_routes(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def set_country_routes(
        self,
        body: cm.PutMessagingCountryRoutesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingCountryRoutesResponseDataItem:
        """Route SMS to a country through a provider. `provider_id` is the id of your SMS provider
        or one of its fallback providers; the other providers still back it up when failover is
        on. Replaces an earlier route for the country.
        """
        return self._t.request(
            method="PUT",
            path="/v1/messaging/country_routes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_country_route(
        self,
        country: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessagingCountryRoutesByCountryResponse:
        """Remove the route for a country."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/messaging/country_routes/{_enc(country)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_settings(
        self,
    ) -> cm.GetMessagingSettingsResponse:
        """Messaging behaviour: automatic suppression, failover and ledger retention."""
        return self._t.request(
            method="GET",
            path="/v1/messaging/settings",
        )

    def set_settings(
        self,
        body: cm.PutMessagingSettingsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingSettingsResponse:
        """Change messaging behaviour. Send only the fields to change. Audited."""
        return self._t.request(
            method="PUT",
            path="/v1/messaging/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_suppressions(
        self,
        *,
        email: str | None = None,
        after: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessagingSuppressionsResponse:
        """The email suppression list, or one address with `email`."""
        return self._t.request(
            method="GET",
            path="/v1/messaging/suppressions",
            query=_qd({'email': email, 'after': after, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_suppressions(
        self,
        *,
        email: str | None = None,
        after: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetMessagingSuppressionsResponseDataItem]:
        """Every item of :meth:`list_suppressions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_suppressions(email=email, after=after, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_suppression(
        self,
        body: cm.PostMessagingSuppressionsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingSuppressionsResponse:
        """Add one or many addresses (a bounce or complaint webhook forwarder can post here).
        Existing entries are updated.
        """
        return self._t.request(
            method="POST",
            path="/v1/messaging/suppressions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_suppression(
        self,
        email: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessagingSuppressionsByEmailResponse:
        """Remove an address from the suppression list."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/messaging/suppressions/{_enc(email)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class MessagingProviders:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def set_push(
        self,
        body: cm.PushProviderApnsFcm | cm.PushProviderExpo,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Configure the push sender used for push MFA and in-app sign-in approval. The body is
        discriminated by `transport`: `apns_fcm` (one row carrying APNS and/or FCM credentials;
        devices are routed by their platform) or `expo` (an Expo access token, write-only;
        delivers to ExponentPushToken devices registered with platform `expo`). Unknown or
        missing keys are refused with a 422 naming `config.<key>`. Secrets are write-only.
        """
        return self._t.request(
            method="PUT",
            path="/v1/messaging_providers/push",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_fallbacks(
        self,
        channel: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessagingProvidersByChannelFallbacksResponse:
        """The fallback providers of a channel (`email`, `sms` or `push`), in the order they are
        tried after your own provider. `failover_order` lists `primary` then each active
        fallback.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_fallbacks(
        self,
        channel: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMessagingProvidersByChannelFallbacksResponseDataItem]:
        """Every item of :meth:`list_fallbacks`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_fallbacks(channel, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_fallback(
        self,
        channel: str,
        body: cm.PostMessagingProvidersByChannelFallbacksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingProvidersByChannelFallbacksResponseDataItem:
        """Add a fallback provider (up to 5 per channel). When your provider errors, Atlas tries
        the fallbacks in order; the ledger shows each attempt. A provider refusing one recipient
        does not fail over. The body is validated per transport exactly like PUT
        /v1/messaging_providers/{channel}. Credentials are yours and write-only.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def set_fallbacks_order(
        self,
        channel: str,
        body: cm.PutMessagingProvidersByChannelFallbacksOrderBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingProvidersByChannelFallbacksResponse:
        """Set the order of the channel's fallback providers. `ids` lists every fallback exactly
        once.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks/order",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_fallback(
        self,
        channel: str,
        fallback_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessagingProvidersByChannelFallbacksByIdResponse:
        """Remove a fallback provider, and any country route that pointed at it."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks/{_enc(fallback_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set_fallback(
        self,
        channel: str,
        fallback_id: str,
        body: cm.PutMessagingProvidersByChannelFallbacksByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingProvidersByChannelFallbacksResponseDataItem:
        """Change a fallback provider. An omitted secret keeps the stored one."""
        return self._t.request(
            method="PUT",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks/{_enc(fallback_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class MfaCampaigns:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMfaCampaignsResponse:
        """List MFA rollout campaigns with their completion numbers, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/mfa_campaigns",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMfaCampaignsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostMfaCampaignsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaCampaignsResponseDataItem:
        """Start an MFA rollout campaign: ask everyone, a group, an organization or an organization
        role to enrol a second factor. Before grace_until users are nagged on the client prompt
        (GET /v1/client/me/mfa/campaign) every nag_interval_days; with enforce, sign-in after
        the deadline requires a second factor. The target must exist and each required factor
        must be enabled for the application (400 otherwise). Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/mfa_campaigns",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        mfa_campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaCampaignsResponseDataItem:
        """End a campaign now. The nag and the enforcement stop at once; the campaign and its
        numbers stay readable.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        mfa_campaign_id: str,
    ) -> cm.GetMfaCampaignsResponseDataItem:
        """Read one MFA campaign with its completion numbers."""
        return self._t.request(
            method="GET",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}",
        )

    def update(
        self,
        mfa_campaign_id: str,
        body: cm.PatchMfaCampaignsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaCampaignsResponseDataItem:
        """Change a running campaign: name, required factors, deadline (null removes it), nag
        interval or enforcement. The target is fixed; end the campaign and start another to
        change who it reaches.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_users(
        self,
        mfa_campaign_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMfaCampaignsByIdUsersResponse:
        """List the users a campaign has touched (nagged, exempted or given their own required
        factors), newest first. `limit` up to 500.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}/users",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_users(
        self,
        mfa_campaign_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetMfaCampaignsByIdUsersResponseDataItem]:
        """Every item of :meth:`list_users`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_users(mfa_campaign_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_user(
        self,
        mfa_campaign_id: str,
        user_id: str,
    ) -> cm.GetMfaCampaignsByIdUsersResponseDataItem:
        """One user's standing in a campaign: their own required factors and exemption, nag
        history, and what they still owe (`effective`).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}/users/{_enc(user_id)}",
        )

    def set_user(
        self,
        mfa_campaign_id: str,
        user_id: str,
        body: cm.PutMfaCampaignsByIdUsersByUserIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaCampaignsByIdUsersResponseDataItem:
        """Set one user's own required factors and/or an exemption until a date. Send null to clear
        either. The user's own factors replace the campaign's for them.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}/users/{_enc(user_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class MfaFactorQuarantines:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        user_id: str | None = None,
        active: bool | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMfaFactorQuarantinesResponse:
        """Second factors held in quarantine because they were enrolled while the account looked
        compromised.
        """
        return self._t.request(
            method="GET",
            path="/v1/mfa_factor_quarantines",
            query=_qd({'user_id': user_id, 'active': active, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        user_id: str | None = None,
        active: bool | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetMfaFactorQuarantinesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(user_id=user_id, active=active, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def release(
        self,
        mfa_factor_quarantine_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaFactorQuarantinesResponseDataItem:
        """Release a quarantined factor so it can complete sign-ins."""
        return self._t.request(
            method="POST",
            path=f"/v1/mfa_factor_quarantines/{_enc(mfa_factor_quarantine_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class MigrationsSource:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def verify(
        self,
        source: str,
        body: cm.PostMigrationsBySourceVerifyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostMigrationsBySourceVerifyResponse:
        """Dual-run check: is this old `source` token valid? Answers only while the source's
        `dual_run_until` window is open (403 closed otherwise). Nothing is consumed and no
        session is created. Every call is counted per day in GET /v1/migrations/status. Returns
        `valid`, `reason` (invalid | expired | unavailable) and the mapped Atlas `user_id` when
        the user was imported.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class MigrationsStatus:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
        *,
        quiet_days: int | None = None,
    ) -> cm.GetMigrationsStatusResponse:
        """Where the move stands: imported users by credential type (bcrypt, argon2, scrypt,
        pbkdf2, other, social, none; imported = has an external_id), bridged sessions, imported
        legacy sessions still live, failed bridge attempts by reason, daily use per source, and
        `safe_to_delete_old_auth` with the blockers that keep it false (recent use, live
        sessions, an open dual-run window, an enabled bridge, or `no_enabled_source` when no
        bridge or verifier was ever enabled or used, so nothing has been proven quiet).
        `quiet_days` (default 14, max 90) sets how long the old auth must be unused.
        """
        return self._t.request(
            method="GET",
            path="/v1/migrations/status",
            query=_qd({'quiet_days': quiet_days}),
        )


class OauthApplicationTypes:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthApplicationTypesResponse:
        """The application types `application_type` accepts when creating an OAuth client (web,
        spa, native, device, mcp), with the defaults each applies to the fields you leave out.
        """
        return self._t.request(
            method="GET",
            path="/v1/oauth_application_types",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOauthApplicationTypesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class OauthClients:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def set_organization_access(
        self,
        oauth_client_id: str,
        body: cm.PutOauthClientsByIdOrganizationAccessBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutOauthClientsByIdOrganizationAccessResponse:
        """Set who may use an application. `open` (default): any organization. `restricted`: only
        organizations granted access (and, when a grant lists roles, members holding them); a
        sign-in outside an entitled organization is refused with `access_denied` at the
        authorize endpoint.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/organization_access",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_organizations(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdOrganizationsResponse:
        """The organizations that have access to an application, with the application's access
        mode.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/organizations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_organizations(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOauthClientsByIdOrganizationsResponseDataItem]:
        """Every item of :meth:`list_organizations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_organizations(oauth_client_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def list_token_exchange_profiles(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdTokenExchangeProfilesResponse:
        """List the custom subject_token_type URIs an OAuth client may present to the token-
        exchange grant.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_token_exchange_profiles(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOauthClientsByIdTokenExchangeProfilesResponseDataItem]:
        """Every item of :meth:`list_token_exchange_profiles`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_token_exchange_profiles(oauth_client_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_token_exchange_profile(
        self,
        oauth_client_id: str,
        body: cm.PostOauthClientsByIdTokenExchangeProfilesBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Register a custom subject_token_type (a urn: or https URI that is not a standard Atlas
        or IETF token type) for a confidential client. An exchange with it runs your
        `custom_token_exchange` Action, which validates the token and names the user to issue
        tokens for.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_token_exchange_profile(
        self,
        oauth_client_id: str,
        profile_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove a token exchange profile."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles/{_enc(profile_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def update_token_exchange_profile(
        self,
        oauth_client_id: str,
        profile_id: str,
        body: cm.PatchOauthClientsByIdTokenExchangeProfilesByProfileIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Rename or enable / disable a token exchange profile."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles/{_enc(profile_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_usage(
        self,
        oauth_client_id: str,
        *,
        days: int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdUsageResponse:
        """Per-day usage of one OAuth client for the last `days` days (1 to 90, default 30): token
        endpoint calls, access tokens issued, distinct active users, errors and rate-limited
        calls, with totals. The path takes the oac_ id or the public client_id. The developer
        can read the same report at GET /oauth2/register/{client_id}/usage with the client's
        registration_access_token.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/usage",
            query=_qd({'days': days, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_usage(
        self,
        oauth_client_id: str,
        *,
        days: int | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetOauthClientsByIdUsageResponseDataItem]:
        """Every item of :meth:`list_usage`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_usage(oauth_client_id, days=days, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_webhook(
        self,
        oauth_client_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove the client's event webhook. 204."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_webhook(
        self,
        oauth_client_id: str,
    ) -> cm.GetOauthClientsByIdWebhookResponse:
        """The webhook this client receives user events on (404 when it has none)."""
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook",
        )

    def set_webhook(
        self,
        oauth_client_id: str,
        body: cm.PutOauthClientsByIdWebhookBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOauthClientsByIdWebhookResponse:
        """Create or update the client's event webhook: a signed, retried endpoint that receives
        events about users who granted the client access, never the instance's own stream.
        user.updated carries only what the user's granted scopes allow (email with the email
        scope, name and picture with profile). enabled_events may also name your own types
        declared with PUT /v1/instance/app_event_types; those reach the client only for users
        who granted the type's required scope. The signing secret is returned once, on create
        (201). Audited.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class OauthGrants:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def import_(
        self,
        body: cm.PostOauthGrantsImportBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOauthGrantsImportResponse:
        """Carry over what users granted a previous OAuth provider: records their consent and
        stores refresh-token hashes (bcrypt or sha256, never the tokens). An app holding an old
        refresh token gets a new access token from the token endpoint once, with a new Atlas
        refresh token; from then on it rotates as usual. Import the clients first (POST
        /v1/oauth_clients with client_id). The response lists one result per submitted row
        (index, status imported|failed, client_id, user_id, refresh_tokens, message) plus
        totals. Failures are reported per row and never stop the others. With `?dry_run=true`
        every row is validated exactly as a real import would and the same report comes back at
        the top level with `dry_run: true`, but nothing is written. `would_return` carries the
        same report for older callers and is deprecated: read the top-level fields.
        """
        return self._t.request(
            method="POST",
            path="/v1/oauth_grants/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class OauthPublishers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthPublishersResponse:
        """List the verified-publisher claims of your OAuth apps, with the apps attached to each."""
        return self._t.request(
            method="GET",
            path="/v1/oauth_publishers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOauthPublishersResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostOauthPublishersBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOauthPublishersResponseDataItem:
        """Claim a publisher name for a domain. Returns the DNS TXT record (record_name and
        record_value) to publish; then call verify. Nothing changes for any app until the domain
        is verified and the app is attached. Audited as oauth_publisher.created; emits
        oauth_publisher.updated.
        """
        return self._t.request(
            method="POST",
            path="/v1/oauth_publishers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        oauth_publisher_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOauthPublishersByIdResponse:
        """Delete a publisher. Its apps stay as they are (a shared-sector app keeps its sector, so
        no subject identifier changes). Refused with 409 while apps are attached to a shared-
        sector publisher. Audited; emits oauth_publisher.updated.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        oauth_publisher_id: str,
    ) -> cm.GetOauthPublishersResponseDataItem:
        """Get one OAuth publisher, with its domain verification status."""
        return self._t.request(
            method="GET",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}",
        )

    def update(
        self,
        oauth_publisher_id: str,
        body: cm.PatchOauthPublishersByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOauthPublishersResponseDataItem:
        """Change the name, the shared sector or the consent skip. Send only the fields to change.
        The domain cannot change: create a new publisher. Turning shared_sector off is refused
        while apps are attached. Audited; emits oauth_publisher.updated.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_client(
        self,
        oauth_publisher_id: str,
        client_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOauthPublishersResponseDataItem:
        """Detach an app from a publisher. The consent screen stops naming the publisher for it and
        its repeat consent is no longer shared; a shared sector it already took stays.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}/clients/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set_client(
        self,
        oauth_publisher_id: str,
        client_id: str,
        body: cm.PutOauthPublishersByIdClientsByClientIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOauthPublishersResponseDataItem:
        """Attach an app (its public client_id) to a verified publisher. The app's homepage_url
        must be an https URL on the publisher's domain, and an app belongs to one publisher.
        With a shared sector the app must be pairwise and takes the publisher's sector; if it
        already has another sector, send allow_subject_change: true to confirm that users'
        subject identifiers in it change. Attaching an app already attached returns the
        publisher unchanged.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}/clients/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def verify(
        self,
        oauth_publisher_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOauthPublishersByIdVerifyResponse:
        """Look up the DNS TXT record and mark the publisher verified when it is there. A record
        that is gone un-verifies the publisher; a DNS lookup that fails for another reason
        changes nothing. record_found tells what this check saw. Audited as
        oauth_publisher.verified when the status changes.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Opa:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_bundle(
        self,
        store: str,
    ) -> str:
        """An OPA bundle (gzipped tarball with .manifest and data.json) holding the store's model
        and unexpired tuples under data.atlas.fga.{store id}, for Rego you write over Atlas
        data. Supports ETag and If-None-Match (304).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/opa/bundles/{_enc(store)}",
        )

    def create_log(
        self,
        body: list[dict[str, Any]] | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """OPA decision log ingestion: accepts the gzipped JSON array OPA's decision_logs plugin
        posts and records each event in the Atlas decision log (source `opa`), sampled and
        redacted by the instance settings.
        """
        return self._t.request(
            method="POST",
            path="/v1/opa/logs",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def status(
        self,
        body: dict[str, Any] | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Accepts OPA status updates and ignores them, so a default OPA configuration does not log
        errors.
        """
        return self._t.request(
            method="POST",
            path="/v1/opa/status",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def x_data_v1(
        self,
        body: cm.PostOpaV1DataBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """OPA Data API over Atlas. POST { "input": ... } to atlas/abac/allow (boolean),
        atlas/abac/decision, atlas/fga/{store}/allow (input user, relation, object) or
        atlas/fga/{store}/objects (input user, relation, type); the answer is { "result": ... }.
        An unknown path answers 200 with no result, as OPA does. Not a Rego runtime: Atlas
        evaluates Cedar and relationship models.
        """
        return self._t.request(
            method="POST",
            path="/v1/opa/v1/data/*",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Openfga:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_stores_assertion(
        self,
        store: str,
        model: str,
    ) -> dict[str, Any]:
        """Read the stored assertions for a model version."""
        return self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{_enc(store)}/assertions/{_enc(model)}",
        )

    def set_stores_assertion(
        self,
        store: str,
        model: str,
        body: cm.PutOpenfgaStoresByStoreAssertionsByModelBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> None:
        """Replace the stored assertions for a model version."""
        return self._t.request(
            method="PUT",
            path=f"/v1/openfga/stores/{_enc(store)}/assertions/{_enc(model)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class OrgRoleSets:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrgRoleSetsResponse:
        """List role sets: named sets of roles an organization may assign, each with a default
        role.
        """
        return self._t.request(
            method="GET",
            path="/v1/org_role_sets",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOrgRoleSetsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostOrgRoleSetsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrgRoleSetsResponseDataItem:
        """Create a role set. role_keys must be instance-wide roles that exist; org:admin is always
        allowed and need not be listed. 409 when the key is taken. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/org_role_sets",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        org_role_set_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrgRoleSetsByIdResponse:
        """Delete a role set. 409 while an organization still uses it."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/org_role_sets/{_enc(org_role_set_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        org_role_set_id: str,
    ) -> cm.GetOrgRoleSetsResponseDataItem:
        """One role set, by id or key."""
        return self._t.request(
            method="GET",
            path=f"/v1/org_role_sets/{_enc(org_role_set_id)}",
        )

    def update(
        self,
        org_role_set_id: str,
        body: cm.PatchOrgRoleSetsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrgRoleSetsResponseDataItem:
        """Change a role set. Members already holding a role the set no longer lists keep it; only
        new assignments are checked.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/org_role_sets/{_enc(org_role_set_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class OrgTemplates:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrgTemplatesResponse:
        """List organization templates."""
        return self._t.request(
            method="GET",
            path="/v1/org_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOrgTemplatesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostOrgTemplatesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrgTemplatesResponseDataItem:
        """Create an organization template: custom roles (with existing permissions), policy, role
        set and default role, seat limit and warning level, and metadata. 409 when the key is
        taken. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/org_templates",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        org_template_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrgTemplatesByIdResponse:
        """Delete a template. Organizations made from it are not touched."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/org_templates/{_enc(org_template_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        org_template_id: str,
    ) -> cm.GetOrgTemplatesResponseDataItem:
        """One template, by id or key."""
        return self._t.request(
            method="GET",
            path=f"/v1/org_templates/{_enc(org_template_id)}",
        )

    def update(
        self,
        org_template_id: str,
        body: cm.PatchOrgTemplatesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrgTemplatesResponseDataItem:
        """Change a template. Organizations already made from it are not touched."""
        return self._t.request(
            method="PATCH",
            path=f"/v1/org_templates/{_enc(org_template_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def create_organization(
        self,
        org_template_id: str,
        body: cm.PostOrgTemplatesByIdOrganizationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrgTemplatesByIdOrganizationsResponse:
        """Create an organization from a template. The organization is created the normal way
        (hooks, slug rules, organization.created), then gets the template's custom roles,
        policy, role set and default role, seat settings and metadata. `public_metadata` and
        `private_metadata` merge over the template's. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/org_templates/{_enc(org_template_id)}/organizations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class OrganizationConnections:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationConnectionsResponse:
        """B2B connections between organizations, optionally those involving one organization."""
        return self._t.request(
            method="GET",
            path="/v1/organization_connections",
            query=_qd({'organization_id': organization_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetOrganizationConnectionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(organization_id=organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostOrganizationConnectionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationConnectionsResponse:
        """Invite a partner organization to use an application the supplier organization holds.
        Returns a one-time `token` for the partner's administrator; the invitation lasts 14
        days.
        """
        return self._t.request(
            method="POST",
            path="/v1/organization_connections",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        organization_connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationConnectionsResponseDataItem:
        """Revoke a connection (or a pending invitation). The partner organization loses access to
        the application.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/organization_connections/{_enc(organization_connection_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def accept(
        self,
        organization_connection_id: str,
        body: cm.PostOrganizationConnectionsByIdAcceptBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationConnectionsResponseDataItem:
        """Accept an invitation with its token: the partner organization gains access to the
        application. The token works once.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organization_connections/{_enc(organization_connection_id)}/accept",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Organizations:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_app_webhook_endpoints_deliveries(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        status: Literal['pending', 'success', 'failed'] | None = None,
        event_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        trace: str | None = None,
    ) -> cm.GetWebhookEndpointsByIdDeliveriesResponse:
        """The endpoint's delivery log: payload, response and retry state for each attempt,
        filterable by status, app event type and time.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/deliveries",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'status': status, 'event_type': event_type, 'since': since, 'until': until, 'trace': trace}),
        )

    def iter_list_app_webhook_endpoints_deliveries(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        limit: int | None = None,
        status: Literal['pending', 'success', 'failed'] | None = None,
        event_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
        trace: str | None = None,
    ) -> Iterator[cm.WebhookDelivery]:
        """Every item of :meth:`list_app_webhook_endpoints_deliveries`, following the cursor page
        by page.
        """
        cursor: str | None = None
        while True:
            page = self.list_app_webhook_endpoints_deliveries(organization_id, endpoint_id, limit=limit, status=status, event_type=event_type, since=since, until=until, trace=trace, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def redeliver_delivery_app_webhook_endpoints(
        self,
        organization_id: str,
        endpoint_id: str,
        delivery_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdDeliveriesByDeliveryIdRedeliverResponse:
        """Redeliver one past delivery as a fresh attempt (same event id). 409 when the event has
        passed its 90-day retention; a delivery of another endpoint is a 404.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/deliveries/{_enc(delivery_id)}/redeliver",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def replay_app_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        body: cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdReplayBody | None = None,
        *,
        since: str | None = None,
        until: str | None = None,
        event_type: str | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Re-send every event of this organization since `since` (or since=failing_since) that the
        endpoint subscribes to and has not received, including events published while it was
        disabled. At most 1,000 per call; running it again queues nothing new. 409 if the
        endpoint is disabled.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/replay",
            query=_qd({'since': since, 'until': until, 'event_type': event_type, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def reveal_secret_app_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdRevealSecretResponse:
        """Show the current whsec_ signing secret again. Audited."""
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/reveal_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def rotate_secret_app_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdWebhookEndpointsByEndpointIdRotateSecretResponse:
        """Rotate the whsec_ signing secret. The previous secret keeps signing alongside the new
        one (a second v1 entry in webhook-signature) for 24 hours.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/rotate_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_applications(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationsByIdApplicationsResponse:
        """The OAuth applications an organization has been given access to."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/applications",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_applications(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetOauthClientsByIdOrganizationsResponseDataItem]:
        """Every item of :meth:`list_applications`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_applications(organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_application(
        self,
        organization_id: str,
        client_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrganizationsByIdApplicationsByClientIdResponse:
        """Take an organization's access to an application away."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{_enc(organization_id)}/applications/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set_application(
        self,
        organization_id: str,
        client_id: str,
        body: cm.PutOrganizationsByIdApplicationsByClientIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOauthClientsByIdOrganizationsResponseDataItem:
        """Give an organization access to an application (by client id or id), optionally limited
        to some organization roles. Idempotent; send `enabled: false` to pause access without
        removing it. Only matters while the application is `restricted`.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/applications/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_audit_logs(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        action: str | None = None,
        format: str | None = None,
        from_: str | None = None,
        to: str | None = None,
    ) -> cm.GetOrganizationsByIdAuditLogsResponse:
        """The organization's audit trail: actions on the organization or naming it. A page, newest
        first, or with `format=jsonl` the whole trail as newline-delimited JSON for download
        (capped at 100000 rows, then a truncated marker). Filter with `action` (exact, or a
        prefix ending in "."), `from` and `to` (ISO dates).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/audit_logs",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'action': action, 'format': format, 'from': from_, 'to': to}),
        )

    def iter_list_audit_logs(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
        action: str | None = None,
        format: str | None = None,
        from_: str | None = None,
        to: str | None = None,
    ) -> Iterator[cm.GetOrganizationsByIdAuditLogsResponseDataItem]:
        """Every item of :meth:`list_audit_logs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_audit_logs(organization_id, limit=limit, action=action, format=format, from_=from_, to=to, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def list_directory_sync_runs(
        self,
        organization_id: str,
        *,
        limit: str | None = None,
        status: Literal['queued', 'running', 'succeeded', 'failed'] | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationsByIdDirectorySyncRunsResponse:
        """Directory sync runs of one organization (its LDAP connections and HR/directory pull
        sources together), newest first. Filter with status. A failed run can be retried with
        POST /v1/organizations/{id}/directory_sync_runs/{runId}/retry.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/directory_sync_runs",
            query=_qd({'limit': limit, 'status': status, 'starting_after': starting_after}),
        )

    def iter_list_directory_sync_runs(
        self,
        organization_id: str,
        *,
        limit: str | None = None,
        status: Literal['queued', 'running', 'succeeded', 'failed'] | None = None,
    ) -> Iterator[cm.GetOrganizationsByIdDirectorySyncRunsResponseDataItem]:
        """Every item of :meth:`list_directory_sync_runs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_directory_sync_runs(organization_id, limit=limit, status=status, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def retry_directory_sync_run(
        self,
        organization_id: str,
        run_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationsByIdDirectorySyncRunsResponseDataItem:
        """Queue a new run for the source of a failed run; the new run records retry_of. Only a
        failed run can be retried (400), and only while the source is active and has no run
        queued or running (409). Answers 202 with the queued run; the worker executes it.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/directory_sync_runs/{_enc(run_id)}/retry",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def import_invitation(
        self,
        organization_id: str,
        body: cm.PostOrganizationsByIdInvitationsImportBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdInvitationsImportResponse:
        """Import up to 500 invitations that already exist in another system and keep their links
        working: each row carries the `token_sha256` of the token already issued and its
        original `expires_at`. A pending invitation to the same address with the same token is
        `unchanged`; with another token it is replaced. A bad row is reported as `invalid_row`
        and does not stop the others. `dry_run` checks every row and writes nothing. Accepts
        Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/invitations/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_it_alerts(
        self,
        organization_id: str,
        *,
        kind: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationsByIdItAlertsResponse:
        """Recent alerts sent to an organization's IT contacts, newest first: a single sign-on
        signing certificate nearing expiry, failing sign-ins, failing SCIM requests. Filter with
        kind (certificate_expiring, sso_failure, scim_error); page with limit and
        starting_after. Each alert also fired the organization.it_alert webhook event. Another
        instance's or org's id is a 404.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/it_alerts",
            query=_qd({'kind': kind, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_it_alerts(
        self,
        organization_id: str,
        *,
        kind: str | None = None,
        limit: str | None = None,
    ) -> Iterator[cm.GetOrganizationsByIdItAlertsResponseDataItem]:
        """Every item of :meth:`list_it_alerts`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_it_alerts(organization_id, kind=kind, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_it_health(
        self,
        organization_id: str,
    ) -> cm.GetOrganizationsByIdItHealthResponse:
        """Live health of one organization's enterprise setup, for its IT admin: each SSO
        connection's last successful and failed sign-in and signing-certificate expiry, the
        directory's last SCIM request and errors, the last run of each directory sync, the email
        domains' verification state, and the issues that need attention. Read from what Atlas
        already recorded; it probes nothing. The hosted admin portal shows the same report.
        Needs the scim:read scope as well as sso_connections:read. Needs scim:read as well as
        sso_connections:read. Another instance's or org's id is a 404.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/it_health",
        )

    def create_membership_import(
        self,
        organization_id: str,
        body: cm.PostOrganizationsByIdMembershipImportsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdMembershipImportsResponse:
        """Import up to 5000 memberships into an organization as a background job. Send
        `memberships` (a list of { email or user_id, role, expires_at, public_metadata }) or
        `csv` (header row with email, user_id, role, expires_at). Each row goes through the same
        checks as adding a member: the seat limit, the role set, hooks and events. `on_existing`
        is `skip` (default) or `update`; `invite_missing` invites an email no account has. A bad
        row is recorded and the rest continue. Answers 202 with the job: poll GET /v1/jobs/{id},
        errors at GET /v1/jobs/{id}/errors, and import_job.completed is sent when it ends.
        Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/membership_imports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_membership(
        self,
        organization_id: str,
        user_id: str,
    ) -> cm.GetOrganizationsByIdMembershipsByUserIdResponse:
        """Read one membership: role, `role_source`, scope, in the same shape as a list item. 404
        when the user is not a member.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/memberships/{_enc(user_id)}",
        )

    def set_membership(
        self,
        organization_id: str,
        user_id: str,
        body: cm.PutOrganizationsByIdMembershipsByUserIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutOrganizationsByIdMembershipsByUserIdResponse:
        """Create or update a membership. Body: `role` (required), `role_source` (optional, as on
        PATCH), and the seat's own `public_metadata`, `private_metadata`, `permissions` (extra
        permission keys that join org_permissions in the session token) and
        `allowed_sign_in_methods` (a session signed in another way mints without this
        organization's claims). 201 when it adds the member, 200 when it changes the role. When
        a directory (SCIM, SSO or LDAP) manages the existing role and `role_source` does not
        name that same source, nothing changes and the answer is 200 with `unchanged: true` and
        the current `role_source`. Emits organizationMembership.created or
        organizationMembership.updated. Accepts Idempotency-Key.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/memberships/{_enc(user_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_mfa_status(
        self,
        organization_id: str,
        *,
        session_id: str,
    ) -> cm.GetOrganizationsByIdMfaStatusResponse:
        """Does this session meet THIS organization's MFA policy? The same check the token mint
        runs for the active organization, answered for any organization (Atlas id or external
        id), so an app that acts in a per-request organization need not make it the active one.
        A non-member answers `member: false, ok: false`. 404 for an unknown organization or a
        session of another instance.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/mfa_status",
            query=_qd({'session_id': session_id}),
        )

    def get_role_policy(
        self,
        organization_id: str,
    ) -> cm.GetOrganizationsByIdRolePolicyResponse:
        """The roles an organization may assign and the role a new seat gets by default."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/role_policy",
        )

    def set_role_policy(
        self,
        organization_id: str,
        body: cm.PutOrganizationsByIdRolePolicyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationsByIdRolePolicyResponse:
        """Point an organization at a role set and/or give it its own default role (null clears
        either). Adding a member, accepting an invitation or changing a role to one outside the
        set is refused with 422 ROLE_NOT_IN_ROLE_SET; org:admin and the organization's own
        custom roles are always allowed, and directory syncs report what the directory says.
        Existing members are not changed.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/role_policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_scim_requests(
        self,
        organization_id: str,
        *,
        limit: str | None = None,
        starting_after: str | None = None,
        status: Literal['ok', 'error'] | None = None,
        token_id: str | None = None,
        resource: str | None = None,
        since: str | None = None,
    ) -> cm.GetOrganizationsByIdScimRequestsResponse:
        """The requests the organization's directory sent to the SCIM endpoint, newest first, kept
        30 days: method, path, resource, the status Atlas answered, why a failed one failed, the
        source IP and the duration. Never the request body. Includes requests refused by a
        token's IP allow-list. Filter with status (ok or error), token_id, resource and since;
        page with limit and starting_after.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/scim/requests",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'status': status, 'token_id': token_id, 'resource': resource, 'since': since}),
        )

    def iter_list_scim_requests(
        self,
        organization_id: str,
        *,
        limit: str | None = None,
        status: Literal['ok', 'error'] | None = None,
        token_id: str | None = None,
        resource: str | None = None,
        since: str | None = None,
    ) -> Iterator[cm.GetOrganizationsByIdScimRequestsResponseDataItem]:
        """Every item of :meth:`list_scim_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_scim_requests(organization_id, limit=limit, status=status, token_id=token_id, resource=resource, since=since, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_seats(
        self,
        organization_id: str,
    ) -> cm.GetOrganizationsByIdSeatsResponse:
        """Seats used, pending invitations and seats left for an organization."""
        return self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/seats",
        )

    def set_seats(
        self,
        organization_id: str,
        body: cm.PutOrganizationsByIdSeatsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationsByIdSeatsResponse:
        """Set the seat limit (max_allowed_memberships; null = unlimited) and the warning level.
        Lowering the limit below the members already seated removes nobody; new seats are
        refused. Emits organization.seats_low when used seats reach warn_percent of the limit
        and organization.seat_limit_reached when the limit is reached or someone is turned away,
        each once per crossing.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/seats",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def redeliver_delivery_webhook_endpoints(
        self,
        organization_id: str,
        endpoint_id: str,
        delivery_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdDeliveriesByDeliveryIdRedeliverResponse:
        """Redeliver one past delivery as a fresh attempt (same event id). 409 when the event has
        passed its 90-day retention; a delivery of another endpoint is a 404.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/deliveries/{_enc(delivery_id)}/redeliver",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def replay_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        body: cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdReplayBody | None = None,
        *,
        since: str | None = None,
        until: str | None = None,
        event_type: str | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Re-send every event of this organization since `since` (or since=failing_since) that the
        endpoint subscribes to and has not received. At most 1,000 per call; running it again
        queues nothing new. 409 if the endpoint is disabled.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/replay",
            query=_qd({'since': since, 'until': until, 'event_type': event_type, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def reveal_secret_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdRevealSecretResponse:
        """Show the current whsec_ signing secret of one of the organization's endpoints again.
        Audited.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/reveal_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def test_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        wait: str | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.WebhookTestResult:
        """Send a signed webhook.test event to this endpoint only. With ?wait=10s the attempt is
        made now and its result returned; otherwise it is queued (201).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/test",
            query=_qd({'wait': wait, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class PasskeyCampaigns:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPasskeyCampaignsResponse:
        """List passkey campaigns with their completion metrics (eligible, prompted, enrolled),
        newest first.
        """
        return self._t.request(
            method="GET",
            path="/v1/passkey_campaigns",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetPasskeyCampaignsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostPasskeyCampaignsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPasskeyCampaignsResponseDataItem:
        """Start a passkey enrolment campaign. While it runs, signed-in users in the segment who
        have no passkey are told to show the passkey prompt (GET /v1/client/me/passkeys/prompt),
        at most once per frequency_cap_days.
        """
        return self._t.request(
            method="POST",
            path="/v1/passkey_campaigns",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        passkey_campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPasskeyCampaignsResponseDataItem:
        """End a campaign now. The prompt stops at once; the campaign and its numbers stay
        readable.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/passkey_campaigns/{_enc(passkey_campaign_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        passkey_campaign_id: str,
    ) -> cm.GetPasskeyCampaignsResponseDataItem:
        """Read one passkey campaign with its completion metrics."""
        return self._t.request(
            method="GET",
            path=f"/v1/passkey_campaigns/{_enc(passkey_campaign_id)}",
        )


class Policies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_audience(
        self,
        policy_id: str,
    ) -> cm.GetPoliciesByIdAudienceResponse:
        """Who a policy is asked of: everyone, or the members of the listed organizations."""
        return self._t.request(
            method="GET",
            path=f"/v1/policies/{_enc(policy_id)}/audience",
        )

    def set_audience(
        self,
        policy_id: str,
        body: cm.PutPoliciesByIdAudienceBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPoliciesByIdAudienceResponse:
        """Set a policy's audience. orgs asks only members of the listed organizations (1-200, all
        must exist) at their next sign-in, and never at sign-up; everyone (the default) clears
        the list. A user who is in none of the organizations is not asked and is not blocked.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/policies/{_enc(policy_id)}/audience",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_versions_translations(
        self,
        policy_id: str,
        version_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPoliciesByIdVersionsByVersionIdTranslationsResponse:
        """A policy version's texts in other languages."""
        return self._t.request(
            method="GET",
            path=f"/v1/policies/{_enc(policy_id)}/versions/{_enc(version_id)}/translations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_versions_translations(
        self,
        policy_id: str,
        version_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetPoliciesByIdVersionsByVersionIdTranslationsResponseDataItem]:
        """Every item of :meth:`list_versions_translations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_versions_translations(policy_id, version_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_versions_translation(
        self,
        policy_id: str,
        version_id: str,
        locale: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePoliciesByIdVersionsByVersionIdTranslationsByLocaleResponse:
        """Remove a translation from a draft version. A published version's translations stay
        (409).
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/policies/{_enc(policy_id)}/versions/{_enc(version_id)}/translations/{_enc(locale)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set_versions_translation(
        self,
        policy_id: str,
        version_id: str,
        locale: str,
        body: cm.PutPoliciesByIdVersionsByVersionIdTranslationsByLocaleBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPoliciesByIdVersionsByVersionIdTranslationsResponseDataItem:
        """Add or replace the text of a version in one language (content_markdown or content_html,
        sanitised like the version itself). GET /v1/client/policies?locale= then serves it, and
        an acceptance records the hash of the text that was shown. A published version can gain
        languages but a language already there cannot change (409); a draft can change freely.
        400 for an external policy.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/policies/{_enc(policy_id)}/versions/{_enc(version_id)}/translations/{_enc(locale)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Provisioning:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def preview(
        self,
        body: cm.PostProvisioningPreviewBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostProvisioningPreviewResponse:
        """Evaluate an attribute mapping for one user and return each attribute's value and the
        payload a connector would receive. Takes the mapping and lookups, or a target_id to use
        its own, and a real user_id or a made-up sample user. Writes nothing and contacts
        nobody; this is the live preview behind the mapping editor.
        """
        return self._t.request(
            method="POST",
            path="/v1/provisioning/preview",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ProvisioningConnectors:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetProvisioningConnectorsResponse:
        """List the outbound provisioning connector kinds (scim, google_workspace, microsoft_graph,
        rest, ad_writeback, sql) with the credentials and settings each needs, whether it needs
        a relay agent, and the functions the mapping expression language offers.
        """
        return self._t.request(
            method="GET",
            path="/v1/provisioning_connectors",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetProvisioningConnectorsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class RateLimitOverrides:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        subject_type: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRateLimitOverridesResponse:
        """List per-subject overrides, oldest first."""
        return self._t.request(
            method="GET",
            path="/v1/rate_limit_overrides",
            query=_qd({'subject_type': subject_type, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        subject_type: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetRateLimitOverridesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(subject_type=subject_type, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete(
        self,
        subject_type: str,
        subject_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteRateLimitOverridesBySubjectTypeBySubjectIdResponse:
        """Remove the override for one subject. Emits rate_limit_policy.updated."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/rate_limit_overrides/{_enc(subject_type)}/{_enc(subject_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        subject_type: str,
        subject_id: str,
    ) -> cm.GetRateLimitOverridesResponseDataItem:
        """The override for one subject, or 404."""
        return self._t.request(
            method="GET",
            path=f"/v1/rate_limit_overrides/{_enc(subject_type)}/{_enc(subject_id)}",
        )

    def set(
        self,
        subject_type: str,
        subject_id: str,
        body: cm.PutRateLimitOverridesBySubjectTypeBySubjectIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRateLimitOverridesResponseDataItem:
        """Pin one subject (an API key, user, organization or machine of this instance, or one IP
        address) to a policy of its kind (policy_id) or to an inline limit (limit with
        window_seconds, optional burst). An override beats every other rule, including the key's
        own rate_limit. Replaces any earlier override for the subject; the same content again
        changes nothing. expires_at ends it on its own. An override pointing at a disabled
        policy does not apply. Emits rate_limit_policy.updated.
        """
        return self._t.request(
            method="PUT",
            path=f"/v1/rate_limit_overrides/{_enc(subject_type)}/{_enc(subject_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class RateLimitPolicies:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        subject: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRateLimitPoliciesResponse:
        """List the rate-limit policies for your own API, optionally for one subject kind."""
        return self._t.request(
            method="GET",
            path="/v1/rate_limit_policies",
            query=_qd({'subject': subject, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        subject: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetRateLimitPoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(subject=subject, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostRateLimitPoliciesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRateLimitPoliciesResponseDataItem:
        """Create a rate-limit policy: a limit per window for one kind of subject (API key, user,
        organization, machine or IP). Atlas stores and distributes it; your service enforces it.
        Mark one policy per subject kind as the default, and add plan_overrides to give a
        billing plan its own limit. Precedence for a subject: a per-subject override, then an
        API key's own rate_limit, then the default policy's entry for the subject's plan, then
        the default policy. Names are unique (409); a second default for a subject kind is
        refused (409). Honours Idempotency-Key. Emits rate_limit_policy.updated.
        """
        return self._t.request(
            method="POST",
            path="/v1/rate_limit_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_resolve(
        self,
        *,
        key_id: str | None = None,
        user_id: str | None = None,
        org_id: str | None = None,
        machine_id: str | None = None,
        ip: str | None = None,
    ) -> cm.GetRateLimitPoliciesResolveResponse:
        """The limit that applies to one subject right now and which rule chose it. Send exactly
        one of key_id, user_id, org_id, machine_id or ip. A subject nothing applies to returns
        rate_limit null. The version changes whenever the effective limit changes, so a cached
        copy stays valid until it differs.
        """
        return self._t.request(
            method="GET",
            path="/v1/rate_limit_policies/resolve",
            query=_qd({'key_id': key_id, 'user_id': user_id, 'org_id': org_id, 'machine_id': machine_id, 'ip': ip}),
        )

    def delete(
        self,
        rate_limit_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteRateLimitPoliciesByIdResponse:
        """Delete a policy. Refused with 409 while per-subject overrides still point at it. Emits
        rate_limit_policy.updated.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/rate_limit_policies/{_enc(rate_limit_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        rate_limit_policy_id: str,
    ) -> cm.GetRateLimitPoliciesResponseDataItem:
        """One rate-limit policy."""
        return self._t.request(
            method="GET",
            path=f"/v1/rate_limit_policies/{_enc(rate_limit_policy_id)}",
        )

    def update(
        self,
        rate_limit_policy_id: str,
        body: cm.PatchRateLimitPoliciesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRateLimitPoliciesResponseDataItem:
        """Change a policy. Send only the fields to change; the version goes up by one. Sending the
        same values again changes nothing. subject cannot change. Emits
        rate_limit_policy.updated with the before and after.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/rate_limit_policies/{_enc(rate_limit_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ReferralRewardRules:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetReferralRewardRulesResponse:
        """The instance's referral reward terms. Rewards are off until you turn them on."""
        return self._t.request(
            method="GET",
            path="/v1/referral_reward_rules",
        )

    def set(
        self,
        body: cm.PutReferralRewardRulesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetReferralRewardRulesResponse:
        """Replace the referral reward terms (a field you leave out returns to its default). At
        least one of `referrer_amount` and `referee_amount` must be above zero to turn rewards
        on. Rewards are credits on the billing credit ledger; they are created only for
        referrals Atlas has attributed and not flagged, once the trigger is met, and are granted
        after `hold_days`.
        """
        return self._t.request(
            method="PUT",
            path="/v1/referral_reward_rules",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ReferralRewards:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        status: Literal['pending', 'granted', 'voided'] | None = None,
        recipient_user_id: str | None = None,
        referrer_user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetReferralRewardsResponse:
        """The reward ledger, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/referral_rewards",
            query=_qd({'status': status, 'recipient_user_id': recipient_user_id, 'referrer_user_id': referrer_user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        status: Literal['pending', 'granted', 'voided'] | None = None,
        recipient_user_id: str | None = None,
        referrer_user_id: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetReferralRewardsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(status=status, recipient_user_id=recipient_user_id, referrer_user_id=referrer_user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def run(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostReferralRewardsRunResponse:
        """Discover qualifying referrals and grant the rewards whose hold has ended now, instead of
        waiting for the periodic sweep.
        """
        return self._t.request(
            method="POST",
            path="/v1/referral_rewards/run",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        referral_reward_id: str,
    ) -> cm.GetReferralRewardsResponseDataItem:
        """Read one referral reward by id."""
        return self._t.request(
            method="GET",
            path=f"/v1/referral_rewards/{_enc(referral_reward_id)}",
        )

    def void(
        self,
        referral_reward_id: str,
        body: cm.PostReferralRewardsByIdVoidBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetReferralRewardsResponseDataItem:
        """Void a pending reward (a fraud call). A granted reward is already a credit: post a
        negative credit to take it back (400).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/referral_rewards/{_enc(referral_reward_id)}/void",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class RefreshTokens:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        user_id: str | None = None,
        client_id: str | None = None,
        status: Literal['active', 'revoked', 'expired', 'replaced'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRefreshTokensResponse:
        """Search the refresh grants OAuth apps hold, by `user_id`, `client_id` and `status`. The
        tokens and their hashes are never returned.
        """
        return self._t.request(
            method="GET",
            path="/v1/refresh_tokens",
            query=_qd({'user_id': user_id, 'client_id': client_id, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        user_id: str | None = None,
        client_id: str | None = None,
        status: Literal['active', 'revoked', 'expired', 'replaced'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetRefreshTokensResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(user_id=user_id, client_id=client_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def revoke(
        self,
        body: cm.PostRefreshTokensRevokeBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Revoke refresh grants in bulk: by `ids`, or every active grant of a `user_id` and / or
        `client_id`. A request with no filter is refused. Each revoked grant ends the sessions
        minted from it and sends `grant.revoked`.
        """
        return self._t.request(
            method="POST",
            path="/v1/refresh_tokens/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Region:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetRegionResponse:
        """Where the instance lives: its region pin, its failover region, Frontend API origin
        isolation and the region table of this deployment. On a single-region deployment
        `regions_enabled` is false and nothing is pinned.
        """
        return self._t.request(
            method="GET",
            path="/v1/region",
        )

    def set(
        self,
        body: cm.PutRegionBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRegionResponse:
        """Pin the instance to this stack's region (`pin: true`; there is no unpin, because the
        data lives there), name its failover region, or set Frontend API origin isolation
        (`off`, `enforce`, or null for the deployment default). Send only the fields to change.
        Audited.
        """
        return self._t.request(
            method="PUT",
            path="/v1/region",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_failover(
        self,
        *,
        mount_host: str,
        base_path: str | None = None,
    ) -> cm.GetRegionFailoverResponse:
        """The upstreams a path-mounted Frontend API's reverse proxy lists to fail over to the
        instance's failover region, with ready nginx and Caddy rules. 422 when the instance has
        no failover region or the region table has no origin for it.
        """
        return self._t.request(
            method="GET",
            path="/v1/region/failover",
            query=_qd({'mount_host': mount_host, 'base_path': base_path}),
        )


class ResourceRoleAssignments:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_changes(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetResourceRoleAssignmentsChangesResponse:
        """The change feed of role assignments, oldest first: every assignment created (re-
        assigning a role to update `inherit` counts) and every one deleted, including those that
        ended because their resource or resource type was deleted. Keep the `next_cursor` of
        each page and send it back as `after`; a caught-up poll returns an empty page and the
        same cursor. Without `after` it replays every live assignment as `created`, then what
        changed since. Feeds a local mirror (`createResourceRoleMirror`) that answers permission
        checks with no network call; the `resource_role_assignment.created` / `.deleted`
        webhooks carry the same changes between polls.
        """
        return self._t.request(
            method="GET",
            path="/v1/resource_role_assignments/changes",
            query=_qd({'after': after, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_changes(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.ResourceRoleAssignmentChange]:
        """Every item of :meth:`list_changes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_changes(after=after, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class ResourceServers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_revoked_tokens(
        self,
        resource_server_id: str,
        *,
        since: int | None = None,
        limit: int | None = None,
        after: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetResourceServersByIdRevokedTokensResponse:
        """The OAuth tokens revoked for this API, oldest first, for a resource server that polls
        this list instead of asking Atlas per request (`createAccessTokenVerifier({ revocation:
        true })`). Each item is a refresh-token family that ended (`family_id`, the `fid` claim
        of every access token minted from it: a refresh token was reused, the client called
        /oauth2/revoke, or an admin, the user or a logout ended the grant) or one access token
        revoked on its own (`jti`). Reject a token whose `fid` or `jti` is listed. Rows are kept
        for 48 hours (`retention_seconds`), longer than any access token can live. Page with
        `after` (the `next_cursor` of the previous page); `server_time` is when the answer was
        computed: poll again with `since` a little before it. The `oauth_tokens.revoked` webhook
        carries the same facts for a push.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/resource_servers/{_enc(resource_server_id)}/revoked_tokens",
            query=_qd({'since': since, 'limit': limit, 'after': after, 'starting_after': starting_after}),
        )

    def iter_list_revoked_tokens(
        self,
        resource_server_id: str,
        *,
        since: int | None = None,
        limit: int | None = None,
        after: str | None = None,
    ) -> Iterator[cm.GetResourceServersByIdRevokedTokensResponseDataItem]:
        """Every item of :meth:`list_revoked_tokens`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_revoked_tokens(resource_server_id, since=since, limit=limit, after=after, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class RiskBasedMfa:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def replay(
        self,
        body: cm.PostRiskBasedMfaReplayBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostRiskBasedMfaReplayResponse:
        """What-if replay: re-score the recorded sign-ins of the last `days` days (1 to 30) under
        the current risk policy and under the policy with `candidate` applied (any of
        step_up_threshold, on_high_risk_no_factor, weights, signals, level_actions, baseline, as
        in PATCH /v1/risk_based_mfa), and report how levels and actions move, how many sign-ins
        would see more or less friction, and up to 25 changed sign-ins. Reported risk signals
        are replayed over the time each was live; reputation feeds are not. Changes nothing.
        """
        return self._t.request(
            method="POST",
            path="/v1/risk_based_mfa/replay",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class RiskSignals:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        user_id: str | None = None,
        ip: str | None = None,
        status: Literal['active', 'all'] | None = None,
        limit: int | None = None,
        before: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRiskSignalsResponse:
        """List reported risk signals, newest first. Filter by user_id or ip, and with
        `status=active` keep only live ones. Page with `before` (the previous page's
        `next_cursor`).
        """
        return self._t.request(
            method="GET",
            path="/v1/risk_signals",
            query=_qd({'user_id': user_id, 'ip': ip, 'status': status, 'limit': limit, 'before': before, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        user_id: str | None = None,
        ip: str | None = None,
        status: Literal['active', 'all'] | None = None,
        limit: int | None = None,
        before: str | None = None,
    ) -> Iterator[cm.GetRiskSignalsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(user_id=user_id, ip=ip, status=status, limit=limit, before=before, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostRiskSignalsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskSignalsResponseDataItem:
        """Report a risk signal from your own fraud or abuse systems. Name the subject with exactly
        one of user_id, email (a verified address of a user) or ip. While the signal is live and
        risk-based MFA is on, it adds points to every sign-in evaluation of that user or from
        that IP (low 10, medium 25, high 50, critical 100; the total is capped at 100), so it
        can raise the friction Atlas applies and never lowers it. ttl_seconds 60 to 2592000,
        default 3600. Honours Idempotency-Key. Emits risk_signal.created.
        """
        return self._t.request(
            method="POST",
            path="/v1/risk_signals",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        risk_signal_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskSignalsResponseDataItem:
        """End a risk signal now. Its points leave the next evaluation; the row stays readable with
        status `revoked`.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/risk_signals/{_enc(risk_signal_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        risk_signal_id: str,
    ) -> cm.GetRiskSignalsResponseDataItem:
        """Read one risk signal."""
        return self._t.request(
            method="GET",
            path=f"/v1/risk_signals/{_enc(risk_signal_id)}",
        )


class RiskyUsers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        state: Literal['at_risk', 'confirmed_compromised', 'dismissed', 'remediated'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRiskyUsersResponse:
        """The risky-user report: users with a standing risk score, filterable by state."""
        return self._t.request(
            method="GET",
            path="/v1/risky_users",
            query=_qd({'state': state, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        state: Literal['at_risk', 'confirmed_compromised', 'dismissed', 'remediated'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetRiskyUsersResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(state=state, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get(
        self,
        user_id: str,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """One user's risk state, level, score and reasons."""
        return self._t.request(
            method="GET",
            path=f"/v1/risky_users/{_enc(user_id)}",
        )

    def confirm(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """Confirm the account as compromised. The user reads as high risk to access policies until
        remediated.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/confirm",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def dismiss(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """Dismiss the risk (false alarm). The score resets."""
        return self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/dismiss",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def force_password_change(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostRiskyUsersByUserIdForcePasswordChangeResponse:
        """Require a new password at the next sign-in and end every session."""
        return self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/force_password_change",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def force_reauth(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostRiskyUsersByUserIdForcePasswordChangeResponse:
        """End every session so the user signs in, and passes MFA, again."""
        return self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/force_reauth",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def remediate(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """Mark the risk remediated. The score resets."""
        return self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/remediate",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class SamlIdp:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_service_providers(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSamlIdpServiceProvidersResponse:
        """List the SAML service providers Atlas issues assertions to, with their NameID format,
        encryption, request-signing, algorithm and logout settings.
        """
        return self._t.request(
            method="GET",
            path="/v1/saml_idp/service_providers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_service_providers(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetSamlIdpServiceProvidersResponseDataItem]:
        """Every item of :meth:`list_service_providers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_service_providers(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def import_metadata_service_provider(
        self,
        body: cm.PostSamlIdpServiceProvidersImportMetadataBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSamlIdpServiceProvidersImportMetadataResponse:
        """Read a service provider's SAML metadata (pasted XML or an https URL) into entity id, ACS
        URLs, NameID format, request-signing and encryption certificates and logout endpoint.
        With save_as the service provider is saved (201); without it nothing is stored.
        """
        return self._t.request(
            method="POST",
            path="/v1/saml_idp/service_providers/import_metadata",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_service_provider(
        self,
        service_provider_id: str,
    ) -> cm.GetSamlIdpServiceProvidersResponseDataItem:
        """Read one SAML service provider's settings."""
        return self._t.request(
            method="GET",
            path=f"/v1/saml_idp/service_providers/{_enc(service_provider_id)}",
        )

    def update_service_provider(
        self,
        service_provider_id: str,
        body: cm.PatchSamlIdpServiceProvidersByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetSamlIdpServiceProvidersResponseDataItem:
        """Change a SAML service provider's NameID format (emailAddress, persistent, transient,
        unspecified), assertion encryption, request-signing certificates, signature and digest
        algorithms, Response signing, assertion lifetime, authentication context and single-
        logout endpoint.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/saml_idp/service_providers/{_enc(service_provider_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ScimProvisioningTargets:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_failures(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetScimProvisioningTargetsByIdFailuresResponse:
        """The failed-provision inbox: users and organizations whose last push to this target
        failed, with the error and the number of consecutive attempts.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/scim_provisioning_targets/{_enc(scim_provisioning_target_id)}/failures",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_failures(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetScimProvisioningTargetsByIdFailuresResponseDataItem]:
        """Every item of :meth:`list_failures`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_failures(scim_provisioning_target_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def list_logs(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: str | None = None,
        starting_after: str | None = None,
        failures: str | None = None,
        resource_id: str | None = None,
    ) -> cm.GetScimProvisioningTargetsByIdLogsResponse:
        """The target's provisioning log, newest first (30 days): one entry per push with the
        operation, the downstream status and the error. Filter with failures=true or
        resource_id.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/scim_provisioning_targets/{_enc(scim_provisioning_target_id)}/logs",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'failures': failures, 'resource_id': resource_id}),
        )

    def iter_list_logs(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: str | None = None,
        failures: str | None = None,
        resource_id: str | None = None,
    ) -> Iterator[cm.GetScimProvisioningTargetsByIdLogsResponseDataItem]:
        """Every item of :meth:`list_logs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_logs(scim_provisioning_target_id, limit=limit, failures=failures, resource_id=resource_id, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def retry_failed(
        self,
        scim_provisioning_target_id: str,
        body: cm.PostScimProvisioningTargetsByIdRetryFailedBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Retry failed users and groups now (up to 50), or one with resource_type and resource_id.
        Each goes through the same sync as sync_user and sync_group; the result says how each
        went.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{_enc(scim_provisioning_target_id)}/retry_failed",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class ScimResourceTypes:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetScimResourceTypesResponse:
        """List the custom SCIM resource types this instance serves beyond Users and Groups."""
        return self._t.request(
            method="GET",
            path="/v1/scim_resource_types",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetScimResourceTypesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostScimResourceTypesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Define a custom SCIM resource type: a name, an endpoint served at /scim/v2/<endpoint>, a
        schema URN and attribute definitions (type, multiValued, required, mutability).
        Directory tokens then create, read, filter, patch and delete resources of it, per
        organization.
        """
        return self._t.request(
            method="POST",
            path="/v1/scim_resource_types",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        scim_resource_type_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a custom SCIM resource type and every resource of it."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/scim_resource_types/{_enc(scim_resource_type_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        scim_resource_type_id: str,
    ) -> cm.GetScimResourceTypesResponseDataItem:
        """Read one custom SCIM resource type."""
        return self._t.request(
            method="GET",
            path=f"/v1/scim_resource_types/{_enc(scim_resource_type_id)}",
        )


class ScimTokens:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def rotate(
        self,
        scim_token_id: str,
        body: cm.PostScimTokensByIdRotateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetScimTokensResponseDataItem:
        """Rotate a live SCIM token: mint its replacement (same organization, connection, scopes,
        role mappings, IP allow-list and profile lock) and retire the old one after
        grace_period_seconds (default one day; 0 revokes it now), so the identity provider can
        be switched over without a gap in provisioning. The new secret is revealed once. Only a
        live token can be rotated (409 otherwise). An operator token needs a recent MFA. Accepts
        Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/scim_tokens/{_enc(scim_token_id)}/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class SecurityAdvisories:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
        security_advisory_id: str,
    ) -> cm.GetSecurityAdvisoriesResponseDataItem:
        """One security advisory for this instance, with `subjects`: the affected users and email
        addresses it names while it applies (up to 100; `subjects_truncated` is true past that
        and `count` stays the full number). 404 for an unknown id.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/security_advisories/{_enc(security_advisory_id)}",
        )


class Sessions:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get_export(
        self,
        *,
        user_id: str | None = None,
        organization_id: str | None = None,
        ip: str | None = None,
        country: str | None = None,
        device: str | None = None,
        risk_level: Literal['low', 'medium', 'high'] | None = None,
        min_risk_score: int | None = None,
        created_after: int | None = None,
        created_before: int | None = None,
        active: bool | None = None,
        format: Literal['csv', 'ndjson'] | None = None,
        limit: int | None = None,
    ) -> str:
        """Export the sessions matching a filter as CSV (default) or NDJSON, newest first. Same
        filters as GET /v1/sessions. `limit` defaults to 10000 (at most 50000); `x-atlas-
        truncated: true` when more matched. Custom data and tokens are never included. Audited
        as session.exported.
        """
        return self._t.request(
            method="GET",
            path="/v1/sessions/export",
            query=_qd({'user_id': user_id, 'organization_id': organization_id, 'ip': ip, 'country': country, 'device': device, 'risk_level': risk_level, 'min_risk_score': min_risk_score, 'created_after': created_after, 'created_before': created_before, 'active': active, 'format': format, 'limit': limit}),
        )

    def list_revocations(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSessionsRevocationsResponse:
        """The session revocation feed: sessions revoked after a point, oldest first, as `{ sid,
        sub, revoked_at, reason }` (`sub` is the user). `after` is epoch milliseconds to start
        from (default one hour ago, at most 24 hours back) or the `next_after` of the previous
        page. Poll it, or fetch the signed list at /v1/sessions/revocations/status-list.
        """
        return self._t.request(
            method="GET",
            path="/v1/sessions/revocations",
            query=_qd({'after': after, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_revocations(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetSessionsRevocationsResponseDataItem]:
        """Every item of :meth:`list_revocations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_revocations(after=after, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_revocations_status_list(
        self,
        *,
        window_seconds: int | None = None,
    ) -> cm.GetSessionsRevocationsStatusListResponse:
        """A compact signed list of recently revoked sessions for a verifier that cannot call Atlas
        per request (an edge function, a Lambda authorizer). `token` is a JWT (`typ:
        statuslist+jwt`) signed with the instance signing key: verify it against the instance
        JWKS, then reject any session token whose `sid` hashes (first 8 bytes of SHA-256) into
        the list carried in `h`. It covers the last `window_seconds` (default 3600): ask for at
        least the longest session token lifetime you accept. `truncated: true` means more
        sessions were revoked than fit; use the feed instead. The token itself lives two
        minutes.
        """
        return self._t.request(
            method="GET",
            path="/v1/sessions/revocations/status-list",
            query=_qd({'window_seconds': window_seconds}),
        )

    def revoke_by_filter(
        self,
        body: cm.PostSessionsRevokeByFilterBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSessionsRevokeByFilterResponse:
        """Revoke every active session matching a filter, as an async job. Give at least one of
        user_id, organization_id, ip, country, device, risk_level, min_risk_score,
        created_after, created_before. With `dry_run: true` nothing changes and the answer is `{
        matched }`: look at the count first. Otherwise a job is created (202); poll GET
        /v1/sessions/revoke_jobs/{id}. Each session ends the way a single revoke ends it
        (webhook, back-channel logout, revocation cache). Honours Idempotency-Key. Audited.
        """
        return self._t.request(
            method="POST",
            path="/v1/sessions/revoke_by_filter",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_revoke_jobs(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSessionsRevokeJobsResponse:
        """Recent revoke-by-filter jobs, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/sessions/revoke_jobs",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_revoke_jobs(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetSessionsRevokeJobsResponseDataItem]:
        """Every item of :meth:`list_revoke_jobs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_revoke_jobs(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_revoke_job(
        self,
        revoke_job_id: str,
    ) -> cm.GetSessionsRevokeJobsResponseDataItem:
        """One revoke-by-filter job and its progress (`matched`, `revoked`, `failed`, `status`).
        404 for a job of another instance.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/sessions/revoke_jobs/{_enc(revoke_job_id)}",
        )

    def list_revoked(
        self,
        *,
        since: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSessionsRevokedResponse:
        """Sessions revoked since a time (revoked by the user, an operator, a ban, a password
        reset...), oldest first, for a verifier that polls this list instead of asking Atlas per
        request. Looks back at most 24 hours; page with `cursor` (the `next_cursor` of the
        previous page). `server_time` is when the answer was computed: poll again with `since` a
        little before it. Each item is `{ sid, user_id, revoked_at, reason }`; `sid` is the
        `sid` claim of the session token.
        """
        return self._t.request(
            method="GET",
            path="/v1/sessions/revoked",
            query=_qd({'since': since, 'limit': limit, 'cursor': cursor, 'starting_after': starting_after}),
        )

    def iter_list_revoked(
        self,
        *,
        since: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> Iterator[cm.GetSessionsRevokedResponseDataItem]:
        """Every item of :meth:`list_revoked`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_revoked(since=since, limit=limit, cursor=cursor, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_binding(
        self,
        session_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteSessionsByIdBindingResponse:
        """Remove a session's DPoP binding so it can bind a new key (a user who lost their device
        key). Audited.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/sessions/{_enc(session_id)}/binding",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_binding(
        self,
        session_id: str,
    ) -> cm.GetSessionsByIdBindingResponse:
        """Which DPoP key (by thumbprint) a session is bound to, and whether it was attested."""
        return self._t.request(
            method="GET",
            path=f"/v1/sessions/{_enc(session_id)}/binding",
        )

    def list_events(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSessionsByIdEventsResponse:
        """One session's timeline, oldest first: `created`, `step_up`, `organization_changed`,
        `risk_elevated`, `revoked` (with the reason). Sessions that predate the timeline get
        `created` and `revoked` from their own row, marked `synthesized`. 404 for a session of
        another instance.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/sessions/{_enc(session_id)}/events",
            query=_qd({'limit': limit, 'after': after, 'starting_after': starting_after}),
        )

    def iter_list_events(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
    ) -> Iterator[cm.GetSessionsByIdEventsResponseDataItem]:
        """Every item of :meth:`list_events`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_events(session_id, limit=limit, after=after, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_risk(
        self,
        session_id: str,
    ) -> cm.GetSessionsByIdRiskResponse:
        """The session's advisory risk: `{ score (0-100), level (low|medium|high), reasons[],
        computed_at }`. Reasons come from signals Atlas already holds: `new_device`,
        `new_country`, `impossible_travel` (against the user's previous session), `bot_likely`
        and `breached_password` (at sign-in). The same object is on the session (`risk`) and,
        when `session.includeRiskClaim` is on, in the session token as the `risk` claim;
        `risk.elevated` is sent when a session turns high. Advisory only: Atlas never allows or
        denies anything because of it. Fields are null and `reasons` empty when the session was
        never assessed, which means unknown, not safe.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/sessions/{_enc(session_id)}/risk",
        )


class Ssf:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def create_event(
        self,
        body: cm.PostSsfEventsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Raise a Shared Signals event for one of your users: the CAEP and RISC events Atlas has
        no flow for (opt-in, opt-out-initiated, opt-out-cancelled, opt-out-effective,
        identifier-recycled, recovery-activated ...). It reaches every stream that asked for the
        event and whose subject rules allow the user. 202.
        """
        return self._t.request(
            method="POST",
            path="/v1/ssf/events",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_status(
        self,
        *,
        stream_id: str | None = None,
    ) -> cm.GetSsfStatusResponse:
        """SSF 1.0 stream status endpoint: the status (enabled, paused, disabled) of the stream
        named by the `stream_id` query parameter.
        """
        return self._t.request(
            method="GET",
            path="/v1/ssf/status",
            query=_qd({'stream_id': stream_id}),
        )

    def status(
        self,
        body: cm.PostSsfStatusBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 stream status endpoint: set the status of the stream named by `stream_id`."""
        return self._t.request(
            method="POST",
            path="/v1/ssf/status",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_streams_subjects(
        self,
        stream_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSsfStreamsByIdSubjectsResponse:
        """The subjects a receiver added to or removed from a stream, with the stream's
        `default_subjects` (ALL or NONE).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/ssf/streams/{_enc(stream_id)}/subjects",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_streams_subjects(
        self,
        stream_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetSsfStreamsByIdSubjectsResponseDataItem]:
        """Every item of :meth:`list_streams_subjects`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_streams_subjects(stream_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def add_subject(
        self,
        body: cm.PostSsfSubjectsAddBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 add subject: start (or, on an ALL stream, resume) events for one subject on a
        stream. Subject formats: iss_sub (this issuer), email, phone_number, opaque, account,
        did, uri. 200 with an empty body.
        """
        return self._t.request(
            method="POST",
            path="/v1/ssf/subjects/add",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def remove_subject(
        self,
        body: cm.PostSsfSubjectsRemoveBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 remove subject: stop events for one subject on a stream (on an ALL stream), or
        drop an earlier add (on a NONE stream). 204.
        """
        return self._t.request(
            method="POST",
            path="/v1/ssf/subjects/remove",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def verify(
        self,
        body: cm.PostSsfVerifyBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 verification endpoint: queue a verification event carrying `state` for the
        stream named by `stream_id`. 204.
        """
        return self._t.request(
            method="POST",
            path="/v1/ssf/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class SsoConnections:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_login_history(
        self,
        sso_connection_id: str,
        *,
        limit: str | None = None,
        starting_after: str | None = None,
        outcome: Literal['success', 'failure', 'test'] | None = None,
    ) -> cm.GetSsoConnectionsByIdLoginHistoryResponse:
        """Sign-ins through one enterprise connection, newest first, kept 90 days: successful,
        failed (with a short failure code) and test sign-ins, with the source IP. The summary
        carries the last successful and failed sign-in and the 24-hour counts. Filter with
        outcome; page with limit and starting_after.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/sso_connections/{_enc(sso_connection_id)}/login_history",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'outcome': outcome}),
        )

    def iter_list_login_history(
        self,
        sso_connection_id: str,
        *,
        limit: str | None = None,
        outcome: Literal['success', 'failure', 'test'] | None = None,
    ) -> Iterator[cm.GetSsoConnectionsByIdLoginHistoryResponseDataItem]:
        """Every item of :meth:`list_login_history`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_login_history(sso_connection_id, limit=limit, outcome=outcome, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def test(
        self,
        sso_connection_id: str,
        body: cm.PostSsoConnectionsByIdTestBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSsoConnectionsByIdTestResponse:
        """Check an enterprise connection without signing anyone in. SAML: the IdP entity ID, an
        https SSO URL and a signing certificate are set (and the encryption key, when assertions
        must be encrypted). OIDC: the issuer is reachable and matches its discovery document;
        oidc_issuer tries another issuer without saving it. A failed check answers 200 with ok
        false and the reason. The answer lists what it did not check (client credentials,
        assertion signature): only POST /v1/sso_connections/{id}/test_login proves those.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{_enc(sso_connection_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def test_login(
        self,
        sso_connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSsoConnectionsByIdTestLoginResponse:
        """Begin an interactive OIDC test sign-in: returns an authorization_url to open in a
        browser. The callback shows the claims the identity provider returned and issues no
        session and provisions no user. The test is filed in the connection's login history as
        `test`. SAML connections use POST /v1/sso_connections/{id}/test instead (400).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{_enc(sso_connection_id)}/test_login",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class StepUp:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def assert_(
        self,
        body: cm.PostStepUpAssertBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostStepUpAssertResponse:
        """Ask whether a session meets a named step-up policy right now. Send the session token the
        caller presented and the policy name. The answer reads the session itself (a step-up a
        second ago counts), after checking the token signature, issuer and revocation. Always
        200 with `allowed`: a denial is an answer, with a `reason` and the `step_up` meta to put
        in your 403 STEP_UP_REQUIRED. On allow, `receipt` is a short-lived signed JWT (`typ:
        step-up-receipt+jwt`, claims policy, sid, sub, auth_time, amr, acr, jti) a downstream
        backend can verify offline. 404 for an unknown policy and 409 for a disabled one: never
        an implicit allow. Not cacheable.
        """
        return self._t.request(
            method="POST",
            path="/v1/step_up/assert",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_policies(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetStepUpPoliciesResponse:
        """List the named step-up policies of the instance."""
        return self._t.request(
            method="GET",
            path="/v1/step_up/policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_policies(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetStepUpPoliciesResponseDataItem]:
        """Every item of :meth:`list_policies`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_policies(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_policy(
        self,
        body: cm.PostStepUpPoliciesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetStepUpPoliciesResponseDataItem:
        """Create a named step-up policy: how recent and how strong a re-authentication a sensitive
        action needs. Names are unique (400 when taken). A policy no method could satisfy
        (phishing_resistant with allowed_methods that exclude passkey) is refused. Honours
        Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/step_up/policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_policy(
        self,
        policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteStepUpPoliciesByIdResponse:
        """Delete a step-up policy. An assertion that names it afterwards answers 404, so a service
        that still asks fails closed.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/step_up/policies/{_enc(policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_policy(
        self,
        policy_id: str,
    ) -> cm.GetStepUpPoliciesResponseDataItem:
        """Read one step-up policy."""
        return self._t.request(
            method="GET",
            path=f"/v1/step_up/policies/{_enc(policy_id)}",
        )

    def update_policy(
        self,
        policy_id: str,
        body: cm.PatchStepUpPoliciesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetStepUpPoliciesResponseDataItem:
        """Change a step-up policy. Send only the fields to change. The change applies to the next
        assertion.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/step_up/policies/{_enc(policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class Suppressions:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        reason: str | None = None,
        address: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSuppressionsResponse:
        """The suppression list: addresses, numbers and device tokens Atlas will not send to. An
        entry is added automatically when your provider reports a hard bounce, a spam complaint,
        an unsubscribe or an invalid number (turn that off with auto_suppress), or by hand. A
        send to a suppressed recipient is refused before it reaches your provider (email: 422
        EMAIL_ADDRESS_UNREACHABLE) and shows as `suppressed` in the ledger.
        """
        return self._t.request(
            method="GET",
            path="/v1/suppressions",
            query=_qd({'channel': channel, 'reason': reason, 'address': address, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        reason: str | None = None,
        address: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetSuppressionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(channel=channel, reason=reason, address=address, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostSuppressionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSuppressionsResponse:
        """Add one address or up to 1000 to the suppression list. Adding one that is already there
        updates its reason. Audited; emits message_suppression.created for new entries.
        """
        return self._t.request(
            method="POST",
            path="/v1/suppressions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        suppression_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteSuppressionsByIdResponse:
        """Take an address off the suppression list; messages to it are sent again. Audited."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/suppressions/{_enc(suppression_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        suppression_id: str,
    ) -> cm.GetSuppressionsResponseDataItem:
        """Read one suppressed address and why it is suppressed."""
        return self._t.request(
            method="GET",
            path=f"/v1/suppressions/{_enc(suppression_id)}",
        )


class TelemetryExport:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetTelemetryExportResponse:
        """The instance's OTLP export settings for MCP gateway and connection relay calls."""
        return self._t.request(
            method="GET",
            path="/v1/telemetry_export",
        )

    def set(
        self,
        body: cm.PutTelemetryExportBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetTelemetryExportResponse:
        """Configure OTLP/HTTP export of gateway tool calls and relay calls as spans and metrics
        (atlas.calls, atlas.call.duration) to your collector. The endpoint must be https and
        public; headers (for example an API token) are sealed and never returned. Delivery is
        batched and best effort.
        """
        return self._t.request(
            method="PUT",
            path="/v1/telemetry_export",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def test(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostTelemetryExportTestResponse:
        """Send one test span to the configured collector now. Answers ok or the collector's error;
        never fails the request.
        """
        return self._t.request(
            method="POST",
            path="/v1/telemetry_export/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Usage:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_connections(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        group_by: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsageConnectionsResponse:
        """Usage records for connections: relay calls, action runs, agent token and action use, and
        MCP gateway calls, counted from the audit trail over a range of up to 92 days. Never
        reads what was sent or received.
        """
        return self._t.request(
            method="GET",
            path="/v1/usage/connections",
            query=_qd({'from': from_, 'to': to, 'group_by': group_by, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_connections(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        group_by: str | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsageConnectionsResponseDataItem]:
        """Every item of :meth:`list_connections`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_connections(from_=from_, to=to, group_by=group_by, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class Users:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_bulk_actions(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        status: Literal['pending', 'processing', 'completed', 'failed', 'cancelled'] | None = None,
    ) -> cm.GetUsersBulkActionsResponse:
        """The bulk user actions of the instance, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/users/bulk_actions",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'status': status}),
        )

    def iter_list_bulk_actions(
        self,
        *,
        limit: int | None = None,
        status: Literal['pending', 'processing', 'completed', 'failed', 'cancelled'] | None = None,
    ) -> Iterator[cm.GetUsersBulkActionsResponseDataItem]:
        """Every item of :meth:`list_bulk_actions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_bulk_actions(limit=limit, status=status, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_bulk_action(
        self,
        body: cm.PostUsersBulkActionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersBulkActionsResponseDataItem:
        """Run one action over many users: ban, unban, revoke_sessions, add_to_org, set_metadata,
        delete or require_action. Pick users with user_ids, or with a search (filter, query,
        segment_id). With dry_run: true nothing changes and the answer is the matched count, how
        many the action would skip and why, and a sample of ids. Without it a job starts (202)
        that the worker runs in chunks: poll GET /v1/users/bulk_actions/{id} for progress,
        cancel with POST …/cancel. Each user gets the same effects, events and audit rows as the
        single-user call; one failing user does not stop the rest. delete needs expected_count
        (from a dry run) and the users:delete scope, add_to_org the organizations:write scope; a
        user on legal hold, or one who must hand over organizations first, is skipped. Honours
        Idempotency-Key. Emits bulk_user_action.completed or .failed.
        """
        return self._t.request(
            method="POST",
            path="/v1/users/bulk_actions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_bulk_action(
        self,
        bulk_action_id: str,
    ) -> cm.GetUsersBulkActionsResponseDataItem:
        """One bulk user action: status, progress, counts and the first errors."""
        return self._t.request(
            method="GET",
            path=f"/v1/users/bulk_actions/{_enc(bulk_action_id)}",
        )

    def cancel_bulk_action(
        self,
        bulk_action_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersBulkActionsResponseDataItem:
        """Stop a bulk action. One that has not started is cancelled at once; a running one stops
        after the chunk in hand (users already handled stay handled). 409 when it already
        finished.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/bulk_actions/{_enc(bulk_action_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def create_deleted_address(
        self,
        body: cm.PostUsersDeletedAddressesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersDeletedAddressesResponse:
        """Remember email addresses and E.164 phone numbers of accounts that were deleted before
        this instance recorded deletions, so deletedUserReturn "block" refuses them. Same keyed,
        unreadable hash a delete writes. Up to 5000 per call, safe to repeat. The answer counts
        new, already remembered and invalid entries (with the first invalid positions). Honours
        Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path="/v1/users/deleted_addresses",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def check_deleted_address(
        self,
        body: cm.PostUsersDeletedAddressesCheckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersDeletedAddressesCheckResponse:
        """Whether an address is remembered as belonging to a deleted account, whatever the
        instance's deletedUserReturn mode.
        """
        return self._t.request(
            method="POST",
            path="/v1/users/deleted_addresses/check",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_search_fields(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersSearchFieldsResponse:
        """What a user search can filter on: the built-in fields, plus every metadata path the
        instance metadata schema declares (public_metadata.plan, ...) with its type, allowed
        values and whether it is required. Use it to autocomplete a filter builder. A name with
        <...> is a pattern you fill in.
        """
        return self._t.request(
            method="GET",
            path="/v1/users/search/fields",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_search_fields(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsersSearchFieldsResponseDataItem]:
        """Every item of :meth:`list_search_fields`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_search_fields(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def count_view_search(
        self,
        view_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Count a saved search (a segment) now and keep the number and the time on it
        (member_count, counted_at).
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/search/views/{_enc(view_id)}/count",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_age_assurance(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdAgeAssuranceResponse:
        """The age assurance records of a user, newest first, with whether each is trusted by
        compliance.minors.trustedAgeMethods.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/age_assurance",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_age_assurance(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsersByIdAgeAssuranceResponseDataItem]:
        """Every item of :meth:`list_age_assurance`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_age_assurance(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def age_assurance(
        self,
        user_id: str,
        body: cm.PostUsersByIdAgeAssuranceBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersByIdAgeAssuranceResponseDataItem:
        """Record that a method established the user is at least over_age years old (self_declared,
        id_document, payment_card, estimation, credential, third_party, admin). The record holds
        the outcome and an opaque reference, never the evidence. id_document needs the user's
        approved identity verification (verification_id). third_party states its own
        assurance_level. When compliance.minors.trustedAgeMethods lists the method and over_age
        reaches the user's age of consent, the user is no longer treated as a minor. Emits
        user.age_assurance_recorded. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/age_assurance",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def revoke_age_assurance(
        self,
        user_id: str,
        assurance_id: str,
        body: cm.PostUsersByIdAgeAssuranceByAssuranceIdRevokeBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersByIdAgeAssuranceResponseDataItem:
        """Withdraw an age assurance record. The user is re-assessed from their date of birth.
        Revoking twice returns the same record.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/age_assurance/{_enc(assurance_id)}/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_approval_devices(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdApprovalDevicesResponse:
        """Every device the user can approve from (registered signing keys, passkeys and verified
        push devices), each marked trusted or not, with the `trusted_device_id` to revoke. Needs
        `approvals:read` (`users:read` keeps working).
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/approval_devices",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_approval_devices(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsersByIdApprovalDevicesResponseDataItem]:
        """Every item of :meth:`list_approval_devices`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_approval_devices(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def trust_approval_device(
        self,
        user_id: str,
        body: cm.PostUsersByIdApprovalDevicesTrustBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersByIdApprovalDevicesResponseDataItem:
        """Trust one of the user's devices for approval decisions. Send `kind` (`device_key`,
        `passkey` or `push_device`), the device `ref` and an optional `label`. A device that
        does not exist or is not this user's is a 404. Trusting a trusted device changes
        nothing; trusting one whose trust was revoked restores it with the same id. Emits
        approval_trusted_device.added. Accepts Idempotency-Key. Needs `approvals:write`. → 201.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/approval_devices/trust",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_approval_device(
        self,
        user_id: str,
        device_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteUsersByIdApprovalDevicesByDeviceIdResponse:
        """Stop trusting a device by its `trusted_device_id`. Approvals it already decided keep
        their receipts; a request that needs a trusted device refuses it from now on. A trusted-
        device id that is unknown, another user's or already revoked is a 404. Emits
        approval_trusted_device.revoked. Needs `approvals:write`.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/approval_devices/{_enc(device_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def cancel_approval_request(
        self,
        user_id: str,
        approval_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetUsersByIdApprovalRequestsByApprovalIdResponse:
        """Withdraw a pending transaction-approval request so the device can no longer answer it.
        404 for a request that is not this user's, 409 once it is approved, denied, expired or
        already cancelled. Emits approval_request.cancelled.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/approval_requests/{_enc(approval_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def contain(
        self,
        user_id: str,
        body: cm.PostUsersByIdReferralFlagBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersByIdContainResponse:
        """Contain an account in one action: sign-in disabled, password invalidated (a new one is
        required), sessions and OIDC sessions ended, personal API tokens, API keys, agent
        grants, device keys, desktop devices, remembered devices and temporary passes revoked.
        Sends `user.banned` (and the Shared Signals account-disabled event) and
        `user.contained`, and writes one audit record. Idempotent.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/contain",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_cookie_consents(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteCookieConsentsSubjectsBySubjectResponse:
        """Erase the cookie consent records linked to a user. Deleting the user does this too.
        Audited.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/cookie_consents",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def reconfirm_deletion(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.User:
        """Resume a PAUSED scheduled deletion: a `pre_user_deletion` Action held it until the
        person re-confirmed, and your backend confirms on their behalf. The deletion keeps its
        original schedule and reminder plan, no mail is sent (nothing was cancelled), and
        user.deletion_resumed is emitted; it then runs on its date. 409 when the user has no
        scheduled deletion or it is not paused.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/deletion/reconfirm",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def create_external_account(
        self,
        user_id: str,
        body: cm.PostUsersByIdExternalAccountsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.UserExternalAccount:
        """Attach a non-sign-in identity (a chat id, a marketplace username) to a user for display
        and notifications. `provider` must be namespaced like `telegram:bot`; `sign_in` must be
        false or omitted. The account is returned on the user object (`external_accounts`,
        `sign_in: false`) and in `user.updated`, and can never be used to sign in. Idempotent on
        the same user; 409 when another user holds it.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/external_accounts",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_external_account(
        self,
        user_id: str,
        account_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteUsersByIdExternalAccountsByAccountIdResponse:
        """Remove a link-only account added with POST /v1/users/{id}/external_accounts. Sign-in
        identities are removed through the identities routes.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/external_accounts/{_enc(account_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def import_identity_verification(
        self,
        user_id: str,
        body: cm.PostUsersByIdIdentityVerificationsImportBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIdentityVerificationsResponseDataItem:
        """Record a check the person already passed at the verification service (Stripe Identity,
        Persona or Veriff, whichever connector is set up). Atlas re-reads the session through
        the connector and records an approved check only if the service reports it verified (409
        otherwise); the check carries the SERVICE's verification time, so it counts as the MFA-
        recovery baseline once the configured baseline age has passed since then. The same
        session for the same user returns the existing check (200); a session already recorded
        for another user is 409. Sends `identity_verification.completed`.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/identity_verifications/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_identity_verification(
        self,
        user_id: str,
        attempt_id: str,
    ) -> cm.GetUsersByIdIdentityVerificationsByAttemptIdResponse:
        """Read one of a user's identity checks (needs only `users:read`). A pending check is
        refreshed from the verification service. When you opted into verified attributes and the
        check is approved, the FIRST read also returns them in `verified_attributes`; that read
        destroys Atlas's copy (and redacts the provider's where the provider supports it), so a
        second read, or a webhook delivery that already succeeded, has none. 404 for a check
        that belongs to another user.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/identity_verifications/{_enc(attempt_id)}",
        )

    def delete_journeys(
        self,
        user_id: str,
        *,
        journey_id: str | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteUsersByIdJourneysResponse:
        """Start a user's onboarding over: deletes their runs and the open steps those journeys
        asked of them, so the journey asks again at the next sign-in. journey_id limits it to
        one journey. Audited.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/journeys",
            query=_qd({'journey_id': journey_id, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_journeys(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFlowsByIdRunsResponse:
        """One user's journey runs, newest first, with what they saved so far (draft, by step) so
        an onboarding resumes where they stopped.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/journeys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_journeys(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetFlowsByIdRunsResponseDataItem]:
        """Every item of :meth:`list_journeys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_journeys(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def get_legal_hold(
        self,
        user_id: str,
    ) -> cm.GetUsersByIdLegalHoldResponse:
        """Whether the user is on legal hold, the active hold, and every hold they ever had."""
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/legal_hold",
        )

    def legal_hold(
        self,
        user_id: str,
        body: cm.PostUsersByIdLegalHoldBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetLegalHoldsResponseDataItem:
        """Place a legal hold on a user. While it is active no path erases them: the delete call, a
        scheduled deletion (it stays scheduled and does not run), a data subject request, a
        workflow and a bulk delete all refuse or wait, and a merge that would delete this user
        is refused (409 LEGAL_HOLD). Placing a hold on a user already held returns the existing
        hold (200). Audited; emits user.legal_hold_placed. Honours Idempotency-Key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/legal_hold",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def release_legal_hold(
        self,
        user_id: str,
        body: cm.PostUsersByIdLegalHoldReleaseBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetLegalHoldsResponseDataItem:
        """Release the active legal hold. A deletion that was waiting on it runs on the next pass.
        404 when there is no active hold. Audited; emits user.legal_hold_released.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/legal_hold/release",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def merge(
        self,
        user_id: str,
        body: cm.PostUsersByIdMergeBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Merge another user INTO this one (the one kept). Emails, phones, social accounts, MFA
        factors, passkeys, API tokens, devices, organization and group memberships, app roles,
        consents, billing subscriptions and credits move across (a membership the target already
        has is left as it is, and the target's role wins); metadata merges key by key with the
        target winning; blank profile fields are filled. The source user's sessions end and it
        is deleted, firing `user.deleted` and `user.merged`. Refused when the users are the
        same, the source is banned and the target is not, or the target is a guest. `dry_run`
        reports what would move. Needs users:write and users:delete.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/merge",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_owned_organizations(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdOwnedOrganizationsResponse:
        """The organizations this user is the only admin of that still have other members: what
        deleting them would orphan. Hand each one over (promote another member to admin) before
        deleting. Empty when none.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/owned_organizations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_owned_organizations(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsersByIdOwnedOrganizationsResponseDataItem]:
        """Every item of :meth:`list_owned_organizations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_owned_organizations(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def resync_referral(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersByIdReferralResyncResponse:
        """Re-report one user to the referral platform: their sign-up call is sent again now (same
        customerRef, original signed-up time, the stored arrival context, the user's current
        email and name) and the answer (code, link, partner) is applied to the user. For a user
        whose earlier answer is final on the platform (e.g. enroll_email_taken) but has since
        been fixed there. A code the user already has is kept. 404 for an unknown user; 422
        REFERRALS_NOT_CONFIGURED when referral attribution is off. With `?dry_run=true` nothing
        is sent.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/referral/resync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def release(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetContainmentsResponseDataItem:
        """Release a contained account. The user can sign in again and still owes the password
        change.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def list_temporary_access(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdTemporaryAccessResponse:
        """The user's active temporary access passes (never the codes)."""
        return self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/temporary_access",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_temporary_access(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetUsersByIdTemporaryAccessResponseDataItem]:
        """Every item of :meth:`list_temporary_access`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_temporary_access(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def temporary_access(
        self,
        user_id: str,
        body: cm.PostUsersByIdTemporaryAccessBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersByIdTemporaryAccessResponse:
        """Issue a temporary access pass: a time-limited code (60 seconds to 7 days, one use by
        default) that signs the user in with `strategy: "temporary_access_pass"`, counts as MFA
        for that sign-in, and (unless `require_enrolment` is false) makes them register a
        passkey or second factor. Optionally bound to an IP. The code is shown once.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/temporary_access",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_temporary_access(
        self,
        user_id: str,
        pass_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteUsersByIdTemporaryAccessByPassIdResponse:
        """Revoke a temporary access pass."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/temporary_access/{_enc(pass_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class Vc:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_deferred(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'issued'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetVcDeferredResponse:
        """List deferred issuances waiting for an operator decision."""
        return self._t.request(
            method="GET",
            path="/v1/vc/deferred",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_deferred(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'issued'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetVcDeferredResponseDataItem]:
        """Every item of :meth:`list_deferred`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_deferred(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def approve_deferred(
        self,
        deferred_id: str,
        body: cm.PostVcDeferredByIdApproveBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Approve a deferred issuance; the wallet receives the credential at the deferred
        credential endpoint.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/vc/deferred/{_enc(deferred_id)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def deny_deferred(
        self,
        deferred_id: str,
        body: cm.PostVcDeferredByIdDenyBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Deny a deferred issuance; the wallet is told issuance was refused."""
        return self._t.request(
            method="POST",
            path=f"/v1/vc/deferred/{_enc(deferred_id)}/deny",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_presentation_requests_dc_api_request(
        self,
        presentation_request_id: str,
    ) -> cm.GetVcPresentationRequestsByIdDcApiRequestResponse:
        """The OpenID4VP request for the Digital Credentials API (navigator.credentials.get), for a
        presentation request with expected_origins.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/vc/presentation_requests/{_enc(presentation_request_id)}/dc_api_request",
        )


class WebBotAuth:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def get(
        self,
    ) -> cm.GetWebBotAuthResponse:
        """The instance allow and block lists of signed-bot directories."""
        return self._t.request(
            method="GET",
            path="/v1/web_bot_auth",
        )

    def set(
        self,
        body: cm.PutWebBotAuthBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWebBotAuthResponse:
        """Set the allow and/or block list (each replaces its list; omit one to keep it). Entries
        are an https directory URL or host, or { directory, name }. At most 100 per list; a
        directory cannot be on both.
        """
        return self._t.request(
            method="PUT",
            path="/v1/web_bot_auth",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_directories(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAgentAccessRequestsResponse:
        """The listed directories, one row each with its list (allow or block)."""
        return self._t.request(
            method="GET",
            path="/v1/web_bot_auth/directories",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_directories(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Every item of :meth:`list_directories`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_directories(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_directory(
        self,
        body: cm.PostWebBotAuthDirectoriesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Put one directory on the allow or block list; it leaves the other list if it was there."""
        return self._t.request(
            method="POST",
            path="/v1/web_bot_auth/directories",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_directory(
        self,
        directory_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteWebBotAuthDirectoriesByIdResponse:
        """Take a directory off both lists."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/web_bot_auth/directories/{_enc(directory_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class WebhookEndpoints:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_dlq(
        self,
        webhook_endpoint_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWebhookEndpointsByIdDlqResponse:
        """The dead-letter queue of an endpoint: deliveries that used every attempt, newest first,
        each with the payload that was sent, the last response and the error. `depth` counts
        what nobody has acknowledged yet. Pull a page, handle it (or fix the receiver and
        requeue), then acknowledge, so a consumer that cannot take pushes can work failures off
        as a queue. Cursor: `starting_after` with the `next_cursor` of the previous page.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{_enc(webhook_endpoint_id)}/dlq",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_dlq(
        self,
        webhook_endpoint_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.WebhookDelivery]:
        """Every item of :meth:`list_dlq`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_dlq(webhook_endpoint_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def ack_dlq(
        self,
        webhook_endpoint_id: str,
        body: cm.PostWebhookEndpointsByIdDlqAckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostWebhookEndpointsByIdDlqAckResponse:
        """Acknowledge dead-lettered deliveries you handled: they stop appearing in the queue.
        Acknowledging a delivery that is not dead-lettered (or already acknowledged) is ignored,
        so a retry is harmless. Up to 100 ids a call.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(webhook_endpoint_id)}/dlq/ack",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def requeue_dlq(
        self,
        webhook_endpoint_id: str,
        body: cm.PostWebhookEndpointsByIdDlqAckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostWebhookEndpointsByIdDlqRequeueResponse:
        """Send dead-lettered deliveries again as fresh first attempts (flagged `atlas-redelivery:
        1`) and take them out of the queue. An event past its 90-day retention cannot be sent
        again and stays in the queue (`skipped`). Up to 100 ids a call.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(webhook_endpoint_id)}/dlq/requeue",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class WorkflowApprovals:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'timed_out'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowApprovalsResponse:
        """Approvals that workflow `approval` steps have asked for, newest first."""
        return self._t.request(
            method="GET",
            path="/v1/workflow_approvals",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'timed_out'] | None = None,
        limit: int | None = None,
    ) -> Iterator[cm.GetWorkflowApprovalsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def decide(
        self,
        workflow_approval_id: str,
        body: cm.PostWorkflowApprovalsByIdDecideBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWorkflowApprovalsResponseDataItem:
        """Approve or deny a workflow approval. The run resumes at once. A secret-key caller may
        decide for anyone; pass `user_id` to record who decided.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/workflow_approvals/{_enc(workflow_approval_id)}/decide",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class WorkflowTemplates:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowTemplatesResponse:
        """Starter workflows (joiner, mover, leaver, inactive user, expiring guest) with the
        parameters each needs.
        """
        return self._t.request(
            method="GET",
            path="/v1/workflow_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetWorkflowTemplatesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class WorkflowTriggers:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowTriggersResponse:
        """The events a workflow can start on (`trigger.type = webhook_event`): each name, what it
        means, which fields its data carries (usable as `event.<field>` in a trigger filter or a
        step) and which part of the product emits it.
        """
        return self._t.request(
            method="GET",
            path="/v1/workflow_triggers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetWorkflowTriggersResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class Workflows:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def from_template(
        self,
        body: cm.PostWorkflowsFromTemplateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.Workflow:
        """Create a workflow from a starter template. It is created disabled unless `enabled` is
        true, so you can look it over first.
        """
        return self._t.request(
            method="POST",
            path="/v1/workflows/from_template",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def invoke(
        self,
        workflow_id: str,
        body: cm.PostWorkflowsByIdInvokeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.WorkflowRun:
        """Start a workflow whose trigger is `manual` with an `input` object (read as `input.*` in
        steps). Runs until it finishes or parks on a wait, retry or approval; the returned run
        says which.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/invoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def list_kv(
        self,
        workflow_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowsByIdKvResponse:
        """The workflow's key-value table (what `kv` steps read and write)."""
        return self._t.request(
            method="GET",
            path=f"/v1/workflows/{_enc(workflow_id)}/kv",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_kv(
        self,
        workflow_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetWorkflowsByIdKvResponseDataItem]:
        """Every item of :meth:`list_kv`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_kv(workflow_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def delete_kv(
        self,
        workflow_id: str,
        key: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWorkflowsByIdKvResponseDataItem:
        """Delete a key from the workflow key-value table."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/workflows/{_enc(workflow_id)}/kv/{_enc(key)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def set_kv(
        self,
        workflow_id: str,
        key: str,
        body: cm.PutWorkflowsByIdKvByKeyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWorkflowsByIdKvResponseDataItem:
        """Set a key in the workflow key-value table."""
        return self._t.request(
            method="PUT",
            path=f"/v1/workflows/{_enc(workflow_id)}/kv/{_enc(key)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def get_run(
        self,
        workflow_id: str,
        run_id: str,
    ) -> cm.WorkflowRun:
        """One run with its per-step log: each step's path, status, attempt, detail and output."""
        return self._t.request(
            method="GET",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}",
        )

    def cancel_run(
        self,
        workflow_id: str,
        run_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.WorkflowRun:
        """Cancel a run that is running or waiting (a timer, a retry back-off or an approval). The
        step in flight finishes; nothing after it runs, and any approval it was waiting on is
        closed. Fires `workflow.run_cancelled`. 400 for a run that already ended or a dry run.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def resume_run(
        self,
        workflow_id: str,
        run_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.WorkflowRun:
        """Retry a failed run from the step that failed, keeping its variables and earlier outputs."""
        return self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}/resume",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def retry_run(
        self,
        workflow_id: str,
        run_id: str,
        body: cm.PostWorkflowsByIdRunsByRunIdRetryBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.WorkflowRun:
        """Retry a failed or cancelled run from a chosen step (`from_step`, a step path from the
        run's step log such as `2` or `1.then.0`). Variables and the outputs of earlier steps
        are kept; the chosen step and everything after it run again. The step must be where the
        run stopped or earlier. To retry from the step that failed, use POST
        /v1/workflows/{id}/runs/{runId}/resume.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}/retry",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class WsfedConnections:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWsfedConnectionsResponse:
        """List WS-Federation relying-party connections (sign people in through AD FS or another
        WS-Federation provider).
        """
        return self._t.request(
            method="GET",
            path="/v1/wsfed_connections",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetWsfedConnectionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create(
        self,
        body: cm.PostWsfedConnectionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWsfedConnectionsResponseDataItem:
        """Add a WS-Federation connection. Give the provider's federation metadata (metadata_url or
        metadata_xml) or its issuer, passive endpoint and signing certificates, and the realm.
        Sign-in starts at POST /v1/client/sign_ins/wsfed.
        """
        return self._t.request(
            method="POST",
            path="/v1/wsfed_connections",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete(
        self,
        wsfed_connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a WS-Federation connection."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/wsfed_connections/{_enc(wsfed_connection_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get(
        self,
        wsfed_connection_id: str,
    ) -> cm.GetWsfedConnectionsResponseDataItem:
        """Read one WS-Federation connection with the reply URL to enter at the provider."""
        return self._t.request(
            method="GET",
            path=f"/v1/wsfed_connections/{_enc(wsfed_connection_id)}",
        )

    def update(
        self,
        wsfed_connection_id: str,
        body: cm.PatchWsfedConnectionsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWsfedConnectionsResponseDataItem:
        """Change a WS-Federation connection; sending metadata refreshes the certificates after a
        provider rollover.
        """
        return self._t.request(
            method="PATCH",
            path=f"/v1/wsfed_connections/{_enc(wsfed_connection_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class PlatformApps:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_instances_clones(
        self,
        app_id: str,
        instance_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        kind: Literal['clone', 'preview'] | None = None,
    ) -> cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponse:
        """The clones and previews of one instance, newest first (deleted ones are left out)."""
        return self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'kind': kind}),
        )

    def iter_list_instances_clones(
        self,
        app_id: str,
        instance_id: str,
        *,
        limit: int | None = None,
        kind: Literal['clone', 'preview'] | None = None,
    ) -> Iterator[cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponseDataItem]:
        """Every item of :meth:`list_instances_clones`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_instances_clones(app_id, instance_id, limit=limit, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_instances_clone(
        self,
        app_id: str,
        instance_id: str,
        body: cm.PostPlatformAppsByIdInstancesByInstanceIdClonesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPlatformAppsByIdInstancesByInstanceIdClonesResponse:
        """Clone an instance of an owned app into a new development-mode instance, with or without
        data, or open a per-pull-request preview (mode preview, keyed on ref, deleted when
        ttl_hours passes). Returns the new instance's id, publishable key and Frontend API host,
        and its first secret key, shown once. The copy never carries secrets (configuration
        secrets are removed; API keys and provider connections are not copied), private metadata
        of users and organizations, webhook endpoints, signing keys, passwords or second
        factors. The new instance is in development mode: no email or SMS is sent until it has
        its own provider keys. Up to 50 live previews and 10 clones per source instance. Needs
        platform:apps:write (an operator token needs recent MFA). A section over 2000 rows is
        copied in batches by a background job: the call answers 202 with status copying and the
        secret, and GET on the clone shows progress (up to 100000 rows per section). Honours
        Idempotency-Key; a repeat for a live ref returns it (200, no secret). Audited. Emits
        instance_clone.created.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_instances_clone(
        self,
        app_id: str,
        instance_id: str,
        clone_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponseDataItem:
        """Delete a clone or preview together with its instance and everything in it (users,
        configuration, keys). Only an instance a clone created, under the same app and owner,
        can be removed this way. Audited. Emits instance_clone.deleted.
        """
        return self._t.request(
            method="DELETE",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones/{_enc(clone_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    def get_instances_clone(
        self,
        app_id: str,
        instance_id: str,
        clone_id: str,
    ) -> cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponseDataItem:
        """One clone or preview: status, what was copied, what could not be placed, and when a
        preview expires.
        """
        return self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones/{_enc(clone_id)}",
        )

    def create_narrow_secret_key(
        self,
        app_id: str,
        body: cm.PostPlatformAppsByIdNarrowSecretKeysBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPlatformAppsByIdNarrowSecretKeysResponse:
        """Narrow the secret keys of an app after onboarding: a key holding every scope becomes a
        runtime key, with no new secret.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/narrow_secret_keys",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class PlatformAtlasIdApps:
    _t: _SyncTransport

    def __init__(self, transport: _SyncTransport) -> None:
        self._t = transport

    def list_adoption_codes(
        self,
        atlas_id_app_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPlatformAtlasIdAppsByIdAdoptionCodesResponse:
        """The adoption codes issued for an app and what became of them (never the code itself)."""
        return self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{_enc(atlas_id_app_id)}/adoption_codes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    def iter_list_adoption_codes(
        self,
        atlas_id_app_id: str,
        *,
        limit: int | None = None,
    ) -> Iterator[cm.GetPlatformAtlasIdAppsByIdAdoptionCodesResponseDataItem]:
        """Every item of :meth:`list_adoption_codes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = self.list_adoption_codes(atlas_id_app_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    def create_adoption_code(
        self,
        atlas_id_app_id: str,
        body: cm.PostPlatformAtlasIdAppsByIdAdoptionCodesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPlatformAtlasIdAppsByIdAdoptionCodesResponseDataItem:
        """Issue a one-time code that lets an instance of the account adopt this app with its own
        secret key.
        """
        return self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{_enc(atlas_id_app_id)}/adoption_codes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    def delete_adoption_code(
        self,
        atlas_id_app_id: str,
        code_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePlatformAtlasIdAppsByIdAdoptionCodesByCodeIdResponse:
        """Withdraw an adoption code that has not been redeemed."""
        return self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{_enc(atlas_id_app_id)}/adoption_codes/{_enc(code_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class CatalogClient:
    """Namespaces for the resources the hand-written client has no attribute for."""
    abac_policies: AbacPolicies
    abuse_signals: AbuseSignals
    administrative_units: AdministrativeUnits
    agent_access_reviews: AgentAccessReviews
    agent_delegations: AgentDelegations
    allowlist_identifiers: AllowlistIdentifiers
    approval_requests: ApprovalRequests
    atlas_id_apps: AtlasIdApps
    audit: Audit
    audit_retention: AuditRetention
    authenticator_policies: AuthenticatorPolicies
    authz: Authz
    authz_pdps: AuthzPdps
    blocklist_identifiers: BlocklistIdentifiers
    changes: Changes
    chat_integrations: ChatIntegrations
    cloud_access: CloudAccess
    compliance: Compliance
    config: Config
    connection_actions: ConnectionActions
    connection_provider_changes: ConnectionProviderChanges
    connection_provider_event_log: ConnectionProviderEventLog
    connection_provider_topics: ConnectionProviderTopics
    connection_providers: ConnectionProviders
    connection_reconnect_settings: ConnectionReconnectSettings
    containments: Containments
    cookie_consents: CookieConsents
    dev: Dev
    device_assurance_policies: DeviceAssurancePolicies
    device_integrations: DeviceIntegrations
    device_sso: DeviceSso
    dsr_console: DsrConsole
    erasure_connector_catalog: ErasureConnectorCatalog
    erasure_connectors: ErasureConnectors
    federation: Federation
    flows: Flows
    fraud: Fraud
    impersonations: Impersonations
    legal_holds: LegalHolds
    machine_trust_policies: MachineTrustPolicies
    mcp_registry: McpRegistry
    message_receivers: MessageReceivers
    messages: Messages
    messaging: Messaging
    mfa_campaigns: MfaCampaigns
    mfa_factor_quarantines: MfaFactorQuarantines
    migrations__source: MigrationsSource
    migrations_status: MigrationsStatus
    oauth_application_types: OauthApplicationTypes
    oauth_grants: OauthGrants
    oauth_publishers: OauthPublishers
    opa: Opa
    org_role_sets: OrgRoleSets
    org_templates: OrgTemplates
    organization_connections: OrganizationConnections
    passkey_campaigns: PasskeyCampaigns
    provisioning: Provisioning
    provisioning_connectors: ProvisioningConnectors
    rate_limit_overrides: RateLimitOverrides
    rate_limit_policies: RateLimitPolicies
    referral_reward_rules: ReferralRewardRules
    referral_rewards: ReferralRewards
    refresh_tokens: RefreshTokens
    region: Region
    resource_role_assignments: ResourceRoleAssignments
    risk_signals: RiskSignals
    risky_users: RiskyUsers
    saml_idp: SamlIdp
    scim_resource_types: ScimResourceTypes
    step_up: StepUp
    suppressions: Suppressions
    telemetry_export: TelemetryExport
    web_bot_auth: WebBotAuth
    webhook_endpoints: WebhookEndpoints
    workflow_approvals: WorkflowApprovals
    workflow_templates: WorkflowTemplates
    workflow_triggers: WorkflowTriggers
    wsfed_connections: WsfedConnections

    def _wire_catalog(self, transport: _SyncTransport) -> None:
        self.abac_policies = AbacPolicies(transport)
        self.abuse_signals = AbuseSignals(transport)
        self.administrative_units = AdministrativeUnits(transport)
        self.agent_access_reviews = AgentAccessReviews(transport)
        self.agent_delegations = AgentDelegations(transport)
        self.allowlist_identifiers = AllowlistIdentifiers(transport)
        self.approval_requests = ApprovalRequests(transport)
        self.atlas_id_apps = AtlasIdApps(transport)
        self.audit = Audit(transport)
        self.audit_retention = AuditRetention(transport)
        self.authenticator_policies = AuthenticatorPolicies(transport)
        self.authz = Authz(transport)
        self.authz_pdps = AuthzPdps(transport)
        self.blocklist_identifiers = BlocklistIdentifiers(transport)
        self.changes = Changes(transport)
        self.chat_integrations = ChatIntegrations(transport)
        self.cloud_access = CloudAccess(transport)
        self.compliance = Compliance(transport)
        self.config = Config(transport)
        self.connection_actions = ConnectionActions(transport)
        self.connection_provider_changes = ConnectionProviderChanges(transport)
        self.connection_provider_event_log = ConnectionProviderEventLog(transport)
        self.connection_provider_topics = ConnectionProviderTopics(transport)
        self.connection_providers = ConnectionProviders(transport)
        self.connection_reconnect_settings = ConnectionReconnectSettings(transport)
        self.containments = Containments(transport)
        self.cookie_consents = CookieConsents(transport)
        self.dev = Dev(transport)
        self.device_assurance_policies = DeviceAssurancePolicies(transport)
        self.device_integrations = DeviceIntegrations(transport)
        self.device_sso = DeviceSso(transport)
        self.dsr_console = DsrConsole(transport)
        self.erasure_connector_catalog = ErasureConnectorCatalog(transport)
        self.erasure_connectors = ErasureConnectors(transport)
        self.federation = Federation(transport)
        self.flows = Flows(transport)
        self.fraud = Fraud(transport)
        self.impersonations = Impersonations(transport)
        self.legal_holds = LegalHolds(transport)
        self.machine_trust_policies = MachineTrustPolicies(transport)
        self.mcp_registry = McpRegistry(transport)
        self.message_receivers = MessageReceivers(transport)
        self.messages = Messages(transport)
        self.messaging = Messaging(transport)
        self.mfa_campaigns = MfaCampaigns(transport)
        self.mfa_factor_quarantines = MfaFactorQuarantines(transport)
        self.migrations__source = MigrationsSource(transport)
        self.migrations_status = MigrationsStatus(transport)
        self.oauth_application_types = OauthApplicationTypes(transport)
        self.oauth_grants = OauthGrants(transport)
        self.oauth_publishers = OauthPublishers(transport)
        self.opa = Opa(transport)
        self.org_role_sets = OrgRoleSets(transport)
        self.org_templates = OrgTemplates(transport)
        self.organization_connections = OrganizationConnections(transport)
        self.passkey_campaigns = PasskeyCampaigns(transport)
        self.provisioning = Provisioning(transport)
        self.provisioning_connectors = ProvisioningConnectors(transport)
        self.rate_limit_overrides = RateLimitOverrides(transport)
        self.rate_limit_policies = RateLimitPolicies(transport)
        self.referral_reward_rules = ReferralRewardRules(transport)
        self.referral_rewards = ReferralRewards(transport)
        self.refresh_tokens = RefreshTokens(transport)
        self.region = Region(transport)
        self.resource_role_assignments = ResourceRoleAssignments(transport)
        self.risk_signals = RiskSignals(transport)
        self.risky_users = RiskyUsers(transport)
        self.saml_idp = SamlIdp(transport)
        self.scim_resource_types = ScimResourceTypes(transport)
        self.step_up = StepUp(transport)
        self.suppressions = Suppressions(transport)
        self.telemetry_export = TelemetryExport(transport)
        self.web_bot_auth = WebBotAuth(transport)
        self.webhook_endpoints = WebhookEndpoints(transport)
        self.workflow_approvals = WorkflowApprovals(transport)
        self.workflow_templates = WorkflowTemplates(transport)
        self.workflow_triggers = WorkflowTriggers(transport)
        self.wsfed_connections = WsfedConnections(transport)


class CatalogPlatformClient:
    """Namespaces for the resources the hand-written client has no attribute for."""

    def _wire_catalog(self, transport: _SyncTransport) -> None:
        pass
