"""Generated async Backend API / Platform API operations (do not edit).

The async peer of ``_catalog.py``, derived from it by ``scripts/gen_async.py``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Literal

from . import catalog_models as cm
from ._transport import _AsyncTransport
from ._util import _enc, _qd


class AsyncAbac:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def authorize_token(
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
        return await self._t.request(
            method="POST",
            path="/v1/abac/authorize_token",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def export_cedar(
        self,
        body: cm.PostAbacCedarExportBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Convert Cedar policy text to the Cedar JSON policy format (annotations, decimal and ip
        extension calls included).
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac/cedar/export",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def import_cedar(
        self,
        body: cm.PostAbacCedarImportBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Convert Cedar JSON policies to policy text. With `name`, also create the policy from
        them.
        """
        return await self._t.request(
            method="POST",
            path="/v1/abac/cedar/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_token_mapping(
        self,
    ) -> dict[str, Any]:
        """How access-token claims become a policy principal and its parents, and which extra token
        issuers are trusted.
        """
        return await self._t.request(
            method="GET",
            path="/v1/abac/token_mapping",
        )

    async def set_token_mapping(
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
        return await self._t.request(
            method="PUT",
            path="/v1/abac/token_mapping",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAbacPolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_cedar_json(
        self,
        abac_policy_id: str,
    ) -> dict[str, Any]:
        """The current version of a stored policy as Cedar JSON."""
        return await self._t.request(
            method="GET",
            path=f"/v1/abac_policies/{_enc(abac_policy_id)}/cedar_json",
        )


class AsyncAbuseSignals:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/abuse_signals",
            query=_qd({'kind': kind, 'outcome': outcome, 'attempt_id': attempt_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        kind: Literal['sign_up', 'recovery'] | None = None,
        outcome: Literal['allowed', 'scored', 'blocked'] | None = None,
        attempt_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAbuseSignalsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(kind=kind, outcome=outcome, attempt_id=attempt_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_summary(
        self,
        *,
        days: int | None = None,
    ) -> cm.GetAbuseSignalsSummaryResponse:
        """Counts of abuse signals by kind and outcome over the last N days."""
        return await self._t.request(
            method="GET",
            path="/v1/abuse_signals/summary",
            query=_qd({'days': days}),
        )


class AsyncAccessPolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def impact(
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
        return await self._t.request(
            method="POST",
            path="/v1/access_policies/impact",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_insights(
        self,
        *,
        days: int | None = None,
    ) -> cm.AccessPolicyInsights:
        """Report-only insights: how often `report_only` policies would have blocked or stepped up
        a request in the last `days`, per policy and per day.
        """
        return await self._t.request(
            method="GET",
            path="/v1/access_policies/insights",
            query=_qd({'days': days}),
        )


class AsyncActions:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def rollback(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/actions/{_enc(action_id)}/rollback",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update_rollout(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/actions/{_enc(action_id)}/rollout",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_versions(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/actions/{_enc(action_id)}/versions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_versions(
        self,
        action_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetActionsByIdVersionsResponseDataItem]:
        """Every item of :meth:`list_versions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_versions(action_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_version(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/actions/{_enc(action_id)}/versions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_version(
        self,
        action_id: str,
        version: str,
    ) -> cm.GetActionsByIdVersionsResponseDataItem:
        """One version of an Action, with its code."""
        return await self._t.request(
            method="GET",
            path=f"/v1/actions/{_enc(action_id)}/versions/{_enc(version)}",
        )


class AsyncAdministrativeUnits:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAdministrativeUnitsResponse:
        """List administrative units: named sets of users that a scoped organization administrator
        may manage.
        """
        return await self._t.request(
            method="GET",
            path="/v1/administrative_units",
            query=_qd({'organization_id': organization_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAdministrativeUnitsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(organization_id=organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostAdministrativeUnitsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAdministrativeUnitsResponseDataItem:
        """Create an administrative unit. Without a `filter` it is static and you list its members;
        with one it is dynamic and its members are whoever match.
        """
        return await self._t.request(
            method="POST",
            path="/v1/administrative_units",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        administrative_unit_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAdministrativeUnitsByIdResponse:
        """Delete a unit. A membership scope that named it stops reaching those people."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        administrative_unit_id: str,
    ) -> cm.GetAdministrativeUnitsResponseDataItem:
        """Read one unit by id or key."""
        return await self._t.request(
            method="GET",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}",
        )

    async def update(
        self,
        administrative_unit_id: str,
        body: cm.PatchAdministrativeUnitsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAdministrativeUnitsResponseDataItem:
        """Change a unit's name, description or filter."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_members(
        self,
        administrative_unit_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAdministrativeUnitsByIdMembersResponse:
        """The listed members of a static unit (409 for a dynamic unit)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}/members",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_members(
        self,
        administrative_unit_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAdministrativeUnitsByIdMembersResponseDataItem]:
        """Every item of :meth:`list_members`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_members(administrative_unit_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_member(
        self,
        administrative_unit_id: str,
        body: cm.PostAdministrativeUnitsByIdMembersBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAdministrativeUnitsByIdMembersResponse:
        """Add and remove people on a static unit."""
        return await self._t.request(
            method="POST",
            path=f"/v1/administrative_units/{_enc(administrative_unit_id)}/members",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAgentAccessReviews:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAgentAccessReviewsResponse:
        """The agent access reviews, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/agent_access_reviews",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAgentAccessReviewsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostAgentAccessReviewsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentAccessReviewsResponseDataItem:
        """Start an access review of agents' live grants: one item per grant, assigned to the
        agent's sponsor (else its owner), who certifies or revokes it.
        """
        return await self._t.request(
            method="POST",
            path="/v1/agent_access_reviews",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        agent_access_review_id: str,
        *,
        decision: str | None = None,
        reviewer_user_id: str | None = None,
    ) -> cm.GetAgentAccessReviewsByIdResponse:
        """One review with its items; filter by decision or reviewer."""
        return await self._t.request(
            method="GET",
            path=f"/v1/agent_access_reviews/{_enc(agent_access_review_id)}",
            query=_qd({'decision': decision, 'reviewer_user_id': reviewer_user_id}),
        )

    async def close(
        self,
        agent_access_review_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentAccessReviewsResponseDataItem:
        """Close a review; no further decisions are accepted."""
        return await self._t.request(
            method="POST",
            path=f"/v1/agent_access_reviews/{_enc(agent_access_review_id)}/close",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def decide_item(
        self,
        agent_access_review_id: str,
        item_id: str,
        body: cm.PostAgentAccessReviewsByIdItemsByItemIdDecideBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAgentAccessReviewsByIdResponseItemsItem:
        """Certify or revoke one item. A revoke ends that grant immediately."""
        return await self._t.request(
            method="POST",
            path=f"/v1/agent_access_reviews/{_enc(agent_access_review_id)}/items/{_enc(item_id)}/decide",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAgentDelegations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/agent_delegations",
            query=_qd({'machine_id': machine_id, 'delegator_user_id': delegator_user_id, 'root_id': root_id, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        machine_id: str | None = None,
        delegator_user_id: str | None = None,
        root_id: str | None = None,
        status: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetAgentDelegationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(machine_id=machine_id, delegator_user_id=delegator_user_id, root_id=root_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/agent_delegations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke_for_user(
        self,
        body: cm.PostAgentDelegationsRevokeForUserBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAgentDelegationsRevokeForUserResponse:
        """Revoke every delegation a user made (and everything below them), for example when they
        leave or are suspected compromised.
        """
        return await self._t.request(
            method="POST",
            path="/v1/agent_delegations/revoke_for_user",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        agent_delegation_id: str,
    ) -> cm.GetAgentDelegationsByIdResponse:
        """One delegation with its last evaluations."""
        return await self._t.request(
            method="GET",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}",
        )

    async def evaluate(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}/evaluate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_graph(
        self,
        agent_delegation_id: str,
    ) -> cm.GetAgentDelegationsByIdGraphResponse:
        """The delegation graph around one delegation: the chain above it and every delegation
        below it, with the edges between them.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}/graph",
        )

    async def revoke(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/agent_delegations/{_enc(agent_delegation_id)}/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAgents:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def verify_request(
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
        return await self._t.request(
            method="POST",
            path="/v1/agents/verify_request",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_activity(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/agents/{_enc(agent_id)}/activity",
            query=_qd({'since': since, 'before': before, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_activity(
        self,
        agent_id: str,
        *,
        since: str | None = None,
        before: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetAgentsByIdActivityResponseDataItem]:
        """Every item of :meth:`list_activity`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_activity(agent_id, since=since, before=before, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_lifecycle(
        self,
        agent_id: str,
    ) -> cm.GetAgentsByIdLifecycleResponse:
        """An agent's sponsor, backup sponsor and expiry."""
        return await self._t.request(
            method="GET",
            path=f"/v1/agents/{_enc(agent_id)}/lifecycle",
        )

    async def set_lifecycle(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/agents/{_enc(agent_id)}/lifecycle",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def renew(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/agents/{_enc(agent_id)}/renew",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAllowlistIdentifiers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAllowlistIdentifiersResponse:
        """List allowlist identifiers (emails, @domains, phones) permitted in allow-list-only mode."""
        return await self._t.request(
            method="GET",
            path="/v1/allowlist_identifiers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.AllowlistIdentifier]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostAllowlistIdentifiersBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.AllowlistIdentifier:
        """Add an allowlist identifier: an exact email, an @domain, or an E.164 phone."""
        return await self._t.request(
            method="POST",
            path="/v1/allowlist_identifiers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        allowlist_identifier_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAllowlistIdentifiersByIdResponse:
        """Remove an allowlist identifier. Another instance id is 404, never 403."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/allowlist_identifiers/{_enc(allowlist_identifier_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncAnalytics:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_captcha(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal['day', 'week', 'month'] | None = None,
        organization_id: str | None = None,
        format: Literal['json', 'csv', 'parquet'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAnalyticsCaptchaResponse:
        """Captcha challenges per provider and flow: issued, passed, failed, refused, and the solve
        rate (passed over passed plus failed). No organization slice. A provider that records no
        issue event shows 0 issued.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/captcha",
            query=_qd({'from': from_, 'to': to, 'days': days, 'granularity': granularity, 'organization_id': organization_id, 'format': format, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_captcha(
        self,
        *,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal['day', 'week', 'month'] | None = None,
        organization_id: str | None = None,
        format: Literal['json', 'csv', 'parquet'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAnalyticsCaptchaResponseDataItem]:
        """Every item of :meth:`list_captcha`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_captcha(from_=from_, to=to, days=days, granularity=granularity, organization_id=organization_id, format=format, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_sms(
        self,
        *,
        rate_per_message: float | None = None,
        currency: str | None = None,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal['day', 'week', 'month'] | None = None,
        organization_id: str | None = None,
        format: Literal['json', 'csv', 'parquet'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAnalyticsSmsResponse:
        """SMS messages by destination country: sent, delivered, failed. Atlas sends through your
        own provider, which bills you; pass `rate_per_message` (and optionally `currency`) to
        add `estimated_cost` (messages times that rate, not a billed amount). No organization
        slice.
        """
        return await self._t.request(
            method="GET",
            path="/v1/analytics/sms",
            query=_qd({'rate_per_message': rate_per_message, 'currency': currency, 'from': from_, 'to': to, 'days': days, 'granularity': granularity, 'organization_id': organization_id, 'format': format, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_sms(
        self,
        *,
        rate_per_message: float | None = None,
        currency: str | None = None,
        from_: int | str | None = None,
        to: int | str | None = None,
        days: int | None = None,
        granularity: Literal['day', 'week', 'month'] | None = None,
        organization_id: str | None = None,
        format: Literal['json', 'csv', 'parquet'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAnalyticsSmsResponseDataItem]:
        """Every item of :meth:`list_sms`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_sms(rate_per_message=rate_per_message, currency=currency, from_=from_, to=to, days=days, granularity=granularity, organization_id=organization_id, format=format, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncApiKeys:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_posture(
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
        return await self._t.request(
            method="GET",
            path="/v1/api_keys/posture",
            query=_qd({'issue': issue, 'stale_days': stale_days, 'never_used_days': never_used_days, 'max_scopes': max_scopes, 'starting_after': starting_after, 'limit': limit}),
        )

    async def iter_list_posture(
        self,
        *,
        issue: str | None = None,
        stale_days: str | None = None,
        never_used_days: str | None = None,
        max_scopes: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetApiKeysPostureResponseDataItem]:
        """Every item of :meth:`list_posture`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_posture(issue=issue, stale_days=stale_days, never_used_days=never_used_days, max_scopes=max_scopes, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_callers(
        self,
        api_key_id: str,
        *,
        window_days: str | None = None,
        limit: int | None = None,
    ) -> cm.GetApiKeysByIdCallersResponse:
        """Who uses a key: the busiest caller addresses, user agents and route buckets over the
        last days.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/api_keys/{_enc(api_key_id)}/callers",
            query=_qd({'window_days': window_days, 'limit': limit}),
        )

    async def rotate(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/api_keys/{_enc(api_key_id)}/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAppCatalog:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_custom_presets(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAppCatalogCustomPresetsResponse:
        """List this instance's private SAML presets, in the portable form POST
        /v1/app_catalog/custom_presets accepts, so a preset can be moved between environments.
        """
        return await self._t.request(
            method="GET",
            path="/v1/app_catalog/custom_presets",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_custom_presets(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAppCatalogCustomPresetsResponseDataItem]:
        """Every item of :meth:`list_custom_presets`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_custom_presets(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_custom_preset(
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
        return await self._t.request(
            method="POST",
            path="/v1/app_catalog/custom_presets",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_custom_preset(
        self,
        custom_preset_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a private preset. Apps already installed from it keep working."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/app_catalog/custom_presets/{_enc(custom_preset_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAppCatalogRequestsResponse:
        """The queue of apps people asked for, most wanted first. Filter with status (open,
        building, available, declined).
        """
        return await self._t.request(
            method="GET",
            path="/v1/app_catalog/requests",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAppCatalogRequestsResponseDataItem]:
        """Every item of :meth:`list_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_requests(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_request(
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
        return await self._t.request(
            method="POST",
            path="/v1/app_catalog/requests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_request(
        self,
        request_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove an app catalog request."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/app_catalog/requests/{_enc(request_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def update_request(
        self,
        request_id: str,
        body: cm.PatchAppCatalogRequestsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Move a request along: status open, building, available or declined, and a note."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/app_catalog/requests/{_enc(request_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def vote_request(
        self,
        request_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAppCatalogRequestsResponseDataItem:
        """Add one vote to an open or in-progress app request (409 when it is available or
        declined, 404 when unknown). One vote per person or key: a repeat vote changes nothing.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/app_catalog/requests/{_enc(request_id)}/vote",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncApprovalRequests:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/approval_requests",
            query=_qd({'status': status, 'user_id': user_id, 'approver_user_id': approver_user_id, 'reference': reference, 'created_after': created_after, 'created_before': created_before, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        status: str | None = None,
        user_id: str | None = None,
        approver_user_id: str | None = None,
        reference: str | None = None,
        created_after: int | None = None,
        created_before: int | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersByIdApprovalRequestsByApprovalIdResponse]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(status=status, user_id=user_id, approver_user_id=approver_user_id, reference=reference, created_after=created_after, created_before=created_before, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/approval_requests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        approval_request_id: str,
        *,
        wait_seconds: int | None = None,
    ) -> cm.GetUsersByIdApprovalRequestsByApprovalIdResponse:
        """Read one approval request with its decisions and, once approved, the signed receipt.
        `wait_seconds` (0 to 25) holds the call open until the request leaves pending, so an
        agent can wait for a human without a tight polling loop. Needs `approvals:read`.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/approval_requests/{_enc(approval_request_id)}",
            query=_qd({'wait_seconds': wait_seconds}),
        )

    async def cancel(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/approval_requests/{_enc(approval_request_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def consume(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/approval_requests/{_enc(approval_request_id)}/consume",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAtlasIdApps:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def adopt(
        self,
        body: cm.PostAtlasIdAppsAdoptBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Adopt an account-level Sign in with Atlas app with the one-time code its owner issued,
        using this instance's own secret key.
        """
        return await self._t.request(
            method="POST",
            path="/v1/atlas_id_apps/adopt",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def release(
        self,
        atlas_id_app_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostAtlasIdAppsByIdReleaseResponse:
        """Hand an adopted app back to its owner. The instance stops managing its grants."""
        return await self._t.request(
            method="POST",
            path=f"/v1/atlas_id_apps/{_enc(atlas_id_app_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncAudit:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_chain(
        self,
    ) -> cm.GetAuditChainResponse:
        """The audit chain: whether it is on, its head, its last checkpoint and how many rows are
        not chained yet.
        """
        return await self._t.request(
            method="GET",
            path="/v1/audit/chain",
        )

    async def set_chain(
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
        return await self._t.request(
            method="PUT",
            path="/v1/audit/chain",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_chain_checkpoints(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuditChainCheckpointsResponse:
        """Signed checkpoints, oldest first. Each is a JWS the instance's signing key made; verify
        it against jwks_uri.
        """
        return await self._t.request(
            method="GET",
            path="/v1/audit/chain/checkpoints",
            query=_qd({'after_seq': after_seq, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_chain_checkpoints(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetAuditChainCheckpointsResponseDataItem]:
        """Every item of :meth:`list_chain_checkpoints`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_chain_checkpoints(after_seq=after_seq, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_chain_checkpoint(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAuditChainCheckpointsResponseDataItem:
        """Sign a checkpoint of the chain head now (the worker does it on its interval). Refused
        with 409 when the chain does not verify. Returns the existing checkpoint when the head
        is already pinned.
        """
        return await self._t.request(
            method="POST",
            path="/v1/audit/chain/checkpoints",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_chain_links(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuditChainLinksResponse:
        """Chain links with the audit rows they cover, oldest first, for an independent verifier
        (`atlas audit verify`).
        """
        return await self._t.request(
            method="GET",
            path="/v1/audit/chain/links",
            query=_qd({'after_seq': after_seq, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_chain_links(
        self,
        *,
        after_seq: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetAuditChainLinksResponseDataItem]:
        """Every item of :meth:`list_chain_links`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_chain_links(after_seq=after_seq, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def verify_chain(
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
        return await self._t.request(
            method="POST",
            path="/v1/audit/chain/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAuditRetention:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> dict[str, Any]:
        """How long the instance audit log is kept: the effective days, whether it is configured,
        and the allowed range (30 to 3,650; the default is 365).
        """
        return await self._t.request(
            method="GET",
            path="/v1/audit_retention",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path="/v1/audit_retention",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAuthenticatorPolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthenticatorPoliciesResponse:
        """List the group-targeted authenticator policies."""
        return await self._t.request(
            method="GET",
            path="/v1/authenticator_policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAuthenticatorPoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/authenticator_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_effective(
        self,
        user_id: str,
    ) -> cm.GetAuthenticatorPoliciesEffectiveByUserIdResponse:
        """The combined authenticator rules that apply to one user through their groups."""
        return await self._t.request(
            method="GET",
            path=f"/v1/authenticator_policies/effective/{_enc(user_id)}",
        )

    async def delete(
        self,
        authenticator_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAuthenticatorPoliciesByIdResponse:
        """Delete an authenticator policy."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/authenticator_policies/{_enc(authenticator_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        authenticator_policy_id: str,
    ) -> cm.GetAuthenticatorPoliciesResponseDataItem:
        """Read one authenticator policy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/authenticator_policies/{_enc(authenticator_policy_id)}",
        )

    async def update(
        self,
        authenticator_policy_id: str,
        body: cm.PatchAuthenticatorPoliciesByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetAuthenticatorPoliciesResponseDataItem:
        """Update an authenticator policy."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/authenticator_policies/{_enc(authenticator_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAuthz:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_events(
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
        return await self._t.request(
            method="GET",
            path="/v1/authz/events",
            query=_qd({'after': after, 'limit': limit, 'store_id': store_id, 'kinds': kinds, 'wait_ms': wait_ms, 'starting_after': starting_after}),
        )

    async def iter_list_events(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
        store_id: str | None = None,
        kinds: str | None = None,
        wait_ms: int | None = None,
    ) -> AsyncIterator[cm.GetAuthzEventsResponseDataItem]:
        """Every item of :meth:`list_events`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_events(after=after, limit=limit, store_id=store_id, kinds=kinds, wait_ms=wait_ms, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def explain(
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
        return await self._t.request(
            method="POST",
            path="/v1/authz/explain",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def check_rbac(
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
        return await self._t.request(
            method="POST",
            path="/v1/authz/rbac/check",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_what_if(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthzWhatIfResponse:
        """Saved what-if runs, newest first, with their summaries."""
        return await self._t.request(
            method="GET",
            path="/v1/authz/what_if",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_what_if(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetAuthzWhatIfResponseDataItem]:
        """Every item of :meth:`list_what_if`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_what_if(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def what_if(
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
        return await self._t.request(
            method="POST",
            path="/v1/authz/what_if",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_what_if(
        self,
        what_if_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAuthzWhatIfByIdResponse:
        """Delete a saved what-if run."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/authz/what_if/{_enc(what_if_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_what_if(
        self,
        what_if_id: str,
    ) -> cm.GetAuthzWhatIfResponseDataItem:
        """One saved what-if run with its full result."""
        return await self._t.request(
            method="GET",
            path=f"/v1/authz/what_if/{_enc(what_if_id)}",
        )


class AsyncAuthzDecisions:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def ingest(
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
        return await self._t.request(
            method="POST",
            path="/v1/authz_decisions/ingest",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncAuthzPdps:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAuthzPdpsResponse:
        """The fleet of local policy decision points that have checked in: the bundle revision each
        is on, when it was last seen and how many decisions it has shipped.
        """
        return await self._t.request(
            method="GET",
            path="/v1/authz_pdps",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.PostAuthzDecisionsIngestResponsePdp]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete(
        self,
        authz_pdp_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteAuthzPdpsByIdResponse:
        """Forget a local policy decision point (it reappears if it checks in again)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/authz_pdps/{_enc(authz_pdp_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncBilling:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def sync_checkout(
        self,
        body: cm.PostBillingCheckoutSyncBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostBillingCheckoutSyncResponse:
        """Read a Stripe Checkout Session back with your own key and record the purchase, for an
        instance that syncs without a Stripe webhook. The session's reference must name this
        instance; any other session is a 404. Idempotent. `status` is `synced`, or `pending`
        when Stripe has not completed the session yet.
        """
        return await self._t.request(
            method="POST",
            path="/v1/billing/checkout/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_connect_accounts(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingConnectAccountsResponse:
        """List the connected accounts, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/billing/connect/accounts",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_connect_accounts(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetBillingConnectAccountsResponseDataItem]:
        """Every item of :meth:`list_connect_accounts`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_connect_accounts(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_connect_account(
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
        return await self._t.request(
            method="POST",
            path="/v1/billing/connect/accounts",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_connect_account(
        self,
        account_id: str,
    ) -> cm.GetBillingConnectAccountsResponseDataItem:
        """Read one connected account as Atlas last saw it. `POST .../refresh` re-reads it from
        Stripe.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/billing/connect/accounts/{_enc(account_id)}",
        )

    async def onboarding_link_account_connect(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/connect/accounts/{_enc(account_id)}/onboarding_link",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def refresh_account_connect(
        self,
        account_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetBillingConnectAccountsResponseDataItem:
        """Re-read the account's onboarding and payout readiness from Stripe and store it."""
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/connect/accounts/{_enc(account_id)}/refresh",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_connect_transfers(
        self,
        *,
        account_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingConnectTransfersResponse:
        """The transfer ledger, newest first, optionally for one account."""
        return await self._t.request(
            method="GET",
            path="/v1/billing/connect/transfers",
            query=_qd({'account_id': account_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_connect_transfers(
        self,
        *,
        account_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetBillingConnectTransfersResponseDataItem]:
        """Every item of :meth:`list_connect_transfers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_connect_transfers(account_id=account_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_connect_transfer(
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
        return await self._t.request(
            method="POST",
            path="/v1/billing/connect/transfers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_connect_transfer(
        self,
        transfer_id: str,
    ) -> cm.GetBillingConnectTransfersResponseDataItem:
        """Read one Connect transfer by id: its amount, destination account and status."""
        return await self._t.request(
            method="GET",
            path=f"/v1/billing/connect/transfers/{_enc(transfer_id)}",
        )

    async def list_coupons(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingCouponsResponse:
        """List the discount codes you offer."""
        return await self._t.request(
            method="GET",
            path="/v1/billing/coupons",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_coupons(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetBillingCouponsResponseDataItem]:
        """Every item of :meth:`list_coupons`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_coupons(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_coupon(
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
        return await self._t.request(
            method="POST",
            path="/v1/billing/coupons",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def validate_coupon(
        self,
        body: cm.PostBillingCouponsValidateBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Would this code work for this subject and plan? `reason`: unknown, inactive, expired,
        exhausted, plan_not_eligible, first_time_only or already_used.
        """
        return await self._t.request(
            method="POST",
            path="/v1/billing/coupons/validate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_coupon(
        self,
        coupon_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteBillingCouponsByIdResponse:
        """Delete a code and stop it being used. Subscriptions that already have the discount keep
        it.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/billing/coupons/{_enc(coupon_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_coupon(
        self,
        coupon_id: str,
    ) -> cm.GetBillingCouponsResponseDataItem:
        """Read one discount code."""
        return await self._t.request(
            method="GET",
            path=f"/v1/billing/coupons/{_enc(coupon_id)}",
        )

    async def update_coupon(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/billing/coupons/{_enc(coupon_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_credits(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBillingCreditsResponse:
        """A subject's account-credit ledger and its balance per currency."""
        return await self._t.request(
            method="GET",
            path="/v1/billing/credits",
            query=_qd({'subject_type': subject_type, 'subject_id': subject_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_credits(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetBillingCreditsResponseDataItem]:
        """Every item of :meth:`list_credits`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_credits(subject_type=subject_type, subject_id=subject_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_credit(
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
        return await self._t.request(
            method="POST",
            path="/v1/billing/credits",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_invoices(
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
        return await self._t.request(
            method="GET",
            path="/v1/billing/invoices",
            query=_qd({'subject_type': subject_type, 'subject_id': subject_id, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_invoices(
        self,
        *,
        subject_type: Literal['user', 'org'] | None = None,
        subject_id: str | None = None,
        status: Literal['draft', 'open', 'paid', 'uncollectible', 'void'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetBillingInvoicesResponseDataItem]:
        """Every item of :meth:`list_invoices`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_invoices(subject_type=subject_type, subject_id=subject_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_invoice(
        self,
        invoice_id: str,
    ) -> cm.GetBillingInvoicesByIdResponse:
        """Read one invoice, with the refunds made against it."""
        return await self._t.request(
            method="GET",
            path=f"/v1/billing/invoices/{_enc(invoice_id)}",
        )

    async def refund_invoice(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/invoices/{_enc(invoice_id)}/refund",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_store_link(
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
        return await self._t.request(
            method="POST",
            path="/v1/billing/store_links",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_stripe_event(
        self,
        body: cm.PostBillingStripeEventsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostBillingStripeEventsResponse:
        """Forward a Stripe event from your own webhook endpoint, for an account that cannot add an
        Atlas endpoint. Post `{ id: "evt_…" }` or the whole event; only the id is read. Atlas
        fetches the event from Stripe with your own key and processes THAT object, never the
        posted body, and ignores anything that is not one of this instance's subscriptions. Safe
        to repeat. `outcome` is `processed` or `ignored`; both are 200.
        """
        return await self._t.request(
            method="POST",
            path="/v1/billing/stripe/events",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def extend_trial_subscription(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{_enc(subscription_id)}/extend_trial",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def sync_subscription(
        self,
        subscription_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.Subscription:
        """Re-read one subscription from Stripe now, with your own key, and apply what Stripe
        reports (status, plan, period, cancellation). For an instance that syncs without a
        Stripe webhook, or to refresh one subscription on demand. A subscription on another
        account, or not Stripe, is refused.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/billing/subscriptions/{_enc(subscription_id)}/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_usage(
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
        return await self._t.request(
            method="GET",
            path="/v1/billing/usage",
            query=_qd({'subject_type': subject_type, 'subject_id': subject_id, 'feature': feature, 'since': since, 'until': until, 'period': period, 'events': events, 'limit': limit, 'starting_after': starting_after}),
        )

    async def batch_usage(
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
        return await self._t.request(
            method="POST",
            path="/v1/billing/usage/batch",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncBlocklistIdentifiers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetBlocklistIdentifiersResponse:
        """List blocklist identifiers that cannot sign up or sign in."""
        return await self._t.request(
            method="GET",
            path="/v1/blocklist_identifiers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.BlocklistIdentifier]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostAllowlistIdentifiersBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.BlocklistIdentifier:
        """Block an identifier (email, @domain, or E.164 phone) from signing up and signing in."""
        return await self._t.request(
            method="POST",
            path="/v1/blocklist_identifiers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        blocklist_identifier_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteBlocklistIdentifiersByIdResponse:
        """Remove a blocklist identifier. Another instance id is 404, never 403."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/blocklist_identifiers/{_enc(blocklist_identifier_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncChanges:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/changes",
            query=_qd({'after': after, 'types': types, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        after: int | None = None,
        types: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetChangesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(after=after, types=types, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_consumers(
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
        return await self._t.request(
            method="GET",
            path="/v1/changes/consumers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_consumers(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetChangesConsumersResponseDataItem]:
        """Every item of :meth:`list_consumers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_consumers(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_consumer(
        self,
        name: str,
    ) -> cm.GetChangesConsumersByNameResponse:
        """Where a named consumer has read up to, and how far behind it is. The position is held on
        the server so a restarted reader resumes where it left off. Positions belong to the API
        key that wrote them.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/changes/consumers/{_enc(name)}",
        )

    async def set_consumers_ack(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/changes/consumers/{_enc(name)}/ack",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_snapshot(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/changes/snapshot/{_enc(resource_type)}",
            query=_qd({'cursor': cursor, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_get_snapshot(
        self,
        resource_type: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Every item of :meth:`get_snapshot`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.get_snapshot(resource_type, cursor=cursor, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncChatIntegrations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChatIntegrationsResponse:
        """List chat integrations (Slack workspaces and Teams bots)."""
        return await self._t.request(
            method="GET",
            path="/v1/chat_integrations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetChatIntegrationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostChatIntegrationsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetChatIntegrationsResponseDataItem:
        """Connect a Slack workspace or a Teams bot using your own app. Slack credentials are
        checked with the workspace before saving.
        """
        return await self._t.request(
            method="POST",
            path="/v1/chat_integrations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        chat_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteChatIntegrationsByIdResponse:
        """Remove an integration and its stored credentials."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        chat_integration_id: str,
    ) -> cm.GetChatIntegrationsResponseDataItem:
        """Read one chat integration."""
        return await self._t.request(
            method="GET",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}",
        )

    async def update(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_interactions(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChatIntegrationsByIdInteractionsResponse:
        """The latest button clicks and what became of them (applied, refused, unlinked, stale)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/interactions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_interactions(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetChatIntegrationsByIdInteractionsResponseDataItem]:
        """Every item of :meth:`list_interactions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_interactions(chat_integration_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def test(
        self,
        chat_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostChatIntegrationsByIdTestResponse:
        """Post a harmless test message to the default channel or conversation."""
        return await self._t.request(
            method="POST",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_user_links(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetChatIntegrationsByIdUserLinksResponse:
        """Chat users linked to Atlas users. A link is made automatically on first click when the
        chat profile email matches a verified email.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/user_links",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_user_links(
        self,
        chat_integration_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetChatIntegrationsByIdUserLinksResponseDataItem]:
        """Every item of :meth:`list_user_links`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_user_links(chat_integration_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_user_link(
        self,
        chat_integration_id: str,
        body: cm.PostChatIntegrationsByIdUserLinksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetChatIntegrationsByIdUserLinksResponseDataItem:
        """Link a chat user to an Atlas user by hand."""
        return await self._t.request(
            method="POST",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/user_links",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_user_link(
        self,
        chat_integration_id: str,
        link_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteChatIntegrationsByIdResponse:
        """Remove the link between a chat user and an Atlas user."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/chat_integrations/{_enc(chat_integration_id)}/user_links/{_enc(link_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncCloudAccess:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_targets(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetCloudAccessTargetsResponse:
        """List the cloud access targets: AWS account and role tiles, Google Cloud workforce-pool
        tiles and Azure trust recipes.
        """
        return await self._t.request(
            method="GET",
            path="/v1/cloud_access/targets",
            query=_qd({'provider': provider, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_targets(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetCloudAccessTargetsResponseDataItem]:
        """Every item of :meth:`list_targets`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_targets(provider=provider, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_target(
        self,
        body: cm.PostCloudAccessTargetsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetCloudAccessTargetsResponseDataItem:
        """Add a cloud access target. An AWS or Google Cloud target becomes a launcher tile that
        signs people in to that account and role (AWS: the Role, RoleSessionName,
        SessionDuration and PrincipalTag attributes) or workforce pool; assignment limits who
        sees it. Azure stores a federated-credential trust recipe. AsyncConfig: aws: account_id (12
        digits), role_name, saml_provider_name, session_duration (900-43200 s), session_tags
        {tag key: user field}, transitive_tag_keys, partition (aws, aws-us-gov, aws-cn). gcp:
        pool_id, provider_id (a Workforce Identity Federation SAML provider). azure:
        app_object_id, subject, credential_name.
        """
        return await self._t.request(
            method="POST",
            path="/v1/cloud_access/targets",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_target(
        self,
        target_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a target and its launcher tile."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_target(
        self,
        target_id: str,
    ) -> cm.GetCloudAccessTargetsResponseDataItem:
        """Read one cloud access target with its launch URL and assignment."""
        return await self._t.request(
            method="GET",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}",
        )

    async def update_target(
        self,
        target_id: str,
        body: cm.PatchCloudAccessTargetsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetCloudAccessTargetsResponseDataItem:
        """Change a target's name, config or assignment. The provider cannot change."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_targets_setup(
        self,
        target_id: str,
    ) -> cm.GetCloudAccessTargetsByIdSetupResponse:
        """What to configure on the cloud side for this target, with ready-to-run snippets: the AWS
        CLI command and role trust policy, the gcloud command for the workforce pool provider,
        or the Azure federated credential.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/cloud_access/targets/{_enc(target_id)}/setup",
        )


class AsyncCompliance:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_inactive_users_preview(
        self,
        *,
        limit: int | None = None,
    ) -> cm.GetComplianceInactiveUsersPreviewResponse:
        """A dry run of the inactive-user policy: who would be warned and who acted on right now,
        without doing anything. Works with the policy off, to size it before turning it on.
        """
        return await self._t.request(
            method="GET",
            path="/v1/compliance/inactive_users/preview",
            query=_qd({'limit': limit}),
        )

    async def get_posture(
        self,
    ) -> cm.GetCompliancePostureResponse:
        """The live compliance posture: which controls the configuration turns on (data rights
        deadline, erasure window, ownership hand-over, policy acceptance, cookie consent store,
        age gating, inactive-user policy, record of processing, downstream erasure) and counts
        of data rights work. Configuration and counts only: no user data and no secrets.
        """
        return await self._t.request(
            method="GET",
            path="/v1/compliance/posture",
        )

    async def list_reports(
        self,
        *,
        kind: Literal['posture', 'ropa'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetComplianceReportsResponse:
        """The kept reports, newest first (claims only; fetch one for its signed form)."""
        return await self._t.request(
            method="GET",
            path="/v1/compliance/reports",
            query=_qd({'kind': kind, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_reports(
        self,
        *,
        kind: Literal['posture', 'ropa'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetComplianceReportsResponseDataItem]:
        """Every item of :meth:`list_reports`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_reports(kind=kind, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_report(
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
        return await self._t.request(
            method="POST",
            path="/v1/compliance/reports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_report(
        self,
        report_id: str,
    ) -> cm.GetComplianceReportsResponseDataItem:
        """One kept report with its signed form (report), key id and jwks_uri."""
        return await self._t.request(
            method="GET",
            path=f"/v1/compliance/reports/{_enc(report_id)}",
        )

    async def get_ropa(
        self,
    ) -> cm.GetComplianceRopaResponse:
        """The live record of processing built from compliance.dataPolicy: the controller, each
        processing activity (purpose, legal basis, data categories, subjects, recipients,
        transfers, retention), retention windows, Atlas's sub-processors, and findings (a
        consent basis with nothing to record it, an activity with no retention, a transfer with
        no recipient).
        """
        return await self._t.request(
            method="GET",
            path="/v1/compliance/ropa",
        )


class AsyncConfig:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_limits(
        self,
    ) -> cm.GetConfigLimitsResponse:
        """The limits the write routes enforce that a config tool can check up front: roles per
        resource type, permissions per app role, implied permissions per permission, key
        patterns and text lengths. `atlas plan` validates a file against these before it writes
        anything.
        """
        return await self._t.request(
            method="GET",
            path="/v1/config/limits",
        )


class AsyncConnectionActions:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionActionsResponse:
        """The action catalog: typed operations per provider (GitHub, Slack, Notion, HubSpot,
        Google and more), first-party and your own definitions.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connection_actions",
            query=_qd({'provider': provider, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        provider: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetConnectionActionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(provider=provider, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_types(
        self,
        *,
        provider: str | None = None,
    ) -> cm.GetConnectionActionsTypesResponse:
        """TypeScript declarations for the action catalog (every provider, or one with `provider`):
        `ConnectionActionCatalog[provider][action] = { input, output }`, generated from the same
        schemas Atlas validates with, plus `ConnectionActionInput` and `ConnectionActionOutput`
        helpers. Save `source` to a .ts file to type `connections.runAction` end to end.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connection_actions/types",
            query=_qd({'provider': provider}),
        )

    async def delete(
        self,
        provider: str,
        name: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a custom action definition (a first-party action of the same name comes back)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connection_actions/{_enc(provider)}/{_enc(name)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        provider: str,
        name: str,
    ) -> cm.GetConnectionActionsResponseDataItem:
        """One action with its input schema."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connection_actions/{_enc(provider)}/{_enc(name)}",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/connection_actions/{_enc(provider)}/{_enc(name)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncConnectionProviderChanges:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/connection_provider_changes",
            query=_qd({'provider': provider, 'status': status, 'kind': kind, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        provider: str | None = None,
        status: Literal['open', 'acknowledged', 'resolved', 'all'] | None = None,
        kind: Literal['output_drift', 'deprecation', 'endpoint_gone'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetConnectionProviderChangesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(provider=provider, status=status, kind=kind, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get(
        self,
        connection_provider_change_id: str,
    ) -> cm.GetConnectionProviderChangesResponseDataItem:
        """Read one provider change."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connection_provider_changes/{_enc(connection_provider_change_id)}",
        )

    async def acknowledge(
        self,
        connection_provider_change_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderChangesResponseDataItem:
        """Mark a change as seen. It stays listed under acknowledged and reopens only if you mark
        it resolved and it happens again.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/connection_provider_changes/{_enc(connection_provider_change_id)}/acknowledge",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def resolve(
        self,
        connection_provider_change_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderChangesResponseDataItem:
        """Mark a change as dealt with. If the provider does it again the change reopens."""
        return await self._t.request(
            method="POST",
            path=f"/v1/connection_provider_changes/{_enc(connection_provider_change_id)}/resolve",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncConnectionProviderEventLog:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/connection_provider_event_log",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'topic': topic, 'kind': kind}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
        topic: str | None = None,
        kind: Literal['lifecycle', 'business'] | None = None,
    ) -> AsyncIterator[cm.GetConnectionProviderEventLogResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, topic=topic, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncConnectionProviderTopics:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetConnectionProviderTopicsResponse:
        """The business topics this instance subscribes provider connections to (Shopify
        orders/create, products/update; eBay ItemSold and Commerce Notification topics).
        Deliveries of these topics arrive as connection.provider_event with kind business.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connection_provider_topics",
        )

    async def set(
        self,
        body: cm.PutConnectionProviderTopicsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionProviderTopicsResponse:
        """Replace the instance's business topics: { topics: { shopify: [...], ebay: [...],
        bigcommerce: [...], square: [...], etsy: [...], tiktok_shop: [...] } }, up to 50 per
        provider (or ["*"] to pass every topic the provider sends through as
        connection.provider_event with the raw payload), spelled as the provider spells them
        (Shopify orders/create; eBay Trading events such as ItemSold, or Commerce Notification
        topic ids in UPPER_SNAKE_CASE). Connections made afterwards subscribe automatically;
        call POST /v1/connections/{id}/provider_subscriptions/sync for existing ones. A topic
        not listed here is acknowledged and ignored on delivery.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/connection_provider_topics",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncConnectionProviders:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_policies(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionProvidersPoliciesResponse:
        """List every provider that has a stored instance policy, in the shape of the single-
        provider read (unique_external_id, whether a webhook secret or dev id is stored,
        events_url). Secrets are never returned.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connection_providers/policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_policies(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetConnectionProvidersPoliciesResponseDataItem]:
        """Every item of :meth:`list_policies`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_policies(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_policy(
        self,
        provider: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove the instance policy for a provider (back to the defaults)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connection_providers/{_enc(provider)}/policy",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_policy(
        self,
        provider: str,
    ) -> cm.GetConnectionProvidersByProviderPolicyResponse:
        """Read the instance policy for one provider's connections: unique_external_id, whether a
        webhook secret is stored, and the one ingress URL (events_url) for that provider's
        uninstall and revocation notices (shopify, bigcommerce, wix, square, ebay).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connection_providers/{_enc(provider)}/policy",
        )

    async def set_policy(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/connection_providers/{_enc(provider)}/policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncConnectionReconnectSettings:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetConnectionReconnectSettingsResponse:
        """The hosted-reconnect settings: whether Atlas emails the owner a reconnect link when a
        connection needs authorization again, how long the link works, where the browser returns
        afterwards and which providers send the email.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connection_reconnect_settings",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path="/v1/connection_reconnect_settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncConnectionTemplates:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionTemplatesResponse:
        """The marketplace connection templates (Discogs, Trade Me, BrickLink, Cardmarket,
        WooCommerce, Bonanza, Poizon, browser-session cookie jars, RSA-signed OAuth 1.0a): for
        each, the connection kind, whether the owner authorizes or you enter the secrets, which
        secret fields, the hosts to allow and the config to send. Read-only.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connection_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetConnectionTemplatesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncConnections:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def complete_oauth(
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
        return await self._t.request(
            method="POST",
            path="/v1/connections/oauth/complete",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def register_oauth_client(
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
        return await self._t.request(
            method="POST",
            path="/v1/connections/oauth_clients/register",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def rehome(
        self,
        body: cm.PostConnectionsRehomeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostConnectionsRehomeResponse:
        """Move OAuth connections from one owner client to another (a retired owner client you can
        now delete, two clients merged). Both clients must be the same provider and environment.
        When both are the same provider app (same client_id) every token stays valid and the
        rows simply move. Otherwise (verify, the default and the only allowed mode) one real
        refresh is made per connection with the TARGET client's credentials and only connections
        the provider accepts move; the others stay on the old client untouched and are reported
        failed with a reason (a failed probe changes no status). Token-family siblings move
        together. Dry run reports what would move without calling the provider. Never returns
        tokens. Idempotent on Idempotency-Key; audited as connection.rehomed (ids and counts).
        """
        return await self._t.request(
            method="POST",
            path="/v1/connections/rehome",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_relay_limits(
        self,
    ) -> cm.GetConnectionsRelayLimitsResponse:
        """The relay size limits of this instance: the largest request body and response body, in
        bytes. Defaults are 256 KiB and 1 MiB.
        """
        return await self._t.request(
            method="GET",
            path="/v1/connections/relay_limits",
        )

    async def set_relay_limits(
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
        return await self._t.request(
            method="PUT",
            path="/v1/connections/relay_limits",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_token_limits(
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
        return await self._t.request(
            method="GET",
            path="/v1/connections/token_limits",
        )

    async def set_token_limits(
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
        return await self._t.request(
            method="PUT",
            path="/v1/connections/token_limits",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_access_rules(
        self,
        connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove every access rule: the connection is open again."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connections/{_enc(connection_id)}/access_rules",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_access_rules(
        self,
        connection_id: str,
    ) -> cm.GetConnectionsByIdAccessRulesResponse:
        """Who may use this connection's credential. No rule means open to every key that has the
        route's scope; one rule or more restricts the connection to the principals the rules
        name.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/access_rules",
        )

    async def set_access_rules(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/connections/{_enc(connection_id)}/access_rules",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_actions(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionActionsResponse:
        """The actions available on a connection (its provider's catalog)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/actions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_actions(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetConnectionActionsResponseDataItem]:
        """Every item of :meth:`list_actions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_actions(connection_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_action(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/actions/{_enc(name)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_activity(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/activity",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'kind': kind, 'outcome': outcome, 'since': since}),
        )

    async def iter_list_activity(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        kind: Literal['relay', 'token_read', 'token_refresh', 'token_exchange', 'status', 'provider_event', 'reconnect_email', 'reconnect_started'] | None = None,
        outcome: Literal['ok', 'error'] | None = None,
        since: str | None = None,
    ) -> AsyncIterator[cm.GetConnectionsByIdActivityResponseDataItem]:
        """Every item of :meth:`list_activity`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_activity(connection_id, limit=limit, kind=kind, outcome=outcome, since=since, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_provider_events(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/provider_events",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'topic': topic, 'kind': kind}),
        )

    async def iter_list_provider_events(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        topic: str | None = None,
        kind: Literal['lifecycle', 'business'] | None = None,
    ) -> AsyncIterator[cm.GetConnectionProviderEventLogResponseDataItem]:
        """Every item of :meth:`list_provider_events`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_provider_events(connection_id, limit=limit, topic=topic, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_provider_event(
        self,
        connection_id: str,
        event_id: str,
    ) -> cm.GetConnectionProviderEventLogResponseDataItem:
        """One persisted provider event with its payload (business topics; absent when it was over
        256 KB).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/provider_events/{_enc(event_id)}",
        )

    async def replay_provider_event(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/provider_events/{_enc(event_id)}/replay",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_provider_subscriptions(
        self,
        connection_id: str,
    ) -> cm.GetConnectionsByIdProviderSubscriptionsResponse:
        """What was last subscribed at the provider for this connection, per topic, with the
        provider's own error when a subscription failed (for example Shopify refusing orders
        topics until the app is approved for protected customer data).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/provider_subscriptions",
        )

    async def sync_provider_subscription(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/provider_subscriptions/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def reconnect_link(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/reconnect_link",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_scoped_token(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/scoped_tokens",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def sign(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/sign",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def downscope_token(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/token/downscope",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def exchange_token(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/token/exchange",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def transfer(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/transfer",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_triggers(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetConnectionsByIdTriggersResponse:
        """The triggers of a connection."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/triggers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_triggers(
        self,
        connection_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetConnectionsByIdTriggersResponseDataItem]:
        """Every item of :meth:`list_triggers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_triggers(connection_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_trigger(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/connections/{_enc(connection_id)}/triggers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_trigger(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/connections/{_enc(connection_id)}/triggers/{_enc(trigger_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_trigger(
        self,
        connection_id: str,
        trigger_id: str,
    ) -> cm.GetConnectionsByIdTriggersResponseDataItem:
        """Read one trigger of a connection."""
        return await self._t.request(
            method="GET",
            path=f"/v1/connections/{_enc(connection_id)}/triggers/{_enc(trigger_id)}",
        )

    async def update_trigger(
        self,
        connection_id: str,
        trigger_id: str,
        body: cm.PatchConnectionsByIdTriggersByTriggerIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetConnectionsByIdTriggersResponseDataItem:
        """Pause or resume a trigger."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/connections/{_enc(connection_id)}/triggers/{_enc(trigger_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncContainments:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetContainmentsResponse:
        """Containment records, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/containments",
            query=_qd({'user_id': user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetContainmentsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(user_id=user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncCookieConsents:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/cookie_consents",
            query=_qd({'user_id': user_id, 'subject': subject, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        user_id: str | None = None,
        subject: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetCookieConsentsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(user_id=user_id, subject=subject, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_subject(
        self,
        subject: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteCookieConsentsSubjectsBySubjectResponse:
        """Erase one visitor's records (an erasure request from someone who is not a user).
        Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/cookie_consents/subjects/{_enc(subject)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_subject(
        self,
        subject: str,
    ) -> cm.GetCookieConsentsSubjectsBySubjectResponse:
        """One visitor's current choice and history. 404 when nothing is recorded."""
        return await self._t.request(
            method="GET",
            path=f"/v1/cookie_consents/subjects/{_enc(subject)}",
        )

    async def get_summary(
        self,
        *,
        days: int | None = None,
    ) -> cm.GetCookieConsentsSummaryResponse:
        """Choices recorded in the last days (default 30): distinct visitors, how many sent a
        Global Privacy Control signal, and how many allow each category.
        """
        return await self._t.request(
            method="GET",
            path="/v1/cookie_consents/summary",
            query=_qd({'days': days}),
        )


class AsyncDataSubjectRequests:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_downstream(
        self,
        data_subject_request_id: str,
    ) -> cm.GetDataSubjectRequestsByIdDownstreamResponse:
        """What each enabled downstream erasure connector has done for this request: pending, done
        (acknowledged by the system or marked by an operator) or not applicable. complete is
        true when every enabled connector is done or not applicable.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/downstream",
        )

    async def create_downstream(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/downstream/{_enc(connector_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def run_downstream(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/downstream/{_enc(connector_id)}/run",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def extend(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/extend",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_notes(
        self,
        data_subject_request_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDataSubjectRequestsByIdNotesResponse:
        """Internal notes on a request, oldest first. Never shown to the data subject."""
        return await self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/notes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_notes(
        self,
        data_subject_request_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDataSubjectRequestsByIdNotesResponseDataItem]:
        """Every item of :meth:`list_notes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_notes(data_subject_request_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_note(
        self,
        data_subject_request_id: str,
        body: cm.PostDataSubjectRequestsByIdNotesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDataSubjectRequestsByIdNotesResponseDataItem:
        """Add an internal note to a request (at most 4000 characters). Honours Idempotency-Key."""
        return await self._t.request(
            method="POST",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/notes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_receipt(
        self,
        data_subject_request_id: str,
    ) -> cm.GetDataSubjectRequestsByIdReceiptResponse:
        """The signed deletion receipt of a completed erasure: proof, signed with the instance key,
        that it ran. The claims carry ids and dates only (instance, request, subject id,
        requested/erased/scrub dates, steps, retention); verify the JWS in `receipt` with the
        keys at `jwks_uri`. Issued the first time it is asked for and stored, so asking again
        returns the same receipt. 409 for a request that is not a completed erasure.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/receipt",
        )

    async def update_triage(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/data_subject_requests/{_enc(data_subject_request_id)}/triage",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncDesktopMfa:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_devices_passkeys(
        self,
        device_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDesktopMfaDevicesByIdPasskeysResponse:
        """List the passkeys registered through a workstation."""
        return await self._t.request(
            method="GET",
            path=f"/v1/desktop_mfa/devices/{_enc(device_id)}/passkeys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_devices_passkeys(
        self,
        device_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDesktopMfaDevicesByIdPasskeysResponseDataItem]:
        """Every item of :meth:`list_devices_passkeys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_devices_passkeys(device_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_devices_passkey(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/desktop_mfa/devices/{_enc(device_id)}/passkeys/{_enc(passkey_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncDev:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def delete_emails(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDevEmailsResponse:
        """Empty the development email inbox (development instances only). Refused on a production
        instance (422 TEST_MODE_ONLY).
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/dev/emails",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_emails(
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
        return await self._t.request(
            method="GET",
            path="/v1/dev/emails",
            query=_qd({'to': to, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_emails(
        self,
        *,
        to: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDevEmailsResponseDataItem]:
        """Every item of :meth:`list_emails`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_emails(to=to, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncDeviceAssurancePolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDeviceAssurancePoliciesResponse:
        """List the device assurance policies."""
        return await self._t.request(
            method="GET",
            path="/v1/device_assurance_policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDeviceAssurancePoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/device_assurance_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def evaluate(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostDeviceAssurancePoliciesEvaluateResponse:
        """Re-evaluate every device against the current assurance policies."""
        return await self._t.request(
            method="POST",
            path="/v1/device_assurance_policies/evaluate",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        device_assurance_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDeviceAssurancePoliciesByIdResponse:
        """Delete a device assurance policy. Devices are re-evaluated."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/device_assurance_policies/{_enc(device_assurance_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        device_assurance_policy_id: str,
    ) -> cm.GetDeviceAssurancePoliciesResponseDataItem:
        """Read one device assurance policy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/device_assurance_policies/{_enc(device_assurance_policy_id)}",
        )

    async def update(
        self,
        device_assurance_policy_id: str,
        body: cm.PatchDeviceAssurancePoliciesByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceAssurancePoliciesResponseDataItem:
        """Update a device assurance policy. Devices are re-evaluated."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/device_assurance_policies/{_enc(device_assurance_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncDeviceIntegrations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDeviceIntegrationsResponse:
        """List the device pull integrations. Credentials are never returned."""
        return await self._t.request(
            method="GET",
            path="/v1/device_integrations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDeviceIntegrationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/device_integrations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        device_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDeviceIntegrationsByIdResponse:
        """Delete a device integration. Devices already pulled stay in the registry."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        device_integration_id: str,
    ) -> cm.GetDeviceIntegrationsResponseDataItem:
        """Read one device integration and its last sync result."""
        return await self._t.request(
            method="GET",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}",
        )

    async def update(
        self,
        device_integration_id: str,
        body: cm.PatchDeviceIntegrationsByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceIntegrationsResponseDataItem:
        """Change a device integration (name, config, credentials, interval, paused or active)."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def sync(
        self,
        device_integration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostDeviceIntegrationsByIdSyncResponse:
        """Pull the integration now."""
        return await self._t.request(
            method="POST",
            path=f"/v1/device_integrations/{_enc(device_integration_id)}/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncDeviceSso:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_registrations(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDeviceSsoRegistrationsResponse:
        """List devices registered for device-bound SSO, optionally for one `user_id`."""
        return await self._t.request(
            method="GET",
            path="/v1/device_sso/registrations",
            query=_qd({'user_id': user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_registrations(
        self,
        *,
        user_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDeviceSsoRegistrationsResponseDataItem]:
        """Every item of :meth:`list_registrations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_registrations(user_id=user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_registration(
        self,
        registration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteDeviceSsoRegistrationsByIdResponse:
        """Delete a device registration and its sessions."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/device_sso/registrations/{_enc(registration_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_registration(
        self,
        registration_id: str,
    ) -> cm.GetDeviceSsoRegistrationsResponseDataItem:
        """Read one device registration."""
        return await self._t.request(
            method="GET",
            path=f"/v1/device_sso/registrations/{_enc(registration_id)}",
        )

    async def revoke_registration(
        self,
        registration_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetDeviceSsoRegistrationsResponseDataItem:
        """Revoke a device registration. Every refresh token it holds stops working at once and its
        next call is refused.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/device_sso/registrations/{_enc(registration_id)}/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncDevices:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_compliance_history(
        self,
        device_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetDevicesByIdComplianceHistoryResponse:
        """The compliance transitions of one device, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/devices/{_enc(device_id)}/compliance_history",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_compliance_history(
        self,
        device_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDevicesByIdComplianceHistoryResponseDataItem]:
        """Every item of :meth:`list_compliance_history`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_compliance_history(device_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncDiagnostics:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_traces(
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
        return await self._t.request(
            method="GET",
            path="/v1/diagnostics/traces",
            query=_qd({'user_id': user_id, 'since': since, 'until': until, 'code': code, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_traces(
        self,
        *,
        user_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        code: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetDiagnosticsTracesResponseDataItem]:
        """Every item of :meth:`list_traces`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_traces(user_id=user_id, since=since, until=until, code=code, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_trace(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/diagnostics/traces/{_enc(trace_id)}",
        )


class AsyncDomains:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        domain_id: str,
    ) -> cm.CustomDomain:
        """Read one custom domain: the same object as a list item, including a path mount's
        verification file and what the last failed check observed.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/domains/{_enc(domain_id)}",
        )

    async def rotate_verification(
        self,
        domain_id: str,
        body: dict[str, Any],
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.CustomDomain:
        """Issue a new random verification token for a path-mounted domain and return the domain
        with the new `verification.token` and `url`. The previous token keeps verifying for 24
        hours (`verification.previous_url`, `previous_valid_until`). Use it when a CDN cache has
        stored a wrong answer for the old URL: the new URL has never been requested, so nothing
        is cached for it. A CNAME domain has no token (400).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/domains/{_enc(domain_id)}/verification/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncDsrConsole:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_requests(
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
        return await self._t.request(
            method="GET",
            path="/v1/dsr_console/requests",
            query=_qd({'status': status, 'type': type, 'assignee': assignee, 'unassigned': unassigned, 'priority': priority, 'label': label, 'overdue': overdue, 'due_within_days': due_within_days, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_requests(
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
    ) -> AsyncIterator[dict[str, Any]]:
        """Every item of :meth:`list_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_requests(status=status, type=type, assignee=assignee, unassigned=unassigned, priority=priority, label=label, overdue=overdue, due_within_days=due_within_days, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_summary(
        self,
    ) -> cm.GetDsrConsoleSummaryResponse:
        """The data rights board in one call: open, overdue, due within 7 days, unassigned, and
        counts by status, type and assignee.
        """
        return await self._t.request(
            method="GET",
            path="/v1/dsr_console/summary",
        )


class AsyncEntitlements:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def consume(
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
        return await self._t.request(
            method="POST",
            path="/v1/entitlements/consume",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def refund_consume(
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
        return await self._t.request(
            method="POST",
            path="/v1/entitlements/consume/refund",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncErasureConnectorCatalog:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetErasureConnectorCatalogResponse:
        """The catalog of downstream systems that commonly hold copies of an account's personal
        data (payments, email, SMS, analytics, support, CRM, storage, monitoring, warehouse),
        with how a copy is erased and what it usually holds.
        """
        return await self._t.request(
            method="GET",
            path="/v1/erasure_connector_catalog",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetErasureConnectorCatalogResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncErasureConnectors:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetErasureConnectorsResponse:
        """The downstream systems this application tracks for erasure."""
        return await self._t.request(
            method="GET",
            path="/v1/erasure_connectors",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetErasureConnectorsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/erasure_connectors",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        erasure_connector_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Stop tracking a downstream system. Past request records of it are removed with it. 204."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        erasure_connector_id: str,
    ) -> cm.GetErasureConnectorsResponseDataItem:
        """One erasure connector."""
        return await self._t.request(
            method="GET",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}",
        )

    async def update(
        self,
        erasure_connector_id: str,
        body: cm.PatchErasureConnectorsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetErasureConnectorsResponseDataItem:
        """Change a connector's name, mode, ack_source, enabled or notes. The key cannot change."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def probe(
        self,
        erasure_connector_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostErasureConnectorsByIdProbeResponse:
        """A read-only call to the vendor that proves the connector's saved key works. Nothing is
        deleted. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/erasure_connectors/{_enc(erasure_connector_id)}/probe",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncFederation:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetFederationResponse:
        """The OpenID Federation configuration of this instance: entity identifier, authority
        hints, trust anchors, subordinates and registration modes.
        """
        return await self._t.request(
            method="GET",
            path="/v1/federation",
        )

    async def resolve(
        self,
        body: cm.PostFederationResolveBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Resolve and validate the trust chain of an entity against the configured trust anchors
        and return the resolved metadata, or why the chain is invalid. Nothing is registered.
        """
        return await self._t.request(
            method="POST",
            path="/v1/federation/resolve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncFga:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def transform_model(
        self,
        body: cm.PostFgaModelsTransformBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Validate an authorization model and convert it: DSL (or modular DSL files) to canonical
        JSON, and JSON to DSL.
        """
        return await self._t.request(
            method="POST",
            path="/v1/fga/models/transform",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_settings(
        self,
    ) -> cm.FgaSettings:
        """How this instance runs fine-grained authorization reads: the result-cache TTL, the
        consistency mode applied to reads that name none, and how long the tuple change log is
        kept.
        """
        return await self._t.request(
            method="GET",
            path="/v1/fga/settings",
        )

    async def set_settings(
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
        return await self._t.request(
            method="PUT",
            path="/v1/fga/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def run_assertion_stores_authorization_models(
        self,
        store_id: str,
        mid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Run the stored assertions of a model version against the real store tuples."""
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/authorization-models/{_enc(mid)}/assertions/run",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_stores_authorization_models_diff(
        self,
        store_id: str,
        mid: str,
        *,
        against: str | None = None,
    ) -> dict[str, Any]:
        """What changed between a model version and the one before it (or `against`): types,
        relations, conditions, and whether the change can alter who has access.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/authorization-models/{_enc(mid)}/diff",
            query=_qd({'against': against}),
        )

    async def get_stores_authorization_models_graph(
        self,
        store_id: str,
        mid: str,
    ) -> dict[str, Any]:
        """The nodes and edges of an authorization model, for a visualizer."""
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/authorization-models/{_enc(mid)}/graph",
        )

    async def get_stores_export(
        self,
        store_id: str,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> str:
        """Export the store tuples as NDJSON (one tuple per line), paged: pass the `atlas-next-
        cursor` response header back as `cursor`.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/export",
            query=_qd({'cursor': cursor, 'limit': limit}),
        )

    async def import_store(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_stores_materializations(
        self,
        store_id: str,
    ) -> dict[str, Any]:
        """The materialized permission sets of a store: which (object type, relation, user type)
        answers are precomputed, their status, the revision they were built at and when a tuple
        expiry will next invalidate them.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations",
        )

    async def create_stores_materialization(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_stores_materialization(
        self,
        store_id: str,
        mid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Remove a materialization; list-objects is then always computed live."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations/{_enc(mid)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def rebuild_materialization_stores(
        self,
        store_id: str,
        mid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Rebuild one materialization now."""
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/materializations/{_enc(mid)}/rebuild",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_stores_snapshot(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/snapshot",
            query=_qd({'since': since, 'cursor': cursor, 'limit': limit}),
        )

    async def create_stores_test(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/fga/stores/{_enc(store_id)}/tests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_stores_watch(
        self,
        store_id: str,
        *,
        since: str | None = None,
        type: str | None = None,
    ) -> str:
        """Server-sent stream of the store tuple changes after `since` (or `Last-Event-ID`). Ends
        after about a minute; reconnect with the last event id.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/stores/{_enc(store_id)}/watch",
            query=_qd({'since': since, 'type': type}),
        )

    async def get_sync(
        self,
    ) -> cm.GetFgaSyncResponse:
        """The managed FGA sync: its settings, how many tuples it owns by kind, the backfill in
        flight and the last run. Needs an API key that is not limited to organizations.
        """
        return await self._t.request(
            method="GET",
            path="/v1/fga/sync",
        )

    async def set_sync(
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
        return await self._t.request(
            method="PUT",
            path="/v1/fga/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def backfill_sync(
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
        return await self._t.request(
            method="POST",
            path="/v1/fga/sync/backfill",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def purge_sync(
        self,
        body: cm.PostFgaSyncPurgeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostFgaSyncPurgeResponse:
        """Remove the tuples the sync wrote (never one that existed before it) and forget them. The
        sync must be disabled (409 otherwise). Send `confirm: true`.
        """
        return await self._t.request(
            method="POST",
            path="/v1/fga/sync/purge",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_sync_runs(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFgaSyncRunsResponse:
        """Sync runs, newest first: backfills, and the incremental passes that changed something."""
        return await self._t.request(
            method="GET",
            path="/v1/fga/sync/runs",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_sync_runs(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetFgaSyncResponseBackfill]:
        """Every item of :meth:`list_sync_runs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_sync_runs(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_sync_run(
        self,
        run_id: str,
    ) -> cm.GetFgaSyncResponseBackfill:
        """One sync run with its counts and any error."""
        return await self._t.request(
            method="GET",
            path=f"/v1/fga/sync/runs/{_enc(run_id)}",
        )

    async def create_test(
        self,
        body: cm.PostFgaStoresByIdTestsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Run an FGA test suite with no store: the model comes from `dsl` or `modules`. Returns
        per-test results and relation coverage. For CI.
        """
        return await self._t.request(
            method="POST",
            path="/v1/fga/tests",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncFlows:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_experiments(
        self,
        flow_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFlowsByIdExperimentsResponse:
        """A journey's A/B experiments, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/experiments",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_experiments(
        self,
        flow_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetFlowsByIdExperimentsResponseDataItem]:
        """Every item of :meth:`list_experiments`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_experiments(flow_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_experiment(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/experiments",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_experiment(
        self,
        flow_id: str,
        experiment_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a draft or stopped experiment and its assignments. Stop a running one first."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_experiment(
        self,
        flow_id: str,
        experiment_id: str,
    ) -> cm.GetFlowsByIdExperimentsResponseDataItem:
        """Get one journey experiment with its variants and results."""
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}",
        )

    async def update_experiment(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_experiments_readout(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}/readout",
        )

    async def start_experiment(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}/start",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def stop_experiment(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/experiments/{_enc(experiment_id)}/stop",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_messages(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/messages",
            query=_qd({'status': status, 'user_id': user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_messages(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        user_id: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetFlowsByIdMessagesResponseDataItem]:
        """Every item of :meth:`list_messages`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_messages(flow_id, status=status, user_id=user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def cancel_message(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/flows/{_enc(flow_id)}/messages/{_enc(message_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_runs(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/flows/{_enc(flow_id)}/runs",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_runs(
        self,
        flow_id: str,
        *,
        status: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetFlowsByIdRunsResponseDataItem]:
        """Every item of :meth:`list_runs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_runs(flow_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncFraud:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def email_risk(
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
        return await self._t.request(
            method="POST",
            path="/v1/fraud/email_risk",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_email_risk_settings(
        self,
    ) -> cm.GetFraudEmailRiskSettingsResponse:
        """Email risk settings: mode, provider, blocking policy and the sign-up gate."""
        return await self._t.request(
            method="GET",
            path="/v1/fraud/email_risk/settings",
        )

    async def set_email_risk_settings(
        self,
        body: cm.PutFraudEmailRiskSettingsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetFraudEmailRiskSettingsResponse:
        """Change email risk settings. `mode`: off, mx or provider (your own verification account;
        the key is write-only). With `gate_sign_up` a `block` verdict refuses the sign-up.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/fraud/email_risk/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncGrants:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        user_id: str | None = None,
        client_id: str | None = None,
        type: Literal['consent', 'managed', 'all'] | None = None,
        status: Literal['active', 'revoked', 'all'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetGrantsResponse:
        """List every grant in one cursor-paged list: users' consent grants and OpenID Grant
        Management grants, told apart by `type`. Filter by `user_id`, `client_id` (the public
        client id), `type` (consent, managed, all) and `status` (active by default; revoking a
        consent removes it, so revoked grants are managed ones).
        """
        return await self._t.request(
            method="GET",
            path="/v1/grants",
            query=_qd({'user_id': user_id, 'client_id': client_id, 'type': type, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        user_id: str | None = None,
        client_id: str | None = None,
        type: Literal['consent', 'managed', 'all'] | None = None,
        status: Literal['active', 'revoked', 'all'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetGrantsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(user_id=user_id, client_id=client_id, type=type, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def consume(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/consume",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def release_lease(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/leases/{_enc(lease_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def refund(
        self,
        grant_type: str,
        grant_id: str,
        body: cm.PostGrantsByGrantTypeByIdRefundBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostGrantsByGrantTypeByIdRefundResponse:
        """Give back all or part of one earlier consume. Never more than that consume took."""
        return await self._t.request(
            method="POST",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/refund",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_usage(
        self,
        grant_type: str,
        grant_id: str,
    ) -> cm.GetGrantsByGrantTypeByIdUsageResponse:
        """The current window of every counter a grant defines, and the leases still holding an
        amount.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/grants/{_enc(grant_type)}/{_enc(grant_id)}/usage",
        )

    async def get(
        self,
        grant_id: str,
    ) -> cm.GetGrantsResponseDataItem:
        """Read one grant of either kind, with its metadata."""
        return await self._t.request(
            method="GET",
            path=f"/v1/grants/{_enc(grant_id)}",
        )

    async def update(
        self,
        grant_id: str,
        body: cm.PatchGrantsByIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetGrantsResponseDataItem:
        """Change a grant's `metadata` (secret key only). The keys you send are merged into what is
        stored: a key sent as null is removed. The result is at most 4 KB of JSON. Audited;
        idempotent.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/grants/{_enc(grant_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncIga:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_activations(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaActivationsResponse:
        """The activation history, newest first, with each activation's live status."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/activations",
            query=_qd({'user_id': user_id, 'entitlement': entitlement, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_activations(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetIgaActivationsResponseDataItem]:
        """Every item of :meth:`list_activations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_activations(user_id=user_id, entitlement=entitlement, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_activation(
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
        return await self._t.request(
            method="POST",
            path="/v1/iga/activations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def end_activation(
        self,
        activation_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaActivationsResponseDataItem:
        """End an activation now: closes the grant, or cancels the pending approval."""
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/activations/{_enc(activation_id)}/end",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_bundles(
        self,
        *,
        catalog: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaBundlesResponse:
        """List access bundles (packages of entitlements requested together)."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/bundles",
            query=_qd({'catalog': catalog, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_bundles(
        self,
        *,
        catalog: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetIgaBundlesResponseDataItem]:
        """Every item of :meth:`list_bundles`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_bundles(catalog=catalog, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_bundle(
        self,
        body: cm.PostIgaBundlesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaBundlesResponseDataItem:
        """Create a bundle: several catalog entitlements, request form fields, and a policy (who
        may ask, guest expiry).
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/bundles",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_bundle(
        self,
        bundle_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteIgaBundlesByIdResponse:
        """Delete a bundle (access already granted stays)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_bundle(
        self,
        bundle_id: str,
    ) -> cm.GetIgaBundlesResponseDataItem:
        """Read one bundle by id or key."""
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}",
        )

    async def update_bundle(
        self,
        bundle_id: str,
        body: cm.PatchIgaBundlesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaBundlesResponseDataItem:
        """Change an access bundle, its entitlements, form fields or policy."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def request_bundle(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/bundles/{_enc(bundle_id)}/request",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_campaign_templates(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaCampaignTemplatesResponse:
        """Ready-made access reviews: inactive users, guest and contractor access, and a quarterly
        two-stage review.
        """
        return await self._t.request(
            method="GET",
            path="/v1/iga/campaign_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_campaign_templates(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetIgaCampaignTemplatesResponseDataItem]:
        """Every item of :meth:`list_campaign_templates`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_campaign_templates(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def from_template_campaign(
        self,
        body: cm.PostIgaCampaignsFromTemplateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaCampaignsResponseDataItem:
        """Create a campaign from a template. `parameters` fill the template (inactive_days;
        company_domains).
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/campaigns/from_template",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_campaigns_recommendations(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/iga/campaigns/{_enc(campaign_id)}/recommendations",
            query=_qd({'reviewer_user_id': reviewer_user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_campaigns_recommendations(
        self,
        campaign_id: str,
        *,
        reviewer_user_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetIgaCampaignsByIdRecommendationsResponseDataItem]:
        """Every item of :meth:`list_campaigns_recommendations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_campaigns_recommendations(campaign_id, reviewer_user_id=reviewer_user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def run_now_campaign(
        self,
        campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaCampaignsResponseDataItem:
        """Start a copy of a recurring campaign now, outside its schedule."""
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/campaigns/{_enc(campaign_id)}/run_now",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def stop_recurrence_campaign(
        self,
        campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaCampaignsResponseDataItem:
        """Stop a recurring campaign. Copies already started are unaffected."""
        return await self._t.request(
            method="POST",
            path=f"/v1/iga/campaigns/{_enc(campaign_id)}/stop_recurrence",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_eligibilities(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetIgaEligibilitiesResponse:
        """People who may activate an entitlement (eligible assignments)."""
        return await self._t.request(
            method="GET",
            path="/v1/iga/eligibilities",
            query=_qd({'user_id': user_id, 'entitlement': entitlement, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_eligibilities(
        self,
        *,
        user_id: str | None = None,
        entitlement: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetIgaEligibilitiesResponseDataItem]:
        """Every item of :meth:`list_eligibilities`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_eligibilities(user_id=user_id, entitlement=entitlement, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_eligibility(
        self,
        body: cm.PostIgaEligibilitiesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetIgaEligibilitiesResponseDataItem:
        """Make a person eligible for an entitlement: they hold nothing until they activate it. The
        entitlement needs `activation_rules`. `expires_at` ends the eligibility.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/eligibilities",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_eligibility(
        self,
        eligibility_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteIgaEligibilitiesByIdResponse:
        """Remove an eligibility. Access already activated stays until it ends."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/iga/eligibilities/{_enc(eligibility_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def import_entitlement(
        self,
        body: cm.PostIgaEntitlementsImportBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostIgaEntitlementsImportResponse:
        """Add catalog entitlements (not requestable, no approval steps) for the groups or app
        roles that exist but are not in the catalog yet.
        """
        return await self._t.request(
            method="POST",
            path="/v1/iga/entitlements/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncImpersonations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/impersonations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetImpersonationsRequestsResponse:
        """List impersonation requests held for approval, newest first. `status`: pending,
        approved, denied or expired.
        """
        return await self._t.request(
            method="GET",
            path="/v1/impersonations/requests",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_requests(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetImpersonationsRequestsResponseDataItem]:
        """Every item of :meth:`list_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_requests(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_request(
        self,
        request_id: str,
    ) -> cm.GetImpersonationsRequestsResponseDataItem:
        """Read one impersonation request: its status, who asked, who decided, and when it expires."""
        return await self._t.request(
            method="GET",
            path=f"/v1/impersonations/requests/{_enc(request_id)}",
        )

    async def approve_request(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/impersonations/requests/{_enc(request_id)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def deny_request(
        self,
        request_id: str,
        body: cm.PostImpersonationsRequestsByIdApproveBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Deny a pending impersonation as a second staff member. Audited; no session is created."""
        return await self._t.request(
            method="POST",
            path=f"/v1/impersonations/requests/{_enc(request_id)}/deny",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def end(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/impersonations/{_enc(impersonation_id)}/end",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncInstance:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_app_event_types(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationsByIdAppEventTypesResponse:
        """The event types third-party apps can subscribe to, each with the scope a user must have
        granted the app.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/app_event_types",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_app_event_types(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOrganizationsByIdAppEventTypesResponseDataItem]:
        """Every item of :meth:`list_app_event_types`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_app_event_types(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def set_app_event_types(
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
        return await self._t.request(
            method="PUT",
            path="/v1/instance/app_event_types",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_config_snapshots(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        source: Literal['manual', 'auto', 'pre_restore', 'cli', 'clone'] | None = None,
    ) -> cm.GetInstanceConfigSnapshotsResponse:
        """The configuration snapshots of the instance, newest first. Filter by source: manual,
        auto, pre_restore (saved before a restore), cli, clone.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/config_snapshots",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'source': source}),
        )

    async def iter_list_config_snapshots(
        self,
        *,
        limit: int | None = None,
        source: Literal['manual', 'auto', 'pre_restore', 'cli', 'clone'] | None = None,
    ) -> AsyncIterator[cm.GetInstanceConfigSnapshotsResponseDataItem]:
        """Every item of :meth:`list_config_snapshots`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_config_snapshots(limit=limit, source=source, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_config_snapshot(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/config_snapshots",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_config_snapshots_diff(
        self,
        *,
        from_: str,
        to: str | None = None,
    ) -> cm.GetInstanceConfigSnapshotsDiffResponse:
        """What changed between two configurations, as a list of paths with the value before and
        after. `from` and `to` are snapshot ids, or `current` for the live configuration (to
        defaults to current). Secrets never appear; allowed origins are reported separately.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/config_snapshots/diff",
            query=_qd({'from': from_, 'to': to}),
        )

    async def delete_config_snapshot(
        self,
        config_snapshot_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceConfigSnapshotsByIdResponse:
        """Delete one snapshot. Audited."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/instance/config_snapshots/{_enc(config_snapshot_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_config_snapshot(
        self,
        config_snapshot_id: str,
    ) -> cm.GetInstanceConfigSnapshotsResponseDataItem:
        """One snapshot with its configuration (auth_config and allowed_origins). Secrets are never
        in it.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/config_snapshots/{_enc(config_snapshot_id)}",
        )

    async def restore_config_snapshot(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/config_snapshots/{_enc(config_snapshot_id)}/restore",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update_cookie_consent(
        self,
        body: cm.PatchInstanceCookieConsentBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutInstanceCookieConsentResponse:
        """Change part of the cookie-consent setting: the fields sent are merged over the stored
        setting and the rest is kept (PUT replaces the whole setting). `null` clears a field;
        sending site_id drops a stored site reference and the other way round. With no stored
        setting, script_url is required. The answer and warnings are those of PUT.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/instance/cookie_consent",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_data_key_provider(
        self,
        body: cm.DeleteInstanceDataKeyProviderBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Remove customer-managed encryption by deleting the wrapped data keys. This crypto-shreds
        everything encrypted under them and cannot be undone; send { "confirm": "shred" }.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/data_key_provider",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_data_key_provider(
        self,
    ) -> dict[str, Any]:
        """Customer-managed encryption status: whether it is on, the key provider, the data key
        versions, the last health check and how long a revoked key keeps working before Atlas
        fails closed.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/data_key_provider",
        )

    async def data_key_provider(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_data_key_provider(
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
        return await self._t.request(
            method="PUT",
            path="/v1/instance/data_key_provider",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def check_data_key_provider(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Check the customer key now: wrap and unwrap a random key through it and open the current
        data keys. `reason` names a failure: key_disabled, key_not_found, access_denied,
        unreachable or invalid_config.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/check",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def rewrap_data_key_provider(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/rewrap",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def rotate_data_key_provider(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Create a new data key version. New data uses it; earlier versions stay until a re-
        encryption sweep reports none left on them.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def rotation_drill_data_key_provider(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/data_key_provider/rotation_drill",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_data_key_provider_rotation_drills(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceDataKeyProviderRotationDrillsResponse:
        """The last 20 rotation drills, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/data_key_provider/rotation_drills",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_data_key_provider_rotation_drills(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.PostInstanceDataKeyProviderRotationDrillResponse]:
        """Every item of :meth:`list_data_key_provider_rotation_drills`, following the cursor page
        by page.
        """
        cursor: str | None = None
        while True:
            page = await self.list_data_key_provider_rotation_drills(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_data_key_provider_rotation_drill(
        self,
        rotation_drill_id: str,
    ) -> cm.PostInstanceDataKeyProviderRotationDrillResponse:
        """Read one key rotation drill: its outcome and what it checked."""
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/data_key_provider/rotation_drills/{_enc(rotation_drill_id)}",
        )

    async def list_deprecations(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceDeprecationsResponse:
        """The deprecation list, each entry saying whether this instance still calls the deprecated
        route or sends the deprecated field (`in_use`, `first_seen_at`).
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/deprecations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_deprecations(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceDeprecationsResponseDataItem]:
        """Every item of :meth:`list_deprecations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_deprecations(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_exports(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceExportsResponse:
        """The tenant exports of the instance, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/exports",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_exports(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceExportsResponseDataItem]:
        """Every item of :meth:`list_exports`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_exports(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_export(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/exports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_export(
        self,
        export_id: str,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """One export: status, row counts per section, the bundle digest and signature. The bundle
        itself is not in this body.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/exports/{_enc(export_id)}",
        )

    async def get_exports_bundle(
        self,
        export_id: str,
    ) -> dict[str, Any]:
        """Download the bundle (canonical JSON: keys sorted, so its SHA-256 holds for the bytes you
        receive). Headers x-atlas-bundle-sha256 and x-atlas-bundle-signature carry the digest
        and the JWS. Needs instance:read and users:read; audited. 409 until the export finished,
        and after it expired.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/exports/{_enc(export_id)}/bundle",
        )

    async def download_url_export(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/exports/{_enc(export_id)}/download_url",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def create_exports_revoke_link(
        self,
        export_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """Invalidate every signed download link handed out for this export."""
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/exports/{_enc(export_id)}/revoke_links",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def delete_hooks_before_first_session(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceHooksBeforeFirstSessionResponse:
        """Turn the hook off and clear its url and signing secret, the same as PATCH with
        {enabled:false, url:null, signing_secret:null}. Audited. Idempotent.
        """
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/hooks/before_first_session",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_hooks_before_first_session(
        self,
    ) -> cm.DeleteInstanceHooksBeforeFirstSessionResponse:
        """Read the before_first_session hook: the endpoint Atlas calls once per user, after their
        email is verified and before their first session token, so your app can link the account
        and stamp its own external_id on that very token. The signing secret is reported as
        signing_secret_set only.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/hooks/before_first_session",
        )

    async def update_hooks_before_first_session(
        self,
        body: cm.PatchInstanceHooksBeforeFirstSessionBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceHooksBeforeFirstSessionResponse:
        """Update the before_first_session hook. Only the fields you send change; null clears.
        Atlas POSTs {"type":"before_first_session","data":{user_id,email,email_verified,provider
        ,provider_user_id,name,external_id}} signed like a webhook (atlas-id, atlas-timestamp,
        atlas-signature). Answer 200 {"external_id":"…"} to set it: it is stored only when the
        user has none and no other user holds it (never overwritten). A timeout or failure never
        blocks the sign-in (it is audited and counted in failed_calls). Not called for
        impersonation or anonymous guests.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/instance/hooks/before_first_session",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test_before_first_session_hooks(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstanceHooksBeforeFirstSessionTestResponse:
        """Send a signed sample call (a user that does not exist) to the hook and report its
        answer. Nothing is stored on any user.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/hooks/before_first_session/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def create_hosted_method_filter(
        self,
        body: cm.PostInstanceHostedMethodFiltersBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstanceHostedMethodFiltersResponse:
        """Limit a hosted sign-in or sign-up page to some sign-in methods. Send the methods
        (`password`, `email_code`, `email_link`, `phone_code`, `passkey`, `username` counts as
        `password`, a family such as `oauth` or `enterprise_sso`, or one provider such as
        `oauth_google`). The answer carries `allowed_methods` and `allowed_methods_sig`: add
        both to the page URL (`query` is them ready to append). The page then offers only those
        methods, and every sign-in or sign-up attempt the page (or a client sending the `token`
        in `X-Atlas-Allowed-Methods`) starts is bound to the list, and a session is refused with
        403 SIGN_IN_METHOD_NOT_ALLOWED for any method outside it, whichever way the attempt
        completes (passkey, a ticket exchanged by your app, a native code). A list that is
        missing its signature or was edited is refused with 400. It narrows what the instance
        and the OAuth client already allow; it never adds a method.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/hosted_method_filters",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_impersonation_policy(
        self,
    ) -> cm.GetInstanceImpersonationPolicyResponse:
        """The instance's staff impersonation policy: require_reason, reason_codes,
        max_duration_seconds, require_approval, read_only_default and notify_user.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/impersonation_policy",
        )

    async def set_impersonation_policy(
        self,
        body: cm.PutInstanceImpersonationPolicyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Change the staff impersonation policy. Send only the fields to change; unknown fields
        are refused. Audited.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/impersonation_policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_imports(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceExportsResponse:
        """The tenant imports of the instance, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/imports",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_imports(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceExportsResponseDataItem]:
        """Every item of :meth:`list_imports`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_imports(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_import(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/imports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_import(
        self,
        import_id: str,
    ) -> cm.GetInstanceExportsResponseDataItem:
        """One import: status, what was created / already existed / failed per section, and what
        could not be placed.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/imports/{_enc(import_id)}",
        )

    async def delete_integrations_forwarding(
        self,
        destination: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Stop forwarding sign-ups to a destination (removes its managed endpoint)."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/instance/integrations/forwarding/{_enc(destination)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_integrations_forwarding(
        self,
        destination: str,
    ) -> cm.GetInstanceIntegrationsForwardingByDestinationResponse:
        """Read the stored sign-up forwarding for a destination: its managed endpoint, active flag
        and non-secret settings. The destination key is never returned. 404 when sign-ups are
        not forwarded there.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/integrations/forwarding/{_enc(destination)}",
        )

    async def set_integrations_forwarding(
        self,
        destination: str,
        body: cm.PutInstanceIntegrationsForwardingByDestinationBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutInstanceIntegrationsForwardingByDestinationResponse:
        """Forward every sign-up (`user.created`) to Lucida, Hermetica or Seolyticize with your own
        server key, or to any HTTPS webhook.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/instance/integrations/forwarding/{_enc(destination)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_integrations_health(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceIntegrationsHealthResponse:
        """Every connected integration and receiver with its last delivery status and time, in one
        list.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/integrations/health",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_integrations_health(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceIntegrationsHealthResponseDataItem]:
        """Every item of :meth:`list_integrations_health`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_integrations_health(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_integrations_mints(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/integrations/{_enc(product)}/mints",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_integrations_mints(
        self,
        product: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceIntegrationsByProductMintsResponseDataItem]:
        """Every item of :meth:`list_integrations_mints`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_integrations_mints(product, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def test_integration(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/integrations/{_enc(product)}/test",
            query=_qd({'wait': wait, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_issuers(
        self,
    ) -> cm.GetInstanceIssuersResponse:
        """The token issuers a verifier should accept: the active one, the planned one while a
        domain claim is pending, and earlier ones still in their overlap window.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/issuers",
        )

    async def list_op_keys(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceOpKeysResponse:
        """The OpenID provider keys beyond the instance signing key: PS256, ES384 and EdDSA signing
        keys and the RSA-OAEP-256 / ECDH-ES keys request objects are encrypted to, with their
        status.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/op_keys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_op_keys(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceOpKeysResponseDataItem]:
        """Every item of :meth:`list_op_keys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_op_keys(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def rotate_op_key(
        self,
        body: cm.PostInstanceOpKeysRotateBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Rotate the key of one algorithm (`alg`). The previous public key stays published for
        `grace_period_seconds` (default 24 h) so tokens it signed keep verifying.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/op_keys/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_org_departure_policy(
        self,
    ) -> cm.GetInstanceOrgDeparturePolicyResponse:
        """What happens to the organization connections a departing member authorized: oldest_admin
        (default), a fixed user, or none.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/org_departure_policy",
        )

    async def set_org_departure_policy(
        self,
        body: cm.PutInstanceOrgDeparturePolicyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Set the departure policy. `transfer_to`: oldest_admin, user (needs `user_id`, who must
        still be a member) or none.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/org_departure_policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_org_role_entitlements(
        self,
    ) -> cm.GetInstanceOrgRoleEntitlementsResponse:
        """The map of organization role key to the feature keys a seat in that role grants. Those
        features join the token's `fea` claim for a member whose active organization role
        matches, on top of (or without) a plan.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/org_role_entitlements",
        )

    async def set_org_role_entitlements(
        self,
        body: cm.PutInstanceOrgRoleEntitlementsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Replace the role to features map. A role left out grants nothing. Takes effect on the
        next token.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/org_role_entitlements",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_preflight_ack(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/preflight/acks",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_privacy_orchestrator_cases(
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
        return await self._t.request(
            method="GET",
            path="/v1/instance/privacy_orchestrator/cases",
            query=_qd({'status': status, 'dismissed': dismissed, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_privacy_orchestrator_cases(
        self,
        *,
        status: Literal['open', 'pending', 'failed', 'cancelled', 'cancel_pending', 'abandoned'] | None = None,
        dismissed: bool | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstancePrivacyOrchestratorCasesResponseDataItem]:
        """Every item of :meth:`list_privacy_orchestrator_cases`, following the cursor page by
        page.
        """
        cursor: str | None = None
        while True:
            page = await self.list_privacy_orchestrator_cases(status=status, dismissed=dismissed, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def dismiss_case_privacy_orchestrator(
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
        return await self._t.request(
            method="POST",
            path="/v1/instance/privacy_orchestrator/cases/dismiss",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def dismiss_case_privacy_orchestrator_2(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/privacy_orchestrator/cases/{_enc(case_id)}/dismiss",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def retry_case_privacy_orchestrator(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/privacy_orchestrator/cases/{_enc(case_id)}/retry",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_scopes(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetInstanceScopesResponse:
        """The scope catalogue: the scopes your product defines, with consent-screen text per
        locale, `sensitive` and `requires_verified_client`.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/scopes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_scopes(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetInstanceScopesResponseDataItem]:
        """Every item of :meth:`list_scopes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_scopes(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def set_scopes(
        self,
        body: cm.PutInstanceScopesBody,
        *,
        mode: str | None = None,
        too_long: str | None = None,
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
        allowed scopes to request it. `requires_client_level` (`any`, `verified` or `certified`)
        sets the level a client needs (`requires_verified_client: true` means `verified`; the
        stricter wins); a `certified` client is an approved one the instance has certified
        (PATCH /v1/oauth_clients/{id} `certified`). `optional: true` lets the user untick the
        scope on the consent screen (the token then carries only the scopes they kept).
        `owner_exempt: true` lets the developer who owns a client request the scope with it on
        their own account whatever the client's level. A name ending `:*` (`listings:*`) is a
        wildcard entry: it covers every `listings:<anything>` for gating, consent text and
        released claims, and a client or grant that holds `listings:*` holds each of them. By
        default the whole list is checked and nothing is written if any entry is bad (422, one
        problem per field). `?mode=partial` applies the valid entries and answers 200 with
        `rejected: [{ index, name, errors }]` (a rejected entry leaves the scope of that name as
        it was). `?too_long=truncate` cuts over-long labels and descriptions instead of refusing
        them and lists each cut in `warnings`.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/scopes",
            query=_qd({'mode': mode, 'too_long': too_long, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_secret_keys(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSecretKeysResponse:
        """Alias of GET /v1/secret_keys. List this instance's secret keys with scopes, owner,
        expiry, last use, last-used IP and provisioning tags. Revoked keys stay listed. Filter
        by tag with ?metadata[key]=value.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/secret_keys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_secret_keys(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetSecretKeysResponseDataItem]:
        """Every item of :meth:`list_secret_keys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_secret_keys(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_secret_key(
        self,
        body: cm.PostSecretKeysBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetSecretKeysResponseDataItem:
        """Alias of POST /v1/secret_keys. Create a scoped secret key: `name`, `scopes[]` (refused
        when unknown, or when the calling key does not hold them; presets `read_only`,
        `privacy:execute`, `privacy:grants:revoke`; or `preset: "app-runtime"` for an app server
        runtime key, or `preset: "integrations"` for the key a connected platform (consent
        manager, referral or support platform) connects with, or `preset: "provisioning"` for a
        deploy-script key that configures the instance: instance settings, domains, messaging
        providers, integrations, webhooks, OAuth clients and providers, redirect URLs, branding
        and keys, with no user, session or organization-member access), `expires_at` (at most a
        year; default one year; "never" is refused), `allowed_ips` (CIDRs), `allowed_origins`
        (browser origins; a request with another Origin gets 403 ORIGIN_NOT_ALLOWED), `owner`
        (default: the creating person or key), `external_ref` (idempotent create: a repeat
        returns the existing key, 200, idempotent_replay, no secret), `metadata` (tags; filter
        the list with ?metadata[key]=value) and `key_format` (`atlas`, the default
        `atlas_<env>_sk_…`, or `legacy` `sk_<env>_…`). The secret is returned once. Minting with
        an operator token needs multi-factor sign-in within 5 minutes (403 STEP_UP_REQUIRED).
        Send `X-Secret-Recipient: x25519:<public key>` to receive the secret sealed (libsodium
        sealed box) as `sealed_secret` instead of in plaintext. Example: a data-rights tool's
        key, { "name": "DSAR executor", "scopes": ["privacy:execute", "privacy:grants:revoke"],
        "expires_at": "2027-04-01" }.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/secret_keys",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_signing_key_schedule(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceSigningKeyScheduleResponse:
        """Turn scheduled rotation off. Keys already published stay as they are."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/signing_key_schedule",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_signing_key_schedule(
        self,
    ) -> cm.GetInstanceSigningKeyScheduleResponse:
        """Read the signing-key rotation schedule."""
        return await self._t.request(
            method="GET",
            path="/v1/instance/signing_key_schedule",
        )

    async def set_signing_key_schedule(
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
        return await self._t.request(
            method="PUT",
            path="/v1/instance/signing_key_schedule",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_staging_copies(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        kind: Literal['clone', 'preview'] | None = None,
    ) -> cm.GetInstanceStagingCopiesResponse:
        """The staging copies and previews of this instance, newest first (deleted ones are left
        out).
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/staging_copies",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'kind': kind}),
        )

    async def iter_list_staging_copies(
        self,
        *,
        limit: int | None = None,
        kind: Literal['clone', 'preview'] | None = None,
    ) -> AsyncIterator[cm.GetInstanceStagingCopiesResponseDataItem]:
        """Every item of :meth:`list_staging_copies`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_staging_copies(limit=limit, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_staging_copy(
        self,
        body: cm.PostInstanceStagingCopiesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostInstanceStagingCopiesResponse:
        """Make a staging copy of this instance with its own secret key: a new development-mode
        instance of the same app, with or without data (same body and rules as the platform
        clone route, without secret_key_preset: the key it answers with holds the app-runtime
        preset). For an instance that is not provisioned under a platform app. The copy never
        carries secrets (configuration secrets are removed; API keys and provider connections
        are not copied), private metadata of users and organizations, webhook endpoints, signing
        keys, passwords or second factors. The new instance is in development mode: no email or
        SMS is sent until it has its own provider keys. Needs instance:write (and users:read
        when include has users). Honours Idempotency-Key; a repeat for a live ref returns it
        (200, no secret). Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/instance/staging_copies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_staging_copy(
        self,
        staging_copy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceStagingCopiesResponseDataItem:
        """Delete a staging copy together with its instance and everything in it. Only an instance
        a copy created can be removed this way. Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/instance/staging_copies/{_enc(staging_copy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_staging_copy(
        self,
        staging_copy_id: str,
    ) -> cm.GetInstanceStagingCopiesResponseDataItem:
        """One staging copy: status, what was copied, what could not be placed."""
        return await self._t.request(
            method="GET",
            path=f"/v1/instance/staging_copies/{_enc(staging_copy_id)}",
        )

    async def refresh_staging_copy(
        self,
        staging_copy_id: str,
        body: cm.PostInstanceStagingCopiesByIdRefreshBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetInstanceStagingCopiesResponseDataItem:
        """Bring a completed staging copy up to date in place: the same instance, keys and host,
        with this instance's configuration merged in again (and the data sections asked for, at
        most the ones it was made with, up to 2000 rows each). synthetic_users { count (1-500),
        seed } adds seeded test users (example.com addresses, the same seed gives the same
        users, so repeating it adds none twice). ttl_hours extends a preview. Emails stay masked
        consistently, so a refresh does not duplicate users. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/instance/staging_copies/{_enc(staging_copy_id)}/refresh",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_user_traits_schema(
        self,
    ) -> cm.UserTraitsSchema:
        """The instance user traits schema: a JSON Schema per metadata bag (public, unsafe and
        private user metadata; public and private organization metadata) and how strictly it
        applies. enforcement is off (the default and what an instance without a schema reports),
        warn or enforce. version is 0 until a schema is stored, then counts up on every change.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/user_traits_schema",
        )

    async def set_user_traits_schema(
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
        return await self._t.request(
            method="PUT",
            path="/v1/instance/user_traits_schema",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_write_budget(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceWriteBudgetResponse:
        """Back to the platform defaults in observe mode."""
        return await self._t.request(
            method="DELETE",
            path="/v1/instance/write_budget",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_write_budget(
        self,
    ) -> cm.DeleteInstanceWriteBudgetResponse:
        """The instance write budgets: writes (mutating Backend API requests), counter_writes
        (grant consume, refund and lease release), events and webhook_fanout, each per 60-second
        window, the mode (observe or enforce), and when a budget was last exceeded.
        """
        return await self._t.request(
            method="GET",
            path="/v1/instance/write_budget",
        )

    async def set_write_budget(
        self,
        body: cm.PutInstanceWriteBudgetBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteInstanceWriteBudgetResponse:
        """Set the write-budget mode and any limit. A limit is an integer from 1 to 10,000,000 per
        minute; null returns one to its default. Unknown fields are refused.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/instance/write_budget",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncLegalHolds:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetLegalHoldsResponse:
        """Every active legal hold of the instance, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/legal_holds",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetLegalHoldsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncLocalizations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def check(
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
        return await self._t.request(
            method="POST",
            path="/v1/localizations/check",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_review_summary(
        self,
    ) -> cm.GetLocalizationsReviewSummaryResponse:
        """Translations per review status, the review queue (in review and changes requested), and
        approved translations whose text changed after approval.
        """
        return await self._t.request(
            method="GET",
            path="/v1/localizations/review_summary",
        )

    async def review(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/localizations/{_enc(localization_id)}/review",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_reviews(
        self,
        localization_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetLocalizationsByIdReviewsResponse:
        """The review decisions on a translation, newest first."""
        return await self._t.request(
            method="GET",
            path=f"/v1/localizations/{_enc(localization_id)}/reviews",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_reviews(
        self,
        localization_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetLocalizationsByIdReviewsResponseDataItem]:
        """Every item of :meth:`list_reviews`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_reviews(localization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncMachineTrustPolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        machine_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMachineTrustPoliciesResponse:
        """List workload trust policies, optionally for one machine."""
        return await self._t.request(
            method="GET",
            path="/v1/machine_trust_policies",
            query=_qd({'machine_id': machine_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        machine_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMachineTrustPoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(machine_id=machine_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/machine_trust_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        machine_trust_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMachineTrustPoliciesByIdResponse:
        """Delete a trust policy. Tokens already minted through it live out their lifetime (at most
        max_ttl_seconds).
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        machine_trust_policy_id: str,
    ) -> cm.GetMachineTrustPoliciesResponseDataItem:
        """Fetch one trust policy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}",
        )

    async def update(
        self,
        machine_trust_policy_id: str,
        body: cm.PatchMachineTrustPoliciesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMachineTrustPoliciesResponseDataItem:
        """Change a trust policy. kind and machine_id cannot change. Needs a recent MFA sign-in."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/machine_trust_policies/{_enc(machine_trust_policy_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMachines:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_revoked(
        self,
        *,
        starting_after: str | None = None,
        since: str | None = None,
        limit: str | None = None,
    ) -> cm.GetMachinesRevokedResponse:
        """The machine deny feed: machines revoked and machine grants ended since a cursor
        (since=<iso|cursor>), oldest first, so a service that verifies machine tokens offline
        can deny a revoked machine within one poll. A `machine` entry denies every token with
        that `sub` issued before `revoked_at`; a `machine_grant` entry denies tokens with that
        `sub` and `aud` (the `audience`) issued before it. Readable with an sk_ bearer or a
        publishable key; a publishable key sees ids, audiences and times only. The revocation
        stream carries the same events as pushes.
        """
        return await self._t.request(
            method="GET",
            path="/v1/machines/revoked",
            query=_qd({'starting_after': starting_after, 'since': since, 'limit': limit}),
        )

    async def iter_list_revoked(
        self,
        *,
        since: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetMachinesRevokedResponseDataItem]:
        """Every item of :meth:`list_revoked`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_revoked(since=since, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def update_grant(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/machines/{_enc(machine_id)}/grants/{_enc(grant_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMcp:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create_elevation(
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
        return await self._t.request(
            method="POST",
            path="/v1/mcp/elevations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMcpGateways:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_packs(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPacksResponse:
        """The tool packs of a gateway: named tool sets assigned to agents, organizations or
        groups.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_packs(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMcpGatewaysByIdPacksResponseDataItem]:
        """Every item of :meth:`list_packs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_packs(mcp_gateway_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_pack(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_pack(
        self,
        mcp_gateway_id: str,
        pack_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMcpGatewaysByIdPacksByPackIdResponse:
        """Delete a tool pack from an MCP gateway."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs/{_enc(pack_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_pack(
        self,
        mcp_gateway_id: str,
        pack_id: str,
    ) -> cm.GetMcpGatewaysByIdPacksResponseDataItem:
        """Read one tool pack of an MCP gateway."""
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs/{_enc(pack_id)}",
        )

    async def update_pack(
        self,
        mcp_gateway_id: str,
        pack_id: str,
        body: cm.PatchMcpGatewaysByIdPacksByPackIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpGatewaysByIdPacksResponseDataItem:
        """Change a tool pack; omitted fields keep their value."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/packs/{_enc(pack_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_pins(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/pins",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_pins(
        self,
        mcp_gateway_id: str,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMcpGatewaysByIdPinsResponseDataItem]:
        """Every item of :meth:`list_pins`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_pins(mcp_gateway_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_pin(
        self,
        mcp_gateway_id: str,
        tool: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Forget a pin; the next tools/list pins whatever the upstream serves then."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/pins/{_enc(tool)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def approve_pin(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/pins/{_enc(tool)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_upstreams(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpGatewaysByIdUpstreamsResponse:
        """The upstreams of a gateway: MCP servers and OpenAPI-described APIs, each exposed under
        its namespace.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_upstreams(
        self,
        mcp_gateway_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMcpGatewaysByIdUpstreamsResponseDataItem]:
        """Every item of :meth:`list_upstreams`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_upstreams(mcp_gateway_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_upstream(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_upstream(
        self,
        mcp_gateway_id: str,
        upstream_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMcpGatewaysByIdUpstreamsByUpstreamIdResponse:
        """Remove an upstream and its tools from the gateway."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_upstream(
        self,
        mcp_gateway_id: str,
        upstream_id: str,
    ) -> cm.GetMcpGatewaysByIdUpstreamsResponseDataItem:
        """Read one upstream of an MCP gateway."""
        return await self._t.request(
            method="GET",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}",
        )

    async def update_upstream(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test_upstream(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/mcp_gateways/{_enc(mcp_gateway_id)}/upstreams/{_enc(upstream_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncMcpRegistry:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMcpRegistryResponse:
        """The instance registry of upstream MCP servers: approved ones, and requests waiting for
        review. A gateway with `registry_only` accepts only approved URLs.
        """
        return await self._t.request(
            method="GET",
            path="/v1/mcp_registry",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMcpRegistryResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostMcpRegistryBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpRegistryResponseDataItem:
        """Add a server to the registry as approved (default), or file it as pending for review."""
        return await self._t.request(
            method="POST",
            path="/v1/mcp_registry",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        mcp_registry_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMcpRegistryByIdResponse:
        """Remove a registry entry."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mcp_registry/{_enc(mcp_registry_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def decide(
        self,
        mcp_registry_id: str,
        body: cm.PostMcpRegistryByIdDecideBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMcpRegistryResponseDataItem:
        """Approve or reject a registry entry."""
        return await self._t.request(
            method="POST",
            path=f"/v1/mcp_registry/{_enc(mcp_registry_id)}/decide",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMessageLinks:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create(
        self,
        body: cm.PostMessageLinksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostMessageLinksResponse:
        """Mint a link to the hosted unsubscribe (type `unsubscribe`, needs `category`) or the
        hosted email-preference page (type `preferences`) for one address, for your own pages
        and mail. Atlas fills the same links in for you when you send with `unsubscribe: true`
        or put {{unsubscribe_url}} / {{preferences_url}} in a message. The link works for that
        address and category only and does not expire. Audited. → 201.
        """
        return await self._t.request(
            method="POST",
            path="/v1/message_links",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMessageReceivers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/message_receivers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMessageReceiversResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete(
        self,
        provider: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessageReceiversByProviderResponse:
        """Forget the stored verification secret of a provider."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/message_receivers/{_enc(provider)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/message_receivers/{_enc(provider)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMessages:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        status: Literal['queued', 'sent', 'delivered', 'bounced', 'complained', 'failed', 'suppressed', 'blocked'] | None = None,
        template: str | None = None,
        category: str | None = None,
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
        return await self._t.request(
            method="GET",
            path="/v1/messages",
            query=_qd({'channel': channel, 'status': status, 'template': template, 'category': category, 'provider': provider, 'recipient': recipient, 'since': since, 'until': until, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        status: Literal['queued', 'sent', 'delivered', 'bounced', 'complained', 'failed', 'suppressed', 'blocked'] | None = None,
        template: str | None = None,
        category: str | None = None,
        provider: str | None = None,
        recipient: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMessagesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(channel=channel, status=status, template=template, category=category, provider=provider, recipient=recipient, since=since, until=until, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostMessagesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagesResponseDataItem | cm.GetMessagesResponse:
        """Send a transactional email from your app through your own email provider and its
        failover. Give `to` (one address, or up to 10, each sent separately) and either
        `template` (the name or id of a template from POST /v1/notification_templates, with
        `data` variables) or `subject` with `html` and/or `text`, sent exactly as you wrote
        them. The message is recorded in the ledger (GET /v1/messages) with category
        `transactional`, your `category` and `tags`, and your provider's delivery callbacks fill
        in its timeline; bounces and complaints suppress the address like sign-in mail. An
        address on the suppression list is not sent to: the message is recorded with status
        `suppressed` and returned. Returns 422 when the instance has no email provider of its
        own (Atlas never sends your mail from its own sender). Accepts an Idempotency-Key. One
        address returns the message; several return a list.
        """
        return await self._t.request(
            method="POST",
            path="/v1/messages",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_summary(
        self,
        *,
        hours: int | None = None,
    ) -> cm.GetMessagesSummaryResponse:
        """How many messages are in each status over the last `hours` (default 24, up to 720)."""
        return await self._t.request(
            method="GET",
            path="/v1/messages/summary",
            query=_qd({'hours': hours}),
        )

    async def get(
        self,
        message_id: str,
    ) -> cm.GetMessagesResponseDataItem:
        """One message with its full status timeline and the providers tried."""
        return await self._t.request(
            method="GET",
            path=f"/v1/messages/{_enc(message_id)}",
        )


class AsyncMessaging:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_country_routes(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessagingCountryRoutesResponse:
        """Per-country SMS routes: numbers in a country go through the named provider (your SMS
        provider or one of its fallbacks) first.
        """
        return await self._t.request(
            method="GET",
            path="/v1/messaging/country_routes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_country_routes(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMessagingCountryRoutesResponseDataItem]:
        """Every item of :meth:`list_country_routes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_country_routes(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def set_country_routes(
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
        return await self._t.request(
            method="PUT",
            path="/v1/messaging/country_routes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_country_route(
        self,
        country: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessagingCountryRoutesByCountryResponse:
        """Remove the route for a country."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/messaging/country_routes/{_enc(country)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_settings(
        self,
    ) -> cm.GetMessagingSettingsResponse:
        """Messaging behaviour: automatic suppression, failover and ledger retention."""
        return await self._t.request(
            method="GET",
            path="/v1/messaging/settings",
        )

    async def set_settings(
        self,
        body: cm.PutMessagingSettingsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingSettingsResponse:
        """Change messaging behaviour. Send only the fields to change. Audited."""
        return await self._t.request(
            method="PUT",
            path="/v1/messaging/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_suppressions(
        self,
        *,
        email: str | None = None,
        after: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMessagingSuppressionsResponse:
        """The email suppression list, or one address with `email`."""
        return await self._t.request(
            method="GET",
            path="/v1/messaging/suppressions",
            query=_qd({'email': email, 'after': after, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_suppressions(
        self,
        *,
        email: str | None = None,
        after: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMessagingSuppressionsResponseDataItem]:
        """Every item of :meth:`list_suppressions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_suppressions(email=email, after=after, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_suppression(
        self,
        body: cm.PostMessagingSuppressionsBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingSuppressionsResponse:
        """Add one or many addresses (a bounce or complaint webhook forwarder can post here).
        Existing entries are updated.
        """
        return await self._t.request(
            method="POST",
            path="/v1/messaging/suppressions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_suppression(
        self,
        email: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessagingSuppressionsByEmailResponse:
        """Remove an address from the suppression list."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/messaging/suppressions/{_enc(email)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncMessagingProviders:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def set_push(
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
        return await self._t.request(
            method="PUT",
            path="/v1/messaging_providers/push",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_fallbacks(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_fallbacks(
        self,
        channel: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMessagingProvidersByChannelFallbacksResponseDataItem]:
        """Every item of :meth:`list_fallbacks`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_fallbacks(channel, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_fallback(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def set_fallbacks_order(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks/order",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_fallback(
        self,
        channel: str,
        fallback_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteMessagingProvidersByChannelFallbacksByIdResponse:
        """Remove a fallback provider, and any country route that pointed at it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks/{_enc(fallback_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_fallback(
        self,
        channel: str,
        fallback_id: str,
        body: cm.PutMessagingProvidersByChannelFallbacksByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMessagingProvidersByChannelFallbacksResponseDataItem:
        """Change a fallback provider. An omitted secret keeps the stored one."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/messaging_providers/{_enc(channel)}/fallbacks/{_enc(fallback_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMfaCampaigns:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMfaCampaignsResponse:
        """List MFA rollout campaigns with their completion numbers, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/mfa_campaigns",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMfaCampaignsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/mfa_campaigns",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        mfa_campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaCampaignsResponseDataItem:
        """End a campaign now. The nag and the enforcement stop at once; the campaign and its
        numbers stay readable.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        mfa_campaign_id: str,
    ) -> cm.GetMfaCampaignsResponseDataItem:
        """Read one MFA campaign with its completion numbers."""
        return await self._t.request(
            method="GET",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}",
        )

    async def update(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_users(
        self,
        mfa_campaign_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetMfaCampaignsByIdUsersResponse:
        """List the users a campaign has touched (nagged, exempted or given their own required
        factors), newest first. `limit` up to 500.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}/users",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_users(
        self,
        mfa_campaign_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMfaCampaignsByIdUsersResponseDataItem]:
        """Every item of :meth:`list_users`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_users(mfa_campaign_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_user(
        self,
        mfa_campaign_id: str,
        user_id: str,
    ) -> cm.GetMfaCampaignsByIdUsersResponseDataItem:
        """One user's standing in a campaign: their own required factors and exemption, nag
        history, and what they still owe (`effective`).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}/users/{_enc(user_id)}",
        )

    async def set_user(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/mfa_campaigns/{_enc(mfa_campaign_id)}/users/{_enc(user_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMfaFactorQuarantines:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/mfa_factor_quarantines",
            query=_qd({'user_id': user_id, 'active': active, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        user_id: str | None = None,
        active: bool | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetMfaFactorQuarantinesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(user_id=user_id, active=active, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def release(
        self,
        mfa_factor_quarantine_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetMfaFactorQuarantinesResponseDataItem:
        """Release a quarantined factor so it can complete sign-ins."""
        return await self._t.request(
            method="POST",
            path=f"/v1/mfa_factor_quarantines/{_enc(mfa_factor_quarantine_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncMigrationsSource:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def create_session(
        self,
        source: str,
        body: cm.PostMigrationsBySourceSessionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostMigrationsBySourceSessionsResponse:
        """Bulk-import live legacy sessions (up to 1000 a call) so the bridge can answer from Atlas
        alone (`mode: session_table`) and close early: the old system no longer has to be
        reachable for a person to cross over. Each row names the legacy session (`token`, or its
        SHA-256 hex as `token_hash`), the person (an Atlas `user_id` or your `external_id`) and
        `expires_at`; `mfa_verified` carries a completed second factor. Rows that cannot be
        linked to a person or have expired are reported in `errors` (`user_not_found`,
        `session_expired`, `invalid_row`, `unknown_field`, `already_exchanged`), never guessed.
        Re-sending a row only refreshes it, so a retry is safe. `dry_run: true` validates and
        counts without writing.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/sessions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verify(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/migrations/{_enc(source)}/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncMigrationsStatus:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        *,
        quiet_days: int | None = None,
        accept_unmigrated: bool | None = None,
    ) -> cm.GetMigrationsStatusResponse:
        """Where the move stands: imported users by credential type (bcrypt, argon2, scrypt,
        pbkdf2, other, social, none; imported = has an external_id), bridged sessions, imported
        legacy sessions still live, failed bridge attempts by reason, daily use per source, and
        `safe_to_delete_old_auth` with the blockers that keep it false (recent use, live
        sessions, an open dual-run window, an enabled bridge, `unmigrated_users` (imported users
        who never signed in on Atlas and hold no session; counted in `unmigrated_users` with a
        `unmigrated_user_sample` of ids), or `no_enabled_source` when no bridge or verifier was
        ever enabled or used, so nothing has been proven quiet). `quiet_days` (default 14, max
        90) sets how long the old auth must be unused.
        """
        return await self._t.request(
            method="GET",
            path="/v1/migrations/status",
            query=_qd({'quiet_days': quiet_days, 'accept_unmigrated': accept_unmigrated}),
        )


class AsyncNativeApps:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetNativeAppsResponse:
        """List the registered native apps with their callback URLs."""
        return await self._t.request(
            method="GET",
            path="/v1/native_apps",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetNativeAppsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostNativeAppsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetNativeAppsResponseDataItem:
        """Register a native app. A development app (platform development, no store identity) needs
        allowed_users (1 to 100) and expires_at (at most 90 days ahead) and may use exp://
        callbacks on production. An ios app needs bundle_id and team_id; an android app needs
        package_name and sha256_cert_fingerprints; every app needs 1 to 10 callback_urls. The
        app is added to the Apple App Site Association and Android Digital Asset Links files
        served on the Frontend API host (https callbacks on that host become Universal / App
        Links) and to the passkey app origins. 409 when the same app is already registered.
        """
        return await self._t.request(
            method="POST",
            path="/v1/native_apps",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_publishable_key(
        self,
    ) -> cm.GetNativeAppsPublishableKeyResponse:
        """Read which registered native apps may use the instance publishable key (an empty list =
        any).
        """
        return await self._t.request(
            method="GET",
            path="/v1/native_apps/publishable_key",
        )

    async def set_publishable_key(
        self,
        body: cm.PutNativeAppsPublishableKeyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetNativeAppsPublishableKeyResponse:
        """Restrict the publishable key to the listed native apps (an empty list removes the
        restriction). With a restriction, a native Frontend API request must send `X-Atlas-App-
        Id` with one of these ids (403 APP_NOT_ALLOWED otherwise); web requests, which carry an
        Origin header and no app id, are not affected. 400 NATIVE_APP_NOT_REGISTERED for an id
        that is not registered.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/native_apps/publishable_key",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        native_app_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteNativeAppsByIdResponse:
        """Unregister a native app. Its callbacks stop working at once, and it is removed from the
        publishable key restriction.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/native_apps/{_enc(native_app_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        native_app_id: str,
    ) -> cm.GetNativeAppsResponseDataItem:
        """Fetch one registered native app."""
        return await self._t.request(
            method="GET",
            path=f"/v1/native_apps/{_enc(native_app_id)}",
        )

    async def update(
        self,
        native_app_id: str,
        body: cm.PatchNativeAppsByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetNativeAppsResponseDataItem:
        """Change a native app: only the fields you send change; callback_urls is replaced as a
        whole. The platform cannot be changed. A development app may have expires_at extended
        (at most 90 days from now) and allowed_users changed.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/native_apps/{_enc(native_app_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOauthApplicationTypes:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthApplicationTypesResponse:
        """The application types `application_type` accepts when creating an OAuth client (web,
        spa, native, device, mcp), with the defaults each applies to the fields you leave out.
        """
        return await self._t.request(
            method="GET",
            path="/v1/oauth_application_types",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthApplicationTypesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncOauthClients:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_consents(
        self,
        oauth_client_id: str,
        *,
        status: Literal['active', 'revoked', 'all'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdConsentsResponse:
        """The users who authorized one OAuth client, one cursor page at a time: user id, granted
        scopes, when they first authorized it and when it was last used. status is active
        (default), revoked or all. The path takes the oac_ id or the public client_id. The
        developer can read the same list at GET /oauth2/register/{client_id}/consents with the
        client's registration_access_token.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/consents",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_consents(
        self,
        oauth_client_id: str,
        *,
        status: Literal['active', 'revoked', 'all'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthClientsByIdConsentsResponseDataItem]:
        """Every item of :meth:`list_consents`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_consents(oauth_client_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def revoke_consent(
        self,
        oauth_client_id: str,
        body: cm.PostOauthClientsByIdConsentsRevokeBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOauthClientsByIdConsentsRevokeResponse:
        """Revoke the consents users gave one OAuth client, and their refresh and access tokens,
        the same way revoking a single grant does: every active consent, or only the users in
        user_ids. The app receives grant.revoked per user and the instance gets the usual token
        revocation events. Audited. Idempotent.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/consents/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def set_organization_access(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/organization_access",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_organizations(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdOrganizationsResponse:
        """The organizations that have access to an application, with the application's access
        mode.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/organizations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_organizations(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthClientsByIdOrganizationsResponseDataItem]:
        """Every item of :meth:`list_organizations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_organizations(oauth_client_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_token_exchange_profiles(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdTokenExchangeProfilesResponse:
        """List the custom subject_token_type URIs an OAuth client may present to the token-
        exchange grant.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_token_exchange_profiles(
        self,
        oauth_client_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthClientsByIdTokenExchangeProfilesResponseDataItem]:
        """Every item of :meth:`list_token_exchange_profiles`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_token_exchange_profiles(oauth_client_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_token_exchange_profile(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_token_exchange_profile(
        self,
        oauth_client_id: str,
        profile_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove a token exchange profile."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles/{_enc(profile_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def update_token_exchange_profile(
        self,
        oauth_client_id: str,
        profile_id: str,
        body: cm.PatchOauthClientsByIdTokenExchangeProfilesByProfileIdBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Rename or enable / disable a token exchange profile."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/token_exchange_profiles/{_enc(profile_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_usage(
        self,
        oauth_client_id: str,
        *,
        days: int | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthClientsByIdUsageResponse:
        """Per-day usage of one OAuth client for the last `days` days (1 to 90, default 30): token
        endpoint calls, access tokens issued, distinct active users, errors and rate-limited
        calls, with totals, a per-day errors_by_code breakdown and the latest error (code,
        endpoint, time). The path takes the oac_ id or the public client_id. The developer can
        read the same report at GET /oauth2/register/{client_id}/usage with the client's
        registration_access_token.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/usage",
            query=_qd({'days': days, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_usage(
        self,
        oauth_client_id: str,
        *,
        days: int | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthClientsByIdUsageResponseDataItem]:
        """Every item of :meth:`list_usage`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_usage(oauth_client_id, days=days, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_webhook(
        self,
        oauth_client_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Remove the client's event webhook. 204."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_webhook(
        self,
        oauth_client_id: str,
    ) -> cm.GetOauthClientsByIdWebhookResponse:
        """The webhook this client receives user events on (404 when it has none)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook",
        )

    async def set_webhook(
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
        (201). Every delivery carries a top-level `creator` ({ id }, the user as this client
        sees them: exactly the `sub` of the tokens issued to it, pairwise or external_id
        included; null when the event has no acting user). Audited.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def rotate_secret_webhook(
        self,
        oauth_client_id: str,
        body: cm.PostOauthClientsByIdWebhookRotateSecretBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOauthClientsByIdWebhookRotateSecretResponse:
        """Rotate the client webhook's signing secret. The new secret is returned exactly once. The
        previous secret keeps signing for `overlap_seconds` (default 86400 = 24 hours, 0 to
        604800 = 7 days; 0 stops it now): during the overlap every delivery's signature header
        carries one entry per secret, the new one first, so a receiver holding either secret
        verifies it. `previous_secret_expires_at` says when the old one stops (epoch ms), or
        null. 404 when the client has no webhook. An operator token needs a recent MFA. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook/rotate_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test_webhook(
        self,
        oauth_client_id: str,
        body: cm.PostOauthClientsByIdWebhookTestBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOauthClientsByIdWebhookTestResponse:
        """Send ONE signed `webhook.test` delivery to this client's webhook URL (and to nobody
        else), in the same envelope as a real delivery, and return the attempt: the HTTP status
        your endpoint answered with, how long it took and the error, if any. With `user_id` (the
        Atlas user id, or the `sub` this client receives) the delivery's `creator` is that user
        (404 for an unknown user; no grant is needed); otherwise `creator` is null. Not retried.
        Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_clients/{_enc(oauth_client_id)}/webhook/test",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOauthConsentRequests:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def set_switch_account(
        self,
        *,
        consent_challenge: str,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutOauthConsentRequestsAcceptResponse:
        """The signed-in user is not the person who should grant this application access. Returns
        redirect_to: the application's original authorization request restarted with
        prompt=login, so the visitor signs in again (as another account) and a fresh consent
        challenge follows. Needs request_url on the challenge. Audited.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_consent_requests/switch_account",
            query=_qd({'consent_challenge': consent_challenge, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncOauthDeviceRequests:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        *,
        device_challenge: str,
    ) -> cm.GetOauthDeviceRequestsResponse:
        """Read a device challenge: the signed-in user, the code they typed, and the application
        and scopes the device asks for. Your device_url page receives the challenge after the
        person enters their code.
        """
        return await self._t.request(
            method="GET",
            path="/v1/oauth_device_requests",
            query=_qd({'device_challenge': device_challenge}),
        )

    async def set_accept(
        self,
        *,
        device_challenge: str,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutOauthDeviceRequestsAcceptResponse:
        """Approve a device challenge. Following redirect_to (in the same browser) binds the
        signed-in user to the device code, records the consent and signs the device in. The link
        is single-use and valid for five minutes. Audited.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_device_requests/accept",
            query=_qd({'device_challenge': device_challenge, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_reject(
        self,
        *,
        device_challenge: str,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutOauthDeviceRequestsAcceptResponse:
        """Deny a device challenge. Following redirect_to marks the code denied, so the device's
        next poll gets access_denied. Audited.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/oauth_device_requests/reject",
            query=_qd({'device_challenge': device_challenge, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncOauthGrants:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def import_(
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
        return await self._t.request(
            method="POST",
            path="/v1/oauth_grants/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOauthPublishers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOauthPublishersResponse:
        """List the verified-publisher claims of your OAuth apps, with the apps attached to each."""
        return await self._t.request(
            method="GET",
            path="/v1/oauth_publishers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthPublishersResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/oauth_publishers",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        oauth_publisher_id: str,
    ) -> cm.GetOauthPublishersResponseDataItem:
        """Get one OAuth publisher, with its domain verification status."""
        return await self._t.request(
            method="GET",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}",
        )

    async def update(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_client(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}/clients/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_client(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}/clients/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verify(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/oauth_publishers/{_enc(oauth_publisher_id)}/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncOpa:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_bundle(
        self,
        store: str,
    ) -> str:
        """An OPA bundle (gzipped tarball with .manifest and data.json) holding the store's model
        and unexpired tuples under data.atlas.fga.{store id}, for Rego you write over Atlas
        data. Supports ETag and If-None-Match (304).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/opa/bundles/{_enc(store)}",
        )

    async def create_log(
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
        return await self._t.request(
            method="POST",
            path="/v1/opa/logs",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def status(
        self,
        body: dict[str, Any] | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Accepts OPA status updates and ignores them, so a default OPA configuration does not log
        errors.
        """
        return await self._t.request(
            method="POST",
            path="/v1/opa/status",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def x_data_v1(
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
        return await self._t.request(
            method="POST",
            path="/v1/opa/v1/data/*",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOpenfga:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_stores_assertion(
        self,
        store: str,
        model: str,
    ) -> dict[str, Any]:
        """Read the stored assertions for a model version."""
        return await self._t.request(
            method="GET",
            path=f"/v1/openfga/stores/{_enc(store)}/assertions/{_enc(model)}",
        )

    async def set_stores_assertion(
        self,
        store: str,
        model: str,
        body: cm.PutOpenfgaStoresByStoreAssertionsByModelBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> None:
        """Replace the stored assertions for a model version."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/openfga/stores/{_enc(store)}/assertions/{_enc(model)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOrgRoleSets:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrgRoleSetsResponse:
        """List role sets: named sets of roles an organization may assign, each with a default
        role.
        """
        return await self._t.request(
            method="GET",
            path="/v1/org_role_sets",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOrgRoleSetsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostOrgRoleSetsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrgRoleSetsResponseDataItem:
        """Create a role set. role_keys must be instance-wide roles that exist; org:admin is always
        allowed and need not be listed. 409 when the key is taken. Honours Idempotency-Key.
        """
        return await self._t.request(
            method="POST",
            path="/v1/org_role_sets",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        org_role_set_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrgRoleSetsByIdResponse:
        """Delete a role set. 409 while an organization still uses it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/org_role_sets/{_enc(org_role_set_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        org_role_set_id: str,
    ) -> cm.GetOrgRoleSetsResponseDataItem:
        """One role set, by id or key."""
        return await self._t.request(
            method="GET",
            path=f"/v1/org_role_sets/{_enc(org_role_set_id)}",
        )

    async def update(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/org_role_sets/{_enc(org_role_set_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOrgTemplates:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrgTemplatesResponse:
        """List organization templates."""
        return await self._t.request(
            method="GET",
            path="/v1/org_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOrgTemplatesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/org_templates",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        org_template_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrgTemplatesByIdResponse:
        """Delete a template. Organizations made from it are not touched."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/org_templates/{_enc(org_template_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        org_template_id: str,
    ) -> cm.GetOrgTemplatesResponseDataItem:
        """One template, by id or key."""
        return await self._t.request(
            method="GET",
            path=f"/v1/org_templates/{_enc(org_template_id)}",
        )

    async def update(
        self,
        org_template_id: str,
        body: cm.PatchOrgTemplatesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrgTemplatesResponseDataItem:
        """Change a template. Organizations already made from it are not touched."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/org_templates/{_enc(org_template_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_organization(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/org_templates/{_enc(org_template_id)}/organizations",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOrganizationConnections:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationConnectionsResponse:
        """B2B connections between organizations, optionally those involving one organization."""
        return await self._t.request(
            method="GET",
            path="/v1/organization_connections",
            query=_qd({'organization_id': organization_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        organization_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOrganizationConnectionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(organization_id=organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/organization_connections",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        organization_connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetOrganizationConnectionsResponseDataItem:
        """Revoke a connection (or a pending invitation). The partner organization loses access to
        the application.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organization_connections/{_enc(organization_connection_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def accept(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organization_connections/{_enc(organization_connection_id)}/accept",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncOrganizationInvitations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        email: str | None = None,
        status: Literal['pending', 'accepted', 'revoked', 'expired', 'declined'] | None = None,
        organization_id: str | None = None,
        limit: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationInvitationsResponse:
        """Search organization invitations across every organization of the instance, newest first:
        by invited `email` (exact, case-insensitive), `status` or `organization_id`. Each row
        carries the organization name and slug. Secret key only (it is a lookup by address).
        Pages with `limit` and `starting_after`.
        """
        return await self._t.request(
            method="GET",
            path="/v1/organization_invitations",
            query=_qd({'email': email, 'status': status, 'organization_id': organization_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        email: str | None = None,
        status: Literal['pending', 'accepted', 'revoked', 'expired', 'declined'] | None = None,
        organization_id: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(email=email, status=status, organization_id=organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncOrganizations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_app_webhook_endpoints_deliveries(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/deliveries",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'status': status, 'event_type': event_type, 'since': since, 'until': until, 'trace': trace}),
        )

    async def iter_list_app_webhook_endpoints_deliveries(
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
    ) -> AsyncIterator[cm.WebhookDelivery]:
        """Every item of :meth:`list_app_webhook_endpoints_deliveries`, following the cursor page
        by page.
        """
        cursor: str | None = None
        while True:
            page = await self.list_app_webhook_endpoints_deliveries(organization_id, endpoint_id, limit=limit, status=status, event_type=event_type, since=since, until=until, trace=trace, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def redeliver_delivery_app_webhook_endpoints(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/deliveries/{_enc(delivery_id)}/redeliver",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def replay_app_webhook_endpoint(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/replay",
            query=_qd({'since': since, 'until': until, 'event_type': event_type, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def reveal_secret_app_webhook_endpoint(
        self,
        organization_id: str,
        endpoint_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostOrganizationsByIdAppWebhookEndpointsByEndpointIdRevealSecretResponse:
        """Show the current whsec_ signing secret again. Audited."""
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/reveal_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def rotate_secret_app_webhook_endpoint(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/app_webhook_endpoints/{_enc(endpoint_id)}/rotate_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_applications(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetOrganizationsByIdApplicationsResponse:
        """The OAuth applications an organization has been given access to."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/applications",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_applications(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetOauthClientsByIdOrganizationsResponseDataItem]:
        """Every item of :meth:`list_applications`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_applications(organization_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_application(
        self,
        organization_id: str,
        client_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrganizationsByIdApplicationsByClientIdResponse:
        """Take an organization's access to an application away."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{_enc(organization_id)}/applications/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_application(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/applications/{_enc(client_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_audit_logs(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/audit_logs",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'action': action, 'format': format, 'from': from_, 'to': to}),
        )

    async def iter_list_audit_logs(
        self,
        organization_id: str,
        *,
        limit: int | None = None,
        action: str | None = None,
        format: str | None = None,
        from_: str | None = None,
        to: str | None = None,
    ) -> AsyncIterator[cm.GetOrganizationsByIdAuditLogsResponseDataItem]:
        """Every item of :meth:`list_audit_logs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_audit_logs(organization_id, limit=limit, action=action, format=format, from_=from_, to=to, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_directory_sync_runs(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/directory_sync_runs",
            query=_qd({'limit': limit, 'status': status, 'starting_after': starting_after}),
        )

    async def iter_list_directory_sync_runs(
        self,
        organization_id: str,
        *,
        limit: str | None = None,
        status: Literal['queued', 'running', 'succeeded', 'failed'] | None = None,
    ) -> AsyncIterator[cm.GetOrganizationsByIdDirectorySyncRunsResponseDataItem]:
        """Every item of :meth:`list_directory_sync_runs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_directory_sync_runs(organization_id, limit=limit, status=status, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def retry_directory_sync_run(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/directory_sync_runs/{_enc(run_id)}/retry",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def import_invitation(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/invitations/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_it_alerts(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/it_alerts",
            query=_qd({'kind': kind, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_it_alerts(
        self,
        organization_id: str,
        *,
        kind: str | None = None,
        limit: str | None = None,
    ) -> AsyncIterator[cm.GetOrganizationsByIdItAlertsResponseDataItem]:
        """Every item of :meth:`list_it_alerts`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_it_alerts(organization_id, kind=kind, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_it_health(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/it_health",
        )

    async def create_membership_import(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/membership_imports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_memberships_by_external_id(
        self,
        organization_id: str,
        user_external_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteOrganizationsByIdMembershipsByExternalIdByUserExternalIdResponse:
        """Cancel a seat that is still waiting for its person. 404 when none is waiting (a seat
        that was already attached is removed by the user id).
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/organizations/{_enc(organization_id)}/memberships/by_external_id/{_enc(user_external_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_memberships_by_external_id(
        self,
        organization_id: str,
        user_external_id: str,
        body: cm.PutOrganizationsByIdMembershipsByExternalIdByUserExternalIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutOrganizationsByIdMembershipsByExternalIdByUserExternalIdResponse:
        """Seat a person by the id your own system gives them (`external_id`), before they have
        signed in. Same body as PUT .../memberships/{userId}. When a user with that external_id
        exists this is that create-or-update (201 when it adds the member, 200 when it changes
        it, `status: "active"`). When none exists the seat waits: 202 with `status: "pending"`,
        and it is attached (with `organizationMembership.created`) when a user with that
        external_id is created, imported or given the id. `user.created` then carries the user's
        `organization_memberships`. `{id}` is the organization's Atlas id or its own
        external_id. Repeating the call replaces the waiting seat.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/memberships/by_external_id/{_enc(user_external_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_membership(
        self,
        organization_id: str,
        user_id: str,
    ) -> cm.GetOrganizationsByIdMembershipsByUserIdResponse:
        """Read one membership: role, `role_source`, scope, in the same shape as a list item. 404
        when the user is not a member.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/memberships/{_enc(user_id)}",
        )

    async def set_membership(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/memberships/{_enc(user_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_mfa_status(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/mfa_status",
            query=_qd({'session_id': session_id}),
        )

    async def get_role_policy(
        self,
        organization_id: str,
    ) -> cm.GetOrganizationsByIdRolePolicyResponse:
        """The roles an organization may assign and the role a new seat gets by default."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/role_policy",
        )

    async def set_role_policy(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/role_policy",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_scim_requests(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/scim/requests",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'status': status, 'token_id': token_id, 'resource': resource, 'since': since}),
        )

    async def iter_list_scim_requests(
        self,
        organization_id: str,
        *,
        limit: str | None = None,
        status: Literal['ok', 'error'] | None = None,
        token_id: str | None = None,
        resource: str | None = None,
        since: str | None = None,
    ) -> AsyncIterator[cm.GetOrganizationsByIdScimRequestsResponseDataItem]:
        """Every item of :meth:`list_scim_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_scim_requests(organization_id, limit=limit, status=status, token_id=token_id, resource=resource, since=since, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_seats(
        self,
        organization_id: str,
    ) -> cm.GetOrganizationsByIdSeatsResponse:
        """Seats used, pending invitations and seats left for an organization."""
        return await self._t.request(
            method="GET",
            path=f"/v1/organizations/{_enc(organization_id)}/seats",
        )

    async def set_seats(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/organizations/{_enc(organization_id)}/seats",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def redeliver_delivery_webhook_endpoints(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/deliveries/{_enc(delivery_id)}/redeliver",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def replay_webhook_endpoint(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/replay",
            query=_qd({'since': since, 'until': until, 'event_type': event_type, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def reveal_secret_webhook_endpoint(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/reveal_secret",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def test_webhook_endpoint(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/organizations/{_enc(organization_id)}/webhook_endpoints/{_enc(endpoint_id)}/test",
            query=_qd({'wait': wait, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncPasskeyCampaigns:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPasskeyCampaignsResponse:
        """List passkey campaigns with their completion metrics (eligible, prompted, enrolled),
        newest first.
        """
        return await self._t.request(
            method="GET",
            path="/v1/passkey_campaigns",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPasskeyCampaignsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/passkey_campaigns",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        passkey_campaign_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPasskeyCampaignsResponseDataItem:
        """End a campaign now. The prompt stops at once; the campaign and its numbers stay
        readable.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/passkey_campaigns/{_enc(passkey_campaign_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        passkey_campaign_id: str,
    ) -> cm.GetPasskeyCampaignsResponseDataItem:
        """Read one passkey campaign with its completion metrics."""
        return await self._t.request(
            method="GET",
            path=f"/v1/passkey_campaigns/{_enc(passkey_campaign_id)}",
        )


class AsyncPca:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_action_registry(
        self,
    ) -> cm.GetPcaActionRegistryResponse:
        """The action registry of the instance: namespaces with their active version and counts,
        publisher and reviewer keys.
        """
        return await self._t.request(
            method="GET",
            path="/v1/pca/action-registry",
        )

    async def list_action_registry_actions(
        self,
        *,
        q: str | None = None,
        state: Literal['confirmed', 'unconfirmed', 'stale', 'deprecated'] | None = None,
        ns: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaActionRegistryActionsResponse:
        """Search the active actions by text, state and namespace."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/action-registry/actions",
            query=_qd({'q': q, 'state': state, 'ns': ns, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_action_registry_actions(
        self,
        *,
        q: str | None = None,
        state: Literal['confirmed', 'unconfirmed', 'stale', 'deprecated'] | None = None,
        ns: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaActionRegistryActionsResponseDataItem]:
        """Every item of :meth:`list_action_registry_actions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_action_registry_actions(q=q, state=state, ns=ns, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_action_registry_action(
        self,
        verb: str,
    ) -> cm.GetPcaActionRegistryActionsByVerbResponse:
        """One action: policy card, effective profile, business rules and history."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/action-registry/actions/{_enc(verb)}",
        )

    async def review_action_action_registry(
        self,
        verb: str,
        body: dict[str, Any],
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryActionsByVerbReviewResponse:
        """Open a published action for review: its active definition and business rules become a
        draft (409 when one already exists), so an action published unconfirmed can be
        confirmed. Takes no body. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/action-registry/actions/{_enc(verb)}/review",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_action_registry_drafts(
        self,
        *,
        ns: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaActionRegistryDraftsResponse:
        """The review queue: drafts with their review view, policy card, lint, business rules in
        plain sentences and the diff against the active version, the riskiest first.
        """
        return await self._t.request(
            method="GET",
            path="/v1/pca/action-registry/drafts",
            query=_qd({'ns': ns, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_action_registry_drafts(
        self,
        *,
        ns: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.PostPcaActionRegistryActionsByVerbReviewResponse]:
        """Every item of :meth:`list_action_registry_drafts`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_action_registry_drafts(ns=ns, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_action_registry_draft(
        self,
        verb: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaActionRegistryDraftsByVerbResponse:
        """Remove a draft from the review queue. Audited."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/action-registry/drafts/{_enc(verb)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_action_registry_draft(
        self,
        verb: str,
    ) -> cm.PostPcaActionRegistryActionsByVerbReviewResponse:
        """One draft with its review view."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/action-registry/drafts/{_enc(verb)}",
        )

    async def update_action_registry_draft(
        self,
        verb: str,
        body: cm.PatchPcaActionRegistryDraftsByVerbBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryActionsByVerbReviewResponse:
        """Edit a draft (title, description, effects, params, reversibility, compensates, traits,
        business rules). Re-validated; any edit drops a confirmation and a rules review.
        Audited.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/pca/action-registry/drafts/{_enc(verb)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def confirm_draft_action_registry(
        self,
        verb: str,
        body: cm.PostPcaActionRegistryDraftsByVerbConfirmBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryActionsByVerbReviewResponse:
        """Confirm a draft: the reviewer's signed attestation (and, for widened rules, a signed
        rules review), with a passkey assertion over a challenge committing to exactly those
        signatures. The passkey must be an active credential of an active reviewer whose pinned
        reviewer key signed; a publisher key never confirms. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/action-registry/drafts/{_enc(verb)}/confirm",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_action_registry_import(
        self,
        body: cm.PostPcaActionRegistryImportsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryImportsResponse:
        """Import actions from a source: a URL the server fetches (https, public addresses only, at
        most 8 MiB; MCP servers are read with initialize + tools/list) or pasted text. Every
        result is unreviewed or suggested and lands as a draft; with track, the URL is kept as a
        source. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/action-registry/imports",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_action_registry_namespaces_diff(
        self,
        ns: str,
        *,
        from_: str,
        to: str,
    ) -> cm.GetPcaActionRegistryNamespacesByNsDiffResponse:
        """The semantic diff between two stored versions, and whether the move needs a reviewer."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/action-registry/namespaces/{_enc(ns)}/diff",
            query=_qd({'from': from_, 'to': to}),
        )

    async def delete_action_registry_namespaces_pin(
        self,
        ns: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaActionRegistryNamespacesByNsPinResponse:
        """Unpin a namespace (later publishes activate again). Audited."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/action-registry/namespaces/{_enc(ns)}/pin",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_action_registry_namespaces_pin(
        self,
        ns: str,
        body: cm.PutPcaActionRegistryNamespacesByNsPinBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaActionRegistryNamespacesByNsPinResponse:
        """Activate and pin a stored version (later publishes are staged). Audited."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/pca/action-registry/namespaces/{_enc(ns)}/pin",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_action_registry_namespaces_versions(
        self,
        ns: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaActionRegistryNamespacesByNsVersionsResponse:
        """The version history of a namespace."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/action-registry/namespaces/{_enc(ns)}/versions",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_action_registry_namespaces_versions(
        self,
        ns: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaActionRegistryNamespacesByNsVersionsResponseDataItem]:
        """Every item of :meth:`list_action_registry_namespaces_versions`, following the cursor
        page by page.
        """
        cursor: str | None = None
        while True:
            page = await self.list_action_registry_namespaces_versions(ns, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_action_registry_namespaces_version(
        self,
        ns: str,
        version: str,
    ) -> cm.GetPcaActionRegistryNamespacesByNsVersionsByVersionResponse:
        """One stored version: pack, rules, traits, deprecated actions and changes."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/action-registry/namespaces/{_enc(ns)}/versions/{_enc(version)}",
        )

    async def create_action_registry_pack(
        self,
        body: cm.PostPcaActionRegistryPacksBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryPacksResponse:
        """Publish a signed pack (with business rules and custom traits) as the next version of its
        namespace. 409 when it widens without a reviewer. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/action-registry/packs",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def publish_action_registry(
        self,
        body: cm.PostPcaActionRegistryPublishBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryPacksResponse:
        """Publish the drafts of a namespace as its next version: the active actions overlaid with
        the drafts (removal drafts deprecate their action), the business rules and rules
        reviews, signed with the instance's publisher key. 409 (reason_code widen_unreviewed)
        when an action or its rules widen without a reviewer's signature. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/action-registry/publish",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_action_registry_publisher_key(
        self,
        body: cm.PostPcaActionRegistryPublisherKeysBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryPublisherKeysResponse:
        """Pin a publisher key (kid, Ed25519 public key). Audited."""
        return await self._t.request(
            method="POST",
            path="/v1/pca/action-registry/publisher-keys",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_action_registry_publisher_key(
        self,
        kid: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Revoke a publisher key. Audited."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/action-registry/publisher-keys/{_enc(kid)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_action_registry_reviewers(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaActionRegistryReviewersResponse:
        """The reviewers who may confirm action definitions, with their keys and passkeys."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/action-registry/reviewers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_action_registry_reviewers(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaActionRegistryReviewersResponseDataItem]:
        """Every item of :meth:`list_action_registry_reviewers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_action_registry_reviewers(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_action_registry_reviewers_enrolment(
        self,
        body: cm.PostPcaActionRegistryReviewersEnrolmentsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistryReviewersEnrolmentsResponse:
        """Create a single-use reviewer enrolment link (24 hours). The reviewer creates a passkey
        and a reviewer key on the hosted page; the key is pinned with the reviewer role.
        Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/action-registry/reviewers/enrolments",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_action_registry_reviewer(
        self,
        reviewer_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaActionRegistryReviewersResponseDataItem:
        """Remove a reviewer: the reviewer key is unpinned (its confirmations stop counting) and
        every passkey revoked. Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/action-registry/reviewers/{_enc(reviewer_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_action_registry_sources(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaActionRegistrySourcesResponse:
        """The tracked import sources, with their schedule and last sync."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/action-registry/sources",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_action_registry_sources(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaActionRegistrySourcesResponseDataItem]:
        """Every item of :meth:`list_action_registry_sources`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_action_registry_sources(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_action_registry_source(
        self,
        body: cm.PostPcaActionRegistrySourcesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaActionRegistrySourcesResponseDataItem:
        """Track a source for manual or scheduled (hourly / daily) sync. Audited."""
        return await self._t.request(
            method="POST",
            path="/v1/pca/action-registry/sources",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_action_registry_source(
        self,
        source_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaActionRegistrySourcesByIdResponse:
        """Stop tracking a source (its drafts stay in the queue). Audited."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/action-registry/sources/{_enc(source_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def update_action_registry_source(
        self,
        source_id: str,
        body: cm.PatchPcaActionRegistrySourcesByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaActionRegistrySourcesResponseDataItem:
        """Change a source: URL, verb (jsonschema) or schedule. Audited."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/pca/action-registry/sources/{_enc(source_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def sync_source_action_registry(
        self,
        source_id: str,
        body: dict[str, Any],
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaActionRegistrySourcesByIdSyncResponse:
        """Sync a source now: added and changed operations become unreviewed drafts, removed ones
        removal drafts; unchanged ones are left as they are. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/action-registry/sources/{_enc(source_id)}/sync",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_action_registry_templates(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaActionRegistryTemplatesResponse:
        """The starter packs (e-commerce, fintech, healthcare, SaaS admin, developer tools)."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/action-registry/templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_action_registry_templates(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaActionRegistryTemplatesResponseDataItem]:
        """Every item of :meth:`list_action_registry_templates`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_action_registry_templates(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def apply_template_action_registry(
        self,
        template_id: str,
        body: cm.PostPcaActionRegistryTemplatesByIdApplyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaActionRegistryDraftsResponse:
        """Add a starter pack's actions (with their business rules and examples) to a namespace as
        drafts. Never confirmed. Audited.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/action-registry/templates/{_enc(template_id)}/apply",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_approvals_settings(
        self,
    ) -> cm.GetPcaApprovalsSettingsResponse:
        """Approval channel settings of this instance (secrets are reported as set / not set, never
        returned).
        """
        return await self._t.request(
            method="GET",
            path="/v1/pca/approvals/settings",
        )

    async def set_approvals_settings(
        self,
        body: cm.PutPcaApprovalsSettingsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaApprovalsSettingsResponse:
        """Update the approval channels (push, email, sms, slack, webhook), default member
        channels, the Slack webhook and the CIBA identity provider. Omitted fields are kept;
        null clears. Audited.
        """
        return await self._t.request(
            method="PUT",
            path="/v1/pca/approvals/settings",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_approvers(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaApproversResponse:
        """List passkey approvers with their members, devices and quorum."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/approvers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_approvers(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaApproversResponseDataItem]:
        """Every item of :meth:`list_approvers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_approvers(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_approvers_enrolment(
        self,
        body: cm.PostPcaApproversEnrolmentsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaApproversEnrolmentsResponse:
        """Create a single-use passkey enrolment link (24 hours): a new approver bound to a user /
        org / machine, a delegate of an existing approver, or another device of a member. Adding
        to an existing approver needs one of its passkeys on the enrolment page. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/approvers/enrolments",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_approver(
        self,
        approver_id: str,
    ) -> cm.GetPcaApproversResponseDataItem:
        """One passkey approver with its members, devices and quorum."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/approvers/{_enc(approver_id)}",
        )

    async def update_approver(
        self,
        approver_id: str,
        body: cm.PatchPcaApproversByIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaApproversResponseDataItem:
        """Change an approver: quorum, display name, or disable it (a disabled approver cannot
        approve). Audited.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/pca/approvers/{_enc(approver_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_approvers_credential(
        self,
        approver_id: str,
        credential_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaApproversResponseDataItem:
        """Revoke a passkey: its wrapped principal key copy is deleted and it can no longer
        approve. Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/approvers/{_enc(approver_id)}/credentials/{_enc(credential_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def update_approvers_member(
        self,
        approver_id: str,
        member_id: str,
        body: cm.PatchPcaApproversByIdMembersByMemberIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaApproversResponseDataItem:
        """Change a member's notification channels, contact details or status. Audited."""
        return await self._t.request(
            method="PATCH",
            path=f"/v1/pca/approvers/{_enc(approver_id)}/members/{_enc(member_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_beacon(
        self,
        body: cm.PostPcaBeaconsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaBeaconsResponse:
        """Issue a dead-man liveness beacon. PRINCIPAL path (no Authorization header): submit
        `beacon`, a v2 beacon signed with the grant principal's own key (scope = a grant_ref
        they issued, or '*'): the principal halts their agents just by withholding, without
        trusting the operator. OPERATOR path (`sk_` + `pca:write`): the server signs with the
        guardian key (`scope`, `validity_ms`). `seq` must strictly increase per (scope, issuer)
        (409 on replay); validity is hard-capped at one hour. A pure-PQ or hybrid principal
        beacon is accepted only under the PQ key pinned for the issuer (POST /v1/pca/pq-pins),
        and only after the issuer check is it charged to the per-source
        pqVerifyUnitsPerSourcePerMin budget (429 when exhausted) and verified, Ed25519 half
        first. Beacons gate adjudication only when `auth_config.pca.beacons` is enabled.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/beacons",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_bond_accounts(
        self,
        *,
        account: str,
    ) -> cm.GetPcaBondAccountsResponse:
        """A bond account's balance (?account=<principal_pub>; also `escrow` and `atlas-treasury`)."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/bond-accounts",
            query=_qd({'account': account}),
        )

    async def create_bond_account(
        self,
        body: cm.PostPcaBondAccountsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPcaBondAccountsResponse:
        """Credit a depositor's bond escrow balance (funds the optimistic fast path). The depositor
        account is the grant's principal_pub; bonds are sized from server policy exposure and
        debited atomically at claim open. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/bond-accounts",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_constitution(
        self,
        body: cm.PostPcaConstitutionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaConstitutionsResponse:
        """Register the grant's CONSTITUTION: a principal-signed set of invariants (never /
        never_unless / cap / rate / never_after / require_prior / require_approval_over) the
        agent must never violate whatever its permissions say. Verified against the grant
        principal's key, immutable once set (a different constitution is 409), and enforced on
        every action inside the admission transaction with a hash-chained, server-persisted
        monitor state. Public (the signature is the authority) or `sk_` + pca:write (still
        principal-signed).
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/constitutions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_grants(
        self,
        *,
        principal: str | None = None,
        agent: str | None = None,
        status: Literal['active', 'revoked'] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaGrantsResponse:
        """List registered grants (grant management): filter by principal, agent (holder) and
        status; keyset pagination.
        """
        return await self._t.request(
            method="GET",
            path="/v1/pca/grants",
            query=_qd({'principal': principal, 'agent': agent, 'status': status, 'limit': limit, 'cursor': cursor, 'starting_after': starting_after}),
        )

    async def iter_list_grants(
        self,
        *,
        principal: str | None = None,
        agent: str | None = None,
        status: Literal['active', 'revoked'] | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncIterator[cm.GetPcaGrantsResponseDataItem]:
        """Every item of :meth:`list_grants`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_grants(principal=principal, agent=agent, status=status, limit=limit, cursor=cursor, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_grant(
        self,
        grant_ref: str,
        body: cm.DeletePcaGrantsByGrantRefBody,
        *,
        scope: Literal['grant', 'agent'] | None = None,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaGrantsByGrantRefResponse:
        """Revoke a grant (scope=grant) or every active grant of its principal and agent
        (scope=agent, operator only). Operator `sk_` + pca:write, or with no Authorization
        header the principal's signature (principal_sig) over the root revocation message. The
        signed revocation epoch is bumped in the same transaction.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/grants/{_enc(grant_ref)}",
            query=_qd({'scope': scope, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_grant(
        self,
        grant_ref: str,
    ) -> cm.GetPcaGrantsByGrantRefResponse:
        """Inspect a grant: the signed chain, its content digest, remaining trust budget, revoked-
        capability count and the current signed revocation epoch.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/grants/{_enc(grant_ref)}",
        )

    async def amend_grant(
        self,
        grant_ref: str,
        body: cm.PostPcaGrantsByGrantRefAmendBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaGrantsByGrantRefAmendResponse:
        """Amend a grant's authority statement. `narrow`, or any change that is provably not wider,
        is signed by the holder or the principal and revises the grant in place (revision + 1; a
        signature names the revision, so it cannot be replayed). A change that widens or is
        incomparable needs the PRINCIPAL's signature, a spent step-up and `new_grant_ref` (a
        registered active grant of the same principal and agent); it creates that successor's
        statement (`supersedes`) and kills the old grant. Public (the signature is the
        authority) or `sk_` + pca:write (still signed).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/grants/{_enc(grant_ref)}/amend",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def set_grants_authority(
        self,
        grant_ref: str,
        body: cm.PutPcaGrantsByGrantRefAuthorityBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PutPcaGrantsByGrantRefAuthorityResponse:
        """Enrol a grant into management: the principal signs its initial authority statement at
        revision 0 (the signature covers {grant, rev: 0, action: 'replace', authority digest}
        under the grant-amend domain). Once; afterwards use amend. Admission then enforces the
        statement as an extra tighten-only ceiling. Public (the signature is the authority) or
        `sk_` + pca:write (still principal-signed).
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/pca/grants/{_enc(grant_ref)}/authority",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_grants_needs(
        self,
        grant_ref: str,
        *,
        status: Literal['pending', 'approved', 'denied'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaGrantsByGrantRefNeedsResponse:
        """A grant's need requests, optionally filtered by status."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/grants/{_enc(grant_ref)}/needs",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_grants_needs(
        self,
        grant_ref: str,
        *,
        status: Literal['pending', 'approved', 'denied'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Every item of :meth:`list_grants_needs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_grants_needs(grant_ref, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_grants_need(
        self,
        grant_ref: str,
        body: cm.PostPcaGrantsByGrantRefNeedsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaGrantsByGrantRefNeedsResponse:
        """File typed needs (incremental authorization). The grant holder signs them at the current
        revision (need-request domain), or the operator files them. Nothing changes until the
        principal approves.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/grants/{_enc(grant_ref)}/needs",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def step_up_grant(
        self,
        grant_ref: str,
        body: dict[str, Any],
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaGrantsByGrantRefStepUpResponse:
        """Issue a single-use step-up challenge for a grant (valid 5 minutes). The principal signs
        its nonce on its own device; a widening spends one.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/grants/{_enc(grant_ref)}/step-up",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def approve_step_up_grants(
        self,
        grant_ref: str,
        challenge_id: str,
        body: cm.PostPcaGrantsByGrantRefStepUpByChallengeIdApproveBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaGrantsByGrantRefStepUpByChallengeIdApproveResponse:
        """Approve a step-up challenge with the grant principal's signature over {grant, challenge,
        nonce} (grant-step-up domain). Once.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/grants/{_enc(grant_ref)}/step-up/{_enc(challenge_id)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def rotate_guardian(
        self,
        body: dict[str, Any],
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaGuardianRotateResponse:
        """Rotate the guardian signing key: a new keypair and epoch + 1; the previous public key is
        retained so STHs, revocation epochs and receipts signed under it still verify. New
        signatures use the new epoch. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/guardian/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_intent_maps_observations(
        self,
        digest: str,
        *,
        limit: int | None = None,
        after: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaIntentMapsByDigestObservationsResponse:
        """List the runtime observations recorded against a map, oldest first. Paginate with
        `after` = the previous page `next_cursor`.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/intent/maps/{_enc(digest)}/observations",
            query=_qd({'limit': limit, 'after': after, 'starting_after': starting_after}),
        )

    async def iter_list_intent_maps_observations(
        self,
        digest: str,
        *,
        limit: int | None = None,
        after: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Every item of :meth:`list_intent_maps_observations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_intent_maps_observations(digest, limit=limit, after=after, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_intent_schema(
        self,
        body: cm.PostPcaIntentSchemasBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaIntentSchemasResponse:
        """Anchor a site's signed action schema (Intent Layer v2, `pca-action-schema` v1 served at
        /.well-known/pca-actions.json). The schema is verified against the site's discovery keys
        (`keys`, the `intent.schema_keys` of its /.well-known/pca-configuration; the suite comes
        from the key entry), content-addressed (`actionSchemaDigest`) and appended to the
        instance's intent transparency log (kind `schema`), so a site cannot show different
        schemas to different users without detection. Audited. 201 anchored, 200 already
        anchored.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/intent/schemas",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def approve_need(
        self,
        need_id: str,
        body: cm.PostPcaNeedsByNeedIdApproveBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaNeedsByNeedIdApproveResponse:
        """Approve a need request. The principal signs the approved needs at the current revision
        (need-approve domain); the approved list must name the same verbs and resources in
        order, and an amount may only be lowered, and only on a need marked adjustable. Needs a
        spent step-up and `new_grant_ref` (the registered successor); the result is a successor
        grant with the merged authority.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/needs/{_enc(need_id)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def deny_need(
        self,
        need_id: str,
        body: cm.PostPcaNeedsByNeedIdDenyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaNeedsByNeedIdDenyResponse:
        """Deny a need request: the principal's signature over the empty approval of this need at
        the current revision, or the operator key.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/pca/needs/{_enc(need_id)}/deny",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_pq_pin(
        self,
        identity: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaPqPinsByIdentityResponse:
        """Remove an identity PQ key pin (the rotation step: delete, then the identity registers a
        new binding at a HIGHER epoch; the delete leaves a tombstone holding the last epoch, so
        the removed binding and every older one is refused). Pure-PQ and hybrid artifacts from
        that identity are refused until it is re-pinned. Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/pq-pins/{_enc(identity)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_principals(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaPrincipalsResponse:
        """The instance's enrolled principals (public key, bound subject, status)."""
        return await self._t.request(
            method="GET",
            path="/v1/pca/principals",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_principals(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaPrincipalsResponseDataItem]:
        """Every item of :meth:`list_principals`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_principals(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_principal(
        self,
        body: cm.PostPcaPrincipalsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaPrincipalsResponse:
        """Enrol a principal public key, binding it to an Atlas identity (user, org, or machine) in
        this instance. A grant whose issuer is an enrolled active principal registers as the
        `verified` tier; an unenrolled issuer is accepted only as `unverified`. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/principals",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_principal(
        self,
        principal_pub: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePcaPrincipalsByPrincipalPubResponse:
        """Disable an enrolled principal. Its existing verified grants are denied at adjudication
        and no new verified grant can be registered under it. Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/pca/principals/{_enc(principal_pub)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def create_undo_record(
        self,
        body: cm.PostPcaUndoRecordsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaUndoRecordsResponse:
        """Register an undo record with the hosted undo ledger. The record's receipt chain must
        verify against the instance's undo signer (auth_config.pca.undoSigner); 409 when none is
        configured. Idempotent on the record id: the same record again returns the stored one,
        different content under the same id is a 409. Audited.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/undo/records",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_undo_record(
        self,
        record_id: str,
    ) -> cm.PostPcaUndoRecordsResponse:
        """A stored undo record (without its encoded PCActn) and the veto waiting on it, if any."""
        return await self._t.request(
            method="GET",
            path=f"/v1/pca/undo/records/{_enc(record_id)}",
        )

    async def set_undo_record(
        self,
        record_id: str,
        body: cm.PostPcaUndoRecordsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaUndoRecordsResponse:
        """Replace an undo record after a transition. Accepted only when the new receipt chain
        verifies, the stored receipts are a prefix of it, the record identity (id, audience,
        grant, holder, principal, compensation, window, PCActn) is unchanged and `ver`
        increases. Moving to vetoed, compensated or compensation_failed settles a pending veto;
        finalizing while a veto is pending is a 409. Audited.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/pca/undo/records/{_enc(record_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_undo_vetoes(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPcaUndoVetoesResponse:
        """Vetoes received by the instance that the resource server has not applied yet, oldest
        first (?limit 1..200, default 100), each with the principal's token. The resource server
        re-verifies the token as of the veto time, applies the veto and PUTs the signed record.
        """
        return await self._t.request(
            method="GET",
            path="/v1/pca/undo/vetoes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_undo_vetoes(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPcaUndoVetoesResponseDataItem]:
        """Every item of :meth:`list_undo_vetoes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_undo_vetoes(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_workflow_receipt(
        self,
        body: cm.PostPcaWorkflowReceiptsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPcaWorkflowReceiptsResponse:
        """Issue a guardian-signed step receipt for a step of a workflow the grant principal
        committed (K5). The operator reports the outcome and outputs of an executed step; the
        receipt chains to the earlier receipts and lets a later step be admitted.
        """
        return await self._t.request(
            method="POST",
            path="/v1/pca/workflow-receipts",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPermissionAliases:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPermissionAliasesResponse:
        """List permission aliases: legacy keys that stand for a canonical permission key."""
        return await self._t.request(
            method="GET",
            path="/v1/permission_aliases",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPermissionAliasesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostPermissionAliasesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPermissionAliasesResponseDataItem:
        """Create or repoint a permission alias from a body ({ alias, permission_key }); the same
        write as PUT /v1/permission_aliases/{alias}.
        """
        return await self._t.request(
            method="POST",
            path="/v1/permission_aliases",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        alias: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePermissionAliasesByAliasResponse:
        """Remove an alias. Writes that still send it are then refused or dropped as an unknown
        key.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/permission_aliases/{_enc(alias)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set(
        self,
        alias: str,
        body: cm.PutPermissionAliasesByAliasBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPermissionAliasesResponseDataItem:
        """Create or repoint an alias. Writes that take permission keys (role grants, seat
        permissions, invitations, implies) accept the alias and store the canonical key; tokens
        always carry the canonical key. The alias must not be a permission key, and the target
        must be an existing permission.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/permission_aliases/{_enc(alias)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPermissions:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def rename(
        self,
        permission_id: str,
        body: cm.PostPermissionsByIdRenameBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPermissionsByIdRenameResponse:
        """Rename a custom permission. The key moves in one transaction everywhere Atlas stores it
        (the permission, seats, invitations, implies, aliases; role grants follow by id) and the
        old key becomes an alias, so code and imports that still send it keep working. Sessions
        minted before the rename carry the old key until they refresh. System permissions cannot
        be renamed. permission.updated is sent with previous_key.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/permissions/{_enc(permission_id)}/rename",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_audience(
        self,
        policy_id: str,
    ) -> cm.GetPoliciesByIdAudienceResponse:
        """Who a policy is asked of: everyone, or the members of the listed organizations."""
        return await self._t.request(
            method="GET",
            path=f"/v1/policies/{_enc(policy_id)}/audience",
        )

    async def set_audience(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/policies/{_enc(policy_id)}/audience",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_versions_translations(
        self,
        policy_id: str,
        version_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPoliciesByIdVersionsByVersionIdTranslationsResponse:
        """A policy version's texts in other languages."""
        return await self._t.request(
            method="GET",
            path=f"/v1/policies/{_enc(policy_id)}/versions/{_enc(version_id)}/translations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_versions_translations(
        self,
        policy_id: str,
        version_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPoliciesByIdVersionsByVersionIdTranslationsResponseDataItem]:
        """Every item of :meth:`list_versions_translations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_versions_translations(policy_id, version_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_versions_translation(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/policies/{_enc(policy_id)}/versions/{_enc(version_id)}/translations/{_enc(locale)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_versions_translation(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/policies/{_enc(policy_id)}/versions/{_enc(version_id)}/translations/{_enc(locale)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncProvisioning:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def preview(
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
        return await self._t.request(
            method="POST",
            path="/v1/provisioning/preview",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncProvisioningConnectors:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetProvisioningConnectorsResponse:
        """List the outbound provisioning connector kinds (scim, google_workspace, microsoft_graph,
        rest, ad_writeback, sql) with the credentials and settings each needs, whether it needs
        a relay agent, and the functions the mapping expression language offers.
        """
        return await self._t.request(
            method="GET",
            path="/v1/provisioning_connectors",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetProvisioningConnectorsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncRateLimitOverrides:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        subject_type: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRateLimitOverridesResponse:
        """List per-subject overrides, oldest first."""
        return await self._t.request(
            method="GET",
            path="/v1/rate_limit_overrides",
            query=_qd({'subject_type': subject_type, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        subject_type: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetRateLimitOverridesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(subject_type=subject_type, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete(
        self,
        subject_type: str,
        subject_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteRateLimitOverridesBySubjectTypeBySubjectIdResponse:
        """Remove the override for one subject. Emits rate_limit_policy.updated."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/rate_limit_overrides/{_enc(subject_type)}/{_enc(subject_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        subject_type: str,
        subject_id: str,
    ) -> cm.GetRateLimitOverridesResponseDataItem:
        """The override for one subject, or 404."""
        return await self._t.request(
            method="GET",
            path=f"/v1/rate_limit_overrides/{_enc(subject_type)}/{_enc(subject_id)}",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path=f"/v1/rate_limit_overrides/{_enc(subject_type)}/{_enc(subject_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncRateLimitPolicies:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        subject: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRateLimitPoliciesResponse:
        """List the rate-limit policies for your own API, optionally for one subject kind."""
        return await self._t.request(
            method="GET",
            path="/v1/rate_limit_policies",
            query=_qd({'subject': subject, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        subject: Literal['key', 'user', 'org', 'machine', 'ip'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetRateLimitPoliciesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(subject=subject, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/rate_limit_policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_resolve(
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
        return await self._t.request(
            method="GET",
            path="/v1/rate_limit_policies/resolve",
            query=_qd({'key_id': key_id, 'user_id': user_id, 'org_id': org_id, 'machine_id': machine_id, 'ip': ip}),
        )

    async def delete(
        self,
        rate_limit_policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteRateLimitPoliciesByIdResponse:
        """Delete a policy. Refused with 409 while per-subject overrides still point at it. Emits
        rate_limit_policy.updated.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/rate_limit_policies/{_enc(rate_limit_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        rate_limit_policy_id: str,
    ) -> cm.GetRateLimitPoliciesResponseDataItem:
        """One rate-limit policy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/rate_limit_policies/{_enc(rate_limit_policy_id)}",
        )

    async def update(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/rate_limit_policies/{_enc(rate_limit_policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncReferralRewardRules:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetReferralRewardRulesResponse:
        """The instance's referral reward terms. Rewards are off until you turn them on."""
        return await self._t.request(
            method="GET",
            path="/v1/referral_reward_rules",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path="/v1/referral_reward_rules",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncReferralRewards:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        status: Literal['pending', 'granted', 'voided'] | None = None,
        recipient_user_id: str | None = None,
        referrer_user_id: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetReferralRewardsResponse:
        """The reward ledger, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/referral_rewards",
            query=_qd({'status': status, 'recipient_user_id': recipient_user_id, 'referrer_user_id': referrer_user_id, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        status: Literal['pending', 'granted', 'voided'] | None = None,
        recipient_user_id: str | None = None,
        referrer_user_id: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetReferralRewardsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(status=status, recipient_user_id=recipient_user_id, referrer_user_id=referrer_user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def run(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostReferralRewardsRunResponse:
        """Discover qualifying referrals and grant the rewards whose hold has ended now, instead of
        waiting for the periodic sweep.
        """
        return await self._t.request(
            method="POST",
            path="/v1/referral_rewards/run",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        referral_reward_id: str,
    ) -> cm.GetReferralRewardsResponseDataItem:
        """Read one referral reward by id."""
        return await self._t.request(
            method="GET",
            path=f"/v1/referral_rewards/{_enc(referral_reward_id)}",
        )

    async def void(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/referral_rewards/{_enc(referral_reward_id)}/void",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncRefreshTokens:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/refresh_tokens",
            query=_qd({'user_id': user_id, 'client_id': client_id, 'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        user_id: str | None = None,
        client_id: str | None = None,
        status: Literal['active', 'revoked', 'expired', 'replaced'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetRefreshTokensResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(user_id=user_id, client_id=client_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def revoke(
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
        return await self._t.request(
            method="POST",
            path="/v1/refresh_tokens/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncRegion:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetRegionResponse:
        """Where the instance lives: its region pin, its failover region, Frontend API origin
        isolation and the region table of this deployment. On a single-region deployment
        `regions_enabled` is false and nothing is pinned.
        """
        return await self._t.request(
            method="GET",
            path="/v1/region",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path="/v1/region",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_failover(
        self,
        *,
        mount_host: str,
        base_path: str | None = None,
    ) -> cm.GetRegionFailoverResponse:
        """The upstreams a path-mounted Frontend API's reverse proxy lists to fail over to the
        instance's failover region, with ready nginx and Caddy rules. 422 when the instance has
        no failover region or the region table has no origin for it.
        """
        return await self._t.request(
            method="GET",
            path="/v1/region/failover",
            query=_qd({'mount_host': mount_host, 'base_path': base_path}),
        )


class AsyncResourceRoleAssignments:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_changes(
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
        return await self._t.request(
            method="GET",
            path="/v1/resource_role_assignments/changes",
            query=_qd({'after': after, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_changes(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.ResourceRoleAssignmentChange]:
        """Every item of :meth:`list_changes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_changes(after=after, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncResourceServers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_revoked_tokens(
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
        revoked on its own (`jti`), or a whole client (`kind: "client"`: its `client_id`, with
        `revoked_at` the cut-off: reject any token whose `azp` is that client and whose `iat` is
        at or before it). Reject a token whose `fid` or `jti` is listed. Rows are kept for 48
        hours (`retention_seconds`), longer than any access token can live. Page with `after`
        (the `next_cursor` of the previous page); `server_time` is when the answer was computed:
        poll again with `since` a little before it. The `oauth_tokens.revoked` webhook carries
        the same facts for a push.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/resource_servers/{_enc(resource_server_id)}/revoked_tokens",
            query=_qd({'since': since, 'limit': limit, 'after': after, 'starting_after': starting_after}),
        )

    async def iter_list_revoked_tokens(
        self,
        resource_server_id: str,
        *,
        since: int | None = None,
        limit: int | None = None,
        after: str | None = None,
    ) -> AsyncIterator[cm.GetResourceServersByIdRevokedTokensResponseDataItem]:
        """Every item of :meth:`list_revoked_tokens`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_revoked_tokens(resource_server_id, since=since, limit=limit, after=after, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncRevocations:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        after: str | None = None,
        since: str | None = None,
        kinds: str | None = None,
        limit: str | None = None,
        wait: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRevocationsResponse:
        """Long-poll the revocation stream: one ordered list of everything that ended a session, a
        refresh-token family, an API key, a machine, a machine grant or a person's access, each
        with ids, reason and actor. Resume by cursor: pass the `next_cursor` of the previous
        answer as `after`. With neither `after` nor `since` it answers empty with a
        `next_cursor` that points at "now", so a new consumer starts from this moment. `wait`
        (seconds, up to 30) holds the request open until an event arrives. Order is commit
        order: the cursor is a sequence number assigned to what has committed, so a consumer
        that follows it never skips an event, however late it committed. Retention is the event
        log's (90 days), and webhook endpoints subscribed to the same event types are its second
        channel. Delivery is at-least-once and in order; keep your handler idempotent.
        """
        return await self._t.request(
            method="GET",
            path="/v1/revocations",
            query=_qd({'after': after, 'since': since, 'kinds': kinds, 'limit': limit, 'wait': wait, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        after: str | None = None,
        since: str | None = None,
        kinds: str | None = None,
        limit: str | None = None,
        wait: str | None = None,
    ) -> AsyncIterator[cm.GetRevocationsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(after=after, since=since, kinds=kinds, limit=limit, wait=wait, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_stream(
        self,
        *,
        after: str | None = None,
        since: str | None = None,
        kinds: str | None = None,
    ) -> str:
        """Server-Sent Events stream of the revocation stream (the same events as `GET
        /v1/revocations`). Each `revocation` event carries the frame as JSON and its `seq` as
        the SSE `id`; resume with `Last-Event-ID` or `after`. A `ready` event carries the cursor
        the stream started from, a `: keep-alive` comment arrives every 15 seconds, and a
        `reconnect` event ends a connection after an hour: reconnect with the last id. At most
        20 streams may be open per instance (429 beyond). Same `kinds` and `since` filters.
        `@atlasauth/backend` `revocationStream` and `createRevocationMirror` consume it with
        reconnect, backoff and resume.
        """
        return await self._t.request(
            method="GET",
            path="/v1/revocations/stream",
            query=_qd({'after': after, 'since': since, 'kinds': kinds}),
            raw=True,
        )


class AsyncRiskBasedMfa:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def replay(
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
        return await self._t.request(
            method="POST",
            path="/v1/risk_based_mfa/replay",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncRiskSignals:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/risk_signals",
            query=_qd({'user_id': user_id, 'ip': ip, 'status': status, 'limit': limit, 'before': before, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        user_id: str | None = None,
        ip: str | None = None,
        status: Literal['active', 'all'] | None = None,
        limit: int | None = None,
        before: str | None = None,
    ) -> AsyncIterator[cm.GetRiskSignalsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(user_id=user_id, ip=ip, status=status, limit=limit, before=before, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/risk_signals",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        risk_signal_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskSignalsResponseDataItem:
        """End a risk signal now. Its points leave the next evaluation; the row stays readable with
        status `revoked`.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/risk_signals/{_enc(risk_signal_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        risk_signal_id: str,
    ) -> cm.GetRiskSignalsResponseDataItem:
        """Read one risk signal."""
        return await self._t.request(
            method="GET",
            path=f"/v1/risk_signals/{_enc(risk_signal_id)}",
        )


class AsyncRiskyUsers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        state: Literal['at_risk', 'confirmed_compromised', 'dismissed', 'remediated'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRiskyUsersResponse:
        """The risky-user report: users with a standing risk score, filterable by state."""
        return await self._t.request(
            method="GET",
            path="/v1/risky_users",
            query=_qd({'state': state, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        state: Literal['at_risk', 'confirmed_compromised', 'dismissed', 'remediated'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetRiskyUsersResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(state=state, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get(
        self,
        user_id: str,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """One user's risk state, level, score and reasons."""
        return await self._t.request(
            method="GET",
            path=f"/v1/risky_users/{_enc(user_id)}",
        )

    async def confirm(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """Confirm the account as compromised. The user reads as high risk to access policies until
        remediated.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/confirm",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def dismiss(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """Dismiss the risk (false alarm). The score resets."""
        return await self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/dismiss",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def force_password_change(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostRiskyUsersByUserIdForcePasswordChangeResponse:
        """Require a new password at the next sign-in and end every session."""
        return await self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/force_password_change",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def force_reauth(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostRiskyUsersByUserIdForcePasswordChangeResponse:
        """End every session so the user signs in, and passes MFA, again."""
        return await self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/force_reauth",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def remediate(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskyUsersResponseDataItem:
        """Mark the risk remediated. The score resets."""
        return await self._t.request(
            method="POST",
            path=f"/v1/risky_users/{_enc(user_id)}/remediate",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncSamlIdp:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_service_providers(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSamlIdpServiceProvidersResponse:
        """List the SAML service providers Atlas issues assertions to, with their NameID format,
        encryption, request-signing, algorithm and logout settings.
        """
        return await self._t.request(
            method="GET",
            path="/v1/saml_idp/service_providers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_service_providers(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetSamlIdpServiceProvidersResponseDataItem]:
        """Every item of :meth:`list_service_providers`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_service_providers(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def import_metadata_service_provider(
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
        return await self._t.request(
            method="POST",
            path="/v1/saml_idp/service_providers/import_metadata",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_service_provider(
        self,
        service_provider_id: str,
    ) -> cm.GetSamlIdpServiceProvidersResponseDataItem:
        """Read one SAML service provider's settings."""
        return await self._t.request(
            method="GET",
            path=f"/v1/saml_idp/service_providers/{_enc(service_provider_id)}",
        )

    async def update_service_provider(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/saml_idp/service_providers/{_enc(service_provider_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncScimProvisioningTargets:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_failures(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetScimProvisioningTargetsByIdFailuresResponse:
        """The failed-provision inbox: users and organizations whose last push to this target
        failed, with the error and the number of consecutive attempts.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/scim_provisioning_targets/{_enc(scim_provisioning_target_id)}/failures",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_failures(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetScimProvisioningTargetsByIdFailuresResponseDataItem]:
        """Every item of :meth:`list_failures`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_failures(scim_provisioning_target_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def list_logs(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/scim_provisioning_targets/{_enc(scim_provisioning_target_id)}/logs",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'failures': failures, 'resource_id': resource_id}),
        )

    async def iter_list_logs(
        self,
        scim_provisioning_target_id: str,
        *,
        limit: str | None = None,
        failures: str | None = None,
        resource_id: str | None = None,
    ) -> AsyncIterator[cm.GetScimProvisioningTargetsByIdLogsResponseDataItem]:
        """Every item of :meth:`list_logs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_logs(scim_provisioning_target_id, limit=limit, failures=failures, resource_id=resource_id, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def retry_failed(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/scim_provisioning_targets/{_enc(scim_provisioning_target_id)}/retry_failed",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncScimResourceTypes:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetScimResourceTypesResponse:
        """List the custom SCIM resource types this instance serves beyond Users and Groups."""
        return await self._t.request(
            method="GET",
            path="/v1/scim_resource_types",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetScimResourceTypesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/scim_resource_types",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        scim_resource_type_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a custom SCIM resource type and every resource of it."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/scim_resource_types/{_enc(scim_resource_type_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        scim_resource_type_id: str,
    ) -> cm.GetScimResourceTypesResponseDataItem:
        """Read one custom SCIM resource type."""
        return await self._t.request(
            method="GET",
            path=f"/v1/scim_resource_types/{_enc(scim_resource_type_id)}",
        )


class AsyncScimTokens:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def rotate(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/scim_tokens/{_enc(scim_token_id)}/rotate",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncSecurityAdvisories:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
        security_advisory_id: str,
    ) -> cm.GetSecurityAdvisoriesResponseDataItem:
        """One security advisory for this instance, with `subjects`: the affected users and email
        addresses it names while it applies (up to 100; `subjects_truncated` is true past that
        and `count` stays the full number). 404 for an unknown id.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/security_advisories/{_enc(security_advisory_id)}",
        )


class AsyncSessions:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get_export(
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
        return await self._t.request(
            method="GET",
            path="/v1/sessions/export",
            query=_qd({'user_id': user_id, 'organization_id': organization_id, 'ip': ip, 'country': country, 'device': device, 'risk_level': risk_level, 'min_risk_score': min_risk_score, 'created_after': created_after, 'created_before': created_before, 'active': active, 'format': format, 'limit': limit}),
        )

    async def list_revocations(
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
        return await self._t.request(
            method="GET",
            path="/v1/sessions/revocations",
            query=_qd({'after': after, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_revocations(
        self,
        *,
        after: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetSessionsRevocationsResponseDataItem]:
        """Every item of :meth:`list_revocations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_revocations(after=after, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_revocations_status_list(
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
        return await self._t.request(
            method="GET",
            path="/v1/sessions/revocations/status-list",
            query=_qd({'window_seconds': window_seconds}),
        )

    async def revoke_by_filter(
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
        return await self._t.request(
            method="POST",
            path="/v1/sessions/revoke_by_filter",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_revoke_jobs(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSessionsRevokeJobsResponse:
        """Recent revoke-by-filter jobs, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/sessions/revoke_jobs",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_revoke_jobs(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetSessionsRevokeJobsResponseDataItem]:
        """Every item of :meth:`list_revoke_jobs`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_revoke_jobs(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_revoke_job(
        self,
        revoke_job_id: str,
    ) -> cm.GetSessionsRevokeJobsResponseDataItem:
        """One revoke-by-filter job and its progress (`matched`, `revoked`, `failed`, `status`).
        404 for a job of another instance.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/sessions/revoke_jobs/{_enc(revoke_job_id)}",
        )

    async def list_revoked(
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
        return await self._t.request(
            method="GET",
            path="/v1/sessions/revoked",
            query=_qd({'since': since, 'limit': limit, 'cursor': cursor, 'starting_after': starting_after}),
        )

    async def iter_list_revoked(
        self,
        *,
        since: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> AsyncIterator[cm.GetSessionsRevokedResponseDataItem]:
        """Every item of :meth:`list_revoked`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_revoked(since=since, limit=limit, cursor=cursor, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def set_active_organization(
        self,
        session_id: str,
        body: cm.PutSessionsByIdActiveOrganizationBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.Session:
        """Set (or clear, with organization_id null) the active organization of a session from your
        backend. The user must hold a seat in it (or in an ancestor with role inheritance on)
        and meet its second-factor policy, as for their own switch: an organization they are not
        in is 404, a policy that needs a second factor is 403 STEP_UP_REQUIRED. The next token
        minted for the session (refresh or getToken) carries that organization claims. An ended
        session is 409; an unknown id, or one of another instance, is 404. Returns the session
        with last_active_organization_id.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/sessions/{_enc(session_id)}/active_organization",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_binding(
        self,
        session_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteSessionsByIdBindingResponse:
        """Remove a session's DPoP binding so it can bind a new key (a user who lost their device
        key). Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/sessions/{_enc(session_id)}/binding",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_binding(
        self,
        session_id: str,
    ) -> cm.GetSessionsByIdBindingResponse:
        """Which DPoP key (by thumbprint) a session is bound to, and whether it was attested."""
        return await self._t.request(
            method="GET",
            path=f"/v1/sessions/{_enc(session_id)}/binding",
        )

    async def list_events(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/sessions/{_enc(session_id)}/events",
            query=_qd({'limit': limit, 'after': after, 'starting_after': starting_after}),
        )

    async def iter_list_events(
        self,
        session_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
    ) -> AsyncIterator[cm.GetSessionsByIdEventsResponseDataItem]:
        """Every item of :meth:`list_events`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_events(session_id, limit=limit, after=after, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_risk(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/sessions/{_enc(session_id)}/risk",
        )


class AsyncSsf:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def add_subject(
        self,
        body: cm.PostSsfAddSubjectBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Add a subject to a stream (8.1.3.2). 200, empty body."""
        return await self._t.request(
            method="POST",
            path="/v1/ssf/add_subject",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_configuration(
        self,
        body: dict[str, Any],
        *,
        stream_id: str,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Delete a stream (?stream_id, 8.1.1.5): 204."""
        return await self._t.request(
            method="DELETE",
            path="/v1/ssf/configuration",
            query=_qd({'stream_id': stream_id, 'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_configuration(
        self,
        *,
        stream_id: str | None = None,
    ) -> dict[str, Any]:
        """Read one stream (?stream_id) or all of the receiver's streams (8.1.1.2). Another
        receiver's stream is 404.
        """
        return await self._t.request(
            method="GET",
            path="/v1/ssf/configuration",
            query=_qd({'stream_id': stream_id}),
        )

    async def update_configuration(
        self,
        body: cm.PatchSsfConfigurationBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Update a stream (8.1.1.3): only the members present change; transmitter-supplied members
        must match; the delivery method cannot change.
        """
        return await self._t.request(
            method="PATCH",
            path="/v1/ssf/configuration",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def configuration(
        self,
        body: cm.PostSsfConfigurationBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSsfConfigurationResponse:
        """Create an event stream (OpenID SSF 1.0 8.1.1.1). Receiver-supplied members:
        events_requested, delivery, description. Poll delivery by default (the transmitter
        assigns the endpoint); push needs an https endpoint_url. One stream per receiver (a
        second is 409). The stream belongs to the creating API key.
        """
        return await self._t.request(
            method="POST",
            path="/v1/ssf/configuration",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def set_configuration(
        self,
        body: cm.PutSsfConfigurationBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Replace a stream (8.1.1.4): a missing receiver-supplied member is deleted."""
        return await self._t.request(
            method="PUT",
            path="/v1/ssf/configuration",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_event(
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
        return await self._t.request(
            method="POST",
            path="/v1/ssf/events",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_metadata(
        self,
    ) -> cm.GetSsfMetadataResponse:
        """SSF transmitter configuration metadata (issuer, delivery methods, the five management
        endpoints).
        """
        return await self._t.request(
            method="GET",
            path="/v1/ssf/metadata",
        )

    async def remove_subject(
        self,
        body: cm.PostSsfRemoveSubjectBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Remove a subject from a stream (8.1.3.3). 204; an unknown subject is ignored."""
        return await self._t.request(
            method="POST",
            path="/v1/ssf/remove_subject",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_status(
        self,
        *,
        stream_id: str | None = None,
    ) -> cm.GetSsfStatusResponse:
        """SSF 1.0 stream status endpoint: the status (enabled, paused, disabled) of the stream
        named by the `stream_id` query parameter.
        """
        return await self._t.request(
            method="GET",
            path="/v1/ssf/status",
            query=_qd({'stream_id': stream_id}),
        )

    async def status(
        self,
        body: cm.PostSsfStatusBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 stream status endpoint: set the status of the stream named by `stream_id`."""
        return await self._t.request(
            method="POST",
            path="/v1/ssf/status",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_streams_subjects(
        self,
        stream_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetSsfStreamsByIdSubjectsResponse:
        """The subjects a receiver added to or removed from a stream, with the stream's
        `default_subjects` (ALL or NONE).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/ssf/streams/{_enc(stream_id)}/subjects",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_streams_subjects(
        self,
        stream_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetSsfStreamsByIdSubjectsResponseDataItem]:
        """Every item of :meth:`list_streams_subjects`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_streams_subjects(stream_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def poll_stream(
        self,
        stream_id: str,
        body: cm.PostSsfStreamsByStreamIdPollBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSsfStreamsByStreamIdPollResponse:
        """Poll a stream (RFC 8936): acknowledge with ack, report invalid SETs with setErrs,
        receive up to maxEvents unacknowledged SETs.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/ssf/streams/{_enc(stream_id)}/poll",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def add_subject(
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
        return await self._t.request(
            method="POST",
            path="/v1/ssf/subjects/add",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def remove_subject(
        self,
        body: cm.PostSsfSubjectsRemoveBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 remove subject: stop events for one subject on a stream (on an ALL stream), or
        drop an earlier add (on a NONE stream). 204.
        """
        return await self._t.request(
            method="POST",
            path="/v1/ssf/subjects/remove",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verification(
        self,
        body: cm.PostSsfVerificationBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Request a verification event (8.1.4.2): 204, and a signed SET carrying the optional
        state is delivered on the stream (pushed, or retained for polling).
        """
        return await self._t.request(
            method="POST",
            path="/v1/ssf/verification",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def verify(
        self,
        body: cm.PostSsfVerifyBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """SSF 1.0 verification endpoint: queue a verification event carrying `state` for the
        stream named by `stream_id`. 204.
        """
        return await self._t.request(
            method="POST",
            path="/v1/ssf/verify",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncSsoConnections:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_login_history(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/sso_connections/{_enc(sso_connection_id)}/login_history",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'outcome': outcome}),
        )

    async def iter_list_login_history(
        self,
        sso_connection_id: str,
        *,
        limit: str | None = None,
        outcome: Literal['success', 'failure', 'test'] | None = None,
    ) -> AsyncIterator[cm.GetSsoConnectionsByIdLoginHistoryResponseDataItem]:
        """Every item of :meth:`list_login_history`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_login_history(sso_connection_id, limit=limit, outcome=outcome, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def test(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{_enc(sso_connection_id)}/test",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test_login(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/sso_connections/{_enc(sso_connection_id)}/test_login",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncStepUp:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def assert_(
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
        return await self._t.request(
            method="POST",
            path="/v1/step_up/assert",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_policies(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetStepUpPoliciesResponse:
        """List the named step-up policies of the instance."""
        return await self._t.request(
            method="GET",
            path="/v1/step_up/policies",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_policies(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetStepUpPoliciesResponseDataItem]:
        """Every item of :meth:`list_policies`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_policies(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_policy(
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
        return await self._t.request(
            method="POST",
            path="/v1/step_up/policies",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_policy(
        self,
        policy_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteStepUpPoliciesByIdResponse:
        """Delete a step-up policy. An assertion that names it afterwards answers 404, so a service
        that still asks fails closed.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/step_up/policies/{_enc(policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_policy(
        self,
        policy_id: str,
    ) -> cm.GetStepUpPoliciesResponseDataItem:
        """Read one step-up policy."""
        return await self._t.request(
            method="GET",
            path=f"/v1/step_up/policies/{_enc(policy_id)}",
        )

    async def update_policy(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/step_up/policies/{_enc(policy_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncSuppressions:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
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
        return await self._t.request(
            method="GET",
            path="/v1/suppressions",
            query=_qd({'channel': channel, 'reason': reason, 'address': address, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        channel: Literal['email', 'sms', 'whatsapp', 'voice', 'push'] | None = None,
        reason: str | None = None,
        address: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetSuppressionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(channel=channel, reason=reason, address=address, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
        self,
        body: cm.PostSuppressionsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostSuppressionsResponse:
        """Add one address or up to 1000 to the suppression list. Adding one that is already there
        updates its reason. Audited; emits message_suppression.created for new entries.
        """
        return await self._t.request(
            method="POST",
            path="/v1/suppressions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        suppression_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteSuppressionsByIdResponse:
        """Take an address off the suppression list; messages to it are sent again. Audited."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/suppressions/{_enc(suppression_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        suppression_id: str,
    ) -> cm.GetSuppressionsResponseDataItem:
        """Read one suppressed address and why it is suppressed."""
        return await self._t.request(
            method="GET",
            path=f"/v1/suppressions/{_enc(suppression_id)}",
        )


class AsyncTelemetryExport:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetTelemetryExportResponse:
        """The instance's OTLP export settings for MCP gateway and connection relay calls."""
        return await self._t.request(
            method="GET",
            path="/v1/telemetry_export",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path="/v1/telemetry_export",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def test(
        self,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostTelemetryExportTestResponse:
        """Send one test span to the configured collector now. Answers ok or the collector's error;
        never fails the request.
        """
        return await self._t.request(
            method="POST",
            path="/v1/telemetry_export/test",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncUsage:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_connections(
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
        return await self._t.request(
            method="GET",
            path="/v1/usage/connections",
            query=_qd({'from': from_, 'to': to, 'group_by': group_by, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_connections(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        group_by: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsageConnectionsResponseDataItem]:
        """Every item of :meth:`list_connections`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_connections(from_=from_, to=to, group_by=group_by, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncUsers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_bulk_actions(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        status: Literal['pending', 'processing', 'completed', 'failed', 'cancelled'] | None = None,
    ) -> cm.GetUsersBulkActionsResponse:
        """The bulk user actions of the instance, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/users/bulk_actions",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'status': status}),
        )

    async def iter_list_bulk_actions(
        self,
        *,
        limit: int | None = None,
        status: Literal['pending', 'processing', 'completed', 'failed', 'cancelled'] | None = None,
    ) -> AsyncIterator[cm.GetUsersBulkActionsResponseDataItem]:
        """Every item of :meth:`list_bulk_actions`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_bulk_actions(limit=limit, status=status, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_bulk_action(
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
        return await self._t.request(
            method="POST",
            path="/v1/users/bulk_actions",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_bulk_action(
        self,
        bulk_action_id: str,
    ) -> cm.GetUsersBulkActionsResponseDataItem:
        """One bulk user action: status, progress, counts and the first errors."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/bulk_actions/{_enc(bulk_action_id)}",
        )

    async def cancel_bulk_action(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/bulk_actions/{_enc(bulk_action_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_by_external_id(
        self,
        external_id: str,
        body: cm.PutUsersByExternalIdByExternalIdBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.User:
        """Create-or-update the user keyed by your own id (external_id, the path segment, URL-
        encoded): 201 with the new user when none holds it (the body is that of POST /v1/users,
        email_address required, external_id from the path), else 200 with the existing user
        updated (only first_name, last_name, image_url, public_metadata, private_metadata,
        unsafe_metadata, password and referral_code apply; email fields and the other create-
        only fields are ignored). Two calls racing for a new external_id create exactly one
        user. When nobody holds the id but a user already has the address, the answer is 409
        IDENTIFIER_EXISTS with meta.user_id; send link_by_verified_email: true to adopt that
        user instead (200), which works only when the address is verified in Atlas and the user
        has no external_id yet (a different id is never overwritten). Emits user.created or
        user.updated.
        """
        return await self._t.request(
            method="PUT",
            path=f"/v1/users/by_external_id/{_enc(external_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_deleted(
        self,
        *,
        since: str,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersDeletedResponse:
        """Reconcile missed `user.deleted` webhooks: every user deleted at or after `since`, oldest
        first, as `id`, `external_id` and `deleted_at`. Nothing else about the person is
        returned. Page with `starting_after` = the previous `next_cursor`. Rows exist until the
        personal-data scrub (`compliance.retention.deletedUserGraceDays`, default 30 days), so
        reconcile at least that often; failed deliveries themselves are listed by `GET
        /v1/webhook_dlq?event_type=user.deleted`.
        """
        return await self._t.request(
            method="GET",
            path="/v1/users/deleted",
            query=_qd({'since': since, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_deleted(
        self,
        *,
        since: str,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersDeletedResponseDataItem]:
        """Every item of :meth:`list_deleted`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_deleted(since=since, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_deleted_address(
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
        return await self._t.request(
            method="POST",
            path="/v1/users/deleted_addresses",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def check_deleted_address(
        self,
        body: cm.PostUsersDeletedAddressesCheckBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersDeletedAddressesCheckResponse:
        """Whether an address is remembered as belonging to a deleted account, whatever the
        instance's deletedUserReturn mode.
        """
        return await self._t.request(
            method="POST",
            path="/v1/users/deleted_addresses/check",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_search_fields(
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
        return await self._t.request(
            method="GET",
            path="/v1/users/search/fields",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_search_fields(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersSearchFieldsResponseDataItem]:
        """Every item of :meth:`list_search_fields`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_search_fields(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def count_view_search(
        self,
        view_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Count a saved search (a segment) now and keep the number and the time on it
        (member_count, counted_at).
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/search/views/{_enc(view_id)}/count",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_age_assurance(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdAgeAssuranceResponse:
        """The age assurance records of a user, newest first, with whether each is trusted by
        compliance.minors.trustedAgeMethods.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/age_assurance",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_age_assurance(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersByIdAgeAssuranceResponseDataItem]:
        """Every item of :meth:`list_age_assurance`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_age_assurance(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def age_assurance(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/age_assurance",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def revoke_age_assurance(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/age_assurance/{_enc(assurance_id)}/revoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_approval_devices(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/approval_devices",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_approval_devices(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersByIdApprovalDevicesResponseDataItem]:
        """Every item of :meth:`list_approval_devices`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_approval_devices(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def trust_approval_device(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/approval_devices/trust",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_approval_device(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/approval_devices/{_enc(device_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_approval_requests(
        self,
        user_id: str,
        *,
        status: str | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdApprovalRequestsResponse:
        """Everything one user has open, in one list: approval requests about them (filter with
        `status`; `limit` 1 to 100, default 25) and, while `status` is pending or absent, their
        sign-in "approve in your app" requests (`kind: "sign_in_approval"`, with `purpose`, the
        shuffled `choices` and `requested_from`; the right number is never included). Replaces
        keeping your own pointer to the latest request. Needs `approvals:read` (a key with
        `users:read` keeps working).
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/approval_requests",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_approval_requests(
        self,
        user_id: str,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersByIdApprovalRequestsResponseDataItem]:
        """Every item of :meth:`list_approval_requests`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_approval_requests(user_id, status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def cancel_approval_request(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/approval_requests/{_enc(approval_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def contain(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/contain",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_cookie_consents(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteCookieConsentsSubjectsBySubjectResponse:
        """Erase the cookie consent records linked to a user. Deleting the user does this too.
        Audited.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/cookie_consents",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def create_delegation_token(
        self,
        user_id: str,
        body: cm.PostUsersByIdDelegationTokensBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostUsersByIdDelegationTokensResponse:
        """Mint a short-lived delegation token so your server can act as this user for one purpose.
        The token is limited to a named `audience` and a list of `scopes` (both must be on the
        instance's `delegationTokens` settings), lives at most 300 seconds (default 120), and
        carries an `act` claim naming `actor.sub`, so a service can see it is not the user
        themselves. Refused for banned, deleted and impersonation-protected users, and for an
        `org_id` the user does not belong to. Every mint is audited on the user's trail as
        `user.delegation_token_issued` (the token itself is never stored). Rate limited per key
        and per user. Send an Idempotency-Key to make a retry return the same token.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/delegation_tokens",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def update_deletion(
        self,
        user_id: str,
        body: cm.PatchUsersByIdDeletionBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.User:
        """Move a scheduled deletion to a new date. Send exactly one of `effective_at` (ISO 8601,
        not in the past) or `grace_seconds` (from now). The user's deletion date, the in-flight
        erasure request's scheduled date and the reminder plan all move together; the person is
        mailed the new date and `user.deletion_rescheduled` is emitted. The `pre_user_deletion`
        Actions are asked again for the new date (a refusal is 403 ACTION_BLOCKED) and a legal
        hold refuses the move. 409 when the user has no scheduled deletion, the deletion is
        paused (resume it with POST /v1/users/{id}/deletion/reconfirm first) or the user is
        already erased. Returns the user.
        """
        return await self._t.request(
            method="PATCH",
            path=f"/v1/users/{_enc(user_id)}/deletion",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def reconfirm_deletion(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/deletion/reconfirm",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def create_external_account(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/external_accounts",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_external_account(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/external_accounts/{_enc(account_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def import_identity_verification(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/identity_verifications/import",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_identity_verification(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/identity_verifications/{_enc(attempt_id)}",
        )

    async def delete_journeys(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/journeys",
            query=_qd({'journey_id': journey_id, 'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_journeys(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetFlowsByIdRunsResponse:
        """One user's journey runs, newest first, with what they saved so far (draft, by step) so
        an onboarding resumes where they stopped.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/journeys",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_journeys(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetFlowsByIdRunsResponseDataItem]:
        """Every item of :meth:`list_journeys`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_journeys(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def get_legal_hold(
        self,
        user_id: str,
    ) -> cm.GetUsersByIdLegalHoldResponse:
        """Whether the user is on legal hold, the active hold, and every hold they ever had."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/legal_hold",
        )

    async def legal_hold(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/legal_hold",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def release_legal_hold(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/legal_hold/release",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def merge(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/merge",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_owned_organizations(
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
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/owned_organizations",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_owned_organizations(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersByIdOwnedOrganizationsResponseDataItem]:
        """Every item of :meth:`list_owned_organizations`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_owned_organizations(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def resync_referral(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/referral/resync",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def release(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetContainmentsResponseDataItem:
        """Release a contained account. The user can sign in again and still owes the password
        change.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/release",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def delete_risk_signals(
        self,
        user_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteUsersByIdRiskSignalsResponse:
        """End every live risk signal on one user now. Their points leave the next evaluation; the
        rows stay readable with status `revoked`. Recorded once in the audit log. Safe to
        repeat: with nothing live, it clears nothing.
        """
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/risk_signals",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def list_risk_signals(
        self,
        user_id: str,
        *,
        status: Literal['active', 'all'] | None = None,
        limit: int | None = None,
        before: str | None = None,
        starting_after: str | None = None,
    ) -> cm.GetRiskSignalsResponse:
        """The risk signals reported for one user, newest first; `status=active` keeps only live
        ones. Page with `before`.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/risk_signals",
            query=_qd({'status': status, 'limit': limit, 'before': before, 'starting_after': starting_after}),
        )

    async def iter_list_risk_signals(
        self,
        user_id: str,
        *,
        status: Literal['active', 'all'] | None = None,
        limit: int | None = None,
        before: str | None = None,
    ) -> AsyncIterator[cm.GetRiskSignalsResponseDataItem]:
        """Every item of :meth:`list_risk_signals`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_risk_signals(user_id, status=status, limit=limit, before=before, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_risk_signal(
        self,
        user_id: str,
        body: cm.PostUsersByIdRiskSignalsBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetRiskSignalsResponseDataItem:
        """Raise one user's sign-in risk for a window. The same signal as POST /v1/risk_signals
        with the user named by the path. While it is live and risk-based MFA is on, it adds
        points to every sign-in evaluation of that user (low 10, medium 25, high 50, critical
        100; the total is capped at 100), which can turn into a second factor, an enrolment or a
        block under the instance's risk policy. It never lowers friction. ttl_seconds 60 to
        2592000, default 3600; it expires by itself. Honours Idempotency-Key. Emits
        risk_signal.created.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/risk_signals",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_security_summary(
        self,
        user_id: str,
    ) -> cm.GetUsersByIdSecuritySummaryResponse:
        """One read of how the account is protected: password and when it last changed, sign-in
        methods the user can use right now, linked providers, verified second factors, recovery
        codes left, passkeys, remembered browsers and device keys, and the open sessions (count
        and the newest). Ids and labels only: never a password hash, second-factor secret,
        recovery code, credential id or key material.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/security_summary",
        )

    async def list_temporary_access(
        self,
        user_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetUsersByIdTemporaryAccessResponse:
        """The user's active temporary access passes (never the codes)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/users/{_enc(user_id)}/temporary_access",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_temporary_access(
        self,
        user_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetUsersByIdTemporaryAccessResponseDataItem]:
        """Every item of :meth:`list_temporary_access`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_temporary_access(user_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def temporary_access(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/users/{_enc(user_id)}/temporary_access",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_temporary_access(
        self,
        user_id: str,
        pass_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteUsersByIdTemporaryAccessByPassIdResponse:
        """Revoke a temporary access pass."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/users/{_enc(user_id)}/temporary_access/{_enc(pass_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncVc:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_deferred(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'issued'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetVcDeferredResponse:
        """List deferred issuances waiting for an operator decision."""
        return await self._t.request(
            method="GET",
            path="/v1/vc/deferred",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_deferred(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'issued'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetVcDeferredResponseDataItem]:
        """Every item of :meth:`list_deferred`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_deferred(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def approve_deferred(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/vc/deferred/{_enc(deferred_id)}/approve",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def deny_deferred(
        self,
        deferred_id: str,
        body: cm.PostVcDeferredByIdDenyBody | None = None,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Deny a deferred issuance; the wallet is told issuance was refused."""
        return await self._t.request(
            method="POST",
            path=f"/v1/vc/deferred/{_enc(deferred_id)}/deny",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_presentation_requests_dc_api_request(
        self,
        presentation_request_id: str,
    ) -> cm.GetVcPresentationRequestsByIdDcApiRequestResponse:
        """The OpenID4VP request for the Digital Credentials API (navigator.credentials.get), for a
        presentation request with expected_origins.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/vc/presentation_requests/{_enc(presentation_request_id)}/dc_api_request",
        )


class AsyncWebBotAuth:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def get(
        self,
    ) -> cm.GetWebBotAuthResponse:
        """The instance allow and block lists of signed-bot directories."""
        return await self._t.request(
            method="GET",
            path="/v1/web_bot_auth",
        )

    async def set(
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
        return await self._t.request(
            method="PUT",
            path="/v1/web_bot_auth",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_directories(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetAgentAccessRequestsResponse:
        """The listed directories, one row each with its list (allow or block)."""
        return await self._t.request(
            method="GET",
            path="/v1/web_bot_auth/directories",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_directories(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Every item of :meth:`list_directories`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_directories(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_directory(
        self,
        body: cm.PostWebBotAuthDirectoriesBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Put one directory on the allow or block list; it leaves the other list if it was there."""
        return await self._t.request(
            method="POST",
            path="/v1/web_bot_auth/directories",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_directory(
        self,
        directory_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeleteWebBotAuthDirectoriesByIdResponse:
        """Take a directory off both lists."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/web_bot_auth/directories/{_enc(directory_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncWebhookDlq:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        event_type: str | None = None,
    ) -> cm.GetWebhookDlqResponse:
        """The dead-letter queue of the whole instance: deliveries that used every attempt on any
        endpoint, newest first, each with `endpoint_id`, the payload that was sent, the last
        response and the error. Narrow it with `event_type` (for example `user.deleted`) to find
        every failed delivery of one event; acknowledge or requeue per endpoint with the
        endpoint dlq routes. Cursor: `starting_after` with the `next_cursor` of the previous
        page.
        """
        return await self._t.request(
            method="GET",
            path="/v1/webhook_dlq",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'event_type': event_type}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
        event_type: str | None = None,
    ) -> AsyncIterator[cm.GetWebhookDlqResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, event_type=event_type, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncWebhookEndpoints:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_dlq(
        self,
        webhook_endpoint_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        event_type: str | None = None,
    ) -> cm.GetWebhookEndpointsByIdDlqResponse:
        """The dead-letter queue of an endpoint: deliveries that used every attempt, newest first,
        each with the payload that was sent, the last response and the error. `depth` counts
        what nobody has acknowledged yet. Pull a page, handle it (or fix the receiver and
        requeue), then acknowledge, so a consumer that cannot take pushes can work failures off
        as a queue. Cursor: `starting_after` with the `next_cursor` of the previous page.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/webhook_endpoints/{_enc(webhook_endpoint_id)}/dlq",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'event_type': event_type}),
        )

    async def iter_list_dlq(
        self,
        webhook_endpoint_id: str,
        *,
        limit: int | None = None,
        event_type: str | None = None,
    ) -> AsyncIterator[cm.WebhookDelivery]:
        """Every item of :meth:`list_dlq`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_dlq(webhook_endpoint_id, limit=limit, event_type=event_type, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def ack_dlq(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(webhook_endpoint_id)}/dlq/ack",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def requeue_dlq(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/webhook_endpoints/{_enc(webhook_endpoint_id)}/dlq/requeue",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncWorkflowApprovals:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'timed_out'] | None = None,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowApprovalsResponse:
        """Approvals that workflow `approval` steps have asked for, newest first."""
        return await self._t.request(
            method="GET",
            path="/v1/workflow_approvals",
            query=_qd({'status': status, 'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        status: Literal['pending', 'approved', 'denied', 'timed_out'] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetWorkflowApprovalsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(status=status, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def decide(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/workflow_approvals/{_enc(workflow_approval_id)}/decide",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncWorkflowTemplates:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowTemplatesResponse:
        """Starter workflows (joiner, mover, leaver, inactive user, expiring guest) with the
        parameters each needs.
        """
        return await self._t.request(
            method="GET",
            path="/v1/workflow_templates",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetWorkflowTemplatesResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncWorkflowTriggers:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowTriggersResponse:
        """The events a workflow can start on (`trigger.type = webhook_event`): each name, what it
        means, which fields its data carries (usable as `event.<field>` in a trigger filter or a
        step) and which part of the product emits it.
        """
        return await self._t.request(
            method="GET",
            path="/v1/workflow_triggers",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetWorkflowTriggersResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return


class AsyncWorkflows:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def from_template(
        self,
        body: cm.PostWorkflowsFromTemplateBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.Workflow:
        """Create a workflow from a starter template. It is created disabled unless `enabled` is
        true, so you can look it over first.
        """
        return await self._t.request(
            method="POST",
            path="/v1/workflows/from_template",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def invoke(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/invoke",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def list_kv(
        self,
        workflow_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWorkflowsByIdKvResponse:
        """The workflow's key-value table (what `kv` steps read and write)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/workflows/{_enc(workflow_id)}/kv",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_kv(
        self,
        workflow_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetWorkflowsByIdKvResponseDataItem]:
        """Every item of :meth:`list_kv`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_kv(workflow_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def delete_kv(
        self,
        workflow_id: str,
        key: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWorkflowsByIdKvResponseDataItem:
        """Delete a key from the workflow key-value table."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/workflows/{_enc(workflow_id)}/kv/{_enc(key)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def set_kv(
        self,
        workflow_id: str,
        key: str,
        body: cm.PutWorkflowsByIdKvByKeyBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetWorkflowsByIdKvResponseDataItem:
        """Set a key in the workflow key-value table."""
        return await self._t.request(
            method="PUT",
            path=f"/v1/workflows/{_enc(workflow_id)}/kv/{_enc(key)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def get_run(
        self,
        workflow_id: str,
        run_id: str,
    ) -> cm.WorkflowRun:
        """One run with its per-step log: each step's path, status, attempt, detail and output."""
        return await self._t.request(
            method="GET",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}",
        )

    async def cancel_run(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}/cancel",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def resume_run(
        self,
        workflow_id: str,
        run_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.WorkflowRun:
        """Retry a failed run from the step that failed, keeping its variables and earlier outputs."""
        return await self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}/resume",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def retry_run(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/workflows/{_enc(workflow_id)}/runs/{_enc(run_id)}/retry",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncWsfedConnections:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetWsfedConnectionsResponse:
        """List WS-Federation relying-party connections (sign people in through AD FS or another
        WS-Federation provider).
        """
        return await self._t.request(
            method="GET",
            path="/v1/wsfed_connections",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list(
        self,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetWsfedConnectionsResponseDataItem]:
        """Every item of :meth:`list`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list(limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create(
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
        return await self._t.request(
            method="POST",
            path="/v1/wsfed_connections",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete(
        self,
        wsfed_connection_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> Any:
        """Delete a WS-Federation connection."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/wsfed_connections/{_enc(wsfed_connection_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get(
        self,
        wsfed_connection_id: str,
    ) -> cm.GetWsfedConnectionsResponseDataItem:
        """Read one WS-Federation connection with the reply URL to enter at the provider."""
        return await self._t.request(
            method="GET",
            path=f"/v1/wsfed_connections/{_enc(wsfed_connection_id)}",
        )

    async def update(
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
        return await self._t.request(
            method="PATCH",
            path=f"/v1/wsfed_connections/{_enc(wsfed_connection_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPlatformApps:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_instances_clones(
        self,
        app_id: str,
        instance_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        kind: Literal['clone', 'preview'] | None = None,
    ) -> cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponse:
        """The clones and previews of one instance, newest first (deleted ones are left out)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones",
            query=_qd({'limit': limit, 'starting_after': starting_after, 'kind': kind}),
        )

    async def iter_list_instances_clones(
        self,
        app_id: str,
        instance_id: str,
        *,
        limit: int | None = None,
        kind: Literal['clone', 'preview'] | None = None,
    ) -> AsyncIterator[cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponseDataItem]:
        """Every item of :meth:`list_instances_clones`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_instances_clones(app_id, instance_id, limit=limit, kind=kind, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_instances_clone(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_instances_clone(
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
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones/{_enc(clone_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )

    async def get_instances_clone(
        self,
        app_id: str,
        instance_id: str,
        clone_id: str,
    ) -> cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponseDataItem:
        """One clone or preview: status, what was copied, what could not be placed, and when a
        preview expires.
        """
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones/{_enc(clone_id)}",
        )

    async def refresh_clone_instances(
        self,
        app_id: str,
        instance_id: str,
        clone_id: str,
        body: cm.PostPlatformAppsByIdInstancesByInstanceIdClonesByCloneIdRefreshBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.GetPlatformAppsByIdInstancesByInstanceIdClonesResponseDataItem:
        """Bring a completed clone or preview up to date in place (same instance, keys and host);
        same body and rules as POST /v1/instance/staging_copies/{id}/refresh. Needs
        platform:apps:write.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/instances/{_enc(instance_id)}/clones/{_enc(clone_id)}/refresh",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def create_narrow_secret_key(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/narrow_secret_keys",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def renew_provisioning_key(
        self,
        app_id: str,
        body: cm.PostPlatformAppsByIdProvisioningKeyRenewBody,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.PostPlatformAppsByIdProvisioningKeyRenewResponse:
        """Extend the `provisioning` key of an app created with `secret_key_profile: "web_app"` by
        another 24 hours.
        """
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/apps/{_enc(app_id)}/provisioning_key/renew",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )


class AsyncPlatformAtlasIdApps:
    _t: _AsyncTransport

    def __init__(self, transport: _AsyncTransport) -> None:
        self._t = transport

    async def list_adoption_codes(
        self,
        atlas_id_app_id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> cm.GetPlatformAtlasIdAppsByIdAdoptionCodesResponse:
        """The adoption codes issued for an app and what became of them (never the code itself)."""
        return await self._t.request(
            method="GET",
            path=f"/v1/platform/atlas_id_apps/{_enc(atlas_id_app_id)}/adoption_codes",
            query=_qd({'limit': limit, 'starting_after': starting_after}),
        )

    async def iter_list_adoption_codes(
        self,
        atlas_id_app_id: str,
        *,
        limit: int | None = None,
    ) -> AsyncIterator[cm.GetPlatformAtlasIdAppsByIdAdoptionCodesResponseDataItem]:
        """Every item of :meth:`list_adoption_codes`, following the cursor page by page."""
        cursor: str | None = None
        while True:
            page = await self.list_adoption_codes(atlas_id_app_id, limit=limit, starting_after=cursor)
            for item in page.get("data", []):
                yield item
            cursor = page.get("next_cursor")
            if not page.get("has_more") or not cursor:
                return

    async def create_adoption_code(
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
        return await self._t.request(
            method="POST",
            path=f"/v1/platform/atlas_id_apps/{_enc(atlas_id_app_id)}/adoption_codes",
            query=_qd({'dry_run': True if dry_run else None}),
            body=body,
            idempotency_key=idempotency_key,
        )

    async def delete_adoption_code(
        self,
        atlas_id_app_id: str,
        code_id: str,
        *,
        dry_run: bool = False,
        idempotency_key: str | None = None,
    ) -> cm.DeletePlatformAtlasIdAppsByIdAdoptionCodesByCodeIdResponse:
        """Withdraw an adoption code that has not been redeemed."""
        return await self._t.request(
            method="DELETE",
            path=f"/v1/platform/atlas_id_apps/{_enc(atlas_id_app_id)}/adoption_codes/{_enc(code_id)}",
            query=_qd({'dry_run': True if dry_run else None}),
            idempotency_key=idempotency_key,
        )


class AsyncCatalogClient:
    """Namespaces for the resources the hand-written client has no attribute for."""
    abac_policies: AsyncAbacPolicies
    abuse_signals: AsyncAbuseSignals
    administrative_units: AsyncAdministrativeUnits
    agent_access_reviews: AsyncAgentAccessReviews
    agent_delegations: AsyncAgentDelegations
    allowlist_identifiers: AsyncAllowlistIdentifiers
    approval_requests: AsyncApprovalRequests
    atlas_id_apps: AsyncAtlasIdApps
    audit: AsyncAudit
    audit_retention: AsyncAuditRetention
    authenticator_policies: AsyncAuthenticatorPolicies
    authz: AsyncAuthz
    authz_pdps: AsyncAuthzPdps
    blocklist_identifiers: AsyncBlocklistIdentifiers
    changes: AsyncChanges
    chat_integrations: AsyncChatIntegrations
    cloud_access: AsyncCloudAccess
    compliance: AsyncCompliance
    config: AsyncConfig
    connection_actions: AsyncConnectionActions
    connection_provider_changes: AsyncConnectionProviderChanges
    connection_provider_event_log: AsyncConnectionProviderEventLog
    connection_provider_topics: AsyncConnectionProviderTopics
    connection_providers: AsyncConnectionProviders
    connection_reconnect_settings: AsyncConnectionReconnectSettings
    connection_templates: AsyncConnectionTemplates
    containments: AsyncContainments
    cookie_consents: AsyncCookieConsents
    dev: AsyncDev
    device_assurance_policies: AsyncDeviceAssurancePolicies
    device_integrations: AsyncDeviceIntegrations
    device_sso: AsyncDeviceSso
    dsr_console: AsyncDsrConsole
    erasure_connector_catalog: AsyncErasureConnectorCatalog
    erasure_connectors: AsyncErasureConnectors
    federation: AsyncFederation
    flows: AsyncFlows
    fraud: AsyncFraud
    impersonations: AsyncImpersonations
    legal_holds: AsyncLegalHolds
    machine_trust_policies: AsyncMachineTrustPolicies
    mcp_registry: AsyncMcpRegistry
    message_links: AsyncMessageLinks
    message_receivers: AsyncMessageReceivers
    messages: AsyncMessages
    messaging: AsyncMessaging
    mfa_campaigns: AsyncMfaCampaigns
    mfa_factor_quarantines: AsyncMfaFactorQuarantines
    migrations__source: AsyncMigrationsSource
    migrations_status: AsyncMigrationsStatus
    native_apps: AsyncNativeApps
    oauth_application_types: AsyncOauthApplicationTypes
    oauth_consent_requests: AsyncOauthConsentRequests
    oauth_device_requests: AsyncOauthDeviceRequests
    oauth_grants: AsyncOauthGrants
    oauth_publishers: AsyncOauthPublishers
    opa: AsyncOpa
    org_role_sets: AsyncOrgRoleSets
    org_templates: AsyncOrgTemplates
    organization_connections: AsyncOrganizationConnections
    organization_invitations: AsyncOrganizationInvitations
    passkey_campaigns: AsyncPasskeyCampaigns
    permission_aliases: AsyncPermissionAliases
    provisioning: AsyncProvisioning
    provisioning_connectors: AsyncProvisioningConnectors
    rate_limit_overrides: AsyncRateLimitOverrides
    rate_limit_policies: AsyncRateLimitPolicies
    referral_reward_rules: AsyncReferralRewardRules
    referral_rewards: AsyncReferralRewards
    refresh_tokens: AsyncRefreshTokens
    region: AsyncRegion
    resource_role_assignments: AsyncResourceRoleAssignments
    revocations: AsyncRevocations
    risk_signals: AsyncRiskSignals
    risky_users: AsyncRiskyUsers
    saml_idp: AsyncSamlIdp
    scim_resource_types: AsyncScimResourceTypes
    step_up: AsyncStepUp
    suppressions: AsyncSuppressions
    telemetry_export: AsyncTelemetryExport
    web_bot_auth: AsyncWebBotAuth
    webhook_dlq: AsyncWebhookDlq
    webhook_endpoints: AsyncWebhookEndpoints
    workflow_approvals: AsyncWorkflowApprovals
    workflow_templates: AsyncWorkflowTemplates
    workflow_triggers: AsyncWorkflowTriggers
    wsfed_connections: AsyncWsfedConnections

    def _wire_catalog(self, transport: _AsyncTransport) -> None:
        self.abac_policies = AsyncAbacPolicies(transport)
        self.abuse_signals = AsyncAbuseSignals(transport)
        self.administrative_units = AsyncAdministrativeUnits(transport)
        self.agent_access_reviews = AsyncAgentAccessReviews(transport)
        self.agent_delegations = AsyncAgentDelegations(transport)
        self.allowlist_identifiers = AsyncAllowlistIdentifiers(transport)
        self.approval_requests = AsyncApprovalRequests(transport)
        self.atlas_id_apps = AsyncAtlasIdApps(transport)
        self.audit = AsyncAudit(transport)
        self.audit_retention = AsyncAuditRetention(transport)
        self.authenticator_policies = AsyncAuthenticatorPolicies(transport)
        self.authz = AsyncAuthz(transport)
        self.authz_pdps = AsyncAuthzPdps(transport)
        self.blocklist_identifiers = AsyncBlocklistIdentifiers(transport)
        self.changes = AsyncChanges(transport)
        self.chat_integrations = AsyncChatIntegrations(transport)
        self.cloud_access = AsyncCloudAccess(transport)
        self.compliance = AsyncCompliance(transport)
        self.config = AsyncConfig(transport)
        self.connection_actions = AsyncConnectionActions(transport)
        self.connection_provider_changes = AsyncConnectionProviderChanges(transport)
        self.connection_provider_event_log = AsyncConnectionProviderEventLog(transport)
        self.connection_provider_topics = AsyncConnectionProviderTopics(transport)
        self.connection_providers = AsyncConnectionProviders(transport)
        self.connection_reconnect_settings = AsyncConnectionReconnectSettings(transport)
        self.connection_templates = AsyncConnectionTemplates(transport)
        self.containments = AsyncContainments(transport)
        self.cookie_consents = AsyncCookieConsents(transport)
        self.dev = AsyncDev(transport)
        self.device_assurance_policies = AsyncDeviceAssurancePolicies(transport)
        self.device_integrations = AsyncDeviceIntegrations(transport)
        self.device_sso = AsyncDeviceSso(transport)
        self.dsr_console = AsyncDsrConsole(transport)
        self.erasure_connector_catalog = AsyncErasureConnectorCatalog(transport)
        self.erasure_connectors = AsyncErasureConnectors(transport)
        self.federation = AsyncFederation(transport)
        self.flows = AsyncFlows(transport)
        self.fraud = AsyncFraud(transport)
        self.impersonations = AsyncImpersonations(transport)
        self.legal_holds = AsyncLegalHolds(transport)
        self.machine_trust_policies = AsyncMachineTrustPolicies(transport)
        self.mcp_registry = AsyncMcpRegistry(transport)
        self.message_links = AsyncMessageLinks(transport)
        self.message_receivers = AsyncMessageReceivers(transport)
        self.messages = AsyncMessages(transport)
        self.messaging = AsyncMessaging(transport)
        self.mfa_campaigns = AsyncMfaCampaigns(transport)
        self.mfa_factor_quarantines = AsyncMfaFactorQuarantines(transport)
        self.migrations__source = AsyncMigrationsSource(transport)
        self.migrations_status = AsyncMigrationsStatus(transport)
        self.native_apps = AsyncNativeApps(transport)
        self.oauth_application_types = AsyncOauthApplicationTypes(transport)
        self.oauth_consent_requests = AsyncOauthConsentRequests(transport)
        self.oauth_device_requests = AsyncOauthDeviceRequests(transport)
        self.oauth_grants = AsyncOauthGrants(transport)
        self.oauth_publishers = AsyncOauthPublishers(transport)
        self.opa = AsyncOpa(transport)
        self.org_role_sets = AsyncOrgRoleSets(transport)
        self.org_templates = AsyncOrgTemplates(transport)
        self.organization_connections = AsyncOrganizationConnections(transport)
        self.organization_invitations = AsyncOrganizationInvitations(transport)
        self.passkey_campaigns = AsyncPasskeyCampaigns(transport)
        self.permission_aliases = AsyncPermissionAliases(transport)
        self.provisioning = AsyncProvisioning(transport)
        self.provisioning_connectors = AsyncProvisioningConnectors(transport)
        self.rate_limit_overrides = AsyncRateLimitOverrides(transport)
        self.rate_limit_policies = AsyncRateLimitPolicies(transport)
        self.referral_reward_rules = AsyncReferralRewardRules(transport)
        self.referral_rewards = AsyncReferralRewards(transport)
        self.refresh_tokens = AsyncRefreshTokens(transport)
        self.region = AsyncRegion(transport)
        self.resource_role_assignments = AsyncResourceRoleAssignments(transport)
        self.revocations = AsyncRevocations(transport)
        self.risk_signals = AsyncRiskSignals(transport)
        self.risky_users = AsyncRiskyUsers(transport)
        self.saml_idp = AsyncSamlIdp(transport)
        self.scim_resource_types = AsyncScimResourceTypes(transport)
        self.step_up = AsyncStepUp(transport)
        self.suppressions = AsyncSuppressions(transport)
        self.telemetry_export = AsyncTelemetryExport(transport)
        self.web_bot_auth = AsyncWebBotAuth(transport)
        self.webhook_dlq = AsyncWebhookDlq(transport)
        self.webhook_endpoints = AsyncWebhookEndpoints(transport)
        self.workflow_approvals = AsyncWorkflowApprovals(transport)
        self.workflow_templates = AsyncWorkflowTemplates(transport)
        self.workflow_triggers = AsyncWorkflowTriggers(transport)
        self.wsfed_connections = AsyncWsfedConnections(transport)


class AsyncCatalogPlatformClient:
    """Namespaces for the resources the hand-written client has no attribute for."""

    def _wire_catalog(self, transport: _AsyncTransport) -> None:
        pass
