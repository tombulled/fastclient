from dataclasses import dataclass
from typing import Any, Optional

from .enums import HTTPHeader

__all__ = (
    "NeoClientError",
    "DuplicateParameters",
    "IncompatiblePathParameters",
    "PreparationError",
    "CompositionError",
    "ResolutionError",
    "ConversionError",
    "NotAnOperationError",
    "ExpectedStatusCodeError",
    "ExpectedHeaderError",
    "ExpectedContentTypeError",
    "ServiceInitialisationError",
)


class NeoClientError(Exception):
    pass


class DuplicateParameters(Exception):
    pass


class IncompatiblePathParameters(Exception):
    pass


class PreparationError(Exception):
    pass


class CompositionError(Exception):
    pass


class ResolutionError(Exception):
    pass


@dataclass
class ConversionError(Exception):
    subject: str
    value: Any

    def __str__(self) -> str:
        return f"Cannot convert {self.subject} from type {type(self.value)}"


class NotAnOperationError(Exception):
    pass


class ExpectedStatusCodeError(Exception):
    pass


@dataclass
class ExpectedHeaderError(Exception):
    name: str
    value: Optional[str] = None
    expected_value: Optional[str] = None

    def __str__(self) -> str:
        if self.value is None:
            return f"Response missing expected header {str(self.name)!r}"

        return (
            f"Response header {str(self.name)!r} has incorrect value."
            f" Expected {self.expected_value!r}, got {self.value!r}"
        )


@dataclass
class ExpectedContentTypeError(Exception):
    expected: str
    actual: str

    def __str__(self) -> str:
        return (
            f"Response {HTTPHeader.CONTENT_TYPE} has incorrect value."
            f" Expected {self.expected!r}, got {self.actual!r}"
        )


class ServiceInitialisationError(Exception):
    pass
