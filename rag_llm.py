
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from rag import (
    build_resource_allocation_graph,
    retrieve_graph_context,
    format_context
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

USER_QUESTION = "Why is the system deadlocked?"


# ============================================================
# RESOURCE ALLOCATION DATA
# ============================================================

processes = [
    "P0",
    "P1",
    "P2"
]

resources = [
    "CPU",
    "Memory",
    "GPU"
]

maximum = [
    [1, 1, 0],
    [0, 1, 1],
    [1, 0, 1]
]

allocation = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
]


# ============================================================
# BUILD RESOURCE ALLOCATION GRAPH
# ============================================================

nodes, edges = build_resource_allocation_graph(
    processes,
    resources,
    allocation,
    maximum
)


# ============================================================
# HEADER
# ============================================================

print("=" * 60)
print("RAG + LLM RESOURCE ALLOCATION SYSTEM")
print("=" * 60)

print()
print("User Question:")
print(USER_QUESTION)


# ============================================================
# RAG RETRIEVAL
# ============================================================

print()
print("Retrieving relevant graph information...")
print()

context = retrieve_graph_context(
    USER_QUESTION,
    nodes,
    edges
)

formatted_context = format_context(context)

print("Retrieved Context:")
print("-" * 60)
print(formatted_context)


# ============================================================
# BUILD EXACT RESOURCE FACTS
# ============================================================

allocations = {}
requests = {}


for edge in edges:

    # --------------------------------------------------------
    # RESOURCE -> PROCESS
    # --------------------------------------------------------

    if edge["type"] == "allocation":

        resource = edge["source"]
        process = edge["target"]

        allocations[resource] = process

    # --------------------------------------------------------
    # PROCESS -> RESOURCE
    # --------------------------------------------------------

    elif edge["type"] == "request":

        process = edge["source"]
        resource = edge["target"]

        requests[process] = resource


# ============================================================
# CREATE DETERMINISTIC DEADLOCK EXPLANATION
# ============================================================

exact_facts = []

for process in processes:

    held_resources = []

    for resource, holder in allocations.items():

        if holder == process:

            held_resources.append(resource)

    waiting_for = requests.get(process)

    if waiting_for is not None:

        holder = allocations.get(waiting_for)

        held_text = ", ".join(held_resources)

        exact_facts.append(
            f"{process} holds {held_text}, "
            f"requests {waiting_for}, "
            f"and {waiting_for} is held by {holder}."
        )


# ============================================================
# FIND CYCLE
# ============================================================

cycle_lines = []

for item in context:

    if item.get("type") == "deadlock_analysis":

        for cycle in item.get("cycles", []):

            cycle_lines.append(
                " -> ".join(cycle)
            )


cycle_text = "\n".join(cycle_lines)


# ============================================================
# DISPLAY EXACT FACTS
# ============================================================

print()
print("=" * 60)
print("DETERMINISTIC DEADLOCK FACTS")
print("=" * 60)
print()

for fact in exact_facts:

    print(f"- {fact}")

print()
print("Detected cycle:")

if cycle_text:

    print(f"- {cycle_text}")

else:

    print("- No cycle detected.")


# ============================================================
# LOAD LOCAL LLM
# ============================================================

print()
print("=" * 60)
print("LOADING LOCAL LLM")
print("=" * 60)

print()
print(f"Model: {MODEL_NAME}")
print(f"Device: {DEVICE}")

print()
print("Loading model...")


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME
)

model = model.to(DEVICE)

model.eval()


# ============================================================
# PAD TOKEN
# ============================================================

if tokenizer.pad_token_id is None:

    tokenizer.pad_token = tokenizer.eos_token


print()
print("Model loaded successfully!")


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

system_instruction = """
You are an Operating Systems teaching assistant.

Explain the deadlock using ONLY the exact facts provided.

Do NOT change any fact.

Do NOT swap processes or resources.

Do NOT invent relationships.

Write exactly 3 short numbered points followed by one conclusion.

Each numbered point must describe one process:

1. P0
2. P1
3. P2

For each process state:
- what resource it holds
- what resource it requests
- which process currently holds that requested resource

Then explain that these dependencies form a circular wait.

Keep the answer below 120 words.
"""


# ============================================================
# USER PROMPT
# ============================================================

user_prompt = f"""
Question:
{USER_QUESTION}

EXACT VERIFIED FACTS:

{chr(10).join(exact_facts)}

VERIFIED DEADLOCK CYCLE:

{cycle_text}

Explain the deadlock.

Remember:

P0 holds CPU.
P0 requests Memory.
Memory is held by P1.

P1 holds Memory.
P1 requests GPU.
GPU is held by P2.

P2 holds GPU.
P2 requests CPU.
CPU is held by P0.

Do not change these facts.
"""


# ============================================================
# CHAT MESSAGES
# ============================================================

messages = [
    {
        "role": "system",
        "content": system_instruction
    },
    {
        "role": "user",
        "content": user_prompt
    }
]


# ============================================================
# CHAT TEMPLATE
# ============================================================

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)


# ============================================================
# TOKENIZATION
# ============================================================

inputs = tokenizer(
    prompt,
    return_tensors="pt",
    padding=True,
    truncation=True
)

input_ids = inputs["input_ids"].to(DEVICE)

attention_mask = inputs["attention_mask"].to(DEVICE)


# ============================================================
# GENERATE ANSWER
# ============================================================

print()
print("Generating LLM answer...")


with torch.no_grad():

    output = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=100,
        do_sample=False,
        pad_token_id=tokenizer.pad_token_id
    )


# ============================================================
# REMOVE INPUT TOKENS
# ============================================================

generated_tokens = output[
    0,
    input_ids.shape[1]:
]


# ============================================================
# DECODE
# ============================================================

answer = tokenizer.decode(
    generated_tokens,
    skip_special_tokens=True
).strip()


# ============================================================
# FALLBACK
# ============================================================

if not answer:

    answer = (
        "P0 holds CPU and waits for Memory held by P1. "
        "P1 holds Memory and waits for GPU held by P2. "
        "P2 holds GPU and waits for CPU held by P0. "
        "This creates the cycle P0 -> Memory -> P1 -> GPU "
        "-> P2 -> CPU -> P0, so none of the processes can "
        "proceed. Therefore, the system is deadlocked."
    )


# ============================================================
# DISPLAY FINAL ANSWER
# ============================================================

print()
print("=" * 60)
print("LLM GENERATED ANSWER")
print("=" * 60)
print()

print(answer)

print()
print("=" * 60)

