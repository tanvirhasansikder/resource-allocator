import os
import subprocess
import time
import requests


# ============================================================
# CONFIGURATION
# ============================================================

LLAMA_PATH = (
    r"C:\Users\USER\AppData\Local\Microsoft\WinGet\Packages"
    r"\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\llama-server.exe"
)

MODEL = "bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M"

HOST = "127.0.0.1"
PORT = 8080

HEALTH_URL = f"http://{HOST}:{PORT}/health"


# Keep the process alive while the Python application is running.
_server_process = None


# ============================================================
# CHECK SERVER
# ============================================================

def is_server_running():
    """
    Check whether llama-server is currently running.
    """

    try:
        response = requests.get(
            HEALTH_URL,
            timeout=2
        )

        return response.status_code == 200

    except requests.RequestException:
        return False


# ============================================================
# START SERVER
# ============================================================

def start_server():
    """
    Start llama-server if it is not already running.
    """

    global _server_process

    # --------------------------------------------------------
    # Already running
    # --------------------------------------------------------

    if is_server_running():

        print("\n✓ llama-server is already running.")
        print(f"✓ Server: http://{HOST}:{PORT}")

        return True

    # --------------------------------------------------------
    # Check executable
    # --------------------------------------------------------

    if not os.path.exists(LLAMA_PATH):

        print("\nERROR: llama-server.exe was not found.")

        print("\nExpected location:")
        print(LLAMA_PATH)

        print(
            "\nIf llama.cpp was installed in a different "
            "location, update LLAMA_PATH in llama_server.py."
        )

        return False

    # --------------------------------------------------------
    # Start server
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("STARTING LOCAL LLM SERVER")
    print("=" * 60)

    print(f"\nModel: {MODEL}")
    print(f"Server: http://{HOST}:{PORT}")

    print("\nStarting llama-server...")

    try:

        _server_process = subprocess.Popen(
            [
                LLAMA_PATH,

                "-hf",
                MODEL,

                "--host",
                HOST,

                "--port",
                str(PORT),

                "--alias",
                "Llama-3.2-1B-Instruct"
            ],

            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,

            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:

        print("\nERROR: Failed to start llama-server.")
        print(f"Details: {e}")

        return False

    # --------------------------------------------------------
    # Wait for server
    # --------------------------------------------------------

    print("\nWaiting for Llama server to load...")

    for attempt in range(60):

        time.sleep(1)

        if is_server_running():

            print("\n✓ llama-server is running.")
            print("✓ Local LLM: Llama-3.2-1B-Instruct")
            print(f"✓ Server: http://{HOST}:{PORT}")

            return True

        print(
            f"Loading... {attempt + 1}/60",
            end="\r"
        )

    # --------------------------------------------------------
    # Failed
    # --------------------------------------------------------

    print("\n\nERROR: Llama server did not start.")

    if _server_process is not None:

        try:
            _server_process.terminate()
        except Exception:
            pass

    return False


# ============================================================
# STOP SERVER
# ============================================================

def stop_server():
    """
    Stop the llama-server started by this application.
    """

    global _server_process

    if _server_process is None:
        return

    if _server_process.poll() is None:

        print("\nStopping local Llama server...")

        try:
            _server_process.terminate()

            _server_process.wait(
                timeout=5
            )

        except Exception:

            try:
                _server_process.kill()
            except Exception:
                pass

    _server_process = None


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("\nTesting Llama server...")

    if start_server():

        print("\nLlama server is ready.")

        input(
            "\nPress ENTER to stop the server..."
        )

        stop_server()

    else:

        print(
            "\nCould not start the Llama server."
        )