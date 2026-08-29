# 🖥️ Operating System Resource Allocator

An interactive **Operating System Resource Allocation, Safety Analysis, and Deadlock Simulation System** developed for **CSE323 — Operating Systems**.

The project simulates how an operating system manages limited resources among multiple processes using **Banker's Algorithm**, **Deadlock Detection**, resource allocation and resource release mechanisms.

It also integrates a **Retrieval-Augmented Generation (RAG) pipeline with a locally hosted LLaMA-based Large Language Model (LLM)**, allowing users to ask natural-language questions about the current resource-allocation state and receive factual or AI-generated explanations.

---

## 📌 Project Overview

Resource allocation is a fundamental responsibility of an operating system. When multiple processes compete for limited resources, the operating system must determine whether resources can be safely allocated while avoiding or detecting deadlocks.

This project provides an interactive simulation environment containing **five processes (P0–P4)** and three resource types:

* CPU
* Memory
* GPU

Users can interact with the system to request and release resources, inspect allocation matrices, analyze system safety, detect deadlocks, and ask questions about the current state.

The project combines **classical Operating Systems algorithms with an interactive Streamlit interface and a local LLaMA-based explanation system**.

---

# ✨ Features

## ⚙️ Resource Management

* CPU, Memory, and GPU resource simulation
* Five simulated processes: P0–P4
* Resource request handling
* Resource release
* Available resource tracking
* Process allocation tracking
* Maximum resource requirement tracking
* Remaining Need calculation
* Resource ownership visualization
* System reset functionality

## 🏦 Banker's Algorithm

* Safe-state detection
* Unsafe-state detection
* Resource-request safety checking
* Safe sequence generation
* Temporary allocation during safety analysis
* Prevention of unsafe resource allocation

## 🔒 Deadlock Detection

* Deadlock detection
* Identification of deadlocked processes
* Analysis of remaining resource requirements
* Detection of processes that cannot complete

## 📊 Interactive Streamlit Dashboard

* Wide-layout interactive dashboard
* System status indicators
* Available resource metrics
* Allocation Matrix
* Maximum Matrix
* Need Matrix
* Resource ownership table
* Resource request interface
* Resource release interface
* Banker's Algorithm results
* Deadlock detection results
* RAG + LLM assistant

---

# 🤖 RAG + LLaMA Assistant

A major component of the project is an AI-assisted question-answering system for resource-management analysis.

The assistant allows users to ask questions such as:

```text
What resources does P3 hold?

What is P1's remaining need?

How many CPU resources are available?

Is the system safe?

Why is the system safe?

Is there a deadlock?

Why is the system deadlocked?

Explain Banker's Algorithm simply.

Explain the current resource allocation situation.

What would happen if P0 needed all of its remaining resources?
```

The assistant follows a **hybrid architecture** where deterministic system information is generated first, and the LLM is used primarily for explanation.

---

## 🧠 RAG Architecture

The Resource Allocator is the **source of truth** for the current system state.

When a user asks a question, the system retrieves relevant information directly from the current allocator state.

The RAG context can contain:

* Available resources
* Allocation matrix
* Maximum matrix
* Need matrix
* Process resource ownership
* Banker's Algorithm result
* Safe sequence
* Deadlock status
* Deadlocked processes
* Hypothetical resource analysis

The retrieved information is then provided to the local LLaMA model when an LLM explanation is required.

### Architecture

```text
                         ┌─────────────────────────┐
                         │     Streamlit UI        │
                         │  streamlit_app.py       │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │   ResourceAllocator    │
                         │     allocator.py       │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼──────────────────────┐
              │                       │                      │
              ▼                       ▼                      ▼
      ┌───────────────┐       ┌───────────────┐      ┌───────────────┐
      │    Banker's   │       │   Deadlock    │      │ Current State │
      │   Algorithm   │       │   Detection   │      │   Retrieval   │
      │   banker.py   │       │ deadlock.py   │      │  generate_    │
      └───────────────┘       └───────────────┘      │   context()    │
                                                      └───────┬───────┘
                                                              │
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Deterministic      │
                                                   │ Factual Answer     │
                                                   └─────────┬──────────┘
                                                             │
                                                     If explanation
                                                       is needed
                                                             │
                                                             ▼
                                                   ┌────────────────────┐
                                                   │  Local llama-      │
                                                   │      server        │
                                                   │                    │
                                                   │ Llama-3.2-1B-      │
                                                   │     Instruct       │
                                                   └─────────┬──────────┘
                                                             │
                                                             ▼
                                                   ┌────────────────────┐
                                                   │ Natural-language   │
                                                   │ Explanation        │
                                                   └────────────────────┘
```

---

# 🛡️ LLM Safety Design

The LLM is **not responsible for making resource-management decisions**.

The deterministic components of the application remain responsible for calculating:

* Resource quantities
* Current allocation
* Maximum requirements
* Remaining Need
* Available resources
* Safe/unsafe state
* Safe sequence
* Deadlock status
* Deadlocked processes

The LLM receives the retrieved system information and explains it in natural language.

This separation prevents the LLM from becoming the authority for numerical or system-state decisions.

---

## 🔢 LLM Output Validation

The project also includes an output-validation layer.

Before displaying an LLM-generated response, the system checks for common unsupported claims and validates numerical information against the retrieved context.

The validation process helps prevent the LLM from:

* Inventing resource quantities
* Introducing unsupported numbers
* Contradicting the system's safe/unsafe status
* Contradicting deadlock detection results
* Claiming unsupported allocation information
* Providing unsupported statements such as "optimal allocation"

If an LLM response cannot be safely validated, the system displays a safer fallback message instead.

---

# 🦙 Local LLaMA Server

The project uses a locally hosted **LLaMA-based model** through `llama-server`.

The application communicates with the local server at:

```text
http://127.0.0.1:8080
```

The LLM request uses the OpenAI-compatible endpoint:

```text
http://127.0.0.1:8080/v1/chat/completions
```

The application also checks the server health using:

```text
http://127.0.0.1:8080/health
```

### Active Model

```text
Llama-3.2-1B-Instruct
```

The project also contains a Transformers-based model-loading implementation for compatibility. The normal LLM workflow, however, uses the local `llama-server`.

---

# 🏦 Banker's Algorithm

Banker's Algorithm is used for **deadlock avoidance**.

The system maintains:

* **Available**
* **Allocation**
* **Maximum**
* **Need**

The Need matrix is calculated using:

```text
Need = Maximum - Allocation
```

Before granting a resource request, the allocator evaluates whether the resulting state remains safe.

A request is accepted only when the resulting state can maintain a valid safe sequence.

### Example

```text
Request: [1, 0, 2]
Process: P1

Result: Safe

Safe Sequence:
P1 → P3 → P4 → P0 → P2
```

A safe sequence represents a possible order in which processes can finish while maintaining a safe state.

---

# 🔒 Deadlock Detection

The project implements deadlock detection using the current:

* Available resources
* Allocation matrix
* Remaining Need matrix

The detector identifies processes that cannot obtain their outstanding resource requirements and therefore cannot complete.

Example:

```text
Deadlock detected: True

Deadlocked processes:
P0
P1
P2
```

---

# 📊 Dashboard

The Streamlit dashboard displays the current state of the simulated operating system.

### System Status

The dashboard shows:

* SAFE / UNSAFE state
* DEADLOCK / NO DEADLOCK status
* Available CPU
* Available Memory
* Available GPU

### Resource Matrices

The interface provides three tables:

1. Allocation Matrix
2. Maximum Matrix
3. Need Matrix

### Resource Ownership

The ownership table shows how many units of each resource are currently allocated to each process.

---

# 📥 Resource Requests

Users can select a process and specify:

* CPU request
* Memory request
* GPU request

The allocator evaluates the request and returns the result.

If the request is safe, the resources are allocated and a safe sequence may be displayed.

If the request cannot be safely granted, the system rejects it and provides the corresponding reason.

---

# 📤 Resource Release

Users can also release resources previously allocated to a process.

The system validates the release and updates the current resource state.

The available-resource values and allocation matrices are subsequently updated.

---

# 💬 Question Answering System

The assistant uses a combination of deterministic handlers and LLM generation.

### Deterministic Questions

Questions requiring exact system values are answered directly from the current allocator state.

Examples:

```text
What resources does P3 hold?

What is P1's remaining need?

How many CPU resources are available?

Show the allocation matrix.

Is the system safe?

Is there a deadlock?
```

### LLM Questions

Conceptual or explanatory questions can be processed through the RAG + LLaMA pipeline.

Examples:

```text
Explain Banker's Algorithm simply.

Explain the current resource allocation situation.

Explain resource allocation in simple terms.
```

### Hypothetical Questions

The system also supports hypothetical questions such as:

```text
What would happen if P0 needed all of its remaining resources?
```

Hypothetical analysis does **not modify the actual allocator state**.

---

# 🛠️ Technologies

## Core

* Python
* Streamlit
* NumPy
* Pandas

## Operating Systems

* Banker's Algorithm
* Deadlock Detection
* Resource Allocation
* Resource Release
* Safe-State Analysis

## Artificial Intelligence

* Retrieval-Augmented Generation (RAG)
* LLaMA-based LLM
* llama.cpp / llama-server
* Hugging Face Transformers
* PyTorch

## Development

* Git
* GitHub
* Python Virtual Environment

---

# 📁 Project Structure

```text
resource-allocator/
│
├── streamlit_app.py       # Main Streamlit application
├── banker.py              # Banker's Algorithm
├── allocator.py           # Resource allocation and release
├── deadlock.py            # Deadlock detection
├── rag_llm.py             # RAG + LLM assistant
├── requirements.txt       # Python dependencies
├── README.md              # Project documentation
└── .gitignore             # Git configuration
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/tanvirhasansikder/resource-allocator.git
cd resource-allocator
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

## 3. Activate the virtual environment

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Running the Application

Start the Streamlit application:

```powershell
streamlit run streamlit_app.py
```

Streamlit will provide a local URL where the application can be opened in a browser.

---

# 🦙 Running the LLaMA Server

The LLM assistant requires the local `llama-server` to be running.

The application expects:

```text
http://127.0.0.1:8080
```

Start the LLaMA server before using LLM-based explanations.

The application automatically checks the server's `/health` endpoint to determine whether the local LLM is available.

---

# 🧪 Testing

The project was tested using different resource-management scenarios.

### Safe Request

A request that can be safely granted is accepted after safety analysis.

### Unsafe Request

A request that would result in an unsafe state is rejected.

### Resource Release

Allocated resources can be released and returned to the available-resource pool.

### Deadlock Scenario

The deadlock detector can identify processes involved in a deadlocked state.

Example:

```text
Deadlock detected: True

Deadlocked processes:
P0
P1
P2
```

### RAG + LLaMA Testing

The assistant was tested with:

* Process-specific questions
* Resource availability questions
* Allocation questions
* Maximum requirement questions
* Need questions
* Matrix questions
* Safe-state questions
* Deadlock questions
* Conceptual OS questions
* Hypothetical resource requests

---

# 🎯 Learning Objectives

This project demonstrates practical understanding of:

* Operating system resource management
* Process-resource relationships
* Banker's Algorithm
* Deadlock detection
* Safe and unsafe states
* Resource allocation and release
* Matrix-based algorithm implementation
* Python modular programming
* Streamlit application development
* RAG-based context generation
* Local LLM integration
* Prompt engineering
* LLM output validation
* Debugging
* Testing
* Git and GitHub workflow

---

# 🧩 Development Challenges

Several challenges were encountered during development, including:

* Maintaining consistent resource-allocation states
* Correctly implementing Banker's safety checking
* Handling invalid and excessive resource requests
* Detecting deadlocked processes
* Synchronizing backend state with the Streamlit interface
* Debugging repeated resource-request interactions
* Integrating a locally hosted LLaMA server
* Preventing hallucinated resource values
* Validating LLM-generated answers
* Handling hypothetical questions without modifying the actual system state

These challenges were addressed through iterative implementation, testing, debugging, and refinement.

---

# 🔮 Future Improvements

Potential future improvements include:

* Additional resource types such as Disk and Network
* Graphical Resource Allocation Graph visualization
* Dynamic process creation and termination
* Resource-allocation history
* Expanded automated testing
* Improved deadlock visualization
* More advanced natural-language query understanding
* Enhanced RAG retrieval
* Larger local language models
* Streaming LLM responses

---

# 👨‍💻 Author

**Tanvir Sikder**

CSE323 — Operating Systems Project

---

# 🔗 GitHub Repository

https://github.com/tanvirhasansikder/resource-allocator

---

# 🎥 Project Demonstration

A **2–5 minute video demonstration** is included as part of the course submission.

The demonstration covers:

1. Project overview
2. Interactive dashboard
3. Resource allocation
4. Banker's Algorithm
5. Safe and unsafe resource requests
6. Resource release
7. Deadlock detection
8. Resource ownership
9. RAG context generation
10. LLaMA-based explanation
11. Hypothetical resource analysis

---

## ⭐ Project Highlights

> **Operating Systems + Resource Allocation + Deadlock Detection + RAG + Local LLaMA**

This project combines classical Operating Systems algorithms with modern AI techniques to create an **interactive and explainable resource-management system**.
