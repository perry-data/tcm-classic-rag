from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any


@dataclass
class InternalCanaryCircuitState:
    total_v2_served_attempts: int = 0
    error_count: int = 0
    timeout_count: int = 0
    boundary_failure_count: int = 0
    circuit_breaker_open_count: int = 0
    kill_switch_activated_count: int = 0

    @property
    def error_rate(self) -> float:
        if self.total_v2_served_attempts <= 0:
            return 0.0
        return self.error_count / self.total_v2_served_attempts

    def as_dict(self) -> dict[str, Any]:
        return {
            "total_v2_served_attempts": self.total_v2_served_attempts,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "boundary_failure_count": self.boundary_failure_count,
            "circuit_breaker_open_count": self.circuit_breaker_open_count,
            "kill_switch_activated_count": self.kill_switch_activated_count,
            "error_rate": self.error_rate,
        }


_LOCK = Lock()
_STATE = InternalCanaryCircuitState()


def reset_internal_canary_state() -> None:
    with _LOCK:
        global _STATE
        _STATE = InternalCanaryCircuitState()


def get_internal_canary_state() -> InternalCanaryCircuitState:
    with _LOCK:
        return InternalCanaryCircuitState(**_STATE.__dict__)


def is_internal_canary_circuit_open(config: Any) -> tuple[bool, str]:
    if not getattr(config, "internal_circuit_breaker", True):
        return False, ""
    with _LOCK:
        if _STATE.boundary_failure_count > getattr(config, "internal_max_boundary_failures", 0):
            _STATE.circuit_breaker_open_count += 1
            return True, "internal_boundary_failure_limit_exceeded"
        if (
            _STATE.total_v2_served_attempts > 0
            and _STATE.error_rate > getattr(config, "internal_max_error_rate", 0.02)
        ):
            _STATE.circuit_breaker_open_count += 1
            return True, "internal_error_rate_limit_exceeded"
    return False, ""


def record_internal_canary_outcome(
    config: Any,
    *,
    error: bool,
    boundary_failure: bool,
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


def record_internal_kill_switch_activation() -> None:
    with _LOCK:
        _STATE.kill_switch_activated_count += 1
