# Operating System Resource Allocator

An interactive Operating System Resource Allocation and Deadlock Simulation system developed for CSE323.

## Features

- Banker's Algorithm
- Safe-state detection
- Resource request handling
- Resource release
- Deadlock detection
- Safe sequence generation
- Interactive Streamlit dashboard
- Process allocation visualization
- Remaining resource need calculation

## Technologies

- Python
- Streamlit
- NumPy
- Pandas

## Algorithms

### Banker's Algorithm

The system uses Banker's Algorithm to determine whether a resource request can be safely granted without causing the system to enter an unsafe state.

### Deadlock Detection

The project implements a deadlock detection algorithm to identify processes that cannot complete because their outstanding resource requests cannot be satisfied.

## Project Structure

```text
resource-allocator/
│
├── app.py
├── banker.py
├── allocator.py
├── deadlock.py
├── requirements.txt
├── README.md
└── .gitignore