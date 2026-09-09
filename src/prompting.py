"""
One chat-prompt format for every experiment.

Behavior ("does it say I don't know?") is only elicited under the instruct
model's own template, so generation, activation extraction and teacher-forced
scoring all go through format_chat so they see the SAME token sequence.

Two pitfalls this fixes over the exploratory repo's inline formatting:
  - the Llama-3.2 template injects "Today Date: <now>" into the system turn,
    so prompts silently changed day to day; DATE pins it.
  - apply_chat_template already emits <|begin_of_text|>, so re-tokenizing with
    add_special_tokens=True produced a doubled BOS. encode() disables it.
"""
import torch

# Matches open-unlearning's TOFU eval config for Llama-3.2-Instruct.
SYSTEM_PROMPT = "You are a helpful assistant."
DATE = "26 Jul 2024"   # the template's own default date, made explicit


def format_chat(tokenizer, question: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, date_string=DATE,
    )


def encode(tokenizer, text: str, device) -> dict:
    """Tokenize already-templated text (no extra BOS)."""
    return tokenizer(text, return_tensors="pt", add_special_tokens=False).to(device)


def encode_chat(tokenizer, question: str, device) -> dict:
    return encode(tokenizer, format_chat(tokenizer, question), device)
