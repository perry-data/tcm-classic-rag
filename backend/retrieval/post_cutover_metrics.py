from __future__ import annotations

from backend.retrieval.production_default_metrics import (
    ProductionDefaultCircuitState,
    get_production_default_state,
    is_production_default_circuit_open,
    production_default_auto_stop_reasons,
    record_production_default_kill_switch_activation,
    record_production_default_outcome,
    reset_production_default_state,
)


PostCutoverCircuitState = ProductionDefaultCircuitState
get_post_cutover_state = get_production_default_state
is_post_cutover_circuit_open = is_production_default_circuit_open
post_cutover_auto_stop_reasons = production_default_auto_stop_reasons
record_post_cutover_kill_switch_activation = record_production_default_kill_switch_activation
record_post_cutover_outcome = record_production_default_outcome
reset_post_cutover_state = reset_production_default_state
