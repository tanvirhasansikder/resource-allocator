import streamlit as st
import pandas as pd

from banker import is_safe, calculate_need
from allocator import ResourceAllocator
from deadlock import detect_deadlock


# ======================================================
# PAGE CONFIGURATION
# ======================================================

st.set_page_config(
    page_title="OS Resource Allocator",
    page_icon="⚙️",
    layout="wide"
)


# ======================================================
# TITLE
# ======================================================

st.title("⚙️ Operating System Resource Allocator")

st.markdown(
    """
    **Interactive Resource Allocation and Deadlock Simulator**

    This system demonstrates resource allocation, Banker's Algorithm,
    safe-state checking, resource release, and deadlock detection.
    """
)


# ======================================================
# INITIAL SYSTEM DATA
# ======================================================

RESOURCE_NAMES = [
    "CPU",
    "Memory",
    "GPU"
]

PROCESS_NAMES = [
    "P0",
    "P1",
    "P2",
    "P3",
    "P4"
]

INITIAL_AVAILABLE = [
    3,
    3,
    2
]

INITIAL_MAXIMUM = [
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


# ======================================================
# SESSION STATE
# ======================================================

if "available" not in st.session_state:

    st.session_state.available = INITIAL_AVAILABLE.copy()

if "maximum" not in st.session_state:

    st.session_state.maximum = [
        row.copy()
        for row in INITIAL_MAXIMUM
    ]

if "allocation" not in st.session_state:

    st.session_state.allocation = [
        row.copy()
        for row in INITIAL_ALLOCATION
    ]


# ======================================================
# CURRENT STATE
# ======================================================

available = st.session_state.available
maximum = st.session_state.maximum
allocation = st.session_state.allocation

need = calculate_need(
    maximum,
    allocation
)


# ======================================================
# SYSTEM STATUS
# ======================================================

safe, safe_sequence = is_safe(
    available,
    maximum,
    allocation
)


if safe:

    st.success("✓ SYSTEM IS IN A SAFE STATE")

else:

    st.error("⚠ SYSTEM IS IN AN UNSAFE STATE")


# ======================================================
# RESOURCE SUMMARY
# ======================================================

st.header("📊 Resource Status")

resource_table = pd.DataFrame(
    {
        "Resource": RESOURCE_NAMES,
        "Available": available
    }
)

st.dataframe(
    resource_table,
    use_container_width=True,
    hide_index=True
)


# ======================================================
# PROCESS INFORMATION
# ======================================================

st.header("👥 Process Allocation")

allocation_table = pd.DataFrame(
    allocation,
    index=PROCESS_NAMES,
    columns=RESOURCE_NAMES
)

st.subheader("Current Allocation")

st.dataframe(
    allocation_table,
    use_container_width=True
)


need_table = pd.DataFrame(
    need,
    index=PROCESS_NAMES,
    columns=RESOURCE_NAMES
)

st.subheader("Remaining Need")

st.dataframe(
    need_table,
    use_container_width=True
)


# ======================================================
# SAFE SEQUENCE
# ======================================================

st.header("🔐 Safe Sequence")

if safe:

    sequence_text = " → ".join(
        PROCESS_NAMES[i]
        for i in safe_sequence
    )

    st.info(sequence_text)

else:

    st.warning(
        "No safe sequence exists for the current system state."
    )


# ======================================================
# RESOURCE REQUEST
# ======================================================

st.header("📥 Request Resources")

selected_process = st.selectbox(
    "Select Process",
    PROCESS_NAMES
)

process_id = PROCESS_NAMES.index(
    selected_process
)


col1, col2, col3 = st.columns(3)


with col1:

    cpu_request = st.number_input(
        "CPU",
        min_value=0,
        value=0,
        step=1
    )


with col2:

    memory_request = st.number_input(
        "Memory",
        min_value=0,
        value=0,
        step=1
    )


with col3:

    gpu_request = st.number_input(
        "GPU",
        min_value=0,
        value=0,
        step=1
    )


request = [
    cpu_request,
    memory_request,
    gpu_request
]


if st.button(
    "🔍 Check & Submit Request",
    use_container_width=True
):

    allocator = ResourceAllocator(
        RESOURCE_NAMES,
        PROCESS_NAMES,
        maximum,
        allocation
    )

    allocator.set_available(
        available
    )

    result = allocator.request(
        process_id,
        request
    )


    if result["success"]:

        st.session_state.available = (
            allocator.available
        )

        st.session_state.allocation = (
            allocator.allocation
        )

        st.success(
            result["message"]
        )

        if result["safe_sequence"]:

            sequence = " → ".join(
                PROCESS_NAMES[i]
                for i in result["safe_sequence"]
            )

            st.info(
                f"Safe Sequence: {sequence}"
            )

        st.rerun()

    else:

        st.error(
            result["message"]
        )


# ======================================================
# RESOURCE RELEASE
# ======================================================

st.header("📤 Release Resources")

release_process = st.selectbox(
    "Process releasing resources",
    PROCESS_NAMES,
    key="release_process"
)

release_process_id = PROCESS_NAMES.index(
    release_process
)


release_col1, release_col2, release_col3 = st.columns(3)


with release_col1:

    cpu_release = st.number_input(
        "CPU to release",
        min_value=0,
        value=0,
        step=1
    )


with release_col2:

    memory_release = st.number_input(
        "Memory to release",
        min_value=0,
        value=0,
        step=1
    )


with release_col3:

    gpu_release = st.number_input(
        "GPU to release",
        min_value=0,
        value=0,
        step=1
    )


release = [
    cpu_release,
    memory_release,
    gpu_release
]


if st.button(
    "📤 Release Resources",
    use_container_width=True
):

    allocator = ResourceAllocator(
        RESOURCE_NAMES,
        PROCESS_NAMES,
        maximum,
        allocation
    )

    allocator.set_available(
        available
    )

    result = allocator.release(
        release_process_id,
        release
    )


    if result["success"]:

        st.session_state.available = (
            allocator.available
        )

        st.session_state.allocation = (
            allocator.allocation
        )

        st.success(
            result["message"]
        )

        st.rerun()

    else:

        st.error(
            result["message"]
        )


# ======================================================
# DEADLOCK DETECTION
# ======================================================

st.header("💀 Deadlock Detection")

if st.button(
    "Run Deadlock Detection",
    use_container_width=True
):

    # For demonstration, use current Need
    # as outstanding requests.

    deadlock, processes = detect_deadlock(
        available,
        allocation,
        need
    )


    if deadlock:

        st.error(
            "⚠ DEADLOCK DETECTED"
        )

        deadlocked_names = [
            PROCESS_NAMES[i]
            for i in processes
        ]

        st.write(
            "Deadlocked Processes:",
            ", ".join(deadlocked_names)
        )

    else:

        st.success(
            "✓ No deadlock detected."
        )


# ======================================================
# RESET
# ======================================================

st.header("🔄 Simulation Control")

if st.button(
    "Reset Simulation",
    use_container_width=True
):

    st.session_state.available = (
        INITIAL_AVAILABLE.copy()
    )

    st.session_state.maximum = [
        row.copy()
        for row in INITIAL_MAXIMUM
    ]

    st.session_state.allocation = [
        row.copy()
        for row in INITIAL_ALLOCATION
    ]

    st.rerun()