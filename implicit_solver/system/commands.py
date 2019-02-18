"""
@author: Vincent Bonnet
@description : commands to setup and run simulation
"""

import objects
import numpy as np

def set_render_prefs(obj, prefs):
    # Render preferences used by render.py
    # See : https://matplotlib.org/api/_as_gen/matplotlib.axes.Axes.plot.html for more details
    # fmt = '[color][marker][line]'
    # format of the display State ['fmt', size]
    obj.meta_data['render_prefs'] = prefs

def add_kinematic(scene, shape, position = (0., 0.), rotation = 0., animator = None):
    kinematic = objects.Kinematic(shape, position, rotation)
    scene.add_kinematic(kinematic, animator)
    return kinematic

def add_dynamic(scene, shape, particle_mass):
    dynamic = objects.Dynamic(shape, particle_mass)
    scene.add_dynamic(dynamic)
    return dynamic

def add_wire_bending_constraint(scene, dynamic, stiffness, damping):
    condition = objects.WireBendingCondition([dynamic], stiffness, damping)
    scene.add_condition(condition)
    return condition

def add_edge_constraint(scene, dynamic, stiffness, damping):
    condition = objects.SpringCondition([dynamic], stiffness, damping)
    scene.add_condition(condition)
    return condition

def add_face_constraint(scene, dynamic, stiffness, damping):
    condition = objects.AreaCondition([dynamic], stiffness, damping)
    scene.add_condition(condition)
    return condition

def add_kinematic_attachment(scene, dynamic, kinematic, stiffness, damping, distance):
    condition = objects.KinematicAttachmentCondition(dynamic, kinematic, stiffness, damping, distance)
    scene.add_condition(condition)
    return condition

def add_dynamic_attachment(scene, dynamic0, dynamic1, stiffness, damping, distance):
    condition = objects.DynamicAttachmentCondition(dynamic0, dynamic1, stiffness, damping, distance)
    scene.add_condition(condition)
    return condition

def add_kinematic_collision(scene, dynamic, kinematic, stiffness, damping):
    condition = objects.KinematicCollisionCondition(dynamic, kinematic, stiffness, damping)
    scene.add_condition(condition)
    return condition

def add_gravity(scene, gravity):
    force = objects.Gravity(gravity)
    scene.add_force(force)
    return force

def solve_to_next_frame(scene, solver, context):
    '''
    Solve the scene and move to the next frame
    '''
    for _ in range(context.num_substep):
        context.time += context.dt
        solver.solveStep(scene, context)

def initialize(scene, solver, context):
    '''
    Initialize the solver
    '''
    solver.initialize(scene, context)