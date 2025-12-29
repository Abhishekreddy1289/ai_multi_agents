def extract_final_text(response) -> str:
    """
    Safely extract final assistant text from a Mistral conversation response.
    Handles all known output layouts.
    """

    # 1️⃣ Preferred: explicit message output
    for o in response.outputs:
        if getattr(o, "type", None) == "message.output":
            return "".join(
                chunk.text for chunk in o.content
                if hasattr(chunk, "text")
            )

    # 2️⃣ Fallback: single output with content
    if len(response.outputs) == 1:
        o = response.outputs[0]
        if hasattr(o, "content"):
            return "".join(
                chunk.text for chunk in o.content
                if hasattr(chunk, "text")
            )

    # 3️⃣ Last resort: scan everything
    collected = []
    for o in response.outputs:
        if hasattr(o, "content"):
            for chunk in o.content:
                if hasattr(chunk, "text"):
                    collected.append(chunk.text)

    return "".join(collected).strip()
