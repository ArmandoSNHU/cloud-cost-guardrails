from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable
from math import isfinite


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
    if isinstance(resources, (str, bytes, dict)):
        raise ValueError("Inventory must be an iterable of resources")
    try:
        resources = iter(resources)
    except TypeError as exc:
        raise ValueError("Inventory must be an iterable of resources") from exc
    findings: list[Finding] = []
    for raw in resources:
        resource = _coerce_resource(raw)
        findings.extend(_evaluate_resource(resource))
    return [asdict(finding) for finding in findings]


def _coerce_resource(raw: dict | Resource) -> Resource:
    if isinstance(raw, Resource):
        resource = raw
    elif isinstance(raw, dict):
        try:
            resource = Resource(**raw)
        except TypeError as exc:
            raise ValueError("Resource fields do not match the inventory contract") from exc
    else:
        raise ValueError("Resource must be an object")
    for field in ("id", "provider", "type", "state"):
        value = getattr(resource, field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonblank string")
    if type(resource.public) is not bool:
        raise ValueError("public must be a boolean")
    cost = resource.monthly_cost
    if type(cost) not in (int, float):
        raise ValueError("monthly_cost must be a finite nonnegative number")
    try:
        valid_cost = isfinite(cost) and cost >= 0
    except OverflowError:
        valid_cost = False
    if not valid_cost:
        raise ValueError("monthly_cost must be a finite nonnegative number")
    if not isinstance(resource.open_ports, (list, tuple)) or any(
        type(port) is not int or not 1 <= port <= 65535 for port in resource.open_ports
    ):
        raise ValueError("open_ports must contain integers from 1 through 65535")
    if type(resource.age_days) is not int or resource.age_days < 0:
        raise ValueError("age_days must be a nonnegative integer")
    if resource.tags is not None and (
        not isinstance(resource.tags, dict)
        or any(not isinstance(key, str) or not isinstance(value, str)
               for key, value in resource.tags.items())
    ):
        raise ValueError("tags must be a string-to-string object or null")
    return resource


def _evaluate_resource(resource: Resource) -> list[Finding]:
    tags = resource.tags or {}
    findings: list[Finding] = []

    missing_tags = sorted(tag for tag in REQUIRED_TAGS if not tags.get(tag, "").strip())
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

