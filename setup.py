# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os
from setuptools import find_packages, setup

# This reads the __version__ variable from cirq/_version.py
__version__ = ''
exec(open('cirq/_version.py').read())

name = 'cirq'

description = ('A framework for creating, editing, and invoking '
               'Noisy Intermediate Scale Quantum (NISQ) circuits.')

# README file as long_description.
long_description = io.open('README.rst', encoding='utf-8').read()

# If CIRQ_UNSTABLE_VERSION is set then we use cirq-unstable as the name of the package
# and update the version to this value.
if 'CIRQ_UNSTABLE_VERSION' in os.environ:
    name = 'cirq-unstable'
    __version__ = os.environ['CIRQ_UNSTABLE_VERSION']
    long_description = (
        "**This is a development version of Cirq and may be "
        "unstable.**\n\n**For the latest stable release of Cirq "
        "see**\n`here <https://pypi.org/project/cirq>`__.\n\n" +
        long_description)

# Read in requirements
requirements = open('requirements.txt').readlines()
requirements = [r.strip() for r in requirements]
contrib_requirements = open('cirq/contrib/contrib-requirements.txt').readlines()
contrib_requirements = [r.strip() for r in contrib_requirements]
dev_requirements = open('dev_tools/conf/pip-list-dev-tools.txt').readlines()
dev_requirements = [r.strip() for r in dev_requirements]

cirq_packages = ['cirq'] + [
    'cirq.' + package for package in find_packages(where='cirq')
]

# Sanity check
assert __version__, 'Version string cannot be empty'

setup(name=name,
      version=__version__,
      url='http://github.com/quantumlib/cirq',
      author='The Cirq Developers',
      author_email='cirq@googlegroups.com',
      python_requires=('>=3.6.0'),
      install_requires=requirements,
      extras_require={
          'contrib': contrib_requirements,
          'dev_env': dev_requirements + contrib_requirements,
      },
      license='Apache 2',
      description=description,
      long_description=long_description,
      packages=cirq_packages,
      package_data={
          'cirq': ['py.typed'],
          'cirq.google.api.v1': ['*.proto', '*.pyi'],
          'cirq.google.api.v2': ['*.proto', '*.pyi'],
          'cirq.protocols.json_test_data': ['*'],
      })
