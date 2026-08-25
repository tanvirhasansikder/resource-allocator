from banker import request_resources


class ResourceAllocator:

    def __init__(self, resources, process_names, maximum, allocation):
        """
        Initialize the resource allocation system.
        """

        self.resources = resources
        self.process_names = process_names

        self.maximum = maximum
        self.allocation = allocation

        self.available = [0] * len(resources)

    # --------------------------------------------------
    # Set available resources
    # --------------------------------------------------

    def set_available(self, available):
        """Set currently available resources."""

        self.available = available.copy()

    # --------------------------------------------------
    # Request resources
    # --------------------------------------------------

    def request(self, process_id, request):

        success, message, safe_sequence, new_available, new_allocation = request_resources(
            process_id,
            request,
            self.available,
            self.maximum,
            self.allocation
        )

        if success:

            # Update the actual system state
            self.available = new_available
            self.allocation = new_allocation

        return {
            "success": success,
            "message": message,
            "safe_sequence": safe_sequence
        }

    # --------------------------------------------------
    # Release resources
    # --------------------------------------------------

    def release(self, process_id, release):

        # Make sure the process isn't releasing
        # more resources than it currently holds.

        for j in range(len(release)):

            if release[j] > self.allocation[process_id][j]:

                return {
                    "success": False,
                    "message": (
                        f"{self.process_names[process_id]} "
                        f"cannot release more resources than it holds."
                    )
                }

        # Release resources
        for j in range(len(release)):

            self.allocation[process_id][j] -= release[j]
            self.available[j] += release[j]

        return {
            "success": True,
            "message": "Resources released successfully."
        }

    # --------------------------------------------------
    # Get current system state
    # --------------------------------------------------

    def get_state(self):

        return {
            "available": self.available,
            "maximum": self.maximum,
            "allocation": self.allocation
        }


# ======================================================
# TESTING
# ======================================================

if __name__ == "__main__":

    resources = [
        "CPU",
        "Memory",
        "GPU"
    ]

    processes = [
        "P0",
        "P1",
        "P2",
        "P3",
        "P4"
    ]

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

    available = [3, 3, 2]

    # Create allocator
    allocator = ResourceAllocator(
        resources,
        processes,
        maximum,
        allocation
    )

    # Set available resources
    allocator.set_available(available)

    print("===================================")
    print("INITIAL SYSTEM STATE")
    print("===================================")

    print(allocator.get_state())

    # --------------------------------------------------
    # Test resource request
    # --------------------------------------------------

    print("\n===================================")
    print("RESOURCE REQUEST")
    print("===================================")

    result = allocator.request(
        1,
        [1, 0, 2]
    )

    print(result)

    print("\nState after request:")

    print(allocator.get_state())

    # --------------------------------------------------
    # Test resource release
    # --------------------------------------------------

    print("\n===================================")
    print("RESOURCE RELEASE")
    print("===================================")

    result = allocator.release(
        1,
        [1, 0, 1]
    )

    print(result)

    print("\nFinal state:")

    print(allocator.get_state())