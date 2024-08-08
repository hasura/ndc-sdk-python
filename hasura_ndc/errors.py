from typing import Optional, Dict, Any

class ConnectorError(Exception):
    def __init__(self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.details = details or {}

class BadRequest(ConnectorError):
    """The request did not match the data connector's expectation based on this specification"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(400, message, details)

class Forbidden(ConnectorError):
    """The request could not be handled because a permission check failed - for example, a mutation might fail because a check constraint was not met"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(403, message, details)

class Conflict(ConnectorError):
    """The request could not be handled because it would create a conflicting state for the data source - for example, a mutation might fail because a foreign key constraint was not met"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(409, message, details)

class UnprocessableContent(ConnectorError):
    """The request could not be handled because, while the request was well-formed, it was not semantically correct. For example, a value for a custom scalar type was provided, but with an incorrect type"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(422, message, details)

class InternalServerError(ConnectorError):
    """The request could not be handled because of an error on the server"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(500, message, details)

class NotSupported(ConnectorError):
    """The request could not be handled because it relies on an unsupported capability. Note: this ought to indicate an error on the caller side, since the caller should not generate requests which are incompatible with the indicated capabilities"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(501, message, details)

class BadGateway(ConnectorError):
    """The request could not be handled because an upstream service was unavailable or returned an unexpected response, e.g., a connection to a database server failed"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(502, message, details)