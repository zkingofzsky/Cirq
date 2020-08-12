# Copyright 2020 The Cirq Developers
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

import datetime
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence, TypeVar, Tuple
import warnings

from google.api_core.exceptions import GoogleAPICallError, NotFound
from google.protobuf.timestamp_pb2 import Timestamp

from cirq.google.engine.client import quantum
from cirq.google.engine.client.quantum import types as qtypes

_R = TypeVar('_R')


class EngineException(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


RETRYABLE_ERROR_CODES = [500, 503]


class EngineClient:
    """Client for the Quantum Engine API that deals with the engine protos and
    the gRPC client but not cirq protos or objects. All users are likely better
    served by using the Engine, EngineProgram, EngineJob, EngineProcessor, and
    Calibration objects instead of using this directly.
    """

    def __init__(
            self,
            service_args: Optional[Dict] = None,
            verbose: Optional[bool] = None,
            max_retry_delay_seconds: int = 3600  # 1 hour
    ) -> None:
        """Engine service client.

        Args:
            service_args: A dictionary of arguments that can be used to
                configure options on the underlying gRPC client.
            verbose: Suppresses stderr messages when set to False. Default is
                true.
            max_retry_delay_seconds: The maximum number of seconds to retry when
                a retryable error code is returned.
        """
        self.max_retry_delay_seconds = max_retry_delay_seconds
        if verbose is None:
            verbose = True
        self.verbose = verbose

        if not service_args:
            service_args = {}

        # Suppress warnings about using Application Default Credentials.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.grpc_client = quantum.QuantumEngineServiceClient(
                **service_args)

    @staticmethod
    def _project_name(project_id: str) -> str:
        return 'projects/%s' % project_id

    @staticmethod
    def _program_name_from_ids(project_id: str, program_id: str) -> str:
        return 'projects/%s/programs/%s' % (project_id, program_id)

    @staticmethod
    def _job_name_from_ids(project_id: str, program_id: str,
                           job_id: str) -> str:
        return 'projects/%s/programs/%s/jobs/%s' % (project_id, program_id,
                                                    job_id)

    @staticmethod
    def _processor_name_from_ids(project_id: str, processor_id: str) -> str:
        return 'projects/%s/processors/%s' % (project_id, processor_id)

    @staticmethod
    def _calibration_name_from_ids(project_id: str, processor_id: str,
                                   calibration_time_seconds: int) -> str:
        return 'projects/%s/processors/%s/calibrations/%d' % (
            project_id, processor_id, calibration_time_seconds)

    @staticmethod
    def _reservation_name_from_ids(project_id: str, processor_id: str,
                                   reservation_id: str) -> str:
        return 'projects/%s/processors/%s/reservations/%s' % (
            project_id, processor_id, reservation_id)

    @staticmethod
    def _ids_from_program_name(program_name: str) -> Tuple[str, str]:
        parts = program_name.split('/')
        return parts[1], parts[3]

    @staticmethod
    def _ids_from_job_name(job_name: str) -> Tuple[str, str, str]:
        parts = job_name.split('/')
        return parts[1], parts[3], parts[5]

    @staticmethod
    def _ids_from_processor_name(processor_name: str) -> Tuple[str, str]:
        parts = processor_name.split('/')
        return parts[1], parts[3]

    @staticmethod
    def _ids_from_calibration_name(calibration_name: str
                                  ) -> Tuple[str, str, int]:
        parts = calibration_name.split('/')
        return parts[1], parts[3], int(parts[5])

    def _make_request(self, request: Callable[[], _R]) -> _R:
        # Start with a 100ms retry delay with exponential backoff to
        # max_retry_delay_seconds
        current_delay = 0.1

        while True:
            try:
                return request()
            except GoogleAPICallError as err:
                message = err.message
                # Raise RuntimeError for exceptions that are not retryable.
                # Otherwise, pass through to retry.
                if err.code.value not in RETRYABLE_ERROR_CODES:
                    raise EngineException(message) from err

            current_delay *= 2
            if current_delay > self.max_retry_delay_seconds:
                raise TimeoutError(
                    'Reached max retry attempts for error: {}'.format(message))
            if self.verbose:
                print(message, file=sys.stderr)
                print('Waiting ',
                      current_delay,
                      'seconds before retrying.',
                      file=sys.stderr)
            time.sleep(current_delay)

    def create_program(
            self,
            project_id: str,
            program_id: Optional[str],
            code: qtypes.any_pb2.Any,
            description: Optional[str] = None,
            labels: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, qtypes.QuantumProgram]:
        """Creates a Quantum Engine program.

        Args:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            code: Properly serialized program code.
            description: An optional description to set on the program.
            labels: Optional set of labels to set on the program.

        Returns:
            Tuple of created program id and program
        """

        parent_name = self._project_name(project_id)
        program_name = self._program_name_from_ids(
            project_id, program_id) if program_id else ''
        request = qtypes.QuantumProgram(name=program_name, code=code)
        if description:
            request.description = description
        if labels:
            request.labels.update(labels)

        program = self._make_request(lambda: self.grpc_client.
                                     create_quantum_program(
                                         parent_name, request, False))
        return self._ids_from_program_name(program.name)[1], program

    def get_program(self, project_id: str, program_id: str,
                    return_code: bool) -> qtypes.QuantumProgram:
        """Returns a previously created quantum program.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            return_code: If True returns the serialized program code.
        """
        return self._make_request(lambda: self.grpc_client.get_quantum_program(
            self._program_name_from_ids(project_id, program_id), return_code))

    def set_program_description(self, project_id: str, program_id: str,
                                description: str) -> qtypes.QuantumProgram:
        """Sets the description for a previously created quantum program.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            description: The new program description.

        Returns:
            The updated quantum program.
        """
        program_resource_name = self._program_name_from_ids(
            project_id, program_id)
        return self._make_request(
            lambda: self.grpc_client.update_quantum_program(
                program_resource_name,
                qtypes.QuantumProgram(name=program_resource_name,
                                      description=description),
                qtypes.field_mask_pb2.FieldMask(paths=['description'])))

    def _set_program_labels(self, project_id: str, program_id: str,
                            labels: Dict[str, str],
                            fingerprint: str) -> qtypes.QuantumProgram:
        program_resource_name = self._program_name_from_ids(
            project_id, program_id)
        return self._make_request(
            lambda: self.grpc_client.update_quantum_program(
                program_resource_name,
                qtypes.QuantumProgram(name=program_resource_name,
                                      labels=labels,
                                      label_fingerprint=fingerprint),
                qtypes.field_mask_pb2.FieldMask(paths=['labels'])))

    def set_program_labels(self, project_id: str, program_id: str,
                           labels: Dict[str, str]) -> qtypes.QuantumProgram:
        """Sets (overwriting) the labels for a previously created quantum
        program.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            labels: The entire set of new program labels.

        Returns:
            The updated quantum program.
        """
        program = self.get_program(project_id, program_id, False)
        return self._set_program_labels(project_id, program_id, labels,
                                        program.label_fingerprint)

    def add_program_labels(self, project_id: str, program_id: str,
                           labels: Dict[str, str]) -> qtypes.QuantumProgram:
        """Adds new labels to a previously created quantum program.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            labels: New labels to add to the existing program labels.

        Returns:
            The updated quantum program.
        """
        program = self.get_program(project_id, program_id, False)
        old_labels = program.labels
        new_labels = dict(old_labels)
        new_labels.update(labels)
        if new_labels != old_labels:
            fingerprint = program.label_fingerprint
            return self._set_program_labels(project_id, program_id, new_labels,
                                            fingerprint)
        return program

    def remove_program_labels(self, project_id: str, program_id: str,
                              label_keys: List[str]) -> qtypes.QuantumProgram:
        """Removes labels with given keys from the labels of a previously
        created quantum program.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            label_keys: Label keys to remove from the existing program labels.

        Returns:
            The updated quantum program.
        """
        program = self.get_program(project_id, program_id, False)
        old_labels = program.labels
        new_labels = dict(old_labels)
        for key in label_keys:
            new_labels.pop(key, None)
        if new_labels != old_labels:
            fingerprint = program.label_fingerprint
            return self._set_program_labels(project_id, program_id, new_labels,
                                            fingerprint)
        return program

    def delete_program(self,
                       project_id: str,
                       program_id: str,
                       delete_jobs: bool = False) -> None:
        """Deletes a previously created quantum program.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            delete_jobs: If True will delete all the program's jobs, other this
                will fail if the program contains any jobs.
        """
        self._make_request(lambda: self.grpc_client.delete_quantum_program(
            self._program_name_from_ids(project_id, program_id), delete_jobs))

    def create_job(
            self,
            project_id: str,
            program_id: str,
            job_id: Optional[str],
            processor_ids: Sequence[str],
            run_context: qtypes.any_pb2.Any,
            priority: Optional[int] = None,
            description: Optional[str] = None,
            labels: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, qtypes.QuantumJob]:
        """Creates and runs a job on Quantum Engine.

        Args:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
            run_context: Properly serialized run context.
            processor_ids: List of processor id for running the program.
            priority: Optional priority to run at, 0-1000.
            description: Optional description to set on the job.
            labels: Optional set of labels to set on the job.

        Returns:
            Tuple of created job id and job
        """
        # Check program to run and program parameters.
        if priority and not 0 <= priority < 1000:
            raise ValueError('priority must be between 0 and 1000')

        # Create job.
        job_name = self._job_name_from_ids(project_id, program_id,
                                           job_id) if job_id else ''
        request = qtypes.QuantumJob(
            name=job_name,
            scheduling_config=qtypes.SchedulingConfig(
                processor_selector=qtypes.SchedulingConfig.ProcessorSelector(
                    processor_names=[
                        self._processor_name_from_ids(project_id, processor_id)
                        for processor_id in processor_ids
                    ])),
            run_context=run_context)
        if priority:
            request.scheduling_config.priority = priority
        if description:
            request.description = description
        if labels:
            request.labels.update(labels)
        job = self._make_request(lambda: self.grpc_client.create_quantum_job(
            self._program_name_from_ids(project_id, program_id), request, False)
                                )
        return self._ids_from_job_name(job.name)[2], job

    def get_job(self, project_id: str, program_id: str, job_id: str,
                return_run_context: bool) -> qtypes.QuantumJob:
        """Returns a previously created job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
        """
        return self._make_request(lambda: self.grpc_client.get_quantum_job(
            self._job_name_from_ids(project_id, program_id, job_id),
            return_run_context))

    def set_job_description(self, project_id: str, program_id: str, job_id: str,
                            description: str) -> qtypes.QuantumJob:
        """Sets the description for a previously created quantum job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
            description: The new job description.

        Returns:
            The updated quantum job.
        """
        job_resource_name = self._job_name_from_ids(project_id, program_id,
                                                    job_id)
        return self._make_request(lambda: self.grpc_client.update_quantum_job(
            job_resource_name,
            qtypes.QuantumJob(name=job_resource_name, description=description),
            qtypes.field_mask_pb2.FieldMask(paths=['description'])))

    def _set_job_labels(self, project_id: str, program_id: str, job_id: str,
                        labels: Dict[str, str],
                        fingerprint: str) -> qtypes.QuantumJob:
        job_resource_name = self._job_name_from_ids(project_id, program_id,
                                                    job_id)
        return self._make_request(lambda: self.grpc_client.update_quantum_job(
            job_resource_name,
            qtypes.QuantumJob(name=job_resource_name,
                              labels=labels,
                              label_fingerprint=fingerprint),
            qtypes.field_mask_pb2.FieldMask(paths=['labels'])))

    def set_job_labels(self, project_id: str, program_id: str, job_id: str,
                       labels: Dict[str, str]) -> qtypes.QuantumJob:
        """Sets (overwriting) the labels for a previously created quantum job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
            labels: The entire set of new job labels.

        Returns:
            The updated quantum job.
        """
        job = self.get_job(project_id, program_id, job_id, False)
        return self._set_job_labels(project_id, program_id, job_id, labels,
                                    job.label_fingerprint)

    def add_job_labels(self, project_id: str, program_id: str, job_id: str,
                       labels: Dict[str, str]) -> qtypes.QuantumJob:
        """Adds new labels to a previously created quantum job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
            labels: New labels to add to the existing job labels.

        Returns:
            The updated quantum job.
        """
        job = self.get_job(project_id, program_id, job_id, False)
        old_labels = job.labels
        new_labels = dict(old_labels)
        new_labels.update(labels)
        if new_labels != old_labels:
            fingerprint = job.label_fingerprint
            return self._set_job_labels(project_id, program_id, job_id,
                                        new_labels, fingerprint)
        return job

    def remove_job_labels(self, project_id: str, program_id: str, job_id: str,
                          label_keys: List[str]) -> qtypes.QuantumJob:
        """Removes labels with given keys from the labels of a previously
        created quantum job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
            label_keys: Label keys to remove from the existing job labels.

        Returns:
            The updated quantum job.
        """
        job = self.get_job(project_id, program_id, job_id, False)
        old_labels = job.labels
        new_labels = dict(old_labels)
        for key in label_keys:
            new_labels.pop(key, None)
        if new_labels != old_labels:
            fingerprint = job.label_fingerprint
            return self._set_job_labels(project_id, program_id, job_id,
                                        new_labels, fingerprint)
        return job

    def delete_job(self, project_id: str, program_id: str, job_id: str) -> None:
        """Deletes a previously created quantum job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
        """
        self._make_request(lambda: self.grpc_client.delete_quantum_job(
            self._job_name_from_ids(project_id, program_id, job_id)))

    def cancel_job(self, project_id: str, program_id: str, job_id: str) -> None:
        """Cancels the given job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.
        """
        self._make_request(lambda: self.grpc_client.cancel_quantum_job(
            self._job_name_from_ids(project_id, program_id, job_id)))

    def get_job_results(self, project_id: str, program_id: str,
                        job_id: str) -> qtypes.QuantumResult:
        """Returns the results of a completed job.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            program_id: Unique ID of the program within the parent project.
            job_id: Unique ID of the job within the parent program.

        Returns:
            The quantum result.
        """
        return self._make_request(lambda: self.grpc_client.get_quantum_result(
            self._job_name_from_ids(project_id, program_id, job_id)))

    def list_processors(self, project_id: str) -> List[qtypes.QuantumProcessor]:
        """Returns a list of Processors that the user has visibility to in the
        current Engine project. The names of these processors are used to
        identify devices when scheduling jobs and gathering calibration metrics.

        Params:
            project_id: A project_id of the parent Google Cloud Project.

        Returns:
            A list of metadata of each processor.
        """
        response = self._make_request(
            lambda: self.grpc_client.list_quantum_processors(
                self._project_name(project_id), filter_=''))
        return list(response)

    def get_processor(self, project_id: str,
                      processor_id: str) -> qtypes.QuantumProcessor:
        """Returns a quantum processor.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.

        Returns:
            The quantum processor.
        """
        return self._make_request(
            lambda: self.grpc_client.get_quantum_processor(
                self._processor_name_from_ids(project_id, processor_id)))

    def list_calibrations(self,
                          project_id: str,
                          processor_id: str,
                          filter_str: str = ''
                         ) -> List[qtypes.QuantumCalibration]:
        """Returns a list of quantum calibrations.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            filter: Filter string current only supports 'timestamp' with values
              of epoch time in seconds or short string 'yyyy-MM-dd' or long
              string 'yyyy-MM-dd HH:mm:ss.SSS' both in UTC. For example:
                'timestamp > 1577960125 AND timestamp <= 1578241810'
                'timestamp > 2020-01-02 AND timestamp <= 2020-01-05'
                'timestamp > "2020-01-02 10:15:25.000" AND timestamp <=
                  "2020-01-05 16:30:10.456"'

        Returns:
            A list of calibrations.
        """
        response = self._make_request(
            lambda: self.grpc_client.list_quantum_calibrations(
                self._processor_name_from_ids(project_id, processor_id),
                filter_=filter_str))
        return list(response)

    def get_calibration(self, project_id: str, processor_id: str,
                        calibration_timestamp_seconds: int
                       ) -> qtypes.QuantumCalibration:
        """Returns a quantum calibration.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            calibration_timestamp_seconds: The timestamp of the calibration in
                seconds.

        Returns:
            The quantum calibration.
        """
        return self._make_request(
            lambda: self.grpc_client.get_quantum_calibration(
                self._calibration_name_from_ids(project_id, processor_id,
                                                calibration_timestamp_seconds)))

    def get_current_calibration(self, project_id: str, processor_id: str
                               ) -> Optional[qtypes.QuantumCalibration]:
        """Returns the current quantum calibration for a processor if it has
        one.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.

        Returns:
            The quantum calibration or None if there is no current calibration.
        """
        try:
            return self._make_request(
                lambda: self.grpc_client.get_quantum_calibration(
                    self._processor_name_from_ids(project_id, processor_id) +
                    '/calibrations/current'))
        except EngineException as err:
            if isinstance(err.__cause__, NotFound):
                return None
            raise

    def create_reservation(self,
                           project_id: str,
                           processor_id: str,
                           start: datetime.datetime,
                           end: datetime.datetime,
                           whitelisted_users: Optional[List[str]] = None):
        """Creates a quantum reservation and returns the created object.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            reservation_id: Unique ID of the reservation in the parent project,
                or None if the engine should generate an id
            start: the starting time of the reservation as a datetime object
            end: the ending time of the reservation as a datetime object
            whitelisted_users: a list of emails that can use the reservation.
        """
        parent = self._processor_name_from_ids(project_id, processor_id)
        reservation = qtypes.QuantumReservation(
            name='',
            start_time=Timestamp(seconds=int(start.timestamp())),
            end_time=Timestamp(seconds=int(end.timestamp())),
        )
        if whitelisted_users:
            reservation.whitelisted_users.extend(whitelisted_users)
        return self._make_request(
            lambda: self.grpc_client.create_quantum_reservation(
                parent=parent, quantum_reservation=reservation))

    def cancel_reservation(self, project_id: str, processor_id: str,
                           reservation_id: str):
        """ Cancels a quantum reservation.

        This action is only valid if the associated [QuantumProcessor]
        schedule not been frozen. Otherwise, delete_reservation should
        be used.

        The reservation will be truncated to end at the time when the request is
        serviced and any remaining time will be made available as an open swim
        period. This action will only succeed if the reservation has not yet
        ended and is within the processor's freeze window. If the reservation
        has already ended or is beyond the processor's freeze window, then the
        call will return an error.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            reservation_id: Unique ID of the reservation in the parent project,
        """
        name = self._reservation_name_from_ids(project_id, processor_id,
                                               reservation_id)
        return self._make_request(lambda: self.grpc_client.
                                  cancel_quantum_reservation(name=name))

    def delete_reservation(self, project_id: str, processor_id: str,
                           reservation_id: str):
        """ Deletes a quantum reservation.

        This action is only valid if the associated [QuantumProcessor]
        schedule has not been frozen.  Otherwise, cancel_reservation
        should be used.

        If the reservation has already ended or is within the processor's
        freeze window, then the call will return a `FAILED_PRECONDITION` error.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            reservation_id: Unique ID of the reservation in the parent project,
        """
        name = self._reservation_name_from_ids(project_id, processor_id,
                                               reservation_id)
        return self._make_request(lambda: self.grpc_client.
                                  delete_quantum_reservation(name=name))

    def get_reservation(self, project_id: str, processor_id: str,
                        reservation_id: str):
        """ Gets a quantum reservation from the engine.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            reservation_id: Unique ID of the reservation in the parent project,
        """
        try:
            name = self._reservation_name_from_ids(project_id, processor_id,
                                                   reservation_id)
            return self._make_request(lambda: self.grpc_client.
                                      get_quantum_reservation(name=name))
        except EngineException as err:
            if isinstance(err.__cause__, NotFound):
                return None
            raise

    def list_reservations(self,
                          project_id: str,
                          processor_id: str,
                          filter_str: str = ''
                         ) -> List[qtypes.QuantumReservation]:
        """Returns a list of quantum reservations.

        Only reservations owned by this project will be returned.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            filter: A string for filtering quantum reservations.
                The fields eligible for filtering are start_time and end_time
                Examples:
                    `start_time >= 1584385200`: Reservation began on or after
                        the epoch time Mar 16th, 7pm GMT.
                    `end_time >= "2017-01-02 15:21:15.142"`: Reservation ends on
                        or after Jan 2nd 2017 15:21:15.142

        Returns:
            A list of QuantumReservation objects.
        """
        response = self._make_request(
            lambda: self.grpc_client.list_quantum_reservations(
                self._processor_name_from_ids(project_id, processor_id),
                filter_=filter_str))

        return list(response)

    def update_reservation(self,
                           project_id: str,
                           processor_id: str,
                           reservation_id: str,
                           start: Optional[datetime.datetime] = None,
                           end: Optional[datetime.datetime] = None,
                           whitelisted_users: Optional[List[str]] = None):
        """Updates a quantum reservation.

        This will update a quantum reservation's starting time, ending time,
        and list of whitelisted users.  If any field is not filled, it will
        not be updated.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            reservation_id: Unique ID of the reservation in the parent project,
            start: the new starting time of the reservation as a datetime object
            end: the new ending time of the reservation as a datetime object
            whitelisted_users: a list of emails that can use the reservation.
                The empty list, [], will clear the whitelisted_users while None
                will leave the value unchanged.
        """
        name = self._reservation_name_from_ids(
            project_id, processor_id, reservation_id) if reservation_id else ''

        reservation = qtypes.QuantumReservation(name=name,)
        paths = []
        if start:
            reservation.start_time.seconds = int(start.timestamp())
            paths.append('start_time')
        if end:
            reservation.end_time.seconds = int(end.timestamp())
            paths.append('end_time')
        if whitelisted_users != None:
            reservation.whitelisted_users.extend(whitelisted_users)
            paths.append('whitelisted_users')

        return self._make_request(
            lambda: self.grpc_client.update_quantum_reservation(
                name=name,
                quantum_reservation=reservation,
                update_mask=qtypes.field_mask_pb2.FieldMask(paths=paths)))

    def list_time_slots(self,
                        project_id: str,
                        processor_id: str,
                        filter_str: str = '') -> List[qtypes.QuantumTimeSlot]:
        """Returns a list of quantum time slots on a processor.

        Params:
            project_id: A project_id of the parent Google Cloud Project.
            processor_id: The processor unique identifier.
            filter:  A string expression for filtering the quantum
                time slots returned by the list command. The fields
                eligible for filtering are `start_time`, `end_time`.

        Returns:
            A list of QuantumTimeSlot objects.
        """
        response = self._make_request(
            lambda: self.grpc_client.list_quantum_time_slots(
                self._processor_name_from_ids(project_id, processor_id),
                filter_=filter_str))
        return list(response)
