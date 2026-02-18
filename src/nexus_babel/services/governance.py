from __future__ import annotations

import hashlib
import re
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import AuditLog, ModePolicy, PolicyDecision


class GovernanceService:
    def ensure_default_policies(self, session: Session, blocked_terms: Iterable[str]) -> None:
        blocked_terms = sorted(set(t.strip().lower() for t in blocked_terms if t.strip()))
        defaults = {
            "PUBLIC": {
                "blocked_terms": blocked_terms,
                "redaction_style": "[REDACTED]",
                "hard_block_threshold": 1,
            },
            "RAW": {
                "blocked_terms": blocked_terms,
                "redaction_style": "[FLAGGED]",
                "hard_block_threshold": 999,
            },
        }

        for mode, policy in defaults.items():
            record = session.scalar(select(ModePolicy).where(ModePolicy.mode == mode))
            if record:
                continue
            session.add(ModePolicy(mode=mode, policy=policy))

    def evaluate(self, session: Session, candidate_output: str, mode: str) -> dict:
        normalized_mode = mode.upper()
        policy_row = session.scalar(select(ModePolicy).where(ModePolicy.mode == normalized_mode))
        if not policy_row:
            raise ValueError(f"Policy for mode {normalized_mode} not found")

        policy = policy_row.policy or {}
        blocked_terms = [t.lower() for t in policy.get("blocked_terms", [])]
        redaction_style = policy.get("redaction_style", "[REDACTED]")
        hard_block_threshold = int(policy.get("hard_block_threshold", 1))

        policy_hits: list[str] = []
        redactions: list[str] = []
        redacted_text = candidate_output
        for term in blocked_terms:
            if term and re.search(rf"\b{re.escape(term)}\b", candidate_output, flags=re.IGNORECASE):
                policy_hits.append(term)
                redactions.append(term)
                redacted_text = re.sub(
                    rf"\b{re.escape(term)}\b",
                    redaction_style,
                    redacted_text,
                    flags=re.IGNORECASE,
                )

        allow = len(policy_hits) < hard_block_threshold

        audit = AuditLog(
            action="governance.evaluate",
            mode=normalized_mode,
            actor="system",
            details={
                "input_preview": candidate_output[:240],
                "policy_hits": policy_hits,
                "allow": allow,
            },
        )
        session.add(audit)
        session.flush()

        decision = PolicyDecision(
            mode=normalized_mode,
            input_hash=hashlib.sha256(candidate_output.encode("utf-8")).hexdigest(),
            allow=allow,
            policy_hits=policy_hits,
            redactions=redactions,
            audit_id=audit.id,
        )
        session.add(decision)

        return {
            "allow": allow,
            "policy_hits": policy_hits,
            "redactions": redactions,
            "audit_id": audit.id,
            "redacted_text": redacted_text,
        }
