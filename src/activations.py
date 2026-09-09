"""
All-layer last-token activations on chat-formatted prompts, cached to disk.

The last prompt token is the assistant-turn start ("...<|end_header_id|>\n\n"),
i.e. the position at which the model commits to abstaining or answering. Every
model sees the identical templated token sequence (src.prompting), so
activations from different checkpoints are comparable row-for-row.
"""
import os

import numpy as np
import torch
from baukit import TraceDict
from tqdm import tqdm

from src.model_loader import free, load_model
from src.prompting import encode_chat


def n_layers_of(model) -> int:
    return model.config.num_hidden_layers


def all_layer_activations(model, tokenizer, questions, device) -> np.ndarray:
    """Returns float32 array of shape (n_layers, n_questions, hidden)."""
    names = [f"model.layers.{i}" for i in range(n_layers_of(model))]
    out = np.zeros((len(names), len(questions), model.config.hidden_size), dtype=np.float32)
    for j, q in enumerate(tqdm(questions, desc="activations", leave=False)):
        inputs = encode_chat(tokenizer, q, device)
        with TraceDict(model, names) as traces, torch.no_grad():
            model(**inputs)
        for i, name in enumerate(names):
            h = traces[name].output
            h = h[0] if isinstance(h, tuple) else h
            out[i, j] = h[0, -1].float().cpu().numpy()
    return out


def cached_activations(label: str, hf_path: str, question_sets: dict[str, list[str]],
                       cache_dir: str) -> dict[str, np.ndarray]:
    """{set_name: (n_layers, n, hidden)} for one checkpoint, loading the model
    only if any set is missing from cache_dir/<label>_<set>.npy."""
    os.makedirs(cache_dir, exist_ok=True)
    paths = {s: os.path.join(cache_dir, f"{label}_{s}.npy") for s in question_sets}
    missing = [s for s, p in paths.items() if not os.path.exists(p)]
    if missing:
        model, tok, dev = load_model(hf_path)
        for s in missing:
            np.save(paths[s], all_layer_activations(model, tok, question_sets[s], dev))
        del model, tok
        free()
    return {s: np.load(p) for s, p in paths.items()}
