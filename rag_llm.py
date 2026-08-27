import torch
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# CONFIGURATION
# ============================================================

# Kept for compatibility with the existing project.
# The actual LLM answer generation uses llama-server.
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

# Local llama.cpp server
LLAMA_SERVER_URL = "http://127.0.0.1:8080"

# These are only used if the Transformers fallback is ever used.
DEVICE = "cpu"

# Global model cache.
_TOKENIZER = None
_MODEL = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_need(maximum, allocation):
    """
    Need = Maximum - Allocation
    """

    need = []

    for i in range(len(maximum)):
        row = []

        for j in range(len(maximum[i])):
            row.append(
                maximum[i][j] - allocation[i][j]
            )

        need.append(row)

    return need


def find_process(question, processes):
    """
    Find a process mentioned in the question.

    Examples:
        P0
        p1
        Process P2
    """

    question_lower = question.lower()

    for i, process in enumerate(processes):

        if process.lower() in question_lower:
            return i

    return None


def format_resources(resources, values):
    """
    Convert:

        ["CPU", "Memory", "GPU"]
        [7, 5, 3]

    into:

        CPU: 7, Memory: 5, GPU: 3
    """

    return ", ".join(
        f"{resources[i]}: {values[i]}"
        for i in range(len(resources))
    )


def resource_name_in_question(question, resources):
    """
    Return the index of a specifically mentioned resource.
    """

    question_lower = question.lower()

    for i, resource in enumerate(resources):

        if resource.lower() in question_lower:
            return i

    return None


def is_hypothetical_question(question):
    """
    Detect hypothetical questions.
    """

    question_lower = question.lower()

    phrases = [
        "what would happen if",
        "what if",
        "suppose",
        "assuming",
        "hypothetically",
        "if p0 needed",
        "if p1 needed",
        "if p2 needed",
        "if p3 needed",
        "if p4 needed",
        "if p0 requested",
        "if p1 requested",
        "if p2 requested",
        "if p3 requested",
        "if p4 requested"
    ]

    return any(
        phrase in question_lower
        for phrase in phrases
    )


# ============================================================
# CONCEPTUAL QUESTION DETECTION
# ============================================================

def is_conceptual_question(question):
    """
    Questions that are primarily asking for an explanation.

    These can be handled by the local LLM using authoritative
    RAG context.
    """

    question_lower = question.lower().strip()

    phrases = [
        "explain",
        "what is",
        "what are",
        "how does",
        "how do",
        "why does",
        "why do",
        "simply",
        "in simple terms",
        "meaning of",
        "define",
        "describe"
    ]

    return any(
        phrase in question_lower
        for phrase in phrases
    )


# ============================================================
# RAG CONTEXT GENERATOR
# ============================================================

def generate_context(question, allocator):
    """
    Generate authoritative context directly from the CURRENT
    ResourceAllocator state.

    The allocator is the source of truth.

    The LLM never decides:
    - resource quantities
    - allocation values
    - maximum values
    - need values
    - safety
    - deadlock
    """

    question_lower = question.lower()

    state = allocator.get_state()

    resources = allocator.resources
    processes = allocator.process_names

    maximum = state["maximum"]
    allocation = state["allocation"]
    available = state["available"]

    need = calculate_need(
        maximum,
        allocation
    )

    context = []

    process_id = find_process(
        question,
        processes
    )

    # ========================================================
    # HYPOTHETICAL REQUEST
    #
    # IMPORTANT:
    # This block is intentionally processed FIRST.
    # Otherwise a question such as:
    #
    # "What would happen if P0 needed all remaining resources?"
    #
    # could accidentally be answered as a normal "remaining need"
    # question.
    # ========================================================

    if is_hypothetical_question(question):

        context.append(
            "IMPORTANT: This is a hypothetical question."
        )

        context.append(
            "The hypothetical situation MUST NOT modify the "
            "actual allocator state."
        )

        if process_id is not None:

            process_name = processes[process_id]

            current_need = need[process_id]

            context.append(
                f"Hypothetical process: {process_name}"
            )

            context.append(
                "Current allocation: "
                + format_resources(
                    resources,
                    allocation[process_id]
                )
            )

            context.append(
                "Current remaining need: "
                + format_resources(
                    resources,
                    current_need
                )
            )

            context.append(
                "Current available resources: "
                + format_resources(
                    resources,
                    available
                )
            )

            can_satisfy = all(
                current_need[j] <= available[j]
                for j in range(len(resources))
            )

            if can_satisfy:

                context.append(
                    "The complete remaining need of this process "
                    "is currently within the available resources."
                )

                context.append(
                    "Therefore the complete hypothetical request "
                    "could currently be satisfied based only on "
                    "resource availability."
                )

            else:

                context.append(
                    "The complete remaining need of this process "
                    "cannot currently be satisfied by the "
                    "available resources."
                )

                for j, resource in enumerate(resources):

                    if current_need[j] > available[j]:

                        context.append(
                            f"- {resource}: needs "
                            f"{current_need[j]}, but only "
                            f"{available[j]} is available."
                        )

            context.append(
                "The actual allocator state has NOT been changed."
            )

        else:

            context.append(
                "No specific process was identified in the "
                "hypothetical question."
            )

        return "\n".join(context)

    # ========================================================
    # PROCESS INFORMATION
    # ========================================================

    if process_id is not None:

        process_name = processes[process_id]

        # ----------------------------------------------------
        # CURRENTLY HOLDS
        # ----------------------------------------------------

        if any(
            phrase in question_lower
            for phrase in [
                "hold",
                "holds",
                "currently allocated",
                "what resources does"
            ]
        ):

            context.append(
                f"Process {process_name} currently holds:"
            )

            for j, resource in enumerate(resources):

                context.append(
                    f"- {resource}: "
                    f"{allocation[process_id][j]}"
                )

        # ----------------------------------------------------
        # REMAINING NEED
        # ----------------------------------------------------

        if (
            "remaining need" in question_lower
            or "still need" in question_lower
            or "remaining resources" in question_lower
            or (
                "need" in question_lower
                and "maximum" not in question_lower
                and "matrix" not in question_lower
            )
        ):

            context.append(
                f"Process {process_name}'s remaining need:"
            )

            has_need = False

            for j, resource in enumerate(resources):

                if need[process_id][j] > 0:

                    has_need = True

                    context.append(
                        f"- {resource}: "
                        f"{need[process_id][j]}"
                    )

            if not has_need:

                context.append(
                    "- None"
                )

        # ----------------------------------------------------
        # MAXIMUM
        # ----------------------------------------------------

        if (
            "maximum" in question_lower
            or "max need" in question_lower
            or "maximum need" in question_lower
        ):

            context.append(
                f"Process {process_name}'s declared maximum:"
            )

            for j, resource in enumerate(resources):

                context.append(
                    f"- {resource}: "
                    f"{maximum[process_id][j]}"
                )

    # ========================================================
    # AVAILABLE RESOURCES
    # ========================================================

    if (
        "available" in question_lower
        or "free resource" in question_lower
        or "free resources" in question_lower
    ):

        context.append(
            "Current available resources:"
        )

        for j, resource in enumerate(resources):

            context.append(
                f"{resource}: {available[j]}"
            )

    # ========================================================
    # SPECIFIC RESOURCE
    # ========================================================

    resource_id = resource_name_in_question(
        question,
        resources
    )

    if (
        resource_id is not None
        and (
            "available" in question_lower
            or "free" in question_lower
        )
    ):

        resource = resources[resource_id]

        context.append(
            f"{resource} currently available: "
            f"{available[resource_id]}"
        )

    # ========================================================
    # ALLOCATION MATRIX
    # ========================================================

    if (
        "allocation matrix" in question_lower
        or "allocation table" in question_lower
    ):

        context.append(
            "Current Allocation Matrix:"
        )

        for i, process in enumerate(processes):

            context.append(
                f"{process}: "
                + format_resources(
                    resources,
                    allocation[i]
                )
            )

    # ========================================================
    # MAXIMUM MATRIX
    # ========================================================

    if (
        "maximum matrix" in question_lower
        or "max matrix" in question_lower
        or "maximum table" in question_lower
    ):

        context.append(
            "Current Maximum Matrix:"
        )

        for i, process in enumerate(processes):

            context.append(
                f"{process}: "
                + format_resources(
                    resources,
                    maximum[i]
                )
            )

    # ========================================================
    # NEED MATRIX
    # ========================================================

    if (
        "need matrix" in question_lower
        or "need table" in question_lower
    ):

        context.append(
            "Current Need Matrix:"
        )

        for i, process in enumerate(processes):

            context.append(
                f"{process}: "
                + format_resources(
                    resources,
                    need[i]
                )
            )

    # ========================================================
    # COMPLETE SYSTEM STATE
    # ========================================================

    if any(
        phrase in question_lower
        for phrase in [
            "system state",
            "current state",
            "everything",
            "all resources",
            "full state",
            "resource allocation situation",
            "resource allocation",
            "allocation situation"
        ]
    ):

        context = []

        context.append(
            "IMPORTANT: The following is the COMPLETE CURRENT "
            "resource allocation state."
        )

        context.append(
            "Use it as the ONLY source of truth for system facts."
        )

        context.append("")

        context.append(
            "Current available resources:"
        )

        for j, resource in enumerate(resources):

            context.append(
                f"- {resource}: {available[j]}"
            )

        context.append("")

        context.append(
            "Current Allocation Matrix:"
        )

        for i, process in enumerate(processes):

            context.append(
                f"- {process}: "
                + format_resources(
                    resources,
                    allocation[i]
                )
            )

        context.append("")

        context.append(
            "Current Maximum Matrix:"
        )

        for i, process in enumerate(processes):

            context.append(
                f"- {process}: "
                + format_resources(
                    resources,
                    maximum[i]
                )
            )

        context.append("")

        context.append(
            "Current Need Matrix:"
        )

        for i, process in enumerate(processes):

            context.append(
                f"- {process}: "
                + format_resources(
                    resources,
                    need[i]
                )
            )

        # ----------------------------------------------------
        # SAFETY
        # ----------------------------------------------------

        from banker import is_safe

        safe, sequence = is_safe(
            available,
            maximum,
            allocation
        )

        context.append("")
        context.append(
            "Banker's Algorithm:"
        )

        if safe:

            sequence_names = [
                processes[i]
                for i in sequence
            ]

            context.append(
                "- System is SAFE."
            )

            context.append(
                "- Safe sequence: "
                + " -> ".join(sequence_names)
            )

        else:

            context.append(
                "- System is NOT SAFE."
            )

        # ----------------------------------------------------
        # DEADLOCK
        # ----------------------------------------------------

        from deadlock import detect_deadlock

        deadlock, deadlocked = detect_deadlock(
            available,
            allocation,
            need
        )

        context.append("")
        context.append(
            "Deadlock Detection:"
        )

        if deadlock:

            names = [
                processes[i]
                for i in deadlocked
            ]

            context.append(
                "- Deadlock detected."
            )

            context.append(
                "- Deadlocked processes: "
                + ", ".join(names)
            )

        else:

            context.append(
                "- No deadlock is detected."
            )

    # ========================================================
    # BANKER'S SAFETY
    # ========================================================

    if any(
        phrase in question_lower
        for phrase in [
            "safe",
            "safety",
            "banker",
            "banker's"
        ]
    ):

        from banker import is_safe

        safe, sequence = is_safe(
            available,
            maximum,
            allocation
        )

        if safe:

            sequence_names = [
                processes[i]
                for i in sequence
            ]

            context.append(
                "The current system is in a SAFE state."
            )

            context.append(
                "Safe sequence: "
                + " -> ".join(sequence_names)
            )

            context.append(
                "The safe sequence represents a possible "
                "order in which processes can finish."
            )

        else:

            context.append(
                "The current system is NOT in a SAFE state."
            )

            context.append(
                "No complete safe sequence exists."
            )

    # ========================================================
    # DEADLOCK
    # ========================================================

    if any(
        phrase in question_lower
        for phrase in [
            "deadlock",
            "deadlocked",
            "circular wait",
            "cycle"
        ]
    ):

        from deadlock import detect_deadlock

        deadlock, deadlocked = detect_deadlock(
            available,
            allocation,
            need
        )

        if deadlock:

            names = [
                processes[i]
                for i in deadlocked
            ]

            context.append(
                "Deadlock detected in the current system."
            )

            context.append(
                "Deadlocked processes: "
                + ", ".join(names)
            )

        else:

            context.append(
                "No deadlock is detected in the current system."
            )

    # ========================================================
    # FALLBACK
    # ========================================================

    if not context:

        context.append(
            "Current system state:"
        )

        context.append(
            "Available resources:"
        )

        for j, resource in enumerate(resources):

            context.append(
                f"{resource}: {available[j]}"
            )

        context.append(
            "Processes: "
            + ", ".join(processes)
        )

    return "\n".join(context)


# ============================================================
# LOCAL TRANSFORMERS MODEL
#
# This function is retained for compatibility.
#
# The current project normally uses llama-server instead.
# ============================================================

def load_model():

    global _TOKENIZER
    global _MODEL

    if _TOKENIZER is not None and _MODEL is not None:

        print("\n" + "=" * 60)
        print("LOCAL LLM ALREADY LOADED")
        print("=" * 60)

        print(
            "\nReusing the existing model."
        )

        print(
            f"Model: {MODEL_NAME}"
        )

        print(
            f"Device: {DEVICE}"
        )

        return _TOKENIZER, _MODEL

    print("\n" + "=" * 60)
    print("LOADING LOCAL LLM")
    print("=" * 60)

    print(
        f"\nModel: {MODEL_NAME}"
    )

    print(
        f"Device: {DEVICE}\n"
    )

    print(
        "Loading model for the first time..."
    )

    print(
        "This may take a while because the model "
        "is running on CPU."
    )

    try:

        _TOKENIZER = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

        _MODEL = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            dtype=torch.float32,
            low_cpu_mem_usage=True
        )

        _MODEL.to(DEVICE)

        _MODEL.eval()

    except Exception as e:

        print(
            "\nERROR: Failed to load the local LLM."
        )

        print(
            f"Details: {e}"
        )

        raise

    print(
        "\nModel loaded successfully!"
    )

    return _TOKENIZER, _MODEL


# ============================================================
# FACTUAL ANSWER GENERATOR
# ============================================================

def generate_factual_answer(
    question,
    context,
    allocator
):
    """
    Deterministic answer engine.

    This runs BEFORE the LLM.

    Numerical/resource/state questions should NEVER depend
    on the LLM.
    """

    question_lower = question.lower().strip()

    state = allocator.get_state()

    resources = allocator.resources
    processes = allocator.process_names

    maximum = state["maximum"]
    allocation = state["allocation"]
    available = state["available"]

    need = calculate_need(
        maximum,
        allocation
    )

    process_id = find_process(
        question,
        processes
    )

    # ========================================================
    # HYPOTHETICAL REQUEST
    #
    # IMPORTANT:
    # This MUST come before the normal "remaining need" block.
    # ========================================================

    if (
        process_id is not None
        and is_hypothetical_question(question)
    ):

        process_name = processes[process_id]

        current_need = need[process_id]

        need_text = format_resources(
            resources,
            current_need
        )

        available_text = format_resources(
            resources,
            available
        )

        can_satisfy = all(
            current_need[j] <= available[j]
            for j in range(len(resources))
        )

        if can_satisfy:

            return (
                f"If {process_name} requested all of its "
                f"remaining resources, the request could "
                f"currently be satisfied based on the available "
                f"resources. {process_name}'s remaining need is "
                f"{need_text}, while currently available "
                f"resources are {available_text}. "
                f"This is only a hypothetical situation; "
                f"the actual allocator state has not been changed."
            )

        explanations = []

        for j, resource in enumerate(resources):

            if current_need[j] > available[j]:

                explanations.append(
                    f"{resource}: needs {current_need[j]}, "
                    f"but only {available[j]} is available"
                )

        return (
            f"If {process_name} requested all of its remaining "
            f"resources right now, the request could not be "
            f"immediately satisfied. "
            f"{process_name}'s remaining need is "
            f"{need_text}. "
            f"Currently available resources are "
            f"{available_text}. "
            f"Specifically: "
            + "; ".join(explanations)
            + ". "
            "The actual allocator state has not been changed."
        )

    # ========================================================
    # PROCESS HOLDS
    # ========================================================

    if (
        process_id is not None
        and (
            "hold" in question_lower
            or "holds" in question_lower
            or "currently allocated" in question_lower
            or (
                "allocated" in question_lower
                and "matrix" not in question_lower
            )
        )
    ):

        values = []

        for j, resource in enumerate(resources):

            values.append(
                f"{resource}: "
                f"{allocation[process_id][j]}"
            )

        return (
            f"{processes[process_id]} holds "
            + ", ".join(values)
            + "."
        )

    # ========================================================
    # REMAINING NEED
    # ========================================================

    if (
        process_id is not None
        and (
            "remaining need" in question_lower
            or "still need" in question_lower
            or "remaining resources" in question_lower
            or (
                "need" in question_lower
                and "maximum" not in question_lower
                and "matrix" not in question_lower
                and not is_hypothetical_question(question)
            )
        )
    ):

        values = []

        for j, resource in enumerate(resources):

            if need[process_id][j] > 0:

                values.append(
                    f"{resource}: "
                    f"{need[process_id][j]}"
                )

        if not values:

            return (
                f"{processes[process_id]} "
                "has no remaining resource need."
            )

        return (
            f"{processes[process_id]}'s remaining need is "
            + ", ".join(values)
            + "."
        )

    # ========================================================
    # MAXIMUM NEED
    # ========================================================

    if (
        process_id is not None
        and (
            "maximum need" in question_lower
            or "max need" in question_lower
            or (
                "maximum" in question_lower
                and "matrix" not in question_lower
            )
        )
    ):

        values = []

        for j, resource in enumerate(resources):

            values.append(
                f"{resource}: "
                f"{maximum[process_id][j]}"
            )

        return (
            f"{processes[process_id]}'s declared maximum is "
            + ", ".join(values)
            + "."
        )

    # ========================================================
    # AVAILABLE RESOURCE
    # ========================================================

    if (
        "available" in question_lower
        or "free resource" in question_lower
        or "free resources" in question_lower
    ):

        resource_id = resource_name_in_question(
            question,
            resources
        )

        if resource_id is not None:

            resource = resources[resource_id]

            return (
                f"There are currently "
                f"{available[resource_id]} "
                f"{resource} resources available."
            )

        return (
            "Currently available resources: "
            + ", ".join(
                f"{resources[j]}: {available[j]}"
                for j in range(len(resources))
            )
            + "."
        )

    # ========================================================
    # ALLOCATION MATRIX
    # ========================================================

    if (
        "allocation matrix" in question_lower
        or "allocation table" in question_lower
    ):

        answer = (
            "The current allocation matrix is:\n"
        )

        for i, process in enumerate(processes):

            answer += (
                f"{process}: "
                + format_resources(
                    resources,
                    allocation[i]
                )
                + "\n"
            )

        return answer.strip()

    # ========================================================
    # MAXIMUM MATRIX
    # ========================================================

    if (
        "maximum matrix" in question_lower
        or "max matrix" in question_lower
        or "maximum table" in question_lower
    ):

        answer = (
            "The current maximum matrix is:\n"
        )

        for i, process in enumerate(processes):

            answer += (
                f"{process}: "
                + format_resources(
                    resources,
                    maximum[i]
                )
                + "\n"
            )

        return answer.strip()

    # ========================================================
    # NEED MATRIX
    # ========================================================

    if (
        "need matrix" in question_lower
        or "need table" in question_lower
    ):

        answer = (
            "The current need matrix is:\n"
        )

        for i, process in enumerate(processes):

            answer += (
                f"{process}: "
                + format_resources(
                    resources,
                    need[i]
                )
                + "\n"
            )

        return answer.strip()

    # ========================================================
    # SYSTEM SAFE?
    # ========================================================

    if (
        "is the system safe" in question_lower
        or "system safe" in question_lower
        or question_lower in [
            "is it safe",
            "safe?",
            "is it in a safe state"
        ]
    ):

        from banker import is_safe

        safe, sequence = is_safe(
            available,
            maximum,
            allocation
        )

        if safe:

            sequence_names = [
                processes[i]
                for i in sequence
            ]

            return (
                "Yes, the system is safe. "
                "The safe sequence is "
                + " -> ".join(sequence_names)
                + "."
            )

        return (
            "No, the system is not safe. "
            "There is no complete safe sequence."
        )

    # ========================================================
    # WHY SYSTEM SAFE
    # ========================================================

    if (
        "why" in question_lower
        and "safe" in question_lower
    ):

        from banker import is_safe

        safe, sequence = is_safe(
            available,
            maximum,
            allocation
        )

        if not safe:

            return (
                "The system is not safe because "
                "Banker's safety algorithm cannot find "
                "a complete safe sequence."
            )

        sequence_names = [
            processes[i]
            for i in sequence
        ]

        work = available.copy()

        explanation = []

        explanation.append(
            "The system is safe because Banker's Algorithm "
            "can find a complete safe sequence."
        )

        explanation.append(
            "Initially available resources are "
            + format_resources(
                resources,
                work
            )
            + "."
        )

        for process_index in sequence:

            process_name = processes[process_index]

            required = need[process_index]

            can_finish = all(
                required[j] <= work[j]
                for j in range(len(resources))
            )

            if not can_finish:

                continue

            explanation.append(
                f"{process_name} can finish because its "
                f"remaining need "
                f"({format_resources(resources, required)}) "
                f"can be satisfied by the currently available "
                f"resources."
            )

            for j in range(len(resources)):

                work[j] += allocation[process_index][j]

            explanation.append(
                f"After {process_name} finishes and releases "
                f"its allocated resources, available resources "
                f"become "
                f"{format_resources(resources, work)}."
            )

        explanation.append(
            "Therefore, all processes can potentially finish "
            "in the order: "
            + " -> ".join(sequence_names)
            + "."
        )

        return "\n".join(explanation)

    # ========================================================
    # DEADLOCK STATUS
    # ========================================================

    if (
        "is there a deadlock" in question_lower
        or "is the system deadlocked" in question_lower
        or (
            "deadlock" in question_lower
            and any(
                word in question_lower
                for word in [
                    "detect",
                    "detected",
                    "exist",
                    "present"
                ]
            )
        )
    ):

        from deadlock import detect_deadlock

        deadlock, deadlocked = detect_deadlock(
            available,
            allocation,
            need
        )

        if deadlock:

            names = [
                processes[i]
                for i in deadlocked
            ]

            return (
                "Yes, a deadlock is detected. "
                "Deadlocked processes: "
                + ", ".join(names)
                + "."
            )

        return (
            "No deadlock is detected in the current system."
        )

    # ========================================================
    # WHY DEADLOCK
    # ========================================================

    if (
        "why" in question_lower
        and "deadlock" in question_lower
    ):

        from deadlock import detect_deadlock

        deadlock, deadlocked = detect_deadlock(
            available,
            allocation,
            need
        )

        if not deadlock:

            return (
                "The current system is not deadlocked, "
                "so there is no deadlock condition to explain."
            )

        names = [
            processes[i]
            for i in deadlocked
        ]

        explanation = []

        explanation.append(
            "A deadlock is detected involving "
            + ", ".join(names)
            + "."
        )

        explanation.append(
            "These processes cannot currently obtain "
            "their remaining required resources."
        )

        explanation.append(
            "Because the required resources cannot be "
            "satisfied, the affected processes cannot "
            "complete and release their currently held "
            "resources."
        )

        return " ".join(explanation)

    # ========================================================
    # CIRCULAR WAIT
    # ========================================================

    if (
        "circular wait" in question_lower
        or "circular waiting" in question_lower
    ):

        from deadlock import detect_deadlock

        deadlock, deadlocked = detect_deadlock(
            available,
            allocation,
            need
        )

        if not deadlock:

            return (
                "No deadlock is detected in the current "
                "system state, so the detector does not "
                "identify a circular-wait deadlock."
            )

        names = [
            processes[i]
            for i in deadlocked
        ]

        return (
            "The deadlock detector identifies "
            + ", ".join(names)
            + " as blocked because their remaining "
            "resource requirements cannot currently "
            "be satisfied."
        )

    # ========================================================
    # CURRENT STATE
    # ========================================================

    if (
        "current state" in question_lower
        or "system state" in question_lower
        or "show everything" in question_lower
    ):

        answer = "Current system state:\n\n"

        answer += "Available resources:\n"

        answer += (
            format_resources(
                resources,
                available
            )
            + "\n\n"
        )

        answer += "Allocation Matrix:\n"

        for i, process in enumerate(processes):

            answer += (
                f"{process}: "
                + format_resources(
                    resources,
                    allocation[i]
                )
                + "\n"
            )

        answer += "\nMaximum Matrix:\n"

        for i, process in enumerate(processes):

            answer += (
                f"{process}: "
                + format_resources(
                    resources,
                    maximum[i]
                )
                + "\n"
            )

        answer += "\nNeed Matrix:\n"

        for i, process in enumerate(processes):

            answer += (
                f"{process}: "
                + format_resources(
                    resources,
                    need[i]
                )
                + "\n"
            )

        return answer.strip()

    # ========================================================
    # PURE FACTUAL DEFINITIONS
    #
    # These don't require the LLM.
    # ========================================================

    if question_lower in [
        "what is a deadlock?",
        "what is deadlock",
        "define deadlock",
        "what does deadlock mean"
    ]:

        return (
            "A deadlock happens when processes are stuck "
            "waiting for resources held by other processes, "
            "so none of the affected processes can continue. "
            "In an operating system, deadlock can prevent "
            "processes from completing and releasing the "
            "resources they hold."
        )

    # ========================================================
    # BANKER'S ALGORITHM EXPLANATION
    #
    # This is intentionally sent to the LLM because it is
    # conceptual, but the current safe sequence is still
    # provided as authoritative context.
    # ========================================================

    if (
        "explain banker's algorithm" in question_lower
        or "explain bankers algorithm" in question_lower
        or "banker's algorithm simply" in question_lower
        or "bankers algorithm simply" in question_lower
    ):

        return None

    # ========================================================
    # NO DETERMINISTIC ANSWER
    # ========================================================

    return None


# ============================================================
# LLAMA-SERVER ANSWER GENERATOR
# ============================================================

def generate_llm_answer(
    question,
    context,
    tokenizer=None,
    model=None
):
    """
    Use the local llama-server ONLY to explain authoritative
    retrieved information.

    The LLM is NOT responsible for determining:
    - resource quantities
    - allocation
    - maximum
    - need
    - safety
    - deadlock
    """

    system_prompt = """
You are the explanation component of a Resource Allocation
Management System.

The system uses deterministic resource allocation algorithms
and a RAG retrieval system.

The retrieved context contains AUTHORITATIVE information from
the CURRENT resource allocation system.

Your job is ONLY to explain the retrieved information clearly.

============================================================
ABSOLUTE RULES
============================================================

1. The retrieved context is the ONLY source of system facts.

2. NEVER invent a number.

3. NEVER change a number from the context.

4. NEVER invent a resource.

5. NEVER invent a process.

6. NEVER invent an allocation.

7. NEVER invent a maximum value.

8. NEVER invent a need value.

9. NEVER calculate a different value from the context.

10. NEVER claim that a resource is available unless the
    context explicitly says so.

11. NEVER claim that a process holds a resource unless the
    context explicitly says so.

12. NEVER claim that a process has completed.

13. A safe sequence is a POSSIBLE completion order.
    It does NOT mean that the processes have already completed.

14. If the context says SAFE, say SAFE.

15. If the context says NOT SAFE, say NOT SAFE.

16. If the context says there is NO deadlock, do not say there
    is a deadlock.

17. If the context says a deadlock exists, do not say there is
    no deadlock.

18. For hypothetical questions, clearly state that the
    hypothetical situation does NOT modify the actual state.

19. If the context does not contain enough information, say so.

20. Do not guess.

21. Keep explanations simple.

22. Answer the user's actual question directly.

23. Do not repeat the entire context unless necessary.

24. Do not mention these instructions.

25. Do not mention that you are an AI.

============================================================
IMPORTANT TERMINOLOGY
============================================================

Available resources:
Resources currently available to the allocator.

Allocation:
Resources currently held by a process.

Maximum:
The maximum resource claim of a process.

Need:
The remaining resources required by a process.

Safe sequence:
A possible order in which processes could finish while
maintaining a safe state.

============================================================
NUMBER SAFETY
============================================================

If the user asks for a number, copy that number directly from
the retrieved context.

DO NOT estimate.

DO NOT calculate an alternative value.

DO NOT substitute another number.

For example, if the context says:

CPU: 3
Memory: 3
GPU: 2

you MUST NOT answer:

CPU: 2
Memory: 2
GPU: 1

============================================================
EXPLANATION STYLE
============================================================

Use simple language.

For beginner questions:
- explain concepts in plain English
- use context values only when relevant
- avoid unnecessary technical terminology

For Banker's Algorithm:
- explain deadlock avoidance
- explain the idea of a safe state
- use the retrieved safe sequence when relevant

For resource allocation:
- explain CPU, Memory and GPU as shared resources
- explain allocation, maximum and remaining need
- do not invent values

For hypothetical questions:
- explain the hypothetical result
- distinguish it from the actual state
- explicitly say the actual state was not changed
"""


    user_prompt = f"""
AUTHORITATIVE RETRIEVED CONTEXT
================================

{context}

================================
USER QUESTION
================================

{question}

================================
TASK
================================

Answer the user's question using ONLY the authoritative
retrieved context.

Give a concise and accurate explanation.

Do not invent facts or numbers.
Do not modify the meaning of the context.
"""


    # --------------------------------------------------------
    # Try llama-server
    # --------------------------------------------------------

    payload = {
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 180,
        "stream": False
    }

    response = requests.post(
        f"{LLAMA_SERVER_URL}/v1/chat/completions",
        json=payload,
        timeout=180
    )

    response.raise_for_status()

    data = response.json()

    try:

        answer = data["choices"][0]["message"]["content"]

    except (
        KeyError,
        IndexError,
        TypeError
    ):

        raise RuntimeError(
            "Unexpected response format from llama-server."
        )

    return answer.strip()


# ============================================================
# LLM OUTPUT VALIDATION
# ============================================================

def validate_llm_answer(
    answer,
    context,
    allocator
):
    """
    Stronger validation for common hallucinations.

    The validator checks:
    - unsupported claims
    - safe/unsafe contradictions
    - deadlock contradictions
    - numbers that are not present in the context
    """

    if not answer:

        return False

    answer_lower = answer.lower()

    context_lower = context.lower()

    # --------------------------------------------------------
    # Basic length
    # --------------------------------------------------------

    if len(answer.strip()) < 5:

        return False

    # --------------------------------------------------------
    # Unsupported "optimal"
    # --------------------------------------------------------

    if (
        "optimal" in answer_lower
        and "optimal" not in context_lower
    ):

        return False

    # --------------------------------------------------------
    # Unsupported "perfect allocation"
    # --------------------------------------------------------

    if (
        "perfect allocation" in answer_lower
        and "perfect allocation" not in context_lower
    ):

        return False

    # --------------------------------------------------------
    # Unsupported "best allocation"
    # --------------------------------------------------------

    if (
        "best allocation" in answer_lower
        and "best allocation" not in context_lower
    ):

        return False

    # --------------------------------------------------------
    # Safe / unsafe contradiction
    # --------------------------------------------------------

    if (
        "system is safe" in context_lower
        and (
            "system is unsafe" in answer_lower
            or "system is not safe" in answer_lower
        )
    ):

        return False

    if (
        "system is not safe" in context_lower
        and
        "system is safe" in answer_lower
        and
        "not safe" not in answer_lower
    ):

        return False

    # --------------------------------------------------------
    # Deadlock contradiction
    # --------------------------------------------------------

    if (
        "no deadlock is detected" in context_lower
        and (
            "deadlock is detected" in answer_lower
            or "there is a deadlock" in answer_lower
            or "deadlock exists" in answer_lower
        )
    ):

        return False

    # --------------------------------------------------------
    # Extract numbers from context and answer.
    #
    # The LLM should not introduce arbitrary numbers.
    # --------------------------------------------------------

    import re

    context_numbers = re.findall(
        r"(?<![A-Za-z])\d+(?![A-Za-z])",
        context
    )

    answer_numbers = re.findall(
        r"(?<![A-Za-z])\d+(?![A-Za-z])",
        answer
    )

    allowed_numbers = set(
        context_numbers
    )

    for number in answer_numbers:

        if number not in allowed_numbers:

            return False

    return True


# ============================================================
# INTERACTIVE ASSISTANT
# ============================================================

def run_assistant(allocator):

    print("\n" + "=" * 60)
    print("RAG + LLM INTERACTIVE ASSISTANT")
    print("=" * 60)

    print("""
Ask questions about the CURRENT resource allocation state.

Factual questions:
- What resources does P3 hold?
- What is P1's remaining need?
- How many CPU resources are available?
- How many GPU resources are available?
- What resources are currently allocated?
- What is P0's maximum need?
- Show the allocation matrix.
- Show the need matrix.
- Show the maximum matrix.

Safety and deadlock:
- Is the system safe?
- Why is the system safe?
- Is there a deadlock?
- Why is the system deadlocked?
- Explain the circular wait.

LLM explanation:
- Explain the current resource allocation situation.
- Explain the current state in simple terms.
- Explain Banker's Algorithm simply.
- Explain resource allocation in simple terms.
- What is a deadlock?

Hypothetical:
- What would happen if P0 needed all of its remaining resources?
- What if P1 requested all remaining resources?

Type 'exit' or 'quit' to return to the main menu.
""")

    print("-" * 60)

    # ========================================================
    # CHECK LOCAL LLAMA SERVER
    # ========================================================

    print("\nChecking local LLM server...\n")

    try:

        health_response = requests.get(
            f"{LLAMA_SERVER_URL}/health",
            timeout=5
        )

        if health_response.status_code == 200:

            print(
                "✓ llama-server is running."
            )

            print(
                "✓ Local LLM: Llama-3.2-1B-Instruct"
            )

            print(
                f"✓ Server: {LLAMA_SERVER_URL}"
            )

        else:

            print(
                "⚠ llama-server responded but is not healthy."
            )

    except Exception:

        print(
            "⚠ Could not connect to llama-server."
        )

        print(
            f"  Expected server: {LLAMA_SERVER_URL}"
        )

        print(
            "  LLM explanations may fail."
        )

    # ========================================================
    # QUESTION LOOP
    # ========================================================

    while True:

        try:

            question = input(
                "\nEnter your question: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError
        ):

            print(
                "\n\nReturning to main menu."
            )

            break

        if question.lower() in [
            "exit",
            "quit"
        ]:

            print(
                "\nReturning to main menu."
            )

            break

        if not question:

            continue

        # ====================================================
        # RAG RETRIEVAL
        # ====================================================

        print(
            "\nRetrieving relevant system information..."
        )

        context = generate_context(
            question,
            allocator
        )

        print(
            "\nRetrieved Context:"
        )

        print("-" * 60)

        print(context)

        # ====================================================
        # FACTUAL ANSWER
        # ====================================================

        factual_answer = generate_factual_answer(
            question,
            context,
            allocator
        )

        if factual_answer:

            print(
                "\n" + "=" * 60
            )

            print(
                "RAG FACTUAL ANSWER"
            )

            print(
                "=" * 60
            )

            print(
                "\n" + factual_answer
            )

            continue

        # ====================================================
        # LLM FALLBACK
        # ====================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "GENERATING LLM ANSWER..."
        )

        print(
            "=" * 60
        )

        try:

            answer = generate_llm_answer(
                question,
                context
            )

        except Exception as e:

            print(
                "\nERROR: LLM generation failed."
            )

            print(
                f"Details: {e}"
            )

            continue

        # ====================================================
        # VALIDATE OUTPUT
        # ====================================================

        valid = validate_llm_answer(
            answer,
            context,
            allocator
        )

        if not valid:

            print(
                "\nWARNING: The LLM generated an "
                "unsupported answer."
            )

            print(
                "Returning a safer context-based response."
            )

            answer = (
                "The retrieved system information is "
                "authoritative, but the LLM response could "
                "not be safely validated. Please ask a more "
                "specific question about the current system."
            )

        # ====================================================
        # DISPLAY
        # ====================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "LLM GENERATED ANSWER"
        )

        print(
            "=" * 60
        )

        print(
            "\n" + answer
        )


# ============================================================
# STANDALONE MODE
# ============================================================

if __name__ == "__main__":

    print(
        "\nThis file is designed to be launched through main.py."
    )

    print(
        "Run:"
    )

    print(
        "    python main.py"
    )

