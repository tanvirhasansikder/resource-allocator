def calculate_need(maximum, allocation):
    """
    Calculate the Need matrix.

    Need = Maximum - Allocation
    """

    need = []

    for i in range(len(maximum)):
        row = []

        for j in range(len(maximum[i])):
            value = maximum[i][j] - allocation[i][j]
            row.append(value)

        need.append(row)

    return need


def is_safe(available, maximum, allocation):
    """
    Determine whether the current system is in a safe state.

    Returns:
        (True/False, safe_sequence)
    """

    number_of_processes = len(maximum)

    need = calculate_need(maximum, allocation)

    # Work represents resources currently available
    work = available.copy()

    # Tracks whether each process has finished
    finish = [False] * number_of_processes

    # Stores the safe sequence
    safe_sequence = []

    while len(safe_sequence) < number_of_processes:

        found_process = False

        for i in range(number_of_processes):

            if finish[i]:
                continue

            # Check:
            # Need[i] <= Work
            can_finish = True

            for j in range(len(work)):

                if need[i][j] > work[j]:
                    can_finish = False
                    break

            if can_finish:

                # Pretend that process i finishes
                for j in range(len(work)):
                    work[j] += allocation[i][j]

                finish[i] = True
                safe_sequence.append(i)

                found_process = True

        # No process could finish
        if not found_process:
            break

    # System is safe only if every process can finish
    is_system_safe = len(safe_sequence) == number_of_processes

    return is_system_safe, safe_sequence

def request_resources(process_id, request, available, maximum, allocation):
    """
    Attempt to grant a resource request using Banker's Algorithm.

    Returns:
        success: True/False
        message: Explanation
        safe_sequence: Safe sequence if available
        new_available: Updated available resources
        new_allocation: Updated allocation matrix
    """

    # Calculate current Need matrix
    need = calculate_need(maximum, allocation)

    # --------------------------------------------------
    # Step 1: Check Request <= Need
    # --------------------------------------------------

    for j in range(len(request)):

        if request[j] > need[process_id][j]:

            return (
                False,
                "Request exceeds the process's declared maximum need.",
                [],
                available,
                allocation
            )

    # --------------------------------------------------
    # Step 2: Check Request <= Available
    # --------------------------------------------------

    for j in range(len(request)):

        if request[j] > available[j]:

            return (
                False,
                "Resources are currently unavailable. Process must wait.",
                [],
                available,
                allocation
            )

    # --------------------------------------------------
    # Step 3: Pretend to allocate resources
    # --------------------------------------------------

    temporary_available = available.copy()

    temporary_allocation = [
        row.copy()
        for row in allocation
    ]

    for j in range(len(request)):

        temporary_available[j] -= request[j]

        temporary_allocation[process_id][j] += request[j]

    # --------------------------------------------------
    # Step 4: Check whether resulting state is safe
    # --------------------------------------------------

    safe, safe_sequence = is_safe(
        temporary_available,
        maximum,
        temporary_allocation
    )

    # --------------------------------------------------
    # Step 5: Grant or deny
    # --------------------------------------------------

    if safe:

        return (
            True,
            "Request granted. System remains in a safe state.",
            safe_sequence,
            temporary_available,
            temporary_allocation
        )

    else:

        return (
            False,
            "Request denied. Granting it would make the system unsafe.",
            [],
            available,
            allocation
        )
if __name__ == "__main__":

    available = [3, 3, 2]

    maximum = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
    ]

    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]

    # P1 requests [1, 0, 2]

    process_id = 1

    request = [1, 0, 2]

    success, message, sequence, new_available, new_allocation = request_resources(
        process_id,
        request,
        available,
        maximum,
        allocation
    )

    print("Request:", request)
    print("Process:", f"P{process_id}")
    print()
    print("Result:", success)
    print("Message:", message)
    print("Safe Sequence:", sequence)
    print("New Available:", new_available)