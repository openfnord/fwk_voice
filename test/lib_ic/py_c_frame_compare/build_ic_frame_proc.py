# Copyright 2022 XMOS LIMITED.
# This Software is subject to the terms of the XMOS Public Licence: Version 1.

import shutil
import sys
import os
import xmos_ai_tools.runtime as rt
from cffi import FFI

from extract_state import extract_pre_defs

# One more ../ than necessary - builds in the 'build' folder
MODULE_ROOT = "../../../../modules"
XCORE_MATH = "../../../../build/fwk_voice_deps/lib_xcore_math"

# TFLite Micro configuration
TFLITE_MICRO_ROOT = os.path.dirname(rt.__file__)
TFLITE_MICRO_LIB_DIR = f"{TFLITE_MICRO_ROOT}/lib"
TFLITE_MICRO_INCLUDE = f"{TFLITE_MICRO_ROOT}/include"
TFLITE_MICRO_LIB = f"host_xtflitemicro" # use the host platform

FLAGS = [
    '-std=c++11',
    '-fPIC',
    '-DTF_LITE_STATIC_MEMORY',           # Define TF_LITE_STATIC_MEMORY
    '-DTF_LITE_STRIP_ERROR_STRINGS',     # Define TF_LITE_STRIP_ERROR_STRINGS
]

INCLUDE_DIRS=[
    f"{MODULE_ROOT}/lib_ic/api/",
    f"{MODULE_ROOT}/lib_ic/src/",
    f"{MODULE_ROOT}/lib_vnr/api/common",
    f"{MODULE_ROOT}/lib_vnr/api/features",
    f"{MODULE_ROOT}/lib_vnr/src/features",
    f"{MODULE_ROOT}/lib_vnr/api/inference",
    f"{MODULE_ROOT}/lib_vnr/src/inference/model",
    f"{MODULE_ROOT}/lib_vnr/src/inference",
    f"{XCORE_MATH}/lib_xcore_math/api",
    TFLITE_MICRO_INCLUDE
]

LIBRARY_DIRS = [
    '../../../../build/modules/lib_ic',
    '../../../../build/modules/lib_aec',
    '../../../../build/modules/lib_vnr',
    '../../../../build/fwk_voice_deps/build',
    TFLITE_MICRO_LIB_DIR
]

LIBRARIES = [
    'fwk_voice_module_lib_ic', 
    'fwk_voice_module_lib_aec',
    'fwk_voice_module_lib_vnr_features', 
    'fwk_voice_module_lib_vnr_inference', 
    'lib_xcore_math', 
    TFLITE_MICRO_LIB,
    'm', 
    'stdc++'
] # on Unix, link with the math library. Linking order is important here for gcc compile on Linux!

SRCS = f"../ic_test.c".split()
ffibuilder = FFI()

#Extract all defines and state from lib_ic programatically
predefs = extract_pre_defs()
predefs = predefs.replace("sizeof(uint64_t)", "8")
print(predefs)
# Contains all the C defs visible from Python
ffibuilder.cdef(
predefs +
"""
    void test_init(void);
    ic_state_t test_get_state(void);
    void test_filter(int32_t y_data[IC_FRAME_ADVANCE], int32_t x_data[IC_FRAME_ADVANCE], int32_t output[IC_FRAME_ADVANCE]);
    void test_adapt(float_s32_t vnr);
""".replace("IC_FRAME_ADVANCE", "240")
)

# Contains the C source necessary to allow the cdefs to work
ffibuilder.set_source("ic_test_py",  # name of the output C extension
"""
    #include "ic_api.h"
    void test_init(void);
    ic_state_t test_get_state(void);
    void test_filter(int32_t y_data[IC_FRAME_ADVANCE], int32_t x_data[IC_FRAME_ADVANCE], int32_t output[IC_FRAME_ADVANCE]);
    void test_adapt(float_s32_t vnr);
""",
    sources=SRCS,
    library_dirs=LIBRARY_DIRS,
    libraries=LIBRARIES,
    extra_compile_args=FLAGS,
    include_dirs=INCLUDE_DIRS)

if __name__ == "__main__":
    ffibuilder.compile(tmpdir='build', target='ic_test_py.*', verbose=True)
    #Darwin hack https://stackoverflow.com/questions/2488016/how-to-make-python-load-dylib-on-osx
    if sys.platform == "darwin":
        shutil.copyfile("build/ic_test_py.dylib", "build/ic_test_py.so")

