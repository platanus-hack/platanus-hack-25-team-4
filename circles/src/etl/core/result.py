"""
Result Monad - Railway-Oriented Programming for type-safe error handling.

This module implements a Result type that forces explicit error handling
without relying on exceptions. It follows the Result/Either pattern from
functional programming.

Usage:
    # Returning success
    result = Result.ok(some_value)

    # Returning error
    result = Result.error(some_error)

    # Checking status
    if result.is_ok:
        value = result.value
    else:
        error = result.error_value
"""

from dataclasses import dataclass
from typing import Callable, Generic, Optional, TypeVar, Union

T = TypeVar("T")  # Success type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Mapped success type


@dataclass
class Result(Generic[T, E]):
    """
    Represents a computation that may succeed with value T or fail with error E.

    This is a monad implementation that forces explicit error handling.
    Never raises exceptions for business logic errors.
    """

    _value: Union[T, E]
    _is_error: bool

    @staticmethod
    def ok(value: T) -> "Result[T, E]":
        """
        Create a successful Result.

        Args:
            value: The success value

        Returns:
            Result[T, E]: A successful Result containing the value
        """
        return Result(_value=value, _is_error=False)

    @staticmethod
    def error(error: E) -> "Result[T, E]":
        """
        Create a failed Result.

        Args:
            error: The error value

        Returns:
            Result[T, E]: A failed Result containing the error
        """
        return Result(_value=error, _is_error=True)

    @property
    def is_ok(self) -> bool:
        """Check if Result is successful."""
        return not self._is_error

    @property
    def is_error(self) -> bool:
        """Check if Result is a failure."""
        return self._is_error

    @property
    def value(self) -> T:
        """
        Get the success value. Raises if this is an error.

        Returns:
            T: The success value

        Raises:
            ValueError: If Result is an error
        """
        if self._is_error:
            raise ValueError(f"Cannot get value from error result: {self._value}")
        return self._value

    @property
    def error_value(self) -> E:
        """
        Get the error value. Raises if this is success.

        Returns:
            E: The error value

        Raises:
            ValueError: If Result is a success
        """
        if not self._is_error:
            raise ValueError(f"Cannot get error from ok result")
        return self._value

    def map(self, func: Callable[[T], U]) -> "Result[U, E]":
        """
        Transform the success value if Result is ok.

        Args:
            func: Function to apply to success value

        Returns:
            Result[U, E]: Result with transformed value, or same error
        """
        if self._is_error:
            return Result(_value=self._value, _is_error=True)
        try:
            return Result.ok(func(self._value))
        except Exception as e:
            return Result.error(e)  # type: ignore

    def bind(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """
        Chain operations that return Result (monadic bind).

        Args:
            func: Function that takes success value and returns Result

        Returns:
            Result[U, E]: Result from func or same error
        """
        if self._is_error:
            return Result(_value=self._value, _is_error=True)
        try:
            return func(self._value)
        except Exception as e:
            return Result.error(e)  # type: ignore

    def map_error(self, func: Callable[[E], E]) -> "Result[T, E]":
        """
        Transform the error value if Result is error.

        Args:
            func: Function to apply to error value

        Returns:
            Result[T, E]: Result with transformed error or same value
        """
        if self._is_error:
            try:
                return Result.error(func(self._value))
            except Exception as e:
                return Result.error(e)  # type: ignore
        return self

    def unwrap_or(self, default: T) -> T:
        """
        Get success value or return default if error.

        Args:
            default: Default value if Result is error

        Returns:
            T: Success value or default
        """
        if self._is_error:
            return default
        return self._value

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        """
        Get success value or compute from error.

        Args:
            func: Function to apply to error value

        Returns:
            T: Success value or computed value
        """
        if self._is_error:
            return func(self._value)
        return self._value

    def and_then(self, func: Callable[[], "Result[U, E]"]) -> "Result[U, E]":
        """
        Execute func only if this Result is ok, combining results.

        Args:
            func: Function that returns another Result

        Returns:
            Result[U, E]: Combined result
        """
        if self._is_error:
            return Result(_value=self._value, _is_error=True)
        return func()

    def __repr__(self) -> str:
        """String representation."""
        if self._is_error:
            return f"Result.error({self._value!r})"
        return f"Result.ok({self._value!r})"


class ProcessingError(Exception):
    """
    Standard error type for ETL processing operations.

    Attributes:
        message: Human-readable error message
        error_type: Category of error (validation, processing, persistence, etc.)
        details: Additional context about the error
    """

    def __init__(
        self,
        message: str,
        error_type: str = "processing_error",
        details: Optional[dict] = None,
    ):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}"

    def __repr__(self) -> str:
        return f"ProcessingError({self.error_type!r}, {self.message!r})"
