"""
@author: Vincent Bonnet
@description : Symplectic Euler time integrator
"""

import core
from lib.system.time_integrators import TimeIntegrator
import lib.system.jit.integrator_lib as integrator_lib

class SymplecticEulerIntegrator(TimeIntegrator):
    def __init__(self):
        TimeIntegrator.__init__(self)

    @core.timeit
    def prepare_system(self, scene, details, dt):
        # Reset forces
        integrator_lib.reset_forces(details.dynamics)

        # Compute constraint forces and jacobians
        for condition in scene.conditions:
            condition.pre_compute(details.bundle)
            condition.compute_forces(details.bundle)

        # Add forces to dynamics
        integrator_lib.apply_external_forces_to_nodes(details.dynamics, scene.forces)
        integrator_lib.apply_constraint_forces_to_nodes(details.constraints, details.node)

    @core.timeit
    def assemble_system(self, details, dt):
        # no system to assemble
        pass

    @core.timeit
    def solve_system(self, details, dt):
        integrator_lib.euler_integration(details.dynamics, dt)
