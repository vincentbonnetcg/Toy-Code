"""
@author: Vincent Bonnet
@description : Code Generation to convert function into numba friendly function
"""

# Package used by gen_vectorize.py
import functools
import lib.common as common
import lib.common.code_gen.code_gen_helper as gen

# Possible packages used by the generated functions
# TODO : modify to get the import from original python file
import numba
import numpy as np
import lib.common.jit.node_accessor as na
import lib.common.jit.math_2d as math2D
import lib.objects.components.jit.spring_lib as spring_lib
import lib.objects.components.jit.area_lib as area_lib
from lib.common.convex_hull import ConvexHull


def generate_vectorize_function(function, njit, parallel, debug, block_ids):
    '''
    Returns a tuple (source code, function object)
    '''
    # Generate code
    helper = gen.CodeGenHelper(njit, parallel, debug, block_ids)
    helper.generate_vectorized_function_source(function)

    # Compile code
    generated_function_object = compile(helper.generated_function_source, helper.generated_function_name, 'exec')
    exec(generated_function_object)

    return helper.generated_function_source, vars().get(helper.generated_function_name)


def as_vectorized(function=None, *,njit=True, parallel=False, debug=False, block_ids=False):
    '''
    Decorator with arguments to vectorize a function
    '''
    if function is None:
        return functools.partial(as_vectorized, njit=njit, parallel=parallel, debug=debug, block_ids=block_ids)

    def convert(arg):
        '''
        From DataBlock to DataBlock.blocks
        '''
        if isinstance(arg, common.DataBlock):
            if isinstance(arg.blocks, tuple):
                return arg.blocks
            else:
                raise ValueError("The blocks should be in a tuple. use datablock.lock()")

        return arg

    @functools.wraps(function)
    def execute(*args):
        '''
        Execute the function. At least one argument is expected
        From Book : Beazley, David, and Brian K. Jones. Python Cookbook: Recipes for Mastering Python 3. " O'Reilly Media, Inc.", 2013.
        In Section : 9.6. Defining a Decorator That Takes an Optional Argument
        '''
        # Fetch numpy array from common.DataBlock
        arg_list = list(args)
        for arg_id , arg in enumerate(arg_list):
            arg_list[arg_id] = convert(arg)

        # Call function
        first_argument = args[0] # argument to vectorize
        if isinstance(first_argument, (list, tuple)):
            for datablock in first_argument:
                if isinstance(datablock, common.DataBlock):
                    if not datablock.isEmpty():
                        arg_list[0] = convert(datablock)
                        execute.function(*arg_list)
                else:
                    raise ValueError("The first argument should be a datablock")
        elif isinstance(first_argument, common.DataBlock):
                if not first_argument.isEmpty():
                    execute.function(*arg_list)
        else:
            raise ValueError("The first argument should be a datablock or a list of datablocks")

        return True

    source, function = generate_vectorize_function(function, njit, parallel, debug, block_ids)

    execute.njit = njit
    execute.debug = debug
    execute.parallel = parallel
    execute.block_ids = block_ids
    execute.source = source
    execute.function = function

    return execute
