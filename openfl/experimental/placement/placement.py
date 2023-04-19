# Copyright (C) 2020-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import functools
import ray
from copy import deepcopy
from openfl.experimental.utilities import (
    RedirectStdStreamContext,
    GPUResourcesNotAvailableError,
    get_number_of_gpus,
)
from typing import Callable
import importlib


class RayExecutor:
    def __init__(self):
        self.remote_functions = []
        self.remote_contexts = []

    def ray_put_task(self, ctx, func):
        runtime_module = importlib.import_module(
            "openfl.experimental.runtime.local_runtime"
        )
        collaborator_step_executor = getattr(
            runtime_module, "collaborator_step_executor"
        )
        remote_to_exec = make_remote(collaborator_step_executor, func.num_gpus)
        ref_ctx = ray.put(ctx)
        self.remote_contexts.append(ref_ctx)
        self.remote_functions.append(
            remote_to_exec.remote(collaborator_step_executor, ref_ctx, func)
        )
        del remote_to_exec
        del ref_ctx

    def get_remote_clones(self):
        clones = deepcopy(ray.get(self.remote_functions))
        del self.remote_functions
        # Remove clones from ray object store
        for ctx in self.remote_contexts:
            ray.cancel(ctx)
        return clones


def make_remote(f: Callable, num_gpus: int) -> Callable:
    """
    Assign function to run in its own process using
    Ray

    Args:
        num_gpus: Defines the number of GPUs to request for a task
    """
    f = ray.put(f)

    @functools.wraps(f)
    @ray.remote(num_gpus=num_gpus, max_calls=1)
    def wrapper(*args, **kwargs):
        f = args[0]
        collab_step = args[2].__name__
        print(f"\nRunning {collab_step} in a new process")
        f(args[1], args[2])
        return args[1]

    return wrapper


def aggregator(f: Callable = None) -> Callable:
    """
    Placement decorator that designates that the task will
    run at the aggregator node

    Usage:
    class MyFlow(FLSpec):
        ...
        @aggregator
        def agg_task(self):
           ...
        ...

    """

    print(f'Aggregator step "{f.__name__}" registered')
    f.is_step = True
    f.decorators = []
    f.name = f.__name__
    f.task = True
    f.aggregator_step = True
    f.collaborator_step = False
    if f.__doc__:
        f.__doc__ = "<Node: Aggregator>" + f.__doc__
    f.num_gpus = 0

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        print(f"\nCalling {f.__name__}")
        with RedirectStdStreamContext() as context_stream:
            # context_stream capture stdout and stderr for the function f.__name__
            setattr(wrapper, "_stream_buffer", context_stream)
            f(*args, **kwargs)

    return wrapper


def collaborator(f: Callable = None, *, num_gpus: float = 0) -> Callable:
    """
    Placement decorator that designates that the task will
    run at the collaborator node

    Usage:
    class MyFlow(FLSpec):
        ...
        @collaborator
        def collaborator_task(self):
            ...

        @collaborator(num_gpus=1)
        @def collaborator_gpu_task:
            ...
        ...

    Args:
        num_gpus: [Applicable for Ray backend only]
                  Defines how many GPUs will be made available
                  to the task (Default = 0). Selecting a value < 1 (0.0-1.0]
                  will result in sharing of GPUs between tasks. 1 >= results in
                  exclusive GPU access for the task.
    """

    if f is None:
        return functools.partial(collaborator, num_gpus=num_gpus)

    print(f'Collaborator step "{f.__name__}" registered')
    f.is_step = True
    f.decorators = []
    f.name = f.__name__
    f.task = True
    f.aggregator_step = False
    f.collaborator_step = True
    if f.__doc__:
        f.__doc__ = "<Node: Collaborator>" + f.__doc__
    total_gpus = get_number_of_gpus()
    if total_gpus < num_gpus:
        GPUResourcesNotAvailableError(
            f"cannot assign more than available GPUs ({total_gpus} < {num_gpus})."
        )
    f.num_gpus = num_gpus

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        print(f"\nCalling {f.__name__}")
        with RedirectStdStreamContext() as context_stream:
            # context_stream capture stdout and stderr for the function f.__name__
            setattr(wrapper, "_stream_buffer", context_stream)
            f(*args, **kwargs)

    return wrapper
