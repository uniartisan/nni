# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations

from typing import Any, cast

from .runtime.env_vars import trial_env_vars
from .runtime.trial_command_channel import get_default_trial_command_channel
from .typehint import Parameters, TrialMetric, ParameterRecord

__all__ = [
    'get_next_parameter',
    'get_next_parameters',
    'get_current_parameter',
    'report_intermediate_result',
    'report_final_result',
    'get_experiment_id',
    'get_trial_id',
    'get_sequence_id'
]


_params: ParameterRecord | None = None
_experiment_id = trial_env_vars.NNI_EXP_ID or 'STANDALONE'
_trial_id = trial_env_vars.NNI_TRIAL_JOB_ID or 'STANDALONE'
_sequence_id = int(trial_env_vars.NNI_TRIAL_SEQ_ID) if trial_env_vars.NNI_TRIAL_SEQ_ID is not None else 0


def get_next_parameter() -> Parameters:
    """
    Get the hyperparameters generated by tuner.

    Each trial should and should only invoke this function once.
    Otherwise the behavior is undefined.

    Examples
    --------
    Assuming the :doc:`search space </hpo/search_space>` is:

    .. code-block::

        {
            'activation': {'_type': 'choice', '_value': ['relu', 'tanh', 'sigmoid']},
            'learning_rate': {'_type': 'loguniform', '_value': [0.0001, 0.1]}
        }

    Then this function might return:

    .. code-block::

        {
            'activation': 'relu',
            'learning_rate': 0.02
        }

    Returns
    -------
    :class:`~nni.typehint.Parameters`
        A hyperparameter set sampled from search space.
    """
    global _params
    _params = get_default_trial_command_channel().receive_parameter()
    if _params is None:
        return None  # type: ignore
    return _params['parameters']

def get_next_parameters() -> Parameters:
    """
    Alias of :func:`get_next_parameter`
    """
    return get_next_parameter()

def get_current_parameter(tag: str | None = None) -> Any:
    global _params
    if _params is None:
        return None
    if tag is None:
        return _params['parameters']
    return _params['parameters'][tag]

def get_experiment_id() -> str:
    """
    Return experiment ID.
    """
    return _experiment_id

def get_trial_id() -> str:
    """
    Return unique ID of the trial that is current running.

    This is shown as "ID" in the web portal's trial table.
    """
    return _trial_id

def get_sequence_id() -> int:
    """
    Return sequence nubmer of the trial that is currently running.

    This is shown as "Trial No." in the web portal's trial table.
    """
    return _sequence_id

_intermediate_seq = 0


def overwrite_intermediate_seq(value: int) -> None:
    assert isinstance(value, int)
    global _intermediate_seq
    _intermediate_seq = value


def report_intermediate_result(metric: TrialMetric | dict[str, Any]) -> None:
    """
    Reports intermediate result to NNI.

    ``metric`` should either be a float, or a dict that ``metric['default']`` is a float.

    If ``metric`` is a dict, ``metric['default']`` will be used by tuner,
    and other items can be visualized with web portal.

    Typically ``metric`` is per-epoch accuracy or loss.

    Parameters
    ----------
    metric : :class:`~nni.typehint.TrialMetric`
        The intermeidate result.
    """
    global _intermediate_seq
    assert _params or trial_env_vars.NNI_PLATFORM is None, \
        'nni.get_next_parameter() needs to be called before report_intermediate_result'
    get_default_trial_command_channel().send_metric(
        parameter_id=_params['parameter_id'] if _params else None,
        trial_job_id=trial_env_vars.NNI_TRIAL_JOB_ID,
        type='PERIODICAL',
        sequence=_intermediate_seq,
        value=cast(TrialMetric, metric)
    )
    _intermediate_seq += 1

def report_final_result(metric: TrialMetric | dict[str, Any]) -> None:
    """
    Reports final result to NNI.

    ``metric`` should either be a float, or a dict that ``metric['default']`` is a float.

    If ``metric`` is a dict, ``metric['default']`` will be used by tuner,
    and other items can be visualized with web portal.

    Typically ``metric`` is the final accuracy or loss.

    Parameters
    ----------
    metric : :class:`~nni.typehint.TrialMetric`
        The final result.
    """
    assert _params or trial_env_vars.NNI_PLATFORM is None, \
        'nni.get_next_parameter() needs to be called before report_final_result'
    get_default_trial_command_channel().send_metric(
        parameter_id=_params['parameter_id'] if _params else None,
        trial_job_id=trial_env_vars.NNI_TRIAL_JOB_ID,
        type='FINAL',
        sequence=0,
        value=cast(TrialMetric, metric)
    )
