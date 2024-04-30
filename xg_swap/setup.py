import setuptools
print('setup.py: Plugin Loaded!')

setuptools.setup(
    name="xg_swap",
    version='0.1.0',
    description="XGBoost CNOT PassManager Routing Stage Plugin",
    packages=setuptools.find_packages(exclude=["test*"]),
    entry_points={
        'qiskit.transpiler.routing': [
            'xg_swap = xg_swap.plugin:XGSwapPlugin',
        ],
        'qiskit.transpiler.layout': [
            'xg_swap_layout = xg_swap.plugin:DynSwapLayoutPlugin',
        ],
    }
)
