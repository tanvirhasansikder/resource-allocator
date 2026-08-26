
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ============================================================
# RESOURCE ALLOCATION GRAPH
# ============================================================

def build_resource_allocation_graph(
    processes,
    resources,
    allocation,
    maximum
):
    nodes = []
    edges = []

    for process in processes:
        nodes.append({
            "id": process,
            "label": process,
            "type": "process"
        })

    for resource in resources:
        nodes.append({
            "id": resource,
            "label": resource,
            "type": "resource"
        })

    for i, process in enumerate(processes):

        for j, resource in enumerate(resources):

            allocated = allocation[i][j]
            maximum_required = maximum[i][j]

            if allocated > 0:

                edges.append({
                    "source": resource,
                    "target": process,
                    "type": "allocation",
                    "label": f"Allocated: {allocated}"
                })

            remaining_need = maximum_required - allocated

            if remaining_need > 0:

                edges.append({
                    "source": process,
                    "target": resource,
                    "type": "request",
                    "label": f"Need: {remaining_need}"
                })

    return nodes, edges


# ============================================================
# PROCESS INFORMATION
# ============================================================

def get_process_information(process_id, edges):

    information = {
        "process": process_id,
        "allocated_resources": [],
        "requested_resources": []
    }

    for edge in edges:

        if (
            edge["target"] == process_id
            and edge["type"] == "allocation"
        ):

            information["allocated_resources"].append({
                "resource": edge["source"],
                "amount": edge["label"]
            })

        elif (
            edge["source"] == process_id
            and edge["type"] == "request"
        ):

            information["requested_resources"].append({
                "resource": edge["target"],
                "amount": edge["label"]
            })

    return information


# ============================================================
# RESOURCE INFORMATION
# ============================================================

def get_resource_information(resource_id, edges):

    information = {
        "resource": resource_id,
        "allocated_to": [],
        "requested_by": []
    }

    for edge in edges:

        if (
            edge["source"] == resource_id
            and edge["type"] == "allocation"
        ):

            information["allocated_to"].append({
                "process": edge["target"],
                "amount": edge["label"]
            })

        elif (
            edge["target"] == resource_id
            and edge["type"] == "request"
        ):

            information["requested_by"].append({
                "process": edge["source"],
                "amount": edge["label"]
            })

    return information


# ============================================================
# CYCLE DETECTION
# ============================================================

def find_cycles(nodes, edges):

    graph = {}

    for node in nodes:
        graph[node["id"]] = []

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

                    if cycle not in cycles:
                        cycles.append(cycle)

                except ValueError:
                    pass

        path.pop()
        recursion_stack.remove(node)

    for node in graph:

        if node not in visited:

            dfs(
                node,
                []
            )

    return cycles


# ============================================================
# DEADLOCK INFORMATION
# ============================================================

def get_deadlock_information(nodes, edges):

    cycles = find_cycles(
        nodes,
        edges
    )

    allocations = []
    requests = []

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


# ============================================================
# RAG RETRIEVAL
# ============================================================

def retrieve_graph_context(
    query,
    nodes,
    edges
):

    query = query.lower()

    context = []

    # --------------------------------------------------------
    # PROCESS RETRIEVAL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # RESOURCE RETRIEVAL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # DEADLOCK RETRIEVAL
    # --------------------------------------------------------

    deadlock_keywords = [
        "deadlock",
        "deadlocked",
        "circular wait",
        "cycle",
        "waiting",
        "blocked",
        "cause",
        "causing"
    ]

    if any(
        keyword in query
        for keyword in deadlock_keywords
    ):

        context.append(
            get_deadlock_information(
                nodes,
                edges
            )
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not context:

        context.append({
            "type": "complete_graph",
            "nodes": nodes,
            "edges": edges
        })

    return context


# ============================================================
# FORMAT CONTEXT
# ============================================================

def format_context(context):

    output = []

    output.append(
        "RESOURCE ALLOCATION GRAPH CONTEXT"
    )

    output.append(
        "=" * 40
    )

    for item in context:

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

        elif item.get("type") == "deadlock_analysis":

            output.append(
                "\nDeadlock Analysis:"
            )

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

            output.append(
                "\nCurrent Resource Allocations:"
            )

            for allocation in item["allocations"]:

                output.append(
                    f"- {allocation['resource']} "
                    f"is allocated to "
                    f"{allocation['process']} "
                    f"({allocation['amount']})"
                )

            output.append(
                "\nCurrent Resource Requests:"
            )

            for request in item["requests"]:

                output.append(
                    f"- {request['process']} "
                    f"is requesting "
                    f"{request['resource']} "
                    f"({request['amount']})"
                )

        elif item.get("type") == "complete_graph":

            output.append(
                "\nComplete Graph:"
            )

            for node in item["nodes"]:

                output.append(
                    f"- {node['id']} "
                    f"({node['type']})"
                )

            for edge in item["edges"]:

                output.append(
                    f"- {edge['source']} -> "
                    f"{edge['target']} "
                    f"[{edge['type']}] "
                    f"{edge['label']}"
                )

    return "\n".join(output)


# ============================================================
# DETERMINISTIC GRAPH FACTS
# ============================================================

def get_graph_facts(nodes, edges):

    deadlock = get_deadlock_information(
        nodes,
        edges
    )

    allocation_map = {}

    for allocation in deadlock["allocations"]:

        allocation_map[
            allocation["resource"]
        ] = allocation["process"]

    process_holds = {}

    for allocation in deadlock["allocations"]:

        process = allocation["process"]
        resource = allocation["resource"]

        if process not in process_holds:
            process_holds[process] = []

        process_holds[process].append(
            resource
        )

    process_waits = {}

    for request in deadlock["requests"]:

        process = request["process"]
        resource = request["resource"]

        process_waits[process] = {
            "resource": resource,
            "holder": allocation_map.get(
                resource
            )
        }

    return (
        deadlock,
        allocation_map,
        process_holds,
        process_waits
    )


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(query):

    q = query.lower()

    if (
        "what is" in q
        and "waiting for" in q
    ):
        return "process_waiting"

    if (
        "what is" in q
        and "wait" in q
    ):
        return "process_waiting"

    if (
        "what resource" in q
        and (
            "hold" in q
            or "holds" in q
        )
    ):
        return "process_holds"

    if (
        "what does" in q
        and (
            "hold" in q
            or "holds" in q
        )
    ):
        return "process_holds"

    if (
        "why is" in q
        and (
            "waiting" in q
            or "wait" in q
        )
    ):
        return "process_waiting_explanation"

    if (
        "deadlock" in q
        or "circular wait" in q
        or "deadlocked" in q
    ):
        return "deadlock_explanation"

    if (
        "which process" in q
        and (
            "cause" in q
            or "causing" in q
            or "deadlock" in q
        )
    ):
        return "deadlock_processes"

    return "llm"


# ============================================================
# FIND PROCESS IN QUESTION
# ============================================================

def find_process_in_question(
    query,
    processes
):

    query_upper = query.upper()

    for process in processes:

        if process.upper() in query_upper:
            return process

    return None


# ============================================================
# DETERMINISTIC ANSWER
# ============================================================

def deterministic_answer(
    query,
    nodes,
    edges,
    processes
):

    intent = detect_intent(
        query
    )

    (
        deadlock,
        allocation_map,
        process_holds,
        process_waits
    ) = get_graph_facts(
        nodes,
        edges
    )

    process = find_process_in_question(
        query,
        processes
    )

    # --------------------------------------------------------
    # WHAT IS PROCESS WAITING FOR?
    # --------------------------------------------------------

    if intent == "process_waiting":

        if process is None:
            return None

        if process not in process_waits:
            return (
                f"{process} is not currently "
                "waiting for any resource."
            )

        resource = process_waits[
            process
        ]["resource"]

        holder = process_waits[
            process
        ]["holder"]

        if holder:

            return (
                f"{process} is waiting for {resource}. "
                f"{resource} is currently held by {holder}."
            )

        return (
            f"{process} is waiting for {resource}, "
            "which is currently available."
        )

    # --------------------------------------------------------
    # WHAT RESOURCE DOES PROCESS HOLD?
    # --------------------------------------------------------

    if intent == "process_holds":

        if process is None:
            return None

        resources_held = process_holds.get(
            process,
            []
        )

        if not resources_held:

            return (
                f"{process} currently holds no resources."
            )

        return (
            f"{process} currently holds: "
            + ", ".join(resources_held)
            + "."
        )

    # --------------------------------------------------------
    # WHY IS PROCESS WAITING?
    # --------------------------------------------------------

    if intent == "process_waiting_explanation":

        if process is None:
            return None

        if process not in process_waits:
            return (
                f"{process} is not currently "
                "waiting for a resource."
            )

        resources_held = process_holds.get(
            process,
            []
        )

        resource = process_waits[
            process
        ]["resource"]

        holder = process_waits[
            process
        ]["holder"]

        held_text = (
            ", ".join(resources_held)
            if resources_held
            else "no resources"
        )

        if holder:

            return (
                f"{process} holds {held_text} "
                f"and is waiting for {resource}. "
                f"However, {resource} is currently "
                f"held by {holder}, so {process} "
                "cannot obtain it until the resource "
                "is released."
            )

        return (
            f"{process} holds {held_text} "
            f"and is waiting for {resource}."
        )

    # --------------------------------------------------------
    # WHICH PROCESSES ARE INVOLVED?
    # --------------------------------------------------------

    if intent == "deadlock_processes":

        if not deadlock["has_cycle"]:

            return (
                "No deadlock was detected."
            )

        involved = []

        for cycle in deadlock["cycles"]:

            for node in cycle:

                if node in processes:
                    involved.append(node)

        involved = list(
            dict.fromkeys(involved)
        )

        return (
            "The processes involved in the deadlock "
            "are: "
            + ", ".join(involved)
            + "."
        )

    # --------------------------------------------------------
    # DEADLOCK EXPLANATION
    # --------------------------------------------------------

    if intent == "deadlock_explanation":

        if not deadlock["has_cycle"]:

            return (
                "The Resource Allocation Graph does "
                "not contain a cycle, so no deadlock "
                "was detected."
            )

        explanation = []

        explanation.append(
            "The system is deadlocked because the "
            "Resource Allocation Graph contains a "
            "circular wait."
        )

        for request in deadlock["requests"]:

            process_name = request[
                "process"
            ]

            resource_name = request[
                "resource"
            ]

            holder = allocation_map.get(
                resource_name
            )

            held = process_holds.get(
                process_name,
                []
            )

            held_text = (
                ", ".join(held)
                if held
                else "no resources"
            )

            if holder:

                explanation.append(
                    f"{process_name} holds "
                    f"{held_text} and waits for "
                    f"{resource_name}, which is "
                    f"held by {holder}."
                )

        explanation.append(
            "This creates the cycle: "
            + " -> ".join(
                deadlock["cycles"][0]
            )
        )

        explanation.append(
            "Because every process in the cycle is "
            "waiting for a resource held by another "
            "process in the same cycle, none of them "
            "can proceed."
        )

        return " ".join(
            explanation
        )

    return None


# ============================================================
# LOAD LOCAL LLM
# ============================================================

def load_llm():

    model_name = (
        "Qwen/Qwen2.5-0.5B-Instruct"
    )

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 60)
    print("LOADING LOCAL LLM")
    print("=" * 60)

    print(
        f"\nModel: {model_name}"
    )

    print(
        f"Device: {device}"
    )

    print(
        "\nLoading model..."
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_name
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name
    )

    model.to(device)
    model.eval()

    print(
        "\nModel loaded successfully!"
    )

    return (
        tokenizer,
        model,
        device
    )


# ============================================================
# LLM ANSWER
# ============================================================

def generate_llm_answer(
    question,
    context,
    tokenizer,
    model,
    device
):

    prompt = f"""
You are an Operating Systems assistant.

Answer the user's question using ONLY the supplied
Resource Allocation Graph information.

IMPORTANT:
- Do not invent resources.
- Do not change which process holds a resource.
- Do not change which process requests a resource.
- Do not invent dependencies.
- Be concise and factual.

User Question:
{question}

Resource Allocation Graph:
{context}

Answer:
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are a precise Operating Systems "
                "assistant. Use only the supplied graph "
                "evidence."
            )
        },
        {
            "role": "user",
            "content": prompt
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

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():

        output = model.generate(
            **inputs,
            max_new_tokens=160,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_tokens = output[
        0
    ][
        inputs["input_ids"].shape[1]:
    ]

    answer = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return answer.strip()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print(
        "RAG + LLM RESOURCE ALLOCATION SYSTEM"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # SYSTEM DATA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # BUILD GRAPH
    # --------------------------------------------------------

    nodes, edges = build_resource_allocation_graph(
        processes,
        resources,
        allocation,
        maximum
    )

    # --------------------------------------------------------
    # LOAD LLM ONCE
    # --------------------------------------------------------

    tokenizer, model, device = load_llm()

    # --------------------------------------------------------
    # INTERACTIVE MODE
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)

    print(
        "\nAsk questions about the resource allocation system."
    )

    print(
        "\nExamples:"
    )

    print(
        "- Why is the system deadlocked?"
    )

    print(
        "- Why is P0 waiting?"
    )

    print(
        "- What is P2 waiting for?"
    )

    print(
        "- What resource does P1 hold?"
    )

    print(
        "- Which processes are causing the deadlock?"
    )

    print(
        "- Explain the circular wait."
    )

    print(
        "\nType 'exit' or 'quit' to stop."
    )

    # --------------------------------------------------------
    # QUESTION LOOP
    # --------------------------------------------------------

    while True:

        print("\n" + "-" * 60)

        question = input(
            "\nEnter your question: "
        ).strip()

        if question.lower() in [
            "exit",
            "quit"
        ]:

            print(
                "\nExiting RAG + LLM system."
            )

            break

        if not question:

            print(
                "\nPlease enter a question."
            )

            continue

        # ----------------------------------------------------
        # RETRIEVE
        # ----------------------------------------------------

        print(
            "\nRetrieving relevant graph information..."
        )

        context_data = retrieve_graph_context(
            question,
            nodes,
            edges
        )

        context = format_context(
            context_data
        )

        print(
            "\nRetrieved Context:"
        )

        print(
            "-" * 60
        )

        print(context)

        # ----------------------------------------------------
        # DETERMINE WHETHER QUESTION IS FACTUAL
        # ----------------------------------------------------

        answer = deterministic_answer(
            question,
            nodes,
            edges,
            processes
        )

        # ----------------------------------------------------
        # DETERMINISTIC ANSWER
        # ----------------------------------------------------

        if answer is not None:

            print(
                "\n" + "=" * 60
            )

            print(
                "GRAPH-VERIFIED ANSWER"
            )

            print(
                "=" * 60
            )

            print(
                "\n" + answer
            )

            continue

        # ----------------------------------------------------
        # LLM ANSWER
        # ----------------------------------------------------

        print(
            "\n" + "=" * 60
        )

        print(
            "GENERATING LLM ANSWER..."
        )

        print(
            "=" * 60
        )

        answer = generate_llm_answer(
            question,
            context,
            tokenizer,
            model,
            device
        )

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

