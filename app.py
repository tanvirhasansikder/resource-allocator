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
# DEFAULT CONFIGURATION
# ======================================================

DEFAULT_RESOURCES = ["CPU", "Memory", "GPU"]

DEFAULT_PROCESSES = ["P0", "P1", "P2", "P3", "P4"]

DEFAULT_TOTAL = [10, 7, 7]

DEFAULT_MAXIMUM = [
    [7, 5, 3],
    [3, 2, 2],
    [9, 0, 2],
    [2, 2, 2],
    [4, 3, 3]
]

DEFAULT_ALLOCATION = [
    [0, 1, 0],
    [2, 0, 0],
    [3, 0, 2],
    [2, 1, 1],
    [0, 0, 2]
]


# ======================================================
# SESSION STATE INITIALIZATION
# ======================================================

if "resources" not in st.session_state:

    st.session_state.resources = DEFAULT_RESOURCES.copy()

if "processes" not in st.session_state:

    st.session_state.processes = DEFAULT_PROCESSES.copy()

if "total" not in st.session_state:

    st.session_state.total = DEFAULT_TOTAL.copy()

if "maximum" not in st.session_state:

    st.session_state.maximum = [
        row.copy()
        for row in DEFAULT_MAXIMUM
    ]

if "allocation" not in st.session_state:

    st.session_state.allocation = [
        row.copy()
        for row in DEFAULT_ALLOCATION
    ]


# ======================================================
# HELPER FUNCTIONS
# ======================================================

def calculate_available(total, allocation):

    available = []

    for j in range(len(total)):

        allocated = sum(
            allocation[i][j]
            for i in range(len(allocation))
        )

        available.append(
            total[j] - allocated
        )

    return available


def reset_to_defaults():

    st.session_state.resources = DEFAULT_RESOURCES.copy()

    st.session_state.processes = DEFAULT_PROCESSES.copy()

    st.session_state.total = DEFAULT_TOTAL.copy()

    st.session_state.maximum = [
        row.copy()
        for row in DEFAULT_MAXIMUM
    ]

    st.session_state.allocation = [
        row.copy()
        for row in DEFAULT_ALLOCATION
    ]


# ======================================================
# SIDEBAR
# ======================================================

with st.sidebar:

    st.header("⚙️ System Configuration")

    st.write(
        "Configure the resources and processes used "
        "by the simulator."
    )

    number_of_processes = st.number_input(
        "Number of Processes",
        min_value=1,
        max_value=10,
        value=len(st.session_state.processes),
        step=1
    )

    number_of_resources = st.number_input(
        "Number of Resources",
        min_value=1,
        max_value=6,
        value=len(st.session_state.resources),
        step=1
    )

    resource_names_text = st.text_input(
        "Resource Names",
        value=", ".join(st.session_state.resources),
        help="Example: CPU, Memory, GPU"
    )

    st.divider()

    if st.button(
        "Apply Configuration",
        use_container_width=True
    ):

        names = [
            name.strip()
            for name in resource_names_text.split(",")
            if name.strip()
        ]

        if len(names) != number_of_resources:

            st.error(
                f"Please provide exactly "
                f"{number_of_resources} resource names."
            )

        else:

            st.session_state.resources = names

            st.session_state.processes = [
                f"P{i}"
                for i in range(number_of_processes)
            ]

            st.session_state.total = [
                0
                for _ in range(number_of_resources)
            ]

            st.session_state.maximum = [
                [0] * number_of_resources
                for _ in range(number_of_processes)
            ]

            st.session_state.allocation = [
                [0] * number_of_resources
                for _ in range(number_of_processes)
            ]

            st.success("Configuration applied!")

            st.rerun()

    if st.button(
        "Reset to Default",
        use_container_width=True
    ):

        reset_to_defaults()

        st.rerun()


# ======================================================
# LOAD CURRENT STATE
# ======================================================

resources = st.session_state.resources

processes = st.session_state.processes

total = st.session_state.total

maximum = st.session_state.maximum

allocation = st.session_state.allocation


# ======================================================
# TITLE
# ======================================================

st.title("⚙️ Operating System Resource Allocator")

st.markdown(
    """
    ### Interactive Resource Allocation & Deadlock Simulator

    This application demonstrates **Banker's Algorithm,
    resource allocation, safe-state detection, resource
    release, and deadlock detection**.
    """
)


# ======================================================
# VALIDATE CURRENT STATE
# ======================================================

invalid_allocation = False
invalid_maximum = False


for i in range(len(processes)):

    for j in range(len(resources)):

        if allocation[i][j] > maximum[i][j]:

            invalid_allocation = True


available = calculate_available(
    total,
    allocation
)


for value in available:

    if value < 0:

        invalid_allocation = True


# ======================================================
# SYSTEM STATUS
# ======================================================

st.header("🟢 System Status")


if invalid_allocation:

    st.error(
        "⚠️ Invalid system configuration. "
        "Allocation cannot exceed total resources "
        "or a process's maximum requirement."
    )

    safe = False
    safe_sequence = []

else:

    need = calculate_need(
        maximum,
        allocation
    )

    safe, safe_sequence = is_safe(
        available,
        maximum,
        allocation
    )

    if safe:

        st.success(
            "✓ SYSTEM IS IN A SAFE STATE"
        )

    else:

        st.error(
            "⚠️ SYSTEM IS IN AN UNSAFE STATE"
        )


# ======================================================
# RESOURCE STATUS
# ======================================================

st.header("📊 Resource Status")

resource_table = pd.DataFrame(
    {
        "Resource": resources,
        "Total": total,
        "Allocated": [
            sum(
                allocation[i][j]
                for i in range(len(processes))
            )
            for j in range(len(resources))
        ],
        "Available": available
    }
)

st.dataframe(
    resource_table,
    use_container_width=True,
    hide_index=True
)


# ======================================================
# TOTAL RESOURCE CONFIGURATION
# ======================================================

st.header("📦 Total Resources")

st.caption(
    "Set the total amount of each resource available "
    "in the system."
)

total_df = pd.DataFrame(
    [total],
    columns=resources
)

edited_total = st.data_editor(
    total_df,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="total_editor"
)

if st.button(
    "Update Total Resources",
    use_container_width=True
):

    new_total = [
        max(0, int(edited_total.iloc[0][resource]))
        for resource in resources
    ]

    st.session_state.total = new_total

    st.rerun()


# ======================================================
# MAXIMUM MATRIX
# ======================================================

st.header("📋 Maximum Resource Requirement")

st.caption(
    "Maximum resources each process may require."
)

maximum_df = pd.DataFrame(
    maximum,
    index=processes,
    columns=resources
)

edited_maximum = st.data_editor(
    maximum_df,
    use_container_width=True,
    key="maximum_editor"
)

if st.button(
    "Update Maximum Matrix",
    use_container_width=True
):

    new_maximum = [
        [
            max(
                0,
                int(edited_maximum.iloc[i][resource])
            )
            for resource in resources
        ]
        for i in range(len(processes))
    ]

    st.session_state.maximum = new_maximum

    st.rerun()


# ======================================================
# ALLOCATION MATRIX
# ======================================================

st.header("📌 Current Allocation")

st.caption(
    "Resources currently allocated to each process."
)

allocation_df = pd.DataFrame(
    allocation,
    index=processes,
    columns=resources
)

edited_allocation = st.data_editor(
    allocation_df,
    use_container_width=True,
    key="allocation_editor"
)

if st.button(
    "Update Allocation Matrix",
    use_container_width=True
):

    new_allocation = [
        [
            max(
                0,
                int(edited_allocation.iloc[i][resource])
            )
            for resource in resources
        ]
        for i in range(len(processes))
    ]

    st.session_state.allocation = new_allocation

    st.rerun()


# ======================================================
# NEED MATRIX
# ======================================================

if not invalid_allocation:

    st.header("📐 Remaining Need")

    need = calculate_need(
        maximum,
        allocation
    )

    need_df = pd.DataFrame(
        need,
        index=processes,
        columns=resources
    )

    st.dataframe(
        need_df,
        use_container_width=True
    )


# ======================================================
# SAFE SEQUENCE
# ======================================================

st.header("🔐 Safe Sequence")

if safe:

    sequence_text = " → ".join(
        processes[i]
        for i in safe_sequence
    )

    st.success(
        sequence_text
    )

else:

    st.warning(
        "No safe sequence exists for the current state."
    )


# ======================================================
# RESOURCE REQUEST
# ======================================================

st.header("📥 Resource Request")

selected_process = st.selectbox(
    "Select Process",
    processes,
    key="request_process"
)

process_id = processes.index(
    selected_process
)

st.write(
    f"Request resources for **{selected_process}**:"
)

request_values = []

request_columns = st.columns(
    len(resources)
)

for j, resource in enumerate(resources):

    with request_columns[j]:

        value = st.number_input(
            resource,
            min_value=0,
            value=0,
            step=1,
            key=f"request_{resource}"
        )

        request_values.append(value)


if st.button(
    "🔍 Check & Submit Request",
    use_container_width=True
):

    if invalid_allocation:

        st.error(
            "Fix the invalid system configuration first."
        )

    else:

        allocator = ResourceAllocator(
            resources,
            processes,
            maximum,
            allocation
        )

        allocator.set_available(
            available
        )

        result = allocator.request(
            process_id,
            request_values
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
                    processes[i]
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
    "Process",
    processes,
    key="release_process"
)

release_process_id = processes.index(
    release_process
)

release_values = []

release_columns = st.columns(
    len(resources)
)

for j, resource in enumerate(resources):

    with release_columns[j]:

        value = st.number_input(
            resource,
            min_value=0,
            value=0,
            step=1,
            key=f"release_{resource}"
        )

        release_values.append(value)


if st.button(
    "📤 Release Resources",
    use_container_width=True
):

    allocator = ResourceAllocator(
        resources,
        processes,
        maximum,
        allocation
    )

    allocator.set_available(
        available
    )

    result = allocator.release(
        release_process_id,
        release_values
    )

    if result["success"]:

        st.session_state.allocation = (
            allocator.allocation
        )

        st.session_state.total = [
            available[j]
            + sum(
                allocator.allocation[i][j]
                for i in range(len(processes))
            )
            for j in range(len(resources))
        ]

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

st.caption(
    "Run the deadlock detection algorithm against "
    "the current system state."
)

if st.button(
    "🔎 Run Deadlock Detection",
    use_container_width=True
):

    if invalid_allocation:

        st.error(
            "Fix the invalid configuration first."
        )

    else:

        need = calculate_need(
            maximum,
            allocation
        )

        deadlock, deadlocked_processes = detect_deadlock(
            available,
            allocation,
            need
        )

        if deadlock:

            st.error(
                "⚠️ DEADLOCK DETECTED"
            )

            names = [
                processes[i]
                for i in deadlocked_processes
            ]

            st.write(
                "**Deadlocked Processes:**",
                ", ".join(names)
            )

        else:

            st.success(
                "✓ No deadlock detected."
            )


# ======================================================
# RESET SIMULATION
# ======================================================

st.header("🔄 Simulation Control")

if st.button(
    "Reset Simulation",
    use_container_width=True
):

    reset_to_defaults()

    st.rerun()


# ======================================================
# FOOTER
# ======================================================

st.divider()

st.caption(
    "CSE323 Operating Systems Project • "
    "Interactive Resource Allocation & Deadlock Simulator"
)