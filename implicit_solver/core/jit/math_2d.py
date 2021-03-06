"""
@author: Vincent Bonnet
@description : Maths methods
"""
import math
import numba
import numpy as np

@numba.njit(inline='always')
def dot(u, v):
    '''
    Returns the dotproduct of a 2D vector
    np.dot is generic and fast for array but slow for a single for scalar
    Therefore, it is replaced by a less generic norm
    '''
    return (u[0] * v[0]) + (u[1] * v[1])

@numba.njit(inline='always')
def det(u, v):
    '''
    Returns the determinant of the matrix formed from the column vectors u and v
    '''
    return (u[0] * v[1]) - (u[1] * v[0])

@numba.njit(inline='always')
def norm(v):
    '''
    Returns the norm of a 2D vector
    np.linalg.norm is generic and fast for array but slow for a single for scalar
    Therefore, it is replaced by a less generic norm
    '''
    dot = (v[0] * v[0]) + (v[1] * v[1])
    return math.sqrt(dot)

@numba.njit(inline='always')
def is_close(v0, v1, tol=1.e-8):
    '''
    Returns whether two scalar are similar
    np.isclose is generic and fast for array but slow for a single for scalar
    Therefore, it is replaced by a less generic norm
    '''
    return math.fabs(v0 - v1) < tol

@numba.njit(inline='always')
def distance(x0, x1):
    '''
    Returns distance between x0 and x1
    '''
    distance = norm(x0 - x1)
    return distance

@numba.njit(inline='always')
def area(x0, x1, x2):
    '''
    Returns the area of the 2D triangle from x0, x1, x2
    '''
    u = x1 - x0 # np.subtract(x1, x0)
    v = x2 - x0 # np.subtract(x2, x0)
    area = math.fabs(u[0]*v[1]-v[0]*u[1]) * 0.5
    return area

@numba.njit(inline='always')
def angle(x0, x1, x2):
    '''
    Returns the angle between the segment x0-x1 and x1-x2
    The range is [-pi, pi]
      x1
      /\
     /  \
    x0  x2
    '''
    u = x0 - x1
    v = x1 - x2

    # Discrete angle
    det = u[0]*v[1] - u[1]*v[0]      # determinant
    dot = u[0]*v[0] + u[1]*v[1]      # dot product
    angle = math.atan2(det,dot)  # atan2 return range [-pi, pi]
    return angle

@numba.njit(inline='always')
def curvature(x0, x1, x2):
    '''
    Connect three points :
      x1
      /\
     /  \
    x0  x2
    Compute the curvature : |dT/ds| where T is the tangent and s the surface
    The curvature at any point along a two-dimensional curve is defined as
    the rate of change in tangent direction θ as a function of arc length s.
    With :
    t01 = x1 - x0 and t12 = x2 - x1
    Discrete curvature formula : angle(t12,t01) / ((norm(t01) + norm(t12)) * 0.5)
    '''
    t01 = x1 - x0
    t01norm = norm(t01)
    t01 /= t01norm
    t12 = x2 - x1
    t12norm =  norm(t12)
    t12 /= t12norm

    # Discrete curvature
    det = t01[0]*t12[1] - t01[1]*t12[0]      # determinant
    dot = t01[0]*t12[0] + t01[1]*t12[1]      # dot product
    angle = math.atan2(det,dot)  # atan2 return range [-pi, pi]
    curvature = angle / ((t01norm + t12norm) * 0.5)

    return curvature

@numba.njit(inline='always')
def copy(v):
    '''
    Fast copy of v
    '''
    v_copy = np.zeros(2)
    v_copy[0] = v[0]
    v_copy[1] = v[1]
    return v_copy

@numba.njit(inline='always')
def rotation_matrix(rotation):
    theta = np.radians(rotation)
    c, s = np.cos(theta), np.sin(theta)
    return np.array(((c, -s), (s, c)))
