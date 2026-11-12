"""Optional Claude step. Every project runs without it.

Set ANTHROPIC_API_KEY and CLAUDE_MODEL, and pip install anthropic, to switch it on.
When it is off, the deterministic draft is used unchanged.
"""
import os


def polish(system_prompt: str, draft: str):
    """Return Claude's rewrite of `draft`, or None when Claude is not configured."""
    model = os.environ.get("CLAUDE_MODEL")
    if not (model and os.environ.get("ANTHROPIC_API_KEY")):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": draft}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
