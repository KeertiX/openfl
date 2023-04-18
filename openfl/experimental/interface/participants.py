# Copyright (C) 2020-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""openfl.experimental.interface.participants module."""

import yaml
import importlib
from yaml.loader import SafeLoader
from typing import Dict, Any, Callable


class Participant:
    def __init__(self, name: str = ""):
        self.private_attributes = {}
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def private_attributes(self, attrs: Dict[str, Any]) -> None:
        """
        Set the private attributes of the participant. These attributes will
        only be available within the tasks performed by the participants and
        will be filtered out prior to the task's state being transfered.

        Args:
            attrs: dictionary of ATTRIBUTE_NAME (str) -> object that will be accessible
                   within the participant's task.

                   Example:
                   {'train_loader' : torch.utils.data.DataLoader(...)}

                   In any task performed by this participant performed within the flow,
                   this attribute could be referenced with self.train_loader
        """
        self.private_attributes = attrs


class Collaborator(Participant):
    """
    Defines a collaborator participant
    """
    def __init__(self, config_file: str, **kwargs):
        """
        Create collaborator object
        """
        super().__init__(**kwargs)
        self.config_file = config_file

    def get_name(self) -> str:
        """Get collaborator name"""
        return self._name

    def __set_collaborator_attrs_to_clone(self, clone: Any) -> None:
        """Set collaborator private attributes to clone"""
        # set collaborator private attributes as
        # clone attributes
        for name, attr in self.private_attributes.items():
            setattr(clone, name, attr)

    def __delete_collab_attrs_from_clone(self, clone: Any) -> None:
        """Delete collaborator private attributes from clone"""
        # if clone has collaborator private attributes
        # then remove it
        for attr_name in self.private_attributes:
            if hasattr(clone, attr_name):
                delattr(clone, attr_name)

    def initialize_private_attributes(self) -> None:
        """
        Initialize private attributes to aggregator object
        """
        if len(self.private_attributes) <= 0:
            with open(self.config_file, "r") as f:
                config = yaml.load(f, Loader=SafeLoader)

        shard_desc_template = config["shard_descriptor"]["template"]

        if shard_desc_template is not None:
            filepath, class_name = shard_desc_template.split(".")

            shard_descriptor_module = importlib.import_module(filepath)
            shard_descriptor_class = getattr(shard_descriptor_module, class_name)

            shard_descriptor = shard_descriptor_class(self.config_file)

            self.private_attributes = shard_descriptor.get()

    def execute_func(self, ctx: Any, f_name: str, callback: Callable) -> Any:
        """
        Execute remote function f
        """
        self.__set_collaborator_attrs_to_clone(ctx)

        callback(ctx, f_name)

        self.__delete_collab_attrs_from_clone(ctx)

        return ctx


class Aggregator(Participant):
    """
    Defines an aggregator participant
    """
    def __init__(self, config_file: str, **kwargs):
        super().__init__(**kwargs)
        self.config_file = config_file

    def initialize_private_attributes(self) -> None:
        """
        Assign private attributes to aggregator object
        """
        if len(self.private_attributes) <= 0:
            with open(self.config_file, "r") as f:
                config = yaml.load(f, Loader=SafeLoader)

        shard_desc_template = config["shard_descriptor"]["template"]
        if shard_desc_template is not None:
            filepath, class_name = shard_desc_template.split(".")

            shard_descriptor_module = importlib.import_module(filepath)
            shard_descriptor_class = getattr(shard_descriptor_module, class_name)

            shard_descriptor = shard_descriptor_class(self.config_file)

            self.private_attributes = shard_descriptor.get()
