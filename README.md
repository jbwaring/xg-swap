# XGSwap: eXtreme Gradient boosting Swap for Routing in NISQ Devices

Companion code for [https://arxiv.org/abs/2404.17982] submitted to QCE2024 [https://qce.quantum.ieee.org/2024/].

## Abstract

In the current landscape of noisy intermediate-scale quantum (NISQ) computing, the inherent noise presents significant challenges to achieving high-fidelity long-range entanglement. Furthermore, this challenge is amplified by the limited connectivity of current superconducting devices, necessitating state permutations to establish long-distance entanglement. Traditionally, graph methods are used to satisfy the coupling constraints of a given architecture by routing states along the shortest undirected path between qubits. In this work, we introduce a gradient-boosting machine learning model to predict the fidelity of alternative–potentially longer– routing paths to improve fidelity. This model was trained on 4050 random CNOT gates ranging in length from 2 to 100+ qubits. The experiments were all executed on ibm_quebec, a 127-qubit IBM Quantum System One. Through more than 200+ tests run on actual hardware, our model successfully identified higher fidelity paths in approximately 24% of cases.

## Repository Organization

This repository is composed of four distinct packages :

- `quantxg` holds the XGBoost model as well as weights to get you started with inference.
- `xg-swap` is a Qiskit transpiler plugin enabling the use of `quantxg` within the transpilation process of a `QuantumCircuit`.
- `demo` holds a preconfigured template you can use to get started easily
- `dataset` holds the training data exported from our database, which can be used to further optimize the model should you wish to do so.

## Quick Start

All our packages use `poetry` to manage python dependencies and create virtual environments. Install `poetry` using the guide at [https://python-poetry.org/docs/]. Once poetry is installed, navigate to `/demo` and run `poetry install`.
