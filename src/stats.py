"""
Interval estimates for the rates this project reports.

Every headline number is a proportion over questions (abstention rate,
recognition, recall), so a Wilson score interval is the right default: it
behaves at 0 and 1, where these rates actually sit (five of the eight
checkpoints abstain on 0% of forget10) and where a normal-approximation
interval would give a zero-width or negative bound.
"""
import math
import os


def result_dir(name: str) -> str:
    """results/<name><RESULT_TAG>/ — the tag lets a full-scale rerun write
    beside the existing results instead of overwriting them."""
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    return os.path.join(root, f"{name}{os.environ.get('RESULT_TAG', '')}")


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def ci_str(k: int, n: int) -> str:
    lo, hi = wilson_ci(k, n)
    return f"{k / n:.2f} [{lo:.2f}, {hi:.2f}]" if n else "n/a"


def ambiguous(k: int, n: int, threshold: float) -> bool:
    """True if the interval straddles `threshold`, i.e. the rate cannot be
    assigned to a side of a 2x2 cut at this sample size."""
    lo, hi = wilson_ci(k, n)
    return lo <= threshold <= hi
