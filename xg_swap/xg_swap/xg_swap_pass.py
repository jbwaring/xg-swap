import contextvars
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.layout import Layout
from quantxg.inference import QuantXGUnitaryPredictor
from qiskit.circuit.library.standard_gates import SwapGate
from qiskit.dagcircuit import DAGCircuit
import numpy as np
import networkx as nx
from loguru import logger
from tqdm import tqdm
# TODO: Replace NX with RustWorkx
"""A pass to dynamically swap qubits in a circuit.
"""

CUTOFF = 5


class XGSWAP(TransformationPass):

    def __init__(self, coupling_map, fake_run=False, config=None, **kwargs):
        super().__init__()
        self.coupling_map = coupling_map
        self.fake_run = fake_run
        self.config = config
        cx_equivalence_gate = 'ecr' if 'ecr' in config.basis_gates else 'cx'
        self.unitary_predictor = QuantXGUnitaryPredictor(cx_equivalence_gate)

    def run(self, dag):
        """Run the DynSWAP pass on `dag`.

        Args:
            dag (DAGCircuit): the directed acyclic graph to run on.

        Returns:
            DAGCircuit: Transformed DAG.
        """
        # logger.debug('-run')
        if self.fake_run:
            return self._fake_run(dag)
        canonical_register = dag.qregs['q']
        trivial_layout = Layout.generate_trivial_layout(canonical_register)
        current_layout = trivial_layout.copy()
        new_dag = dag.copy_empty_like()

        for layer in tqdm(dag.serial_layers(), desc="XGSWAP: DAG Serial Layers", total=len(list(dag.serial_layers())), disable=True):
            subdag = layer["graph"]

            for gate in subdag.two_qubit_ops():
                physical_q0 = current_layout[gate.qargs[0]]
                physical_q1 = current_layout[gate.qargs[1]]
                if self.coupling_map.distance(physical_q0, physical_q1) != 1:
                    # Insert a new layer with the SWAP(s).
                    swap_layer = DAGCircuit()
                    swap_layer.add_qreg(canonical_register)
                    path, _ = self.find_best_unitary_path(
                        physical_q0, physical_q1)
                    for swap in range(len(path) - 2):
                        connected_wire_1 = path[swap]
                        connected_wire_2 = path[swap + 1]

                        qubit_1 = current_layout[connected_wire_1]
                        qubit_2 = current_layout[connected_wire_2]

                        # create the swap operation
                        swap_layer.apply_operation_back(
                            SwapGate(), (qubit_1, qubit_2), cargs=(), check=False
                        )

                    # layer insertion
                    order = current_layout.reorder_bits(new_dag.qubits)
                    new_dag.compose(swap_layer, qubits=order)

                    # update current_layout
                    for swap in range(len(path) - 2):
                        current_layout.swap(path[swap], path[swap + 1])

            order = current_layout.reorder_bits(new_dag.qubits)
            new_dag.compose(subdag, qubits=order)

        self.property_set["final_layout"] = current_layout
        return new_dag

    def _fake_run(self, dag):
        """Do a fake run the BasicSwap pass on `dag`.

        Args:
            dag (DAGCircuit): DAG to improve initial layout.

        Returns:
            DAGCircuit: The same DAG.

        Raises:
            TranspilerError: if the coupling map or the layout are not
            compatible with the DAG.
        """
        logger.debug('Fake Run')
        canonical_register = dag.qregs["q"]
        trivial_layout = Layout.generate_trivial_layout(canonical_register)
        current_layout = trivial_layout.copy()

        for layer in tqdm(dag.serial_layers(), desc="XGSWAP: DAG Serial Layers (Layout Pass)", total=len(list(dag.serial_layers())), disable=True):
            subdag = layer["graph"]
            for gate in subdag.two_qubit_ops():
                physical_q0 = current_layout[gate.qargs[0]]
                physical_q1 = current_layout[gate.qargs[1]]
                if self.coupling_map.distance(physical_q0, physical_q1) != 1:
                    path, _ = self.find_best_unitary_path(
                        physical_q0, physical_q1)
                    # update current_layout
                    for swap in range(len(path) - 2):
                        current_layout.swap(path[swap], path[swap + 1])

        self.property_set["final_layout"] = current_layout
        return dag

    def unitary_routing_from_qubit_to_qubit(self, new_dag, canonical_register, current_layout, path):
        # UNITARY ROUTING
        logger.debug('Unitary Routing along path: {}'.format(path))

        # Insert a new layer with the SWAP(s).
        swap_layer = DAGCircuit()
        swap_layer.add_qreg(canonical_register)
        for swap in range(len(path) - 1):
            connected_wire_1 = path[swap]
            connected_wire_2 = path[swap + 1]

            qubit_1 = current_layout[connected_wire_1]
            qubit_2 = current_layout[connected_wire_2]

            logger.debug(
                'SWAP: {} <-> {} ({} <-> {})'.format(qubit_1._index, qubit_2._index, connected_wire_1, connected_wire_2))

            # create the swap operation
            swap_layer.apply_operation_back(
                SwapGate(), (qubit_1, qubit_2), cargs=(), check=False
            )

        # layer insertion
        order = current_layout.reorder_bits(new_dag.qubits)
        new_dag.compose(swap_layer, qubits=order)

        # update current_layout
        for swap in range(len(path) - 2):
            current_layout.swap(path[swap], path[swap + 1])

        return new_dag, current_layout

    def nx_graph_of_coupling_map(self, coupling_map):
        coupling_map_tuple = [tuple(i) for i in coupling_map]
        # build and empty graph
        G = nx.Graph()
        # build a graph with the coupling map from the chip
        G.add_edges_from(coupling_map_tuple)
        return G

    def unitary_fidelity_prediction_for_path(self, path):
        return self.unitary_predictor.predict_fidelity_for_path(
            path, self.coupling_map, self.config.backend_properties)[0]

    def find_best_unitary_path(self, q0, q1):
        graph = self.nx_graph_of_coupling_map(
            self.coupling_map)
        paths = []
        cutoff = CUTOFF
        while len(paths) < 10:
            paths = list(nx.all_simple_paths(
                graph, source=q0, target=q1, cutoff=cutoff))
            cutoff += 10
        paths = [
            path for path in paths if len(path) == len(set(path))]
        paths_fidelity = np.array([
            self.unitary_fidelity_prediction_for_path(p) for p in paths])
        best_path = paths[np.argmax(paths_fidelity)]
        best_fidelity = np.max(paths_fidelity)
        return best_path, best_fidelity
