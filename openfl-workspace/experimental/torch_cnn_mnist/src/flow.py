# Copyright (C) 2020-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from openfl.experimental.interface import FLSpec, Aggregator, Collaborator
from openfl.experimental.runtime import LocalRuntime
from openfl.experimental.placement import aggregator, collaborator


class FederatedFlow(FLSpec):
    """
    Testflow to validate exclude functionality in Federated Flow
    """

    def __init__(self, model=None, optimizer=None, rounds=3, **kwargs):
        super().__init__(**kwargs)
        if model is not None:
            self.model = model
            self.optimizer = optimizer
        else:
            self.model = model
            self.optimizer = optimizer
        self.rounds = rounds

    @aggregator
    def start(self):
        """
        Flow start.
        """
        print("Starting the flow execution")
        self.collaborators = self.runtime.collaborators
        self.next(self.collab_step_one)

    @aggregator
    def collab_step_one(self):
        print("Executing collab step one")

        self.next(
            self.collab_step_two,
            foreach="collaborators",
        )

    @collaborator
    def collab_step_two(self):
        print("Executing collab step two")
        self.next(self.join)

    @aggregator
    def join(self, inputs):
        print("Executing join")
        self.next(self.end)

    @aggregator
    def end(self):
        print("End of the flow")
