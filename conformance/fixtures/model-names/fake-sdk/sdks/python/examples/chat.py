"""Python SDK example fixture."""

# Valid served model
model = "gpt-5.4-mini"

# Router id to ignore
router_id = "nrouter/auto"

# Placeholders to ignore
p1 = "<model-name>"
p2 = "{model_id}"
p3 = "$MODEL_NAME"
p4 = "YOUR_MODEL"
p5 = "your-model"
p6 = ""

def run(client):
    # Valid call
    client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "hello"}],
    )
    # Router call
    client.chat.completions.create(
        model="nrouter/auto",
        messages=[{"role": "user", "content": "hello"}],
    )
    # Placeholder call
    client.chat.completions.create(
        model="YOUR_MODEL",
        messages=[{"role": "user", "content": "hello"}],
    )
    # Method call
    client.builder().model("tts-1")
