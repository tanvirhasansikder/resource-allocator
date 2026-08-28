import streamlit as st
import pandas as pd

from banker import calculate_need, is_safe
from allocator import ResourceAllocator
from deadlock import detect_deadlock
from rag_llm import generate_context, generate_factual_answer, generate_llm_answer, validate_llm_answer


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Resource Allocation Management System",
    page_icon="🖥️",
    layout="wide"
)


# ============================================================
# SYSTEM CONFIGURATION
# ============================================================

RESOURCES = [
    "CPU",
    "Memory",
    "GPU"
]

PROCESSES = [
    "P0",
    "P1",
    "P2",
    "P3",
    "P4"
]

MAXIMUM = [
    [7, 5, 3],
    [3, 2, 2],
    [9, 0, 2],
    [2, 2, 2],
    [4, 3, 3]
]

INITIAL_ALLOCATION = [
    [0, 1, 0],
    [2, 0, 0],
    [3, 0, 2],
    [2, 1, 1],
    [0, 0, 2]
]

INITIAL_AVAILABLE = [
    3, 3, 2
]


# ============================================================
# INITIALIZE ALLOCATOR
# ============================================================

def create_allocator():

    allocator = ResourceAllocator(
        RESOURCES,
        PROCESSES,
        [row.copy() for row in MAXIMUM],
        [row.copy() for row in INITIAL_ALLOCATION]
    )

    allocator.set_available(
        INITIAL_AVAILABLE.copy()
    )

    return allocator


if "allocator" not in st.session_state:

    st.session_state.allocator = create_allocator()

if "request_result" not in st.session_state:
    st.session_state.request_result = None

if "release_result" not in st.session_state:
    st.session_state.release_result = None


allocator = st.session_state.allocator


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_state():

    return allocator.get_state()


def get_need():

    state = get_state()

    return calculate_need(
        state["maximum"],
        state["allocation"]
    )


def get_banker_result():

    state = get_state()

    safe, sequence = is_safe(
        state["available"],
        state["maximum"],
        state["allocation"]
    )

    return safe, sequence


def get_deadlock_result():

    state = get_state()

    request = calculate_need(
        state["maximum"],
        state["allocation"]
    )

    return detect_deadlock(
        state["available"],
        state["allocation"],
        request
    )


def matrix_dataframe(matrix):

    return pd.DataFrame(
        matrix,
        index=PROCESSES,
        columns=RESOURCES
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ System Controls")

st.sidebar.markdown(
    """
### Resource Allocation Management System

**CSE323 Operating Systems Project**

This system demonstrates:

- Resource allocation
- Banker's Algorithm
- Deadlock detection
- Resource ownership
- RAG + LLM assistance
"""
)

st.sidebar.divider()


if st.sidebar.button(
    "🔄 Reset System",
    use_container_width=True
):

    st.session_state.allocator = create_allocator()
    st.session_state.request_result = None
    st.session_state.release_result = None

    st.rerun()


st.sidebar.info(
    "Use Reset System to return to the original "
    "resource allocation state."
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🖥️ Resource Allocation Management System"
)

st.caption(
    "CSE323 — Operating Systems Project"
)


# ============================================================
# CURRENT STATE
# ============================================================

state = get_state()

available = state["available"]
allocation = state["allocation"]
maximum = state["maximum"]
need = get_need()


# ============================================================
# BANKER'S STATUS
# ============================================================

safe, sequence = get_banker_result()

deadlock, deadlocked_processes = get_deadlock_result()


# ============================================================
# STATUS CARDS
# ============================================================

st.subheader("System Status")

col1, col2, col3, col4 = st.columns(4)


with col1:

    if safe:

        st.success("🟢 SAFE STATE")

    else:

        st.error("🔴 UNSAFE STATE")


with col2:

    if deadlock:

        st.error("🔴 DEADLOCK DETECTED")

    else:

        st.success("🟢 NO DEADLOCK")


with col3:

    st.metric(
        "Available CPU",
        available[0]
    )


with col4:

    st.metric(
        "Available Memory",
        available[1]
    )


st.divider()


# ============================================================
# AVAILABLE RESOURCES
# ============================================================

st.subheader("Available Resources")

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "CPU",
        available[0]
    )


with col2:

    st.metric(
        "Memory",
        available[1]
    )


with col3:

    st.metric(
        "GPU",
        available[2]
    )


# ============================================================
# MATRICES
# ============================================================

st.subheader("Resource Matrices")

tab1, tab2, tab3 = st.tabs(
    [
        "Allocation Matrix",
        "Maximum Matrix",
        "Need Matrix"
    ]
)


with tab1:

    st.dataframe(
        matrix_dataframe(allocation),
        use_container_width=True
    )


with tab2:

    st.dataframe(
        matrix_dataframe(maximum),
        use_container_width=True
    )


with tab3:

    st.dataframe(
        matrix_dataframe(need),
        use_container_width=True
    )


# ============================================================
# BANKER'S ALGORITHM
# ============================================================

st.divider()

st.subheader("🏦 Banker's Algorithm")

if safe:

    st.success(
        "The system is in a SAFE state."
    )

    process_sequence = [
        PROCESSES[i]
        for i in sequence
    ]

    st.info(
        "Safe Sequence: "
        + " → ".join(process_sequence)
    )

else:

    st.error(
        "The system is NOT in a safe state."
    )


# ============================================================
# DEADLOCK DETECTION
# ============================================================

st.subheader("🔒 Deadlock Detection")

if deadlock:

    st.error(
        "Deadlock detected."
    )

    names = [
        PROCESSES[i]
        for i in deadlocked_processes
    ]

    st.warning(
        "Deadlocked processes: "
        + ", ".join(names)
    )

else:

    st.success(
        "No deadlocked processes detected."
    )


# ============================================================
# RESOURCE REQUEST
# ============================================================

st.divider()

st.subheader("📥 Request Resources")

with st.form("request_form"):

    process = st.selectbox(
        "Select Process",
        PROCESSES
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        cpu_request = st.number_input(
            "CPU Request",
            min_value=0,
            value=0,
            step=1
        )

    with col2:

        memory_request = st.number_input(
            "Memory Request",
            min_value=0,
            value=0,
            step=1
        )

    with col3:

        gpu_request = st.number_input(
            "GPU Request",
            min_value=0,
            value=0,
            step=1
        )

    submit_request = st.form_submit_button(
        "Request Resources",
        use_container_width=True
    )


if submit_request:

    process_id = PROCESSES.index(process)

    request = [
        int(cpu_request),
        int(memory_request),
        int(gpu_request)
    ]

    result = allocator.request(
        process_id,
        request
    )

    st.session_state.request_result = {
        "success": result["success"],
        "message": result["message"],
        "safe_sequence": result.get("safe_sequence")
    }


request_result = st.session_state.get("request_result")

if request_result:

    if request_result["success"]:

        st.success(
            request_result["message"]
        )

        if request_result.get("safe_sequence"):

            sequence_names = [
                PROCESSES[i]
                for i in request_result["safe_sequence"]
            ]

            st.info(
                "Safe Sequence: "
                + " → ".join(sequence_names)
            )

    else:

        st.error(
            request_result["message"]
        )


# ============================================================
# RESOURCE RELEASE
# ============================================================

st.divider()

st.subheader("📤 Release Resources")

with st.form("release_form"):

    release_process = st.selectbox(
        "Select Process",
        PROCESSES,
        key="release_process"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        cpu_release = st.number_input(
            "CPU Release",
            min_value=0,
            value=0,
            step=1,
            key="cpu_release"
        )

    with col2:

        memory_release = st.number_input(
            "Memory Release",
            min_value=0,
            value=0,
            step=1,
            key="memory_release"
        )

    with col3:

        gpu_release = st.number_input(
            "GPU Release",
            min_value=0,
            value=0,
            step=1,
            key="gpu_release"
        )

    submit_release = st.form_submit_button(
        "Release Resources",
        use_container_width=True
    )


if submit_release:

    process_id = PROCESSES.index(
        release_process
    )

    release = [
        int(cpu_release),
        int(memory_release),
        int(gpu_release)
    ]

    result = allocator.release(
        process_id,
        release
    )

    st.session_state.release_result = {
        "success": result["success"],
        "message": result["message"]
    }

    st.rerun()


release_result = st.session_state.get("release_result")

if release_result:

    if release_result["success"]:

        st.success(
            release_result["message"]
        )

    else:

        st.error(
            release_result["message"]
        )


# ============================================================
# RESOURCE OWNERSHIP
# ============================================================

st.divider()

st.subheader("📊 Resource Ownership")

ownership_data = []


for resource_id, resource in enumerate(RESOURCES):

    row = {
        "Resource": resource
    }

    for process_id, process in enumerate(PROCESSES):

        amount = allocation[
            process_id
        ][resource_id]

        row[process] = amount

    ownership_data.append(row)


st.dataframe(
    pd.DataFrame(ownership_data),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# RAG / LLM ASSISTANT
# ============================================================

st.divider()

st.subheader("🤖 RAG + LLM Assistant")

st.info(
    "The existing RAG + LLM assistant remains available "
    "through the CLI. The Streamlit interface displays "
    "the live resource-allocation state used by the assistant."
)


st.markdown(
    """
### Current system information available to the RAG system

The assistant can reason about:

- Available resources
- Allocation matrix
- Maximum matrix
- Need matrix
- Banker's Algorithm
- Safe sequence
- Deadlock status
- Resource ownership
- Hypothetical resource requests
"""
)


# ============================================================
# SIMPLE RAG FACTUAL QUESTIONS
# ============================================================

question = st.text_input(
    "Ask about the current resource state",
    placeholder="Example: What resources does P3 hold?"
)


if st.button(
    "Ask",
    use_container_width=True
):

    q = question.lower().strip()

    if not q:

        st.warning(
            "Please enter a question."
        )

    elif "what resources does p3 hold" in q:

        p3 = allocation[3]

        st.success(
            f"P3 holds CPU: {p3[0]}, "
            f"Memory: {p3[1]}, "
            f"GPU: {p3[2]}."
        )

    elif "what is p1's remaining need" in q \
            or "what is p1 remaining need" in q:

        p1 = need[1]

        st.success(
            f"P1's remaining need is "
            f"CPU: {p1[0]}, "
            f"Memory: {p1[1]}, "
            f"GPU: {p1[2]}."
        )

    elif "how many cpu" in q \
            and "available" in q:

        st.success(
            f"There are {available[0]} CPU "
            "resources currently available."
        )

    elif "how many gpu" in q \
            and "available" in q:

        st.success(
            f"There are {available[2]} GPU "
            "resources currently available."
        )

    elif "is the system safe" in q:

        if safe:

            sequence_names = [
                PROCESSES[i]
                for i in sequence
            ]

            st.success(
                "Yes. The system is SAFE.\n\n"
                "Safe sequence: "
                + " → ".join(sequence_names)
            )

        else:

            st.error(
                "No. The system is NOT SAFE."
            )

    elif "is there a deadlock" in q:

        if deadlock:

            names = [
                PROCESSES[i]
                for i in deadlocked_processes
            ]

            st.error(
                "Yes. Deadlock detected.\n\n"
                "Affected processes: "
                + ", ".join(names)
            )

        else:

            st.success(
                "No deadlock is detected."
            )

    elif "allocation matrix" in q:

        st.dataframe(
            matrix_dataframe(allocation),
            use_container_width=True
        )

    elif "need matrix" in q:

        st.dataframe(
            matrix_dataframe(need),
            use_container_width=True
        )

    elif "maximum matrix" in q:

        st.dataframe(
            matrix_dataframe(maximum),
            use_container_width=True
        )

    elif "banker's algorithm" in q \
            or "bankers algorithm" in q:

        st.write(
            """
Banker's Algorithm is a deadlock-avoidance algorithm.

Before granting a resource request, the system checks
whether granting that request would leave the system
in a safe state.

A safe state means there is at least one possible
sequence in which every process can finish and release
its resources.

If granting a request would make the system unsafe,
the request is denied.
"""
        )

        if safe:

            sequence_names = [
                PROCESSES[i]
                for i in sequence
            ]

            st.info(
                "Current safe sequence: "
                + " → ".join(sequence_names)
            )

    elif "what is a deadlock" in q:

        st.write(
            """
A deadlock occurs when processes are waiting for
resources held by other processes, and none of them
can continue.

Because the processes cannot continue, they cannot
release their resources, causing the system to remain
stuck.
"""
        )

    elif "resource allocation" in q:

        st.write(
            f"""
The system manages three resource types:

- CPU: {available[0]} currently available
- Memory: {available[1]} currently available
- GPU: {available[2]} currently available

The system is currently
{"SAFE" if safe else "UNSAFE"}.

Deadlock status:
{"Deadlock detected" if deadlock else "No deadlock detected"}.
"""
        )

    elif "why is the system safe" in q:

        if safe:

            work = available.copy()

            st.success(
                "The system is safe because Banker's Algorithm "
                "can find a complete safe sequence."
            )

            for pid in sequence:

                row = need[pid]

                st.write(
                    f"**{PROCESSES[pid]}** can finish because its "
                    f"remaining need is CPU: {row[0]}, "
                    f"Memory: {row[1]}, GPU: {row[2]}."
                )

                work = [
                    work[j] + allocation[pid][j]
                    for j in range(len(RESOURCES))
                ]

                st.write(
                    f"After {PROCESSES[pid]} finishes, available "
                    f"resources become CPU: {work[0]}, "
                    f"Memory: {work[1]}, GPU: {work[2]}."
                )

            st.info(
                "Safe sequence: "
                + " → ".join(PROCESSES[i] for i in sequence)
            )

        else:

            st.error(
                "The system is not safe because no complete "
                "safe sequence exists."
            )

    elif "why is the system deadlocked" in q or "circular wait" in q:

        if deadlock:

            names = [
                PROCESSES[i]
                for i in deadlocked_processes
            ]

            st.error(
                "Deadlock detected among: "
                + ", ".join(names)
            )

        else:

            st.success(
                "No deadlock is currently detected, so there is "
                "no circular wait involving the current state."
            )

    elif "maximum need" in q:

        import re

        match = re.search(r"p([0-4])", q)

        if match:

            pid = int(match.group(1))
            row = maximum[pid]

            st.success(
                f"{PROCESSES[pid]}'s maximum need is "
                f"CPU: {row[0]}, Memory: {row[1]}, GPU: {row[2]}."
            )

        else:

            st.warning(
                "Please specify a process such as P0, P1, P2, P3, or P4."
            )

    elif "remaining need" in q:

        import re

        match = re.search(r"p([0-4])", q)

        if match:

            pid = int(match.group(1))
            row = need[pid]

            st.success(
                f"{PROCESSES[pid]}'s remaining need is "
                f"CPU: {row[0]}, Memory: {row[1]}, GPU: {row[2]}."
            )

        else:

            st.warning(
                "Please specify a process such as P0, P1, P2, P3, or P4."
            )

    elif "resources are currently allocated" in q:

        total = [
            sum(allocation[i][j] for i in range(len(PROCESSES)))
            for j in range(len(RESOURCES))
        ]

        st.success(
            f"Currently allocated: CPU: {total[0]}, "
            f"Memory: {total[1]}, GPU: {total[2]}."
        )

    else:

        # --------------------------------------------------------
        # LLM FALLBACK
        #
        # Keep the original Streamlit UI and all deterministic
        # factual handlers. General/conceptual questions are sent
        # through the same RAG + llama-server pipeline used by the
        # CLI assistant.
        # --------------------------------------------------------
        try:
            with st.spinner("Retrieving context and generating answer..."):
                context = generate_context(question, allocator)

                factual_answer = generate_factual_answer(
                    question,
                    context,
                    allocator
                )

                if factual_answer:
                    st.success(factual_answer)
                else:
                    answer = generate_llm_answer(
                        question,
                        context
                    )

                    if validate_llm_answer(
                        answer,
                        context,
                        allocator
                    ):
                        st.write(answer)
                    else:
                        st.warning(
                            "The LLM response could not be safely "
                            "validated. Please ask a more specific "
                            "question about the current system."
                        )

        except Exception as e:
            st.error(
                "LLM generation failed. Make sure llama-server is "
                "running on http://127.0.0.1:8080."
            )
            st.caption(f"Details: {e}")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CSE323 Resource Allocation Management System "
    "• Banker's Algorithm • Deadlock Detection • RAG + LLM"
)