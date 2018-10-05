"""
@author: Vincent Bonnet
@description : main
"""

import objects as obj
import tools

import solvers as sl
import scene as sc
import math

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

STIFFNESS = 2.0 # in newtons per meter (N/m)
DAMPING = 0.0
PARTICLE_MASS = 0.001 # in Kg

GRAVITY = (0.0, -9.81) # in meters per second^2
NUM_FRAME = 100
FRAME_TIMESTEP = 1.0/24.0 # in seconds
NUM_SUBSTEP = 10 # number of substep per frame

RENDER_FOLDER_PATH = "" # specify a folder to export png files
# Used command  "magick -loop 0 -delay 4 *.png out.gif"  to convert from png to animated gif

'''
 Execute
'''
def createWireScene():
    # Create dynamic objects / kinematic objects / scene
    wire = obj.Wire(WIRE_ROOT_POS, WIRE_END_POS, WIRE_NUM_SEGMENTS, PARTICLE_MASS, STIFFNESS * 50.0, STIFFNESS * 0.1, DAMPING)
    wire.render_prefs = ['co', 0, 'm-', 1]
    movingAnchor = obj.RectangleKinematic(WIRE_ROOT_POS[0], WIRE_ROOT_POS[1], WIRE_ROOT_POS[0] + 0.25, WIRE_ROOT_POS[1] - 0.5)
    movingAnchorPosition = movingAnchor.position
    decayRate = 0.6
    movingAnchorAnimation = lambda time : [[movingAnchorPosition[0] + math.sin(10.0 * time) * math.pow(1.0-decayRate, time), 
                                            movingAnchorPosition[1]], math.sin(time * 10.0) * 90.0 * math.pow(1.0-decayRate, time)]
    movingAnchor.animationFunc = movingAnchorAnimation
    
    #point = kin.PointKinematic(WIRE_END_POS)

    scene = sc.Scene(GRAVITY)
    scene.addDynamic(wire)
    scene.addKinematic(movingAnchor)
    #scene.addKinematic(point)
    scene.updateKinematics(0.0) # set kinematic objects at start frame
    scene.attachToKinematic(wire, movingAnchor, 100.0, 0.0, 0.1)
    #scene.attachToKinematic(wire, point, 100.0, 0.0, 0.1)
    return scene

def createBeamScene():
    # Create dynamic objects / kinematic objects / scene
    beam = obj.Beam(BEAM_POS, BEAM_WIDTH, BEAM_HEIGHT, BEAM_CELL_X, BEAM_CELL_Y, PARTICLE_MASS, STIFFNESS * 10.0, DAMPING)
    beam.render_prefs = ['go', 2, 'k:', 1]

    wireStartPos = [BEAM_POS[0], BEAM_POS[1] + BEAM_HEIGHT]
    wireEndPos = [BEAM_POS[0] + BEAM_WIDTH, BEAM_POS[1] + BEAM_HEIGHT]
    wire = obj.Wire(wireStartPos, wireEndPos, BEAM_CELL_X * 8, PARTICLE_MASS * 0.1, STIFFNESS * 0.5, 0.0, DAMPING)
    wire.render_prefs = ['co', 1, 'm-', 1]

    leftAnchor = obj.RectangleKinematic(BEAM_POS[0] - 0.5, BEAM_POS[1], BEAM_POS[0], BEAM_POS[1] + BEAM_HEIGHT)
    rightAnchor = obj.RectangleKinematic(BEAM_POS[0] + BEAM_WIDTH, BEAM_POS[1], BEAM_POS[0] + BEAM_WIDTH + 0.5, BEAM_POS[1] + BEAM_HEIGHT)

    LPos = leftAnchor.position
    moveLeftAnchor = lambda time: [[LPos[0] + math.sin(2.0 * time) * 0.1, LPos[1] + math.sin(time * 4.0)], 0.0]
    leftAnchor.animationFunc = moveLeftAnchor

    RPos = rightAnchor.position
    moveRightAnchor = lambda time: [[RPos[0] + math.sin(2.0 * time) * -0.1, RPos[1]], 0.0]
    rightAnchor.animationFunc = moveRightAnchor

    scene = sc.Scene(GRAVITY)
    scene.addDynamic(beam)
    scene.addDynamic(wire)
    scene.addKinematic(leftAnchor)
    scene.addKinematic(rightAnchor)
    scene.updateKinematics(0.0) # set kinematic objects at start frame
    scene.attachToKinematic(beam, rightAnchor, 100.0, 0.0, 0.1)
    scene.attachToKinematic(beam, leftAnchor, 100.0, 0.0, 0.1)
    scene.attachToDynamic(beam, wire, 100.0, 0.0, 0.001)

    return scene

scene = createWireScene()

# Create Solver
#solver = sl.SemiImplicitSolver(FRAME_TIMESTEP / NUM_SUBSTEP, NUM_SUBSTEP) #- only debugging - unstable with beam
solver = sl.ImplicitSolver(FRAME_TIMESTEP / NUM_SUBSTEP, NUM_SUBSTEP)

# Run simulation and render
render = tools.Render()
render.setRenderFolderPath(RENDER_FOLDER_PATH)

profiler = tools.profiler.ProfilerSingleton()
for frameId in range(0, NUM_FRAME+1):
    profiler.clearLogs()

    if frameId > 0:
        solver.solveFrame(scene)

    render.showCurrentFrame(scene, frameId)
    render.exportCurrentFrame(str(frameId).zfill(4) + " .png")

    profiler.printLogs()
