"""
@author: Vincent Bonnet
@description : Evaluation of Abstract Syntax Trees
"""

import numba # required by core.code_gen
import core.code_gen as generate
import core
import numpy as np
import unittest

'''
Datablock Functions
'''
class Vertex:
    def __init__(self):
        self.x = np.ones((2,3)) * 2.1
        self.y = 1.5

class Container:
    def __init__(self, datablock):
        self.data = datablock

def create_datablock(num_elements=10):
    datablock = core.DataBlock(Vertex, block_size = 100)
    datablock.initialize(num_elements)
    return datablock

'''
Functions to vectorize
'''
@generate.vectorize
def add_values(v0 : Vertex, v1 : Vertex, other_value):
    v0.x += v1.x + other_value
    v0.y += v1.y + other_value

@generate.vectorize(njit=False)
def add_values_to_list(v0 : Vertex, v1 : Vertex, out_list):
    out_list.append(v0.x + v1.x)

@generate.vectorize_block
def get_num_elements(vertex, ref_counter):
    ref_counter += vertex.blockInfo_size

'''
Tests for code generation
'''
class Tests(unittest.TestCase):

    def test_generated_function_with_blocks_input(self):
        datablock0 = create_datablock()
        datablock1 = create_datablock()
        add_values(datablock0.blocks, datablock1.blocks, 1.0)
        self.assertEqual(datablock0.block(0)['x'][0][0][0], 5.2)
        self.assertEqual(datablock0.block(0)['y'][0], 4.0)

    def test_generated_function_with_datablock_input(self):
        datablock0 = create_datablock()
        datablock1 = create_datablock()
        add_values(datablock0, datablock1, 1.0)
        self.assertEqual(datablock0.block(0)['x'][0][0][0], 5.2)
        self.assertEqual(datablock0.block(0)['y'][0], 4.0)

    def test_function_generated_once(self):
        datablock0 = create_datablock()
        datablock1 = create_datablock()
        add_values(datablock0, datablock1, 1.0)
        function0 = add_values.function
        source0 = add_values.source
        add_values(datablock0, datablock1, 1.0)
        function1 = add_values.function
        source1 = add_values.source
        self.assertEqual(function0, function1)
        self.assertEqual(source0, source1)
        self.assertEqual(add_values.options.njit, True)
        self.assertEqual(function0.__module__, function1.__module__)

    def test_function_without_njit(self):
        datablock0 = create_datablock(15)
        datablock1 = create_datablock(15)
        result_list = []
        add_values_to_list(datablock0, datablock1, result_list)
        self.assertEqual(len(result_list), 15)
        self.assertEqual(result_list[0][0][0], 4.2)

    def test_vectorized_block(self):
        datablock = create_datablock(157)
        counter = np.zeros(1, dtype = np.int32) # use array to pass value as reference
        get_num_elements(datablock, counter)
        self.assertEqual(counter[0], 157)

    def setUp(self):
        print(" CodeGeneration Test:", self._testMethodName)

if __name__ == '__main__':
    unittest.main(Tests())
