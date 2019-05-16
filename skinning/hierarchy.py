"""
@author: Vincent Bonnet
@description : Skeleton and Bone class
"""

# TODO - see bone_children[0] : add support for multiple children per bone

import numpy as np

def distance_from_segment(p, seg_p1, seg_p2):
    '''
    Distance from segment [seg_p1, seg_p2] and point p
    '''
    d = seg_p2 - seg_p1
    d_norm = np.linalg.norm(d)
    d_normalized = d / d_norm
    t = np.dot(p - seg_p1, d_normalized)
    t = min(max(t, 0.0), d_norm)
    projected_p = seg_p1 + d_normalized * t
    return np.linalg.norm(p - projected_p)

def create_skeleton_with_4_bones():
    '''
    Create a skeleton object
    '''
    root_bone = Bone(length = 3.0, rotation = 0.0)
    bone1 = Bone(length = 3.0, rotation = 0.0)
    bone2 = Bone(length = 3.0, rotation = 0.0)
    bone3 = Bone(length = 3.0, rotation = 0.0)

    root_bone.rotation_animation = lambda time : np.sin(time / 2.0 * np.pi) * 20.0
    bone1.rotation_animation = lambda time : np.sin(time / 2.0 * np.pi) * 24.0
    bone2.rotation_animation = lambda time : np.sin(time / 2.0 * np.pi) * 32.0
    bone3.rotation_animation = lambda time : np.sin(time / 2.0 * np.pi) * 36.0

    skeleton = Skeleton([-6.0, 0.0], root_bone)
    skeleton.add_bone(root_bone)
    skeleton.add_bone(bone1, root_bone)
    skeleton.add_bone(bone2, bone1)
    skeleton.add_bone(bone3, bone2)

    return skeleton

def create_skeleton_with_2_bones():
    '''
    Create a skeleton object
    '''
    root_bone = Bone(length = 6.0, rotation = 0.0)
    bone1 = Bone(length = 6.0, rotation = 0.0)

    root_bone.rotation_animation = lambda time : np.sin(time / 2.0 * np.pi) * 0
    bone1.rotation_animation = lambda time : np.sin(time / 2.0 * np.pi) * 90

    skeleton = Skeleton([-6.0, 0.0], root_bone)
    skeleton.add_bone(root_bone)
    skeleton.add_bone(bone1, root_bone)

    return skeleton


class Bone:
    def __init__(self, length = 1.0, rotation = 0.0):
        self.length = length
        self.rotation = rotation # in degrees
        self.rotation_animation = lambda time : rotation
        # hirerarchy info
        self.bone_parent = None
        self.bone_children = []

    def get_homogenous_transform(self):
        '''
        3x3 Matrix combining rotation and displacement
        where R is 2x2 rotation matrix
        and d is 2d vector
        | R  d |
        | 0  1 |
        '''
        H = np.zeros((3,3))
        cos = np.cos(np.deg2rad(self.rotation))
        sin = np.sin(np.deg2rad(self.rotation))
        H[0, 0] = cos
        H[1, 1] = cos
        H[0, 1] = -sin
        H[1, 0] = sin
        H[0, 2] = cos * self.length
        H[1, 2] = sin * self.length
        H[2, 2] = 1.0
        return H

    def animate(self, time):
        self.rotation = self.rotation_animation(time)

class Skeleton:
    def __init__(self, root_position, root_bone):
        self.root_position = np.asarray(root_position)
        self.root_bone = root_bone
        self.bones = []

    def add_bone(self, bone, bone_parent = None):
        self.bones.append(bone)
        if bone_parent is not None:
            bone.bone_parent = bone_parent
            bone_parent.bone_children.append(bone)

    def get_homogenous_transform(self):
        H = np.identity(3)
        H[0, 2] = self.root_position[0]
        H[1, 2] = self.root_position[1]
        return H

    def attach_mesh(self, mesh, max_influences, kernel_func):
        num_vertices = len(mesh.vertex_buffer)
        num_bones = len(self.bones)
        mesh.weights_map = np.zeros((num_bones, num_vertices))
        mesh.local_homogenous_vertex = np.zeros((num_bones, num_vertices, 3))
        bone_segments = self.get_bone_segments()

        # Compute weights per bone per vertices (weights map) from kernel function
        for vertex_id, vertex in enumerate(mesh.vertex_buffer):
            for bone_id, bone_seg in enumerate (bone_segments):
                distance = distance_from_segment(vertex, bone_seg[0], bone_seg[1])
                mesh.weights_map[bone_id][vertex_id] = kernel_func(distance)

        # Updates the weights map by limiting ...
        # the number of influences from the n closest vertices
        num_influences = min(num_bones, max_influences)
        for vertex_id, vertex in enumerate(mesh.vertex_buffer):
            vertex_weights = np.zeros(num_bones)
            for bone_id, bone_seg in enumerate (bone_segments):
                vertex_weights[bone_id] = mesh.weights_map[bone_id][vertex_id]

            vertex_weigths_sorted_index = np.argsort(vertex_weights)
            for vtx_id in range(num_bones - num_influences):
                vertex_weights[vertex_weigths_sorted_index[vtx_id]] = 0.0

            vertex_weights /= np.sum(vertex_weights)
            for bone_id, bone_seg in enumerate (bone_segments):
                mesh.weights_map[bone_id][vertex_id] = vertex_weights[bone_id]

        # Compute the local space for each vertices
        bone_transforms = self.get_bone_homogenous_transforms()

        for vertex_id, vertex in enumerate(mesh.vertex_buffer):

            for bone_id, bone_transform in enumerate(bone_transforms):
                weight = mesh.weights_map[bone_id][vertex_id]

                if (weight == 0.0):
                    local_vertex_homogenous = np.zeros(3)
                    local_vertex_homogenous[2] = 1.0
                    mesh.local_homogenous_vertex[bone_id][vertex_id] = local_vertex_homogenous
                else:
                    T = (bone_transforms[bone_id])
                    vertex_homogenous = np.ones(3)
                    vertex_homogenous[0:2] = vertex
                    local_vertex_homogenous = np.matmul(np.linalg.inv(T), vertex_homogenous) * weight
                    local_vertex_homogenous /= local_vertex_homogenous[2]
                    mesh.local_homogenous_vertex[bone_id][vertex_id] = local_vertex_homogenous

        # Update the world space vertices from the local_homogenous_vertex
        # It should not modify the current configuration and only used for debugging
        self.update_mesh(mesh)


    def get_bone_homogenous_transforms(self):
        '''
        Returns the world space transform of each bones
        '''
        num_bones = len(self.bones)
        bone_transforms = np.zeros((num_bones,3,3))

        H = self.get_homogenous_transform()
        bone_id = 0

        bone = self.root_bone
        while bone is not None:
            # Concatenate transformation matrice
            bone_H = bone.get_homogenous_transform()
            H = np.matmul(H, bone_H)

            # Go to the children
            if len(bone.bone_children) > 0:
                bone = bone.bone_children[0]
            else:
                bone = None

            bone_transforms[bone_id] = H
            bone_id += 1

        return bone_transforms

    def get_bone_segments(self):
        homogenous_coordinate = np.asarray([0.0, 0.0, 1.0])
        bone_transforms = self.get_bone_homogenous_transforms()

        segments = []

        H = self.get_homogenous_transform()

        prev_pos = np.matmul(H, homogenous_coordinate)

        for bone_id, bone_H in enumerate(bone_transforms):

            next_pos = np.matmul(bone_H, homogenous_coordinate)
            segments.append([prev_pos[0:2], next_pos[0:2]])
            prev_pos = next_pos

        return segments

    def animate(self, time):
        for bone in self.bones:
            bone.animate(time)

    def update_mesh(self, mesh):
        bone_transforms = self.get_bone_homogenous_transforms()
        for vertex_id, vertex in enumerate(mesh.vertex_buffer):

            updated_vertex = np.zeros(2)
            for bone_id, bone_transform in enumerate(bone_transforms):
                weight = mesh.weights_map[bone_id][vertex_id]
                T = (bone_transforms[bone_id]) * weight

                world_vertex_homogenous = np.matmul(T, mesh.local_homogenous_vertex[bone_id][vertex_id])

                updated_vertex[0] += world_vertex_homogenous[0]
                updated_vertex[1] += world_vertex_homogenous[1]

            vertex[0] = updated_vertex[0]
            vertex[1] = updated_vertex[1]