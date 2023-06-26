# Copyright (C) 2020-2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Experimental CLI."""

import os
from pathlib import Path

from click import group
from click import pass_context


@group()
@pass_context
def experimental(context):
    """Manage Experimental Environment"""
    context.obj["group"] = "experimental"


@experimental.command(name="activate")
def activate():
    """Activate experimental environment."""
    settings = Path(os.path.join(
        os.path.expanduser('~'), ".openfl",
    )).resolve()

    if not settings.exists():
        settings.mkdir(parents=True, exist_ok=True)

    settings = settings.joinpath("experimental")

    if not settings.exists():
        with open(settings, "w") as f:
            f.write("experimental")
