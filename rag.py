def build_resource_allocation_graph(
    processes,
    resources,
    allocation,
    maximum
):
    """
    Build a Resource Allocation Graph (RAG).

    Resource -> Process:
        Resource is currently allocated to the process.

    Process -> Resource:
        Process is requesting the resource.

    Returns:
        nodes: List of graph nodes
        edges: List of graph edges
    """

    nodes = []
    edges = []

    # ==================================================
    # PROCESS NODES
    # ==================================================

    for process in processes:
        nodes.append({
            "id": process,
            "label": process,
            "type": "process"
        })

    # ==================================================
    # RESOURCE NODES
    # ==================================================

    for resource in resources:
        nodes.append({
            "id": resource,
            "label": resource,
            "type": "resource"
        })

    # ==================================================
    # BUILD GRAPH EDGES
    # ==================================================

    for i, process in enumerate(processes):

        for j, resource in enumerate(resources):

            allocated = allocation[i][j]
            maximum_required = maximum[i][j]

            # Resource -> Process
            # Means the process currently holds
            # the resource.

            if allocated > 0:
                edges.append({
                    "source": resource,
                    "target": process,
                    "type": "allocation",
                    "label": f"Allocated: {allocated}"
                })

            # Process -> Resource
            # Means the process is requesting
            # the resource.

            remaining_need = maximum_required - allocated

            if remaining_need > 0:
                edges.append({
                    "source": process,
                    "target": resource,
                    "type": "request",
                    "label": f"Need: {remaining_need}"
                })

    return nodes, edges


# ======================================================
# PROCESS INFORMATION RETRIEVAL
# ======================================================

def get_process_information(process_id, edges):
    """
    Retrieve allocation and request information
    for a specific process.
    """

    information = {
        "process": process_id,
        "allocated_resources": [],
        "requested_resources": []
    }

    for edge in edges:

        # Resource -> Process
        if (
            edge["target"] == process_id
            and edge["type"] == "allocation"
        ):
            information["allocated_resources"].append({
                "resource": edge["source"],
                "amount": edge["label"]
            })

        # Process -> Resource
        elif (
            edge["source"] == process_id
            and edge["type"] == "request"
        ):
            information["requested_resources"].append({
                "resource": edge["target"],
                "amount": edge["label"]
            })

    return information


# ======================================================
# RESOURCE INFORMATION RETRIEVAL
# ======================================================

def get_resource_information(resource_id, edges):
    """
    Retrieve allocation and request information
    for a specific resource.
    """

    information = {
        "resource": resource_id,
        "allocated_to": [],
        "requested_by": []
    }

    for edge in edges:

        # Resource -> Process
        if (
            edge["source"] == resource_id
            and edge["type"] == "allocation"
        ):
            information["allocated_to"].append({
                "process": edge["target"],
                "amount": edge["label"]
            })

        # Process -> Resource
        elif (
            edge["target"] == resource_id
            and edge["type"] == "request"
        ):
            information["requested_by"].append({
                "process": edge["source"],
                "amount": edge["label"]
            })

    return information


# ======================================================
# GRAPH CYCLE DETECTION
# ======================================================

def find_cycles(nodes, edges):
    """
    Detect cycles in the Resource Allocation Graph.

    Example:

        P0 -> Memory -> P1 -> GPU -> P2 -> CPU -> P0

    represents a circular wait.
    """

    graph = {}

    # Create adjacency list
    for node in nodes:
        graph[node["id"]] = []

    # Add directed edges
    for edge in edges:

        source = edge["source"]
        target = edge["target"]

        if source in graph:
            graph[source].append(target)

    cycles = []

    visited = set()
    recursion_stack = set()

    def dfs(node, path):

        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):

            if neighbor not in visited:

                dfs(
                    neighbor,
                    path
                )

            elif neighbor in recursion_stack:

                try:

                    start_index = path.index(
                        neighbor
                    )

                    cycle = (
                        path[start_index:]
                        + [neighbor]
                    )

                    normalized = tuple(cycle)

                    existing_cycles = [
                        tuple(existing)
                        for existing in cycles
                    ]

                    if normalized not in existing_cycles:
                        cycles.append(cycle)

                except ValueError:
                    pass

        path.pop()
        recursion_stack.remove(node)

    # Run DFS
    for node in graph:

        if node not in visited:

            dfs(
                node,
                []
            )

    return cycles


# ======================================================
# DEADLOCK INFORMATION
# ======================================================

def get_deadlock_information(nodes, edges):
    """
    Build detailed deadlock information.

    Includes:

    - Current resource allocations
    - Current resource requests
    - Detected cycles

    This gives the LLM enough evidence to explain
    why the deadlock exists.
    """

    cycles = find_cycles(
        nodes,
        edges
    )

    allocations = []
    requests = []

    # --------------------------------------------------
    # Separate allocation and request edges
    # --------------------------------------------------

    for edge in edges:

        if edge["type"] == "allocation":

            allocations.append({
                "resource": edge["source"],
                "process": edge["target"],
                "amount": edge["label"]
            })

        elif edge["type"] == "request":

            requests.append({
                "process": edge["source"],
                "resource": edge["target"],
                "amount": edge["label"]
            })

    return {
        "type": "deadlock_analysis",
        "has_cycle": len(cycles) > 0,
        "cycles": cycles,
        "allocations": allocations,
        "requests": requests
    }


# ======================================================
# RAG RETRIEVAL
# ======================================================

def retrieve_graph_context(
    query,
    nodes,
    edges
):
    """
    Retrieve relevant information from the Resource
    Allocation Graph based on a natural-language query.

    Deadlock queries return detailed graph evidence,
    including:

    - allocations
    - requests
    - cycles
    """

    query = query.lower()

    context = []

    # ==================================================
    # PROCESS RETRIEVAL
    # ==================================================

    for node in nodes:

        if node["type"] != "process":
            continue

        process_id = node["id"]

        if process_id.lower() in query:

            context.append(
                get_process_information(
                    process_id,
                    edges
                )
            )

    # ==================================================
    # RESOURCE RETRIEVAL
    # ==================================================

    for node in nodes:

        if node["type"] != "resource":
            continue

        resource_id = node["id"]

        if resource_id.lower() in query:

            context.append(
                get_resource_information(
                    resource_id,
                    edges
                )
            )

    # ==================================================
    # DEADLOCK / CYCLE RETRIEVAL
    # ==================================================

    deadlock_keywords = [
        "deadlock",
        "deadlocked",
        "circular wait",
        "cycle",
        "waiting",
        "blocked"
    ]

    if any(
        keyword in query
        for keyword in deadlock_keywords
    ):

        deadlock_information = get_deadlock_information(
            nodes,
            edges
        )

        context.append(
            deadlock_information
        )

    # ==================================================
    # FALLBACK
    # ==================================================

    if not context:

        context.append({
            "type": "complete_graph",
            "nodes": nodes,
            "edges": edges
        })

    return context


# ======================================================
# FORMAT RETRIEVED CONTEXT
# ======================================================

def format_context(context):
    """
    Convert retrieved graph information into readable
    text suitable for an LLM prompt.
    """

    output = []

    output.append(
        "RESOURCE ALLOCATION GRAPH CONTEXT"
    )

    output.append(
        "=" * 40
    )

    for item in context:

        # ------------------------------------------------
        # PROCESS
        # ------------------------------------------------

        if "process" in item:

            output.append(
                f"\nProcess: {item['process']}"
            )

            output.append(
                "Allocated resources:"
            )

            if item["allocated_resources"]:

                for resource in item[
                    "allocated_resources"
                ]:

                    output.append(
                        f"- {resource['resource']}: "
                        f"{resource['amount']}"
                    )

            else:

                output.append("- None")

            output.append(
                "Requested resources:"
            )

            if item["requested_resources"]:

                for resource in item[
                    "requested_resources"
                ]:

                    output.append(
                        f"- {resource['resource']}: "
                        f"{resource['amount']}"
                    )

            else:

                output.append("- None")

        # ------------------------------------------------
        # RESOURCE
        # ------------------------------------------------

        elif "resource" in item:

            output.append(
                f"\nResource: {item['resource']}"
            )

            output.append(
                "Allocated to:"
            )

            if item["allocated_to"]:

                for process in item["allocated_to"]:

                    output.append(
                        f"- {process['process']}: "
                        f"{process['amount']}"
                    )

            else:

                output.append("- None")

            output.append(
                "Requested by:"
            )

            if item["requested_by"]:

                for process in item["requested_by"]:

                    output.append(
                        f"- {process['process']}: "
                        f"{process['amount']}"
                    )

            else:

                output.append("- None")

        # ------------------------------------------------
        # DEADLOCK
        # ------------------------------------------------

        elif item.get("type") == "deadlock_analysis":

            output.append(
                "\nDeadlock Analysis:"
            )

            # --------------------------------------------
            # Cycle
            # --------------------------------------------

            if item["has_cycle"]:

                output.append(
                    "Circular wait detected."
                )

                output.append(
                    "\nDetected Cycle(s):"
                )

                for cycle in item["cycles"]:

                    output.append(
                        "- " + " -> ".join(cycle)
                    )

            else:

                output.append(
                    "No cycle detected."
                )

            # --------------------------------------------
            # Allocations
            # --------------------------------------------

            output.append(
                "\nCurrent Resource Allocations:"
            )

            if item["allocations"]:

                for allocation in item["allocations"]:

                    output.append(
                        f"- {allocation['resource']} "
                        f"is allocated to "
                        f"{allocation['process']} "
                        f"({allocation['amount']})"
                    )

            else:

                output.append("- None")

            # --------------------------------------------
            # Requests
            # --------------------------------------------

            output.append(
                "\nCurrent Resource Requests:"
            )

            if item["requests"]:

                for request in item["requests"]:

                    output.append(
                        f"- {request['process']} "
                        f"is requesting "
                        f"{request['resource']} "
                        f"({request['amount']})"
                    )

            else:

                output.append("- None")

        # ------------------------------------------------
        # COMPLETE GRAPH
        # ------------------------------------------------

        elif item.get("type") == "complete_graph":

            output.append(
                "\nComplete Graph:"
            )

            output.append(
                "Nodes:"
            )

            for node in item["nodes"]:

                output.append(
                    f"- {node['id']} "
                    f"({node['type']})"
                )

            output.append(
                "Edges:"
            )

            for edge in item["edges"]:

                output.append(
                    f"- {edge['source']} -> "
                    f"{edge['target']} "
                    f"[{edge['type']}] "
                    f"{edge['label']}"
                )

    return "\n".join(output)


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # Processes
    # --------------------------------------------------

    processes = [
        "P0",
        "P1",
        "P2"
    ]

    # --------------------------------------------------
    # Resources
    # --------------------------------------------------

    resources = [
        "CPU",
        "Memory",
        "GPU"
    ]

    # --------------------------------------------------
    # Maximum requirements
    # --------------------------------------------------

    maximum = [
        [1, 1, 0],
        [0, 1, 1],
        [1, 0, 1]
    ]

    # --------------------------------------------------
    # Current allocation
    # --------------------------------------------------

    allocation = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ]

    # ==================================================
    # BUILD RESOURCE ALLOCATION GRAPH
    # ==================================================

    nodes, edges = build_resource_allocation_graph(
        processes,
        resources,
        allocation,
        maximum
    )

    # ==================================================
    # DISPLAY GRAPH
    # ==================================================

    print("=" * 50)
    print("RESOURCE ALLOCATION GRAPH")
    print("=" * 50)

    print("\nNODES:")

    for node in nodes:
        print(node)

    print("\nEDGES:")

    for edge in edges:
        print(edge)

    # ==================================================
    # PROCESS RETRIEVAL TEST
    # ==================================================

    print("\n" + "=" * 50)
    print("PROCESS RETRIEVAL TEST")
    print("=" * 50)

    query = "Why is P0 waiting?"

    print(
        f"\nQuery: {query}"
    )

    context = retrieve_graph_context(
        query,
        nodes,
        edges
    )

    print("\nRetrieved Context:")

    print(
        format_context(context)
    )

    # ==================================================
    # DEADLOCK RETRIEVAL TEST
    # ==================================================

    print("\n" + "=" * 50)
    print("DEADLOCK RETRIEVAL TEST")
    print("=" * 50)

    query = "Why is the system deadlocked?"

    print(
        f"\nQuery: {query}"
    )

    context = retrieve_graph_context(
        query,
        nodes,
        edges
    )

    print("\nRetrieved Context:")

    print(
        format_context(context)
    )