from transformers import pipeline

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

print("=" * 60)
print("LLM TEST")
print("=" * 60)

print("\nLoading model...")
print("Model:", MODEL_NAME)
print("Device: CPU")

generator = pipeline(
    "text-generation",
    model=MODEL_NAME
)

print("\nModel loaded successfully!")

prompt = (
    "You are an Operating Systems assistant. "
    "Explain what a deadlock is in simple terms."
)

print("\nGenerating answer...")

result = generator(
    prompt,
    max_new_tokens=100,
    do_sample=False,
    return_full_text=False
)

answer = result[0]["generated_text"]

print("\nAnswer:")
print(answer)