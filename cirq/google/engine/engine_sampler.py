# Copyright 2019 The Cirq Developers
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
from typing import List, TYPE_CHECKING, Union, Optional, cast

from cirq import work, circuits
from cirq.google import engine, gate_sets

if TYPE_CHECKING:
    import cirq


class QuantumEngineSampler(work.Sampler):
    """A sampler that samples from processors managed by the Quantum Engine.

    Exposes a `cirq.google.Engine` instance as a `cirq.Sampler`.
    """

    def __init__(self, *, engine: 'cirq.google.Engine',
                 processor_id: Union[str, List[str]],
                 gate_set: 'cirq.google.SerializableGateSet'):
        """
        Args:
            engine: Quantum engine instance to use.
            processor_id: String identifier, or list of string identifiers,
                determining which processors may be used when sampling.
            gate_set: Determines how to serialize circuits when requesting
                samples.
        """
        self._processor_ids = ([processor_id] if isinstance(processor_id, str)
                               else processor_id)
        self._gate_set = gate_set
        self._engine = engine

    def run_sweep(
            self,
            program: Union['cirq.Circuit', 'cirq.google.EngineProgram'],
            params: 'cirq.Sweepable',
            repetitions: int = 1,
    ) -> List['cirq.TrialResult']:
        if isinstance(program, engine.EngineProgram):
            job = program.run_sweep(params=params,
                                    repetitions=repetitions,
                                    processor_ids=self._processor_ids)
        else:
            job = self._engine.run_sweep(program=cast(circuits.Circuit,
                                                      program),
                                         params=params,
                                         repetitions=repetitions,
                                         processor_ids=self._processor_ids,
                                         gate_set=self._gate_set)
        return job.results()

    @property
    def engine(self) -> 'cirq.google.Engine':
        return self._engine


def get_engine_sampler(processor_id: str, gate_set_name: str,
                       project_id: Optional[str] = None) \
        -> 'cirq.google.QuantumEngineSampler':
    """Get an EngineSampler assuming some sensible defaults.

    This uses the environment variable GOOGLE_CLOUD_PROJECT for the Engine
    project_id, unless set explicitly.

    Args:
        processor_id: Engine processor ID (from Cloud console or
            ``Engine.list_processors``).
        gate_set_name: One of ['sqrt_iswap', 'sycamore'].
            See `cirq.google.NAMED_GATESETS`.
        project_id: Optional explicit Google Cloud project id. Otherwise,
            this defaults to the environment variable GOOGLE_CLOUD_PROJECT.
            By using an environment variable, you can avoid hard-coding
            personal project IDs in shared code.

    Returns:
        A `QuantumEngineSampler` instance.

    Raises:
         ValueError: If the supplied gate set is not a supported gate set name.
         EnvironmentError: If no project_id is specified and the environment
            variable GOOGLE_CLOUD_PROJECT is not set.
    """
    try:
        gate_set = gate_sets.NAMED_GATESETS[gate_set_name]
    except KeyError:
        raise ValueError(f"Please use one of the following gateset names: "
                         f"{sorted(gate_sets.NAMED_GATESETS.keys())}")

    return engine.get_engine(project_id).sampler(processor_id=processor_id,
                                                 gate_set=gate_set)
