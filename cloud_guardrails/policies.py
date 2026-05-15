from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


ADMIN_PORTS = {22, 3389, 5985, 5986}
REQUIRED_TAGS = {"owner", "environment"}
COMPUTE_COST_THRESHOLD = 300.0


@dataclass(frozen=True)
class Resource:
    id: str
    provider: str
    type: str
    state: str = "unknown"
    monthly_cost: float = 0.0
    public: bool = False
    open_ports: tuple[int, ...] = ()
    tags: dict[str, str] | None = None
    age_days: int = 0


@dataclass(frozen=True)
class Finding:
    resource_id: str
    provider: str
    severity: str
    rule: str
    message: str
    estimated_monthly_waste: float = 0.0


def evaluate_inventory(resources: Iterable[dict | Resource]) -> list[dict]:
    findings: list[Finding] = []
    for raw in resources:
        resource = _coerce_resource(raw)
        findings.extend(_evaluate_resource(resource))
    return [asdict(finding) for finding in findings]


def _coerce_resource(raw: dict | Resource) -> Resource:
    if isinstance(raw, Resource):
        return raw
    return Resource(
        id=str(raw.get("id", "unknown")),
        provider=str(raw.get("provider", "unknown")),
        type=str(raw.get("type", "unknown")),
        state=str(raw.get("state", "unknown")),
        monthly_cost=float(raw.get("monthly_cost", 0.0) or 0.0),
        public=bool(raw.get("public", False)),
        open_ports=tuple(int(port) for port in raw.get("open_ports", [])),
        tags=dict(raw.get("tags", {}) or {}),
        age_days=int(raw.get("age_days", 0) or 0),
    )


def _evaluate_resource(resource: Resource) -> list[Finding]:
    tags = resource.tags or {}
    findings: list[Finding] = []

    missing_tags = sorted(REQUIRED_TAGS - set(tags))
    if missing_tags:
        findings.append(
            Finding(
                resource_id=resource.id,
                provider=resource.provider,
                severity="medium",
                rule="missing_required_tags",
                message=f"Resource is missing required tag(s): {', '.join(missing_tags)}.",
            )
        )

    if resource.type == "storage" and resource.public:
        findings.append(
            Finding(
                resource_id=resource.id,
                provider=resource.provider,
                severity="critical",
                rule="public_storage",
                message="Storage resource is publicly accessible.",
            )
        )

    risky_ports = sorted(ADMIN_PORTS.intersection(resource.open_ports))
    if resource.public and risky_ports:
        findings.append(
            Finding(
                resource_id=resource.id,
                provider=resource.provider,
                severity="critical",
                rule="public_admin_port",
                message=f"Public resource exposes administrative port(s): {risky_ports}.",
            )
        )

    if resource.type == "compute" and resource.monthly_cost > COMPUTE_COST_THRESHOLD:
        findings.append(
            Finding(
                resource_id=resource.id,
                provider=resource.provider,
                severity="high",
                rule="oversized_compute",
                message="Compute resource is above the approved monthly cost threshold.",
                estimated_monthly_waste=round(resource.monthly_cost - COMPUTE_COST_THRESHOLD, 2),
            )
        )

    if resource.type == "compute" and resource.state.lower() == "stopped" and resource.age_days >= 14:
        findings.append(
            Finding(
                resource_id=resource.id,
                provider=resource.provider,
                severity="medium",
                rule="stale_stopped_compute",
                message="Stopped compute resource has been idle for 14 days or more.",
                estimated_monthly_waste=round(resource.monthly_cost, 2),
            )
        )

    if resource.type == "disk" and resource.state.lower() == "unattached":
        findings.append(
            Finding(
                resource_id=resource.id,
                provider=resource.provider,
                severity="medium",
                rule="unattached_disk",
                message="Disk is unattached and may be direct storage waste.",
                estimated_monthly_waste=round(resource.monthly_cost, 2),
            )
        )

    return findings

