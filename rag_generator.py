from rag import (
    build_resource_allocation_graph,
    retrieve_graph_context
)


def generate_answer(query, context):
    """
    Generate a natural-language answer from the
    retrieved Resource Allocation Graph context.
    """

    # ==================================================
    # DEADLOCK ANSWER
    # ==================================================

    for item in context:

        if item.get("type") == "deadlock_analysis":

            if item["has_cycle"]:

                answer = (
                    "The system is deadlocked because a "
                    "circular wait exists between the "
                    "processes and resources.\n\n"
                )

                answer += "Detected cycle(s):\n"

                for cycle in item["cycles"]:

                    answer += (
                        "- "
                        + " -> ".join(cycle)
                        + "\n"
                    )

                answer += (
                    "\nThis means each process in the cycle "
                    "is waiting for a resource currently held "
                    "by another process. Therefore, none of "
                    "the processes can proceed until a "
                    "resource is released."
                )

                return answer

            else:

                return (
                    "No circular wait was detected in the "
                    "current Resource Allocation Graph."
                )

    # ==================================================
    # PROCESS ANSWER
    # ==================================================

    for item in context:

        if "process" not in item:
            continue

        process = item["process"]

        answer = f"{process} resource information:\n\n"

        if item["allocated_resources"]:

            answer += "Currently allocated:\n"

            for resource in item["allocated_resources"]:

                answer += (
                    f"- {resource['resource']}: "
                    f"{resource['amount']}\n"
                )

        else:

            answer += "Currently allocated: None\n"

        if item["requested_resources"]:

            answer += "\nCurrently requesting:\n"

            for resource in item["requested_resources"]:

                answer += (
                    f"- {resource['resource']}: "
                    f"{resource['amount']}\n"
                )

        else:

            answer += "\nCurrently requesting: None"

        return answer

    # ==================================================
    # RESOURCE ANSWER
    # ==================================================

    for item in context:

        if "resource" not in item:
            continue

        resource = item["resource"]

        answer = f"Resource: {resource}\n\n"

        if item["allocated_to"]:

            answer += "Allocated to:\n"

            for process in item["allocated_to"]:

                answer += (
                    f"- {process['process']}: "
                    f"{process['amount']}\n"
                )

        else:

            answer += "Allocated to: None\n"

        if item["requested_by"]:

            answer += "\nRequested by:\n"

            for process in item["requested_by"]:

                answer += (
                    f"- {process['process']}: "
                    f"{process['amount']}\n"
                )

        else:

            answer += "\nRequested by: None"

        return answer

    return (
        "I could not find enough relevant information "
        "in the Resource Allocation Graph."
    )


# ======================================================
# MAIN RAG PIPELINE
# ======================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # Same test data used by rag.py
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Build actual Resource Allocation Graph
    # --------------------------------------------------

    nodes, edges = build_resource_allocation_graph(
        processes,
        resources,
        allocation,
        maximum
    )

    # --------------------------------------------------
    # Ask a question
    # --------------------------------------------------

    query = "Why is the system deadlocked?"

    print("=" * 60)
    print("RESOURCE ALLOCATION RAG")
    print("=" * 60)

    print("\nQuestion:")
    print(query)

    # --------------------------------------------------
    # Retrieve relevant information
    # --------------------------------------------------

    context = retrieve_graph_context(
        query,
        nodes,
        edges
    )

    print("\nRetrieved Context:")
    print("-" * 60)

    for item in context:

        if item.get("type") == "deadlock_analysis":

            print("Deadlock Analysis:")

            if item["has_cycle"]:

                print("Circular wait detected.")

                for cycle in item["cycles"]:

                    print(
                        "Cycle:",
                        " -> ".join(cycle)
                    )

            else:

                print("No circular wait detected.")

    # --------------------------------------------------
    # Generate answer
    # --------------------------------------------------

    answer = generate_answer(
        query,
        context
    )

    print("\nGenerated Answer:")
    print("-" * 60)
    print(answer)