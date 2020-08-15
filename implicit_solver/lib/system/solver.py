"""
@author: Vincent Bonnet
@description : Solver to orchestrate the step of a solver
"""

import lib.common as cm
from lib.objects.jit.data import Node, Area, Bending, Spring, AnchorSpring
from lib.objects.jit.data import Point, Edge, Triangle, Tetrahedron
from lib.system import Scene

class SolverContext:
    '''
    SolverContext to store time, time stepping, etc.
    '''
    def __init__(self, time = 0.0, frame_dt = 1.0/24.0, num_substep = 4, num_frames = 1):
        self.time = time # current time (in seconds)
        self.start_time = time # start time (in seconds)
        self.end_time = time + (num_frames * frame_dt) # end time (in seconds)
        self.frame_dt = frame_dt # time step on a single frame (in seconds)
        self.num_substep = num_substep # number of substep per frame
        self.dt = frame_dt / num_substep # simulation substep (in seconds)
        self.num_frames = num_frames # number of simulated frame (doesn't include initial frame)

class SolverDetails:
    '''
    List of datablocks
    '''
    def __init__(self):
        block_size = 100
        # dynamics
        self.node = cm.DataBlock(Node, block_size) # nodes
        # constraints
        self.area = cm.DataBlock(Area, block_size) # area
        self.bending = cm.DataBlock(Bending, block_size) # bending rod
        self.spring = cm.DataBlock(Spring, block_size) # spring
        self.anchorSpring = cm.DataBlock(AnchorSpring, block_size) # anchor spring
        # kinematics
        self.point = cm.DataBlock(Point, block_size) # point
        self.edge = cm.DataBlock(Edge, block_size) # edge
        self.triangle = cm.DataBlock(Triangle, block_size) # triangle
        self.tetrahedron = cm.DataBlock(Tetrahedron, block_size) # tetrahedron

    def block_from_datatype(self, datatype):
        blocks = [self.node, self.area, self.bending, self.spring, self.anchorSpring]
        blocks += [self.point, self.edge, self.triangle, self.tetrahedron]
        datatypes = [Node, Area, Bending, Spring, AnchorSpring]
        datatypes += [Point, Edge, Triangle, Tetrahedron]
        index = datatypes.index(datatype)
        return blocks[index]

    def dynamics(self):
        return [self.node]

    def conditions(self):
        return [self.area, self.bending, self.spring, self.anchorSpring]

class Solver:
    '''
    Solver Implementation
    '''
    def __init__(self, time_integrator):
        self.time_integrator = time_integrator

    def initialize(self, scene : Scene, details : SolverDetails, context : SolverContext):
        '''
        Initialize the scene
        '''
        scene.init_kinematics(details, context.start_time)
        scene.init_conditions(details)

    @cm.timeit
    def solve_step(self, scene : Scene, details : SolverDetails, context : SolverContext):
        '''
        Solve a single step (pre/step/post)
        '''
        self._pre_step(scene, details, context)
        self._step(scene, details, context)
        self._post_step(scene, details, context)

    @cm.timeit
    def _pre_step(self, scene : Scene, details : SolverDetails, context : SolverContext):
        scene.update_kinematics(details, context.time, context.dt)
        scene.update_conditions(details) # allocate dynamically new conditions

    @cm.timeit
    def _step(self, scene : Scene, details : SolverDetails, context : SolverContext):
        self.time_integrator.prepare_system(scene, details, context.dt)
        self.time_integrator.assemble_system(details, context.dt)
        self.time_integrator.solve_system(details, context.dt)

    @cm.timeit
    def _post_step(self, scene, details, context):
        pass
