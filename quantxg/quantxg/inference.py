from xgboost import XGBRegressor
import os
from loguru import logger

MODEL_NAME = 'xgboost_ident_v2'


class QuantXGUnitaryPredictor():

    def __init__(self, cx_gate_name='cx'):

        self.model = XGBRegressor()
        file_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(file_path, MODEL_NAME + '.json')
        logger.debug(
            "QuantXGUnitaryPredictor -model_name: {}".format(MODEL_NAME))
        self.model.load_model(file_path)
        self.cx = cx_gate_name

    def predict_fidelity_for_path(self, path, coupling_map, properties):
        max_path_length = 100
        padding_value = -1
        cal = {
            'cnot': {},
            'readout': {}
        }
        for edge in coupling_map:
            cal['cnot'][edge] = properties.gate_error(
                qubits=[edge[0], edge[1]], gate=self.cx)
        for i in range(127):
            cal['readout'][i] = properties.readout_error(i)
        cnot_values = list(cal['cnot'].values())
        readout_values = list(cal['readout'].values())

        # Handle the path array
        path_array = path
        fixed_length_path = path_array[:max_path_length] + \
            [padding_value] * (max_path_length - len(path_array))

        # Combine into a feature vector
        feature_vector = cnot_values + readout_values + fixed_length_path

        # Append the feature vector to the feature matrix X
        return self.model.predict([feature_vector])


class QuantXGDynamicPredictor():

    def __init__(self, cx_gate_name='cx'):

        self.model = XGBRegressor()
        # Get current file folder
        file_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(file_path, 'xgboost_dyn.json')
        self.model.load_model(file_path)
        self.cx = cx_gate_name

    def predict_fidelity_for_path(self, path, coupling_map, properties):
        max_path_length = 100
        padding_value = -1
        cal = {
            'cnot': {},
            'readout': {}
        }
        for edge in coupling_map:
            cal['cnot'][edge] = properties.gate_error(
                qubits=[edge[0], edge[1]], gate=self.cx)
        for i in range(127):
            cal['readout'][i] = properties.readout_error(i)
        cnot_values = list(cal['cnot'].values())
        readout_values = list(cal['readout'].values())

        # Handle the path array
        path_array = path
        fixed_length_path = path_array[:max_path_length] + \
            [padding_value] * (max_path_length - len(path_array))

        # Combine into a feature vector
        feature_vector = cnot_values + readout_values + fixed_length_path

        # Append the feature vector to the feature matrix X
        return self.model.predict([feature_vector])
