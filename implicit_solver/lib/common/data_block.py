"""
@author: Vincent Bonnet
@description : Array of Structures of Arrays (AoSoA)

Single Block Memory Layout (with x, v, b as channels)
|-----------------------------|
| x[block_size](np.float)     |
| v[block_size](np.float)     |
| b[block_size](np.int)       |
|-----------------------------|
|blockInfo_numElements (int64)|
|blockInfo_active     (bool)  |
|-----------------------------|

blockInfo_numElements is the number of set elements in the Block
blockInfo_active defines whether or not the Block is active

Datablock is a list of Blocks
"""

import numba
import numpy as np
import keyword
import lib.common.jit.block_utils as block_utils

class DataBlock:

    def __init__(self, class_type, block_size = 100):
        # Data
        self.blocks = numba.typed.List()
        # Data type : (x, y, ...)
        self.dtype_dict = {}
        self.dtype_dict['names'] = [] # list of names
        self.dtype_dict['formats'] = [] # list of tuples (data_type, data_shape)
        self.dtype_value = None
        # Aosoa data type : (x, y, ...) becomes (self.block_size, x, y, ...)
        self.dtype_block_dict = {}
        self.dtype_block_dict['names'] = []
        self.dtype_block_dict['formats'] = []
        self.dtype_block = None
        # Default values
        self.defaults = () #  heterogeneous tuple storing defaults value
        # Block size
        self.block_size = block_size
        # class has an ID
        self.hasID = False
        # Set class
        self.__set_dtype(class_type)
        self.clear()

    def num_blocks(self):
        return len(self.blocks)

    def block(self, block_index):
        # [0] because the self.blocks[block_index] is an array with one element
        return self.blocks[block_index][0]

    def clear(self):
        '''
        Clear the data on the datablock (it doesn't reset the datatype)
        '''
        self.blocks = numba.typed.List()
        # append inactive block
        # it prevents to have empty list which would break the JIT compile to work
        block_dtype = self.get_block_dtype()
        block = block_utils.empty_block(block_dtype)
        self.blocks.append(block)

    def __check_before_add(self, name):
        '''
        Raise exception if 'name' cannot be added
        '''
        if name in ['blockInfo_numElements', 'blockInfo_active']:
            raise ValueError("field name " + name + " is reserved ")

        if keyword.iskeyword(name):
            raise ValueError("field name cannot be a keyword: " + name)

        if name in self.dtype_dict['names']:
            raise ValueError("field name already used : " + name)

    def __set_dtype(self, class_type):
        '''
        Set data type from the class type
        '''
        inst = class_type()

        default_values = []
        for name, value in inst.__dict__.items():
            self.__check_before_add(name)

            self.dtype_block_dict['names'].append(name)
            self.dtype_dict['names'].append(name)
            default_values.append(value)

            if name == 'ID':
                self.hasID = True

            if np.isscalar(value):
                data_type = type(value)
                self.dtype_dict['formats'].append(data_type)
                # The coma after (self.block_size,) is essential
                # In case field_shape == self.block_size == 1,
                # it guarantees an array will be produced and not a single value
                aosoa_field_shape = (self.block_size,)
                self.dtype_block_dict['formats'].append((data_type, aosoa_field_shape))
            else:
                data_type = value.dtype.type
                data_shape = value.shape
                self.dtype_dict['formats'].append((data_type, data_shape))
                aosoa_field_shape = ([self.block_size] + list(data_shape))
                self.dtype_block_dict['formats'].append((data_type, aosoa_field_shape))

        self.defaults = tuple(default_values)

        # add block info
        self.dtype_block_dict['names'].append('blockInfo_numElements')
        self.dtype_block_dict['names'].append('blockInfo_active')
        self.dtype_block_dict['formats'].append(np.int64)
        self.dtype_block_dict['formats'].append(np.bool)

        # create datatype
        self.dtype_block = np.dtype(self.dtype_block_dict, align=True)
        self.dtype_value = np.dtype(self.dtype_dict, align=True)

    def get_block_dtype(self):
        '''
        Returns the the dtype of a block
        '''
        return self.dtype_block

    def get_scalar_dtype(self):
        '''
        Returns the value dtype of the datablock
        '''
        return self.dtype_value

    def initialize(self, num_elements):
        '''
        Initialize blocks and return new block ids
        '''
        self.clear()
        return self.append(num_elements, True)

    def append(self, num_elements : int, reuse_inactive_block : bool = False):
        '''
        Return a list of new blocks
        Initialize with default values
        '''
        block_dtype = self.get_block_dtype()
        block_handles = None

        if self.hasID:
            block_handles = block_utils.append_blocks_with_ID(self.blocks, block_dtype,
                                                      reuse_inactive_block,
                                                      num_elements, self.block_size)
        else:
            block_handles = block_utils.append_blocks(self.blocks, block_dtype,
                                                      reuse_inactive_block,
                                                      num_elements, self.block_size)

        # set default values exept for the reserved attribute ID
        for block_handle in block_handles:
            block_container = self.blocks[block_handle]
            for field_id, default_value in enumerate(self.defaults):
                if self.dtype_block_dict['names'][field_id] != 'ID':
                    block_container[0][field_id][:] = default_value

        return block_handles


    def append_empty(self, num_elements : int, reuse_inactive_block : bool = False):
        '''
        Return a list of uninitialized blocks
        '''
        block_dtype = self.get_block_dtype()
        block_handles = None

        if self.hasID:
            block_handles = block_utils.append_blocks_with_ID(self.blocks, block_dtype,
                                                      reuse_inactive_block,
                                                      num_elements, self.block_size)
        else:
            block_handles = block_utils.append_blocks(self.blocks, block_dtype,
                                                      reuse_inactive_block,
                                                      num_elements, self.block_size)
        return block_handles

    '''
    DISABLE FOR NOW - NEED FIX
    def remove(self, block_handles = None):
        if block_handles is None:
            return

        if 'ID' in self.dtype_dict['names']:
            raise ValueError("ID channel used by this datablock. Another datablock might references this one => cannot delete")

        for block_handle in sorted(block_handles, reverse=True):
            del(self.blocks[block_handle])
    '''

    def is_empty(self):
        return len(self.blocks)==0

    def __len__(self):
        return len(self.blocks)

    '''
    Vectorize Functions on blocks
    '''
    def __take_with_id(self, block_handles = []):
        for block_handle in block_handles:
            block_container = self.blocks[block_handle]
            block_data = block_container[0]
            if block_data['blockInfo_active']:
                yield block_container

    def __take(self):
        for block_container in self.blocks:
            block_data = block_container[0]
            if block_data['blockInfo_active']:
                yield block_container

    def get_blocks(self, block_handles = None):
        if block_handles is None:
            return self.__take()

        return self.__take_with_id(block_handles)

    def compute_num_elements(self, block_handles = None):
        return block_utils.compute_num_elements(self.blocks, block_handles)

    def copyto(self, field_name, values, block_handles = None):
        num_elements = 0

        for block_container in self.get_blocks(block_handles):
            block_data = block_container[0]
            begin_index = num_elements
            block_n_elements = block_data['blockInfo_numElements']
            num_elements += block_n_elements
            end_index = num_elements
            np.copyto(block_data[field_name][0:block_n_elements], values[begin_index:end_index])

    def fill(self, field_name, value, block_handles = None):
        for block_container in self.get_blocks(block_handles):
            block_data = block_container[0]
            block_data[field_name].fill(value)

    def flatten(self, field_name, block_handles = None):
        '''
        Convert block of array into a single array
        '''
        field_id = self.dtype_dict['names'].index(field_name)
        field_dtype = self.dtype_dict['formats'][field_id]

        num_elements = self.compute_num_elements(block_handles)
        result = np.empty(num_elements, field_dtype)

        num_elements = 0
        for block_container in self.get_blocks(block_handles):
            block_data = block_container[0]
            begin_index = num_elements
            block_n_elements = block_data['blockInfo_numElements']
            num_elements += block_n_elements
            end_index = num_elements
            np.copyto(result[begin_index:end_index], block_data[field_id][0:block_n_elements])

        return result

    def set_active(self, active, block_handles = None):
        for block_container in self.get_blocks(block_handles):
            block_data = block_container[0]
            block_data['blockInfo_active'] = active
