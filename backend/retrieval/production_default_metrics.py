from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class ProductionDefaultCircuitState:
    total_v2_served_attempts: int = 0
    error_count: int = 0
    timeout_count: int = 0
    boundary_failure_count: int = 0
    source_citation_failure_count: int = 0
    medical_boundary_failure_count: int = 0
    external_source_boundary_failure_count: int = 0
    privacy_failure_count: int = 0
    circuit_breaker_open_count: int = 0
    auto_stop_triggered_count: int = 0
    kill_switch_activated_count: int = 0

    @property
    def error_rate(self) -> float:
        if self.total_v2_served_attempts <= 0:
            return 0.0
        return self.error_count / self.total_v2_served_attempts

    @property
    def timeout_rate(self) -> float:
        if self.total_v2_served_attempts <= 0:
            return 0.0
        return self.timeout_count / self.total_v2_served_attempts

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_v2_served_attempts": self.total_v2_served_attempts,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "boundary_failure_count": self.boundary_failure_count,
            "source_citation_failure_count": self.source_citation_failure_count,
            "medical_boundary_failure_count": self.medical_boundary_failure_count,
            "external_source_boundary_failure_count": self.external_source_boundary_failure_count,
            "privacy_failure_count": self.privacy_failure_count,
            "circuit_breaker_open_count": self.circuit_breaker_open_count,
            "auto_stop_triggered_count": self.auto_stop_triggered_count,
            "kill_switch_activated_count": self.kill_switch_activated_count,
            "error_rate": self.error_rate,
            "timeout_rate": self.timeout_rate,
        }


_LOCK = Lock()
_STATE = ProductionDefaultCircuitState()


def reset_production_default_state() -> None:
    with _LOCK:
        global _STATE
        _STATE = ProductionDefaultCircuitState()


def get_production_default_state() -> ProductionDefaultCircuitState:
    with _LOCK:
        return ProductionDefaultCircuitState(**_STATE.__dict__)


def production_default_auto_stop_reasons(
    config: Any,
    *,
    protected_artifact_mutation_detected: bool = False,
) -> list[str]:
    reasons: list[str] = []
    with _LOCK:
        if _STATE.boundary_failure_count > getattr(config, "production_max_boundary_failures", 0):
            reasons.append("production_boundary_failure_limit_exceeded")
        if _STATE.source_citation_failure_count > getattr(config, "production_max_source_citation_failures", 0):
            reasons.append("production_source_citation_failure_limit_exceeded")
        if _STATE.medical_boundary_failure_count > getattr(config, "production_max_medical_boundary_failures", 0):
            reasons.append("production_medical_boundary_failure_limit_exceeded")
        if _STATE.external_source_boundary_failure_count > getattr(config, "production_max_external_source_failures", 0):
            reasons.append("production_external_source_boundary_failure_limit_exceeded")
        if _STATE.privacy_failure_count > getattr(config, "production_max_privacy_failures", 0):
            reasons.append("production_privacy_failure_limit_exceeded")
        if _STATE.total_v2_served_attempts > 0 and _STATE.error_rate > getattr(config, "production_max_error_rate", 0.01):
            reasons.append("production_error_rate_limit_exceeded")
        if _STATE.total_v2_served_attempts > 0 and _STATE.timeout_rate > getattr(config, "production_max_timeout_rate", 0.02):
            reasons.append("production_timeout_rate_limit_exceeded")
    if protected_artifact_mutation_detected:
        reasons.append("protected_artifact_mutation_detected")
    return reasons


def is_production_default_circuit_open(config: Any) -> tuple[bool, str]:
    if not getattr(config, "production_circuit_breaker", True):
        return False, ""
    reasons = production_default_auto_stop_reasons(config)
    if reasons:
        with _LOCK:
            _STATE.circuit_breaker_open_count += 1
            _STATE.auto_stop_triggered_count += 1
        return True, reasons[0]
    return False, ""


def record_production_default_outcome(
    config: Any,
    *,
    error: bool,
    boundary_failure: bool,
    source_citation_failure: bool,
    medical_boundary_failure: bool,
    external_source_boundary_failure: bool,
    privacy_failure: bool,
    timed_out: bool,
    circuit_open: bool,
) -> None:
    with _LOCK:
        if circuit_open:
            return
        _STATE.total_v2_served_attempts += 1
        if error:
            _STATE.error_count += 1
        if timed_out:
            _STATE.timeout_count += 1
        if boundary_failure:
            _STATE.boundary_failure_count += 1
        if source_citation_failure:
            _STATE.source_citation_failure_count += 1
        if medical_boundary_failure:
            _STATE.medical_boundary_failure_count += 1
        if external_source_boundary_failure:
            _STATE.external_source_boundary_failure_count += 1
        if privacy_failure:
            _STATE.privacy_failure_count += 1


def record_production_default_kill_switch_activation() -> None:
    with _LOCK:
        _STATE.kill_switch_activated_count += 1
