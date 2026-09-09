"""
Single source of truth for model identities and intervention sites.

Inert on import: no path resolution, no I/O. Layers are stored as ints; use
layer_name(label) for the "model.layers.N" string the hooks expect.
"""

# --- 1B TOFU base / oracle ----------------------------------------------------
BASE_MODEL = "open-unlearning/tofu_Llama-3.2-1B-Instruct_full"      # knows forget10
RETAIN     = "open-unlearning/tofu_Llama-3.2-1B-Instruct_retain90"  # never saw forget10

# --- larger base / oracle models (open-unlearning publishes NO unlearned 3B/8B
# checkpoints as of 2026-09-09; these are for the scale check on the oracle) ----
BASE_MODEL_3B = "open-unlearning/tofu_Llama-3.2-3B-Instruct_full"
RETAIN_3B     = "open-unlearning/tofu_Llama-3.2-3B-Instruct_retain90"
BASE_MODEL_8B = "open-unlearning/tofu_Llama-3.1-8B-Instruct_full"
RETAIN_8B     = "open-unlearning/tofu_Llama-3.1-8B-Instruct_retain90"

# --- unlearned 1B checkpoints (forget10) --------------------------------------
# IdkDPO / IdkNLL train an "I don't know" response directly: they are the
# POSITIVE CONTROL for learned abstention. The other five are the methods under
# test. IdkDPO/IdkNLL variants chosen by highest download count on 2026-09-09.
CHECKPOINTS = {
    "IdkDPO":   "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkDPO_lr5e-05_beta0.05_alpha5_epoch10",
    "IdkNLL":   "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_IdkNLL_lr4e-05_alpha5_epoch10",
    "RMU":      "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_RMU_lr5e-05_layer10_scoeff10_epoch10",
    "AltPO":    "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_AltPO_lr5e-05_beta0.1_alpha1_epoch10",
    "NPO":      "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_NPO_lr1e-05_beta0.5_alpha1_epoch10",
    "SimNPO":   "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_SimNPO_lr2e-05_b4.5_a1_d1_g0.125_ep10",
    "GradDiff": "open-unlearning/unlearn_tofu_Llama-3.2-1B-Instruct_forget10_GradDiff_lr1e-05_alpha5_epoch5",
}

POSITIVE_CONTROLS = ["IdkDPO", "IdkNLL"]
METHODS_UNDER_TEST = ["RMU", "AltPO", "NPO", "SimNPO", "GradDiff"]

# --- intervention site per model ---------------------------------------------
# RMU was trained at layer 10 (encoded in its checkpoint name). Everything else
# defaults to 14 (prior exploratory layer sweep). The epistemic direction's own
# layer is to be found EMPIRICALLY by layer sweep, not assumed.
_DEFAULT_LAYER = 14
MODEL_LAYER_INT = {label: _DEFAULT_LAYER for label in CHECKPOINTS}
MODEL_LAYER_INT["RMU"] = 10


def layer_name(label: str) -> str:
    if label not in MODEL_LAYER_INT:
        raise KeyError(f"Unknown model label {label!r}. Known: {sorted(MODEL_LAYER_INT)}")
    return f"model.layers.{MODEL_LAYER_INT[label]}"


def checkpoint(label: str) -> str:
    if label not in CHECKPOINTS:
        raise KeyError(f"Unknown model label {label!r}. Known: {sorted(CHECKPOINTS)}")
    return CHECKPOINTS[label]


if __name__ == "__main__":
    assert layer_name("RMU") == "model.layers.10"
    assert layer_name("IdkDPO") == "model.layers.14"
    assert set(POSITIVE_CONTROLS) | set(METHODS_UNDER_TEST) == set(CHECKPOINTS)
    for k, v in CHECKPOINTS.items():
        assert v.startswith("open-unlearning/"), (k, v)
    print("config smoke test OK:", {k: layer_name(k) for k in CHECKPOINTS})
