from qiskit.transpiler.preset_passmanagers.plugin import PassManagerStagePlugin
from .xg_swap_pass import XGSWAP
from qiskit.transpiler import PassManager
from loguru import logger
from qiskit.transpiler.passes import (
    SabreLayout,
)
from qiskit.transpiler.passmanager import PassManager
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.passes import SetLayout
from qiskit.transpiler.passes import SabreLayout
from qiskit.transpiler.passes import BarrierBeforeFinalMeasurements
from qiskit.transpiler.preset_passmanagers import common
from qiskit.transpiler.preset_passmanagers.plugin import (
    PassManagerStagePlugin,
)
from qiskit.passmanager.flow_controllers import ConditionalController


class XGSwapPlugin(PassManagerStagePlugin):
    def pass_manager(self, pass_manager_config, optimization_level):
        if optimization_level == 0:
            return None
        return PassManager(
            [
                XGSWAP(
                    coupling_map=pass_manager_config.coupling_map,
                    fake_run=False,
                    config=pass_manager_config
                )
            ]
        )


class XGSwapLayoutPlugin(PassManagerStagePlugin):

    def pass_manager(self, pass_manager_config, optimization_level=None) -> PassManager:
        _given_layout = SetLayout(pass_manager_config.initial_layout)

        def _choose_layout_condition(property_set):
            return not property_set["layout"]

        def _swap_mapped(property_set):
            return property_set["final_layout"] is None

        if pass_manager_config.target is None:
            coupling_map = pass_manager_config.coupling_map
        else:
            coupling_map = pass_manager_config.target

        layout = PassManager()
        layout.append(_given_layout)

        layout_pass = SabreLayout(
            coupling_map,
            max_iterations=4,
            seed=pass_manager_config.seed_transpiler,
            routing_pass=XGSWAP(
                coupling_map=pass_manager_config.coupling_map,
                fake_run=True,
                config=pass_manager_config
            ),
            skip_routing=False,
        )
        layout.append(
            ConditionalController(
                [
                    BarrierBeforeFinalMeasurements(
                        "qiskit.transpiler.internal.routing.protection.barrier"
                    ),
                    layout_pass,
                ],
                condition=_choose_layout_condition,
            )
        )
        embed = common.generate_embed_passmanager(coupling_map)
        layout.append(ConditionalController(
            embed.to_flow_controller(), condition=_swap_mapped))
        return layout


logger.debug("xg_swap loaded (layout + routing)")
