def detect_deadlock(available, allocation, request):
    """
    Detect deadlocked processes.

    Parameters:
        available  -> Available resource vector
        allocation -> Current allocation matrix
        request    -> Outstanding request matrix

    Returns:
        deadlock_exists -> True/False
        deadlocked_processes -> List of process IDs
    """

    number_of_processes = len(allocation)

    # Work represents resources currently available
    work = available.copy()

    # Initially, assume every process may be unfinished
    finish = [False] * number_of_processes

    while True:

        found_process = False

        for i in range(number_of_processes):

            if finish[i]:
                continue

            # Check whether this process's outstanding
            # request can currently be satisfied.

            can_finish = True

            for j in range(len(work)):

                if request[i][j] > work[j]:
                    can_finish = False
                    break

            if can_finish:

                # Pretend that the process completes
                # and releases its allocated resources.

                for j in range(len(work)):
                    work[j] += allocation[i][j]

                finish[i] = True

                found_process = True

        # If no process can finish, stop.
        if not found_process:
            break

    # Processes that could not finish are deadlocked.
    deadlocked_processes = []

    for i in range(number_of_processes):

        if not finish[i]:
            deadlocked_processes.append(i)

    deadlock_exists = len(deadlocked_processes) > 0

    return deadlock_exists, deadlocked_processes


# ======================================================
# TESTING
# ======================================================

if __name__ == "__main__":

    available = [0, 0, 0]

    allocation = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ]

    request = [
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0]
    ]

    deadlock, processes = detect_deadlock(
        available,
        allocation,
        request
    )

    print("Deadlock detected:", deadlock)

    if deadlock:

        print("Deadlocked processes:")

        for process_id in processes:
            print(f"P{process_id}")