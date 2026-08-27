from banker import calculate_need, is_safe
from allocator import ResourceAllocator
from deadlock import detect_deadlock
from rag_llm import run_assistant


# ============================================================
# CONFIGURATION
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
# CREATE RESOURCE ALLOCATOR
# ============================================================

allocator = ResourceAllocator(
    RESOURCES,
    PROCESSES,
    [row.copy() for row in MAXIMUM],
    [row.copy() for row in INITIAL_ALLOCATION]
)

allocator.set_available(
    INITIAL_AVAILABLE.copy()
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_current_need():
    """
    Calculate the current Need matrix.

    Need = Maximum - Allocation
    """

    state = allocator.get_state()

    return calculate_need(
        state["maximum"],
        state["allocation"]
    )


def print_state():
    """
    Display the current resource allocation state.
    """

    state = allocator.get_state()

    print("\n" + "=" * 60)
    print("CURRENT SYSTEM STATE")
    print("=" * 60)

    # --------------------------------------------------------
    # AVAILABLE RESOURCES
    # --------------------------------------------------------

    print("\nAvailable Resources:")

    for i, resource in enumerate(RESOURCES):

        print(
            f"  {resource:<10}: "
            f"{state['available'][i]}"
        )

    # --------------------------------------------------------
    # ALLOCATION MATRIX
    # --------------------------------------------------------

    print("\nAllocation Matrix:")

    print(
        f"{'Process':<10}"
        f"{'CPU':<10}"
        f"{'Memory':<10}"
        f"{'GPU':<10}"
    )

    print("-" * 40)

    for i, process in enumerate(PROCESSES):

        print(
            f"{process:<10}"
            f"{state['allocation'][i][0]:<10}"
            f"{state['allocation'][i][1]:<10}"
            f"{state['allocation'][i][2]:<10}"
        )

    # --------------------------------------------------------
    # MAXIMUM MATRIX
    # --------------------------------------------------------

    print("\nMaximum Matrix:")

    print(
        f"{'Process':<10}"
        f"{'CPU':<10}"
        f"{'Memory':<10}"
        f"{'GPU':<10}"
    )

    print("-" * 40)

    for i, process in enumerate(PROCESSES):

        print(
            f"{process:<10}"
            f"{state['maximum'][i][0]:<10}"
            f"{state['maximum'][i][1]:<10}"
            f"{state['maximum'][i][2]:<10}"
        )

    # --------------------------------------------------------
    # NEED MATRIX
    # --------------------------------------------------------

    print("\nNeed Matrix:")

    need = calculate_current_need()

    print(
        f"{'Process':<10}"
        f"{'CPU':<10}"
        f"{'Memory':<10}"
        f"{'GPU':<10}"
    )

    print("-" * 40)

    for i, process in enumerate(PROCESSES):

        print(
            f"{process:<10}"
            f"{need[i][0]:<10}"
            f"{need[i][1]:<10}"
            f"{need[i][2]:<10}"
        )


# ============================================================
# RESOURCE REQUEST
# ============================================================

def request_resources_menu():
    """
    Interactive resource request.
    """

    print("\n" + "=" * 60)
    print("RESOURCE REQUEST")
    print("=" * 60)

    print("\nProcesses:")

    for i, process in enumerate(PROCESSES):

        print(
            f"{i}. {process}"
        )

    try:

        process_id = int(
            input("\nEnter process number: ")
        )

        if (
            process_id < 0
            or process_id >= len(PROCESSES)
        ):

            print(
                "Invalid process."
            )

            return

        print("\nEnter requested resources:")

        request = []

        for resource in RESOURCES:

            value = int(
                input(
                    f"{resource} request: "
                )
            )

            if value < 0:

                print(
                    "Resource request cannot be negative."
                )

                return

            request.append(value)

        # ----------------------------------------------------
        # Send request to allocator
        # ----------------------------------------------------

        result = allocator.request(
            process_id,
            request
        )

        print("\n" + "-" * 60)
        print("REQUEST RESULT")
        print("-" * 60)

        print(
            f"Process: "
            f"{PROCESSES[process_id]}"
        )

        print(
            f"Request: {request}"
        )

        print(
            f"Success: {result['success']}"
        )

        print(
            f"Message: {result['message']}"
        )

        # ----------------------------------------------------
        # Safe sequence
        # ----------------------------------------------------

        if result.get("safe_sequence"):

            sequence = [
                PROCESSES[i]
                for i in result["safe_sequence"]
            ]

            print(
                "Safe Sequence:",
                " -> ".join(sequence)
            )

    except ValueError:

        print(
            "Please enter valid numeric values."
        )


# ============================================================
# RESOURCE RELEASE
# ============================================================

def release_resources_menu():
    """
    Interactive resource release.
    """

    print("\n" + "=" * 60)
    print("RESOURCE RELEASE")
    print("=" * 60)

    print("\nProcesses:")

    for i, process in enumerate(PROCESSES):

        print(
            f"{i}. {process}"
        )

    try:

        process_id = int(
            input("\nEnter process number: ")
        )

        if (
            process_id < 0
            or process_id >= len(PROCESSES)
        ):

            print(
                "Invalid process."
            )

            return

        print("\nEnter resources to release:")

        release = []

        for resource in RESOURCES:

            value = int(
                input(
                    f"{resource} release: "
                )
            )

            if value < 0:

                print(
                    "Resource release cannot be negative."
                )

                return

            release.append(value)

        # ----------------------------------------------------
        # Release resources
        # ----------------------------------------------------

        result = allocator.release(
            process_id,
            release
        )

        print("\n" + "-" * 60)
        print("RELEASE RESULT")
        print("-" * 60)

        print(
            f"Process: "
            f"{PROCESSES[process_id]}"
        )

        print(
            f"Release: {release}"
        )

        print(
            f"Success: {result['success']}"
        )

        print(
            f"Message: {result['message']}"
        )

    except ValueError:

        print(
            "Please enter valid numeric values."
        )


# ============================================================
# BANKER'S ALGORITHM
# ============================================================

def run_banker():
    """
    Run Banker's safety algorithm on the
    current system state.
    """

    state = allocator.get_state()

    safe, sequence = is_safe(
        state["available"],
        state["maximum"],
        state["allocation"]
    )

    print("\n" + "=" * 60)
    print("BANKER'S ALGORITHM")
    print("=" * 60)

    if safe:

        print(
            "\nSystem is SAFE."
        )

        process_sequence = [
            PROCESSES[i]
            for i in sequence
        ]

        print(
            "Safe Sequence:",
            " -> ".join(process_sequence)
        )

    else:

        print(
            "\nSystem is NOT SAFE."
        )

        print(
            "No complete safe sequence exists."
        )


# ============================================================
# DEADLOCK DETECTION
# ============================================================

def run_deadlock_detection():
    """
    Run deadlock detection using the
    current system state.
    """

    state = allocator.get_state()

    # --------------------------------------------------------
    # Outstanding request
    #
    # Request = Maximum - Allocation
    # --------------------------------------------------------

    request = calculate_need(
        state["maximum"],
        state["allocation"]
    )

    deadlock, deadlocked_processes = detect_deadlock(
        state["available"],
        state["allocation"],
        request
    )

    print("\n" + "=" * 60)
    print("DEADLOCK DETECTION")
    print("=" * 60)

    print(
        "\nDeadlock detected:",
        deadlock
    )

    if deadlock:

        print(
            "\nDeadlocked processes:"
        )

        for process_id in deadlocked_processes:

            print(
                f"  {PROCESSES[process_id]}"
            )

    else:

        print(
            "\nNo deadlocked processes detected."
        )


# ============================================================
# RESOURCE OWNERSHIP
# ============================================================

def show_resource_summary():
    """
    Show a simple resource ownership summary.
    """

    state = allocator.get_state()

    print("\n" + "=" * 60)
    print("RESOURCE OWNERSHIP")
    print("=" * 60)

    for resource_id, resource in enumerate(RESOURCES):

        holders = []

        for process_id, process in enumerate(PROCESSES):

            amount = (
                state["allocation"]
                [process_id]
                [resource_id]
            )

            if amount > 0:

                holders.append(
                    f"{process} ({amount})"
                )

        if holders:

            print(
                f"\n{resource}: "
                + ", ".join(holders)
            )

        else:

            print(
                f"\n{resource}: Available"
            )


# ============================================================
# RAG + LLM
# ============================================================

def run_rag():
    """
    Compatibility wrapper for the RAG assistant.

    The actual assistant is implemented in rag_llm.py.
    The same ResourceAllocator object is passed so the
    assistant can read the CURRENT live state.
    """

    run_assistant(
        allocator
    )


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        print("\n")

        print("=" * 60)

        print(
            "       RESOURCE ALLOCATION MANAGEMENT SYSTEM"
        )

        print("=" * 60)

        print("""
1. View Current System State
2. Request Resources
3. Release Resources
4. Run Banker's Safety Algorithm
5. Detect Deadlock
6. Show Resource Ownership
7. RAG + LLM Assistant
8. Exit
""")

        choice = input(
            "Enter your choice: "
        ).strip()

        # ====================================================
        # OPTION 1
        # ====================================================

        if choice == "1":

            print_state()

        # ====================================================
        # OPTION 2
        # ====================================================

        elif choice == "2":

            request_resources_menu()

        # ====================================================
        # OPTION 3
        # ====================================================

        elif choice == "3":

            release_resources_menu()

        # ====================================================
        # OPTION 4
        # ====================================================

        elif choice == "4":

            run_banker()

        # ====================================================
        # OPTION 5
        # ====================================================

        elif choice == "5":

            run_deadlock_detection()

        # ====================================================
        # OPTION 6
        # ====================================================

        elif choice == "6":

            show_resource_summary()

        # ====================================================
        # OPTION 7
        # ====================================================

        elif choice == "7":

            run_rag()

        # ====================================================
        # OPTION 8
        # ====================================================

        elif choice == "8":

            print(
                "\nExiting Resource Allocation "
                "Management System."
            )

            break

        # ====================================================
        # INVALID OPTION
        # ====================================================

        else:

            print(
                "\nInvalid choice. "
                "Please select 1-8."
            )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()