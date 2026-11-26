from __future__ import annotations


class GatewayError(Exception):
    _IMMUTABLE_FIELDS = frozenset({"code", "message", "status_code", "retryable"})

    def __init__(self, code: str, message: str, status_code: int, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable

    def __setattr__(self, name: str, value: object) -> None:
        if name in self._IMMUTABLE_FIELDS and hasattr(self, name):
            raise AttributeError(f"{name} is immutable")
        super().__setattr__(name, value)

    def public(self, correlation_id: str) -> dict[str, object]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "correlation_id": correlation_id,
                "retryable": self.retryable,
            }
        }
