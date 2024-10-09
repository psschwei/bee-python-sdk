# Copyright 2024 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pathlib
import runpy

import pytest

logger = logging.getLogger(__name__)

all_scripts = list(pathlib.Path(__file__, "../../examples").resolve().rglob("*.py"))
ignore_files = {
    "__init__.py",
    # exclude long-running examples (resort to integration tests)
}

scripts = sorted(script for script in all_scripts if script.name not in ignore_files)


def idfn(val):
    return pathlib.Path(val).name


@pytest.mark.e2e
def test_finds_examples():
    assert all_scripts


@pytest.mark.e2e
@pytest.mark.parametrize("script", scripts, ids=idfn)
def test_example_execution(script):
    logger.info(f"Executing Example script: {script}")
    runpy.run_path(str(script), run_name="__main__")
