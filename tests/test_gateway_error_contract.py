from __future__ import annotations

import copy
import pickle

import pytest

from gateway.errors import GatewayError


def make_error() -> GatewayError:
    return GatewayError("RATE_LIMITED", "Too many requests", 429, True)


def assert_same(a: GatewayError, b: GatewayError) -> None:
    assert (a.code, a.message, a.status_code, a.retryable) == (
        b.code,
        b.message,
        b.status_code,
        b.retryable,
    )
    assert a.args == b.args


def test_gateway_error_pickle_round_trip():
    error = make_error()
    restored = pickle.loads(pickle.dumps(error))
    assert isinstance(restored, GatewayError)
    assert_same(error, restored)


def test_gateway_error_copy_and_deepcopy():
    error = make_error()
    assert_same(error, copy.copy(error))
    assert_same(error, copy.deepcopy(error))


@pytest.mark.parametrize("field", ["code", "message", "status_code", "retryable"])
def test_gateway_error_fields_cannot_be_reassigned_or_deleted(field):
    error = make_error()
    before = getattr(error, field)
    with pytest.raises(AttributeError):
        setattr(error, field, "changed")
    with pytest.raises(AttributeError):
        delattr(error, field)
    assert getattr(error, field) == before


def test_gateway_error_non_contract_attributes_still_work():
    error = make_error()
    error.__traceback__ = None
    error.note = "extra"
    del error.note
