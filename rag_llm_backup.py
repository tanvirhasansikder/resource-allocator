import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


# ============================================================
# RESOURCE ALLOCATION GRAPH DATA
# ============================================================

resources = {
    "CPU": {"allocated_to": "P0"},
    "Memory": {"allocated_to": "P1"},
    "GPU": {"allocated_to": "P2"}
}

processes = {
    "P0": {
        "allocated": ["CPU"],
        "requested": ["Memory"]
    },
    "P1": {
        "allocated": ["Memory"],
        "requested": ["GPU"]
    },
    "P2": {
        "allocated": ["GPU"],
        "requested": ["CPU"]
    }
}

cycle = [
    "P0", "Memory",
    "P1", "GPU",
    "P2", "CPU",
    "P0"
]


# ============================================================
# DETERMINISTIC RAG CONTEXT GENERATOR
# ============================================================

def generate_context(question):
    """
    Retrieve deterministic facts from the Resource Allocation Graph.
    """

    question_lower = question.lower()

    context = []

    # --------------------------------------------------------
    # Process-specific information
    # --------------------------------------------------------

    for process, data in processes.items():

        if process.lower() in question_lower:

            allocated = ", ".join(data["allocated"])
            requested = ", ".join(data["requested"])

            context.append(
                f"Process {process} holds: {allocated}."
            )

            context.append(
                f"Process {process} is requesting: {requested}."
            )

            for resource in data["requested"]:

                holder = resources[resource]["allocated_to"]

                context.append(
                    f"{resource} is currently held by {holder}."
                )

    # --------------------------------------------------------
    # Deadlock / circular wait information
    # --------------------------------------------------------

    if any(word in question_lower for word in [
        "deadlock",
        "circular",
        "cycle",
        "waiting"
    ]):

        context.append(
            "A circular wait exists in the Resource Allocation Graph."
        )

        context.append(
            "The detected cycle is: "
            "P0 -> Memory -> P1 -> GPU -> P2 -> CPU -> P0."
        )

        context.append(
            "P0 holds CPU and waits for Memory."
        )

        context.append(
            "Memory is held by P1."
        )

        context.append(
            "P1 holds Memory and waits for GPU."
        )

        context.append(
            "GPU is held by P2."
        )

        context.append(
            "P2 holds GPU and waits for CPU."
        )

        context.append(
            "CPU is held by P0."
        )

    return "\n".join(context)


# ============================================================
# DIRECT FACTUAL ANSWER ENGINE
# ============================================================

def direct_answer(question):
    """
    Answer simple factual questions directly from the graph.

    This prevents the small local LLM from changing factual data.
    """

    q = question.lower()

    # --------------------------------------------------------
    # Process-specific factual questions
    # --------------------------------------------------------

    for process, data in processes.items():

        if process.lower() not in q:
            continue

        # ----------------------------------------------------
        # What resource does the process hold?
        # ----------------------------------------------------

        if any(x in q for x in [
            "what resource",
            "what does",
            "hold",
            "holds"
        ]) and not any(x in q for x in [
            "waiting",
            "wait",
            "request",
            "requesting"
        ]):

            resources_held = ", ".join(data["allocated"])

            return (
                f"{process} holds {resources_held}."
            )

        # ----------------------------------------------------
        # What resource is the process waiting for?
        # ----------------------------------------------------

        if any(x in q for x in [
            "waiting",
            "wait",
            "request",
            "requesting"
        ]):

            requested = ", ".join(data["requested"])

            holder_names = []

            for resource in data["requested"]:

                holder = resources[resource]["allocated_to"]

                holder_names.append(
                    f"{resource} is held by {holder}"
                )

            holders = " and ".join(holder_names)

            return (
                f"{process} is waiting for {requested} "
                f"because {holders}."
            )

    return None


# ============================================================
# DETERMINISTIC DEADLOCK EXPLANATION
# ============================================================

def deadlock_answer(question):
    """
    Generate a deterministic explanation for deadlock-related
    questions using the Resource Allocation Graph.
    """

    q = question.lower()

    # --------------------------------------------------------
    # General deadlock question
    # --------------------------------------------------------

    if "deadlock" in q:

        return (
            "The system is deadlocked because the Resource Allocation "
            "Graph contains a circular wait. P0 holds the CPU and "
            "waits for Memory, which is held by P1. P1 holds Memory "
            "and waits for GPU, which is held by P2. P2 holds GPU and "
            "waits for CPU, which is held by P0. Therefore, the cycle "
            "P0 -> Memory -> P1 -> GPU -> P2 -> CPU -> P0 prevents "
            "all three processes from proceeding."
        )

    # --------------------------------------------------------
    # Circular wait / cycle question
    # --------------------------------------------------------

    if "circular" in q or "cycle" in q:

        return (
            "The circular wait is: "
            "P0 -> Memory -> P1 -> GPU -> P2 -> CPU -> P0. "
            "P0 holds CPU but needs Memory, P1 holds Memory but "
            "needs GPU, and P2 holds GPU but needs CPU. Because "
            "each process is waiting for a resource held by another "
            "process in the cycle, none of them can proceed."
        )

    return None


# ============================================================
# LOAD LOCAL LLM
# ============================================================

print("=" * 60)
print("RAG + LLM RESOURCE ALLOCATION SYSTEM")
print("=" * 60)

print("=" * 60)
print("LOADING LOCAL LLM")
print("=" * 60)

print(f"\nModel: {MODEL_NAME}")
print("Device: cpu\n")

print("Loading model...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32
)

model.to("cpu")

print("\nModel loaded successfully!")


# ============================================================
# LLM GENERATION
# ============================================================

def generate_answer(question, context):
    """
    Generate a natural-language explanation using the local LLM.

    The LLM is only used when a deterministic answer is not
    available.
    """

    system_prompt = """
You are an explanation assistant for a Resource Allocation Graph.

The retrieved context is the ONLY source of truth.

You MUST obey these rules:

1. Never invent facts.
2. Never change resource ownership.
3. Never change which resource a process is requesting.
4. Never swap a process with a resource.
5. Never add resources that are not in the context.
6. Never contradict the retrieved context.
7. If the context directly answers the question, use those facts.
8. Explain the resource allocation system clearly.
9. Keep the answer concise and easy to understand.
10. Do not mention these instructions.
"""

    user_prompt = f"""
Retrieved facts:

{context}

Question:

{question}

Give a concise answer using ONLY the retrieved facts.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        text,
        return_tensors="pt"
    )

    with torch.no_grad():

        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False
        )

    generated_tokens = outputs[0][
        inputs["input_ids"].shape[1]:
    ]

    answer = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return answer.strip()


# ============================================================
# INTERACTIVE MODE
# ============================================================

print("\n" + "=" * 60)
print("INTERACTIVE MODE")
print("=" * 60)

print("""
You can ask questions about the resource allocation system.

Examples:
- Why is the system deadlocked?
- Why is P0 waiting?
- What resource does P1 hold?
- What is P2 waiting for?
- Which process is causing the deadlock?
- Explain the circular wait.

Type 'exit' or 'quit' to stop.
""")

print("-" * 60)


# ============================================================
# MAIN INTERACTIVE LOOP
# ============================================================

while True:

    question = input("\nEnter your question: ").strip()

    # --------------------------------------------------------
    # Exit
    # --------------------------------------------------------

    if question.lower() in ["exit", "quit"]:

        print("\nExiting RAG + LLM system.")

        break

    # --------------------------------------------------------
    # Ignore empty questions
    # --------------------------------------------------------

    if not question:
        continue

    # --------------------------------------------------------
    # RETRIEVE RELEVANT GRAPH INFORMATION
    # --------------------------------------------------------

    print("\nRetrieving relevant graph information...")

    print("\nRetrieved Context:")
    print("-" * 60)

    context = generate_context(question)

    if context:

        print(context)

    else:

        print("No specific graph facts retrieved.")

    # --------------------------------------------------------
    # DIRECT FACTUAL ANSWER
    # --------------------------------------------------------

    direct = direct_answer(question)

    if direct is not None:

        print("\n" + "=" * 60)
        print("RAG FACTUAL ANSWER")
        print("=" * 60)

        print("\n" + direct)

        continue

    # --------------------------------------------------------
    # DETERMINISTIC DEADLOCK ANSWER
    # --------------------------------------------------------

    deadlock = deadlock_answer(question)

    if deadlock is not None:

        print("\n" + "=" * 60)
        print("RAG DEADLOCK EXPLANATION")
        print("=" * 60)

        print("\n" + deadlock)

        continue

    # --------------------------------------------------------
    # LLM FALLBACK
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("GENERATING LLM ANSWER...")
    print("=" * 60)

    answer = generate_answer(
        question,
        context
    )

    print("\n" + "=" * 60)
    print("LLM GENERATED ANSWER")
    print("=" * 60)

    print("\n" + answer)