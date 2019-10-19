"""
@author: Vincent Bonnet
@description : example scenes for Unit Testing
"""
import os
import math

import lib.objects as objects
import logic
import host_app.rpc.shape_io as io_utils

'''
 Global Constants
'''
WIRE_ROOT_POS = [0.0, 2.0] # in meters
WIRE_END_POS = [0.0, -2.0] # in meters
WIRE_NUM_SEGMENTS = 30

BEAM_POS = [-4.0, 0.0] # in meters
BEAM_WIDTH = 8.0 # in meters
BEAM_HEIGHT = 1.0 # in meters
BEAM_CELL_X = 6 # number of cells along x
BEAM_CELL_Y = 4 # number of cells along y

NODE_MASS = 0.001 # in Kg

GRAVITY = (0.0, -9.81) # in meters per second^2

def get_resources_folder():
    return os.path.dirname(__file__) + "/resources/"

def meta_data_render(width=1.0, color='grey', style='solid', alpha = 1.0):
    return {'width':width, 'color':color, 'style':style, 'alpha' : alpha}

def init_cat_scene(dispatcher, render):
    init_file_scene(dispatcher, render, 'cat.npz')

def init_rabbit_scene(dispatcher, render):
    init_file_scene(dispatcher, render, 'rabbit.npz')

def init_file_scene(dispatcher, render, file_path):
    '''
    Initalizes a scene including a cat shape created by the Maya/mesh_converter.py
    Latest Maya/Houdini doesn't support Python 3.x hence cannot use client.py to send data
    '''
    dispatcher.run('reset_scene')

    # Load Data from file
    filename = get_resources_folder() + file_path
    shape = io_utils.create_shape_from_npz_file(filename)

    # Create collider 0
    anchor0_shape = logic.RectangleShape(min_x=-5.0, min_y=4.0, max_x=4.5, max_y=5.0)
    anchor0_position, anchor_rotation = anchor0_shape.extract_transform_from_shape()
    anchor0_position[0] = -7
    anchor0_position[1] = -13
    anchor0_rotation = 30

    # Create collider 1
    anchor1_shape = logic.RectangleShape(min_x=-5.0, min_y=4.0, max_x=5.0, max_y=5.0)
    anchor1_position, anchor_rotation = anchor1_shape.extract_transform_from_shape()
    anchor1_position[0] = 13
    anchor1_position[1] = -20
    anchor1_rotation = -45

    # Create collider 2
    anchor2_shape = logic.RectangleShape(min_x=-5.0, min_y=4.0, max_x=5.0, max_y=5.0)
    anchor2_position, anchor_rotation = anchor2_shape.extract_transform_from_shape()
    anchor2_position[0] = 0
    anchor2_position[1] = -30
    anchor2_rotation = 45

    # Add objects to the solver
    collider0_handle = dispatcher.run('add_kinematic', shape = anchor0_shape,
                                                         position = anchor0_position,
                                                         rotation = anchor0_rotation)

    collider1_handle = dispatcher.run('add_kinematic', shape = anchor1_shape,
                                                         position = anchor1_position,
                                                         rotation = anchor1_rotation)

    collider2_handle = dispatcher.run('add_kinematic', shape = anchor2_shape,
                                                         position = anchor2_position,
                                                         rotation = anchor2_rotation)

    mesh_handle = dispatcher.run('add_dynamic', shape = shape, node_mass = NODE_MASS)

    edge_condition_handle = dispatcher.run('add_edge_constraint', dynamic = mesh_handle,
                                                           stiffness = 100.0, damping = 0.0)

    dispatcher.run('add_kinematic_collision', dynamic = mesh_handle, kinematic = collider0_handle,
                                               stiffness = 10000.0, damping = 0.0)

    dispatcher.run('add_kinematic_collision', dynamic = mesh_handle, kinematic = collider1_handle,
                                               stiffness = 10000.0, damping = 0.0)

    dispatcher.run('add_kinematic_collision', dynamic = mesh_handle, kinematic = collider2_handle,
                                               stiffness = 10000.0, damping = 0.0)

    dispatcher.run('add_gravity', gravity = GRAVITY)

    # Set render preferences
    dispatcher.run('set_render_prefs', obj = mesh_handle,
                                       prefs = meta_data_render(1.0, 'grey', 'solid'))
    dispatcher.run('set_render_prefs', obj = edge_condition_handle,
                                       prefs = meta_data_render(1.0, 'blue', 'solid'))
    dispatcher.run('set_render_prefs', obj = collider0_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))
    dispatcher.run('set_render_prefs', obj = collider1_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))
    dispatcher.run('set_render_prefs', obj = collider2_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))


    render.set_viewport_limit(-20.0, -40.0, 20.0, 0.0)


def init_multi_wire_example(dispatcher, render):
    '''
    Initalizes a scene with multiple wire attached to a kinematic object
    '''
    dispatcher.run('reset_scene')
    context = dispatcher.run('get_context')
    # wire shape
    wire_shapes = []
    for i in range(6):
        x = -2.0 + (i * 0.25)
        wire_shape = logic.WireShape([x, 1.5], [x, -1.5] , WIRE_NUM_SEGMENTS)
        wire_shapes.append(wire_shape)

    # anchor shape and animation
    moving_anchor_shape = logic.RectangleShape(min_x = -2.0, min_y = 1.5,
                                              max_x = 0.0, max_y =2.0)
    moving_anchor_position, moving_anchor_rotation = moving_anchor_shape.extract_transform_from_shape()
    func = lambda time: [[moving_anchor_position[0] + time,
                          moving_anchor_position[1]], 0.0]

    moving_anchor_animator = objects.Animator(func, context)

    # collider shape
    collider_shape = logic.RectangleShape(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1] - 3,
                                       WIRE_ROOT_POS[0] + 0.5, WIRE_ROOT_POS[1] - 2)
    collider_position, collider_rotation = moving_anchor_shape.extract_transform_from_shape()
    collider_rotation = 45.0

    # Populate Scene with data and conditions
    moving_anchor_handle = dispatcher.run('add_kinematic', shape = moving_anchor_shape,
                                                          position = moving_anchor_position,
                                                          rotation = moving_anchor_rotation,
                                                          animator =moving_anchor_animator)

    collider_handle = dispatcher.run('add_kinematic', shape = collider_shape,
                                                        position = collider_position,
                                                        rotation = collider_rotation)

    for wire_shape in wire_shapes:
        wire_handle = dispatcher.run('add_dynamic', shape = wire_shape, node_mass = NODE_MASS)

        edge_condition_handle = dispatcher.run('add_edge_constraint', dynamic = wire_handle,
                                                               stiffness = 100.0, damping = 0.0)

        dispatcher.run('add_wire_bending_constraint', dynamic= wire_handle,
                                                       stiffness = 0.15, damping = 0.0)

        dispatcher.run('add_kinematic_attachment', dynamic = wire_handle, kinematic = moving_anchor_handle,
                                                   stiffness = 100.0, damping = 0.0, distance = 0.1)

        dispatcher.run('add_kinematic_collision', dynamic = wire_handle, kinematic = collider_handle,
                                                   stiffness = 1000.0, damping = 0.0)

        dispatcher.run('set_render_prefs', obj = wire_handle,
                                           prefs = meta_data_render(1.0, 'blue', 'solid'))
        dispatcher.run('set_render_prefs', obj = edge_condition_handle,
                                           prefs = meta_data_render(1.0, 'green', 'solid'))

    dispatcher.run('add_gravity', gravity = GRAVITY)

    # Set render preferences
    dispatcher.run('set_render_prefs', obj = moving_anchor_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))
    dispatcher.run('set_render_prefs', obj = collider_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))

    render.set_viewport_limit(-2.5, -2.5, 2.5, 2.5)


def init_wire_example(dispatcher, render):
    '''
    Initalizes a scene with a wire attached to a kinematic object
    '''
    dispatcher.run('reset_scene')
    context = dispatcher.run('get_context')
    # wire shape
    wire_shape = logic.WireShape(WIRE_ROOT_POS, WIRE_END_POS, WIRE_NUM_SEGMENTS)

    # collider shape
    collider_shape = logic.RectangleShape(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1] - 3.5,
                                    WIRE_ROOT_POS[0] + 0.5, WIRE_ROOT_POS[1] - 2)

    # anchor shape and animation
    moving_anchor_shape = logic.RectangleShape(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1] - 0.5,
                                              WIRE_ROOT_POS[0] + 0.25, WIRE_ROOT_POS[1])

    moving_anchor_position, moving_anchor_rotation = moving_anchor_shape.extract_transform_from_shape()
    decay_rate = 0.5
    func = lambda time: [[moving_anchor_position[0] + math.sin(time * 10.0) * math.pow(1.0-decay_rate, time),
                          moving_anchor_position[1]], math.sin(time * 10.0) * 90.0 * math.pow(1.0-decay_rate, time)]
    moving_anchor_animator = objects.Animator(func, context)

    # Populate scene with commands
    wire_handle = dispatcher.run('add_dynamic', shape = wire_shape, node_mass = NODE_MASS)
    collider_handle = dispatcher.run('add_kinematic', shape = collider_shape)

    moving_anchor_handle = dispatcher.run('add_kinematic', shape = moving_anchor_shape,
                                                          position = moving_anchor_position,
                                                          rotation = moving_anchor_rotation,
                                                          animator =moving_anchor_animator)

    edge_condition_handle = dispatcher.run('add_edge_constraint', dynamic = wire_handle,
                                                                   stiffness = 100.0, damping = 0.0)
    dispatcher.run('add_wire_bending_constraint', dynamic= wire_handle,
                                                   stiffness = 0.2, damping = 0.0)
    dispatcher.run('add_kinematic_attachment', dynamic = wire_handle, kinematic = moving_anchor_handle,
                                               stiffness = 100.0, damping = 0.0, distance = 0.1)
    dispatcher.run('add_kinematic_collision', dynamic = wire_handle, kinematic = collider_handle,
                                               stiffness = 1000.0, damping = 0.0)
    dispatcher.run('add_gravity', gravity = GRAVITY)

    # Set render preferences
    dispatcher.run('set_render_prefs', obj = wire_handle,
                                       prefs = meta_data_render(1.0, 'blue', 'solid'))
    dispatcher.run('set_render_prefs', obj = edge_condition_handle,
                                       prefs = meta_data_render(1.0, 'green', 'solid'))
    dispatcher.run('set_render_prefs', obj = collider_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))
    dispatcher.run('set_render_prefs', obj = moving_anchor_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))

    render.set_viewport_limit(-2.5, -2.5, 2.5, 2.5)


def init_beam_example(dispatcher, render):
    '''
    Initalizes a scene with a beam and a wire
    '''
    dispatcher.run('reset_scene')
    context = dispatcher.run('get_context')
    # beam shape
    beam_shape = logic.BeamShape(BEAM_POS, BEAM_WIDTH, BEAM_HEIGHT, BEAM_CELL_X, BEAM_CELL_Y)

    # wire shape
    wire_start_pos = [BEAM_POS[0], BEAM_POS[1] + BEAM_HEIGHT]
    wire_end_pos = [BEAM_POS[0] + BEAM_WIDTH, BEAM_POS[1] + BEAM_HEIGHT]
    wire_shape = logic.WireShape(wire_start_pos, wire_end_pos, BEAM_CELL_X * 8)

    # left anchor shape and animation
    left_anchor_shape = logic.RectangleShape(BEAM_POS[0] - 0.5, BEAM_POS[1],
                                            BEAM_POS[0], BEAM_POS[1] + BEAM_HEIGHT)
    l_pos, l_rot = left_anchor_shape.extract_transform_from_shape()
    func = lambda time: [[l_pos[0] + math.sin(2.0 * time) * 0.1, l_pos[1] + math.sin(time * 4.0)], l_rot]
    l_animator = objects.Animator(func, context)

    # right anchor shape and animation
    right_anchor_shape = logic.RectangleShape(BEAM_POS[0] + BEAM_WIDTH, BEAM_POS[1],
                                             BEAM_POS[0] + BEAM_WIDTH + 0.5, BEAM_POS[1] + BEAM_HEIGHT)
    r_pos, r_rot = right_anchor_shape.extract_transform_from_shape()
    func = lambda time: [[r_pos[0] + math.sin(2.0 * time) * -0.1, r_pos[1]], r_rot]
    r_animator = objects.Animator(func, context)

    # Populate Scene with data and conditions
    beam_handle = dispatcher.run('add_dynamic', shape = beam_shape, node_mass = NODE_MASS)
    wire_handle = dispatcher.run('add_dynamic', shape = wire_shape, node_mass = NODE_MASS)

    left_anchor_handle = dispatcher.run('add_kinematic', shape = left_anchor_shape,
                                                         position = l_pos,
                                                         rotation = l_rot,
                                                         animator = l_animator)

    right_anchor_handle = dispatcher.run('add_kinematic', shape = right_anchor_shape,
                                                          position = r_pos,
                                                          rotation = r_rot,
                                                          animator = r_animator)

    beam_edge_condition_handle = dispatcher.run('add_edge_constraint', dynamic = beam_handle,
                                                                       stiffness = 20.0, damping = 0.0)

    wire_edge_condition_handle = dispatcher.run('add_edge_constraint', dynamic = wire_handle,
                                                                       stiffness = 10.0, damping = 0.0)

    dispatcher.run('add_face_constraint', dynamic = beam_handle,
                                           stiffness = 20.0, damping = 0.0)

    dispatcher.run('add_kinematic_attachment', dynamic = beam_handle, kinematic = left_anchor_handle,
                                               stiffness = 100.0, damping = 0.0, distance = 0.1)

    dispatcher.run('add_kinematic_attachment', dynamic = beam_handle, kinematic = right_anchor_handle,
                                               stiffness = 100.0, damping = 0.0, distance = 0.1)

    dispatcher.run('add_dynamic_attachment', dynamic0 = beam_handle, dynamic1 = wire_handle,
                                              stiffness = 100.0, damping = 0.0, distance = 0.001)

    dispatcher.run('add_gravity', gravity = GRAVITY)

    # Set render preferences
    dispatcher.run('set_render_prefs', obj = beam_handle,
                                       prefs = meta_data_render(1.0, 'grey', 'solid'))
    dispatcher.run('set_render_prefs', obj = beam_edge_condition_handle,
                                       prefs = meta_data_render(1.0, 'blue', 'solid'))

    dispatcher.run('set_render_prefs', obj = wire_handle,
                                       prefs = meta_data_render(1.0, 'grey', 'solid'))
    dispatcher.run('set_render_prefs', obj = wire_edge_condition_handle,
                                       prefs = meta_data_render(1.0, 'green', 'solid'))
    dispatcher.run('set_render_prefs', obj = left_anchor_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))
    dispatcher.run('set_render_prefs', obj = right_anchor_handle,
                                       prefs = meta_data_render(1.0, 'orange', 'solid', 0.8))

    render.set_viewport_limit(-3.5, -3.5, 3.5, 3.5)

