"""Closed error codes suitable for later redacted transport adapters."""


class ContentStoreError(Exception):
    code = "content_store_error"

    def __init__(self, diagnostic="operation failed"):
        # Diagnostic strings must be fixed operation names, never exception/SQL/input text.
        super().__init__(self.code + ": " + diagnostic)


class InvalidInput(ContentStoreError):
    code = "invalid_input"


class UnverifiedBinding(ContentStoreError):
    code = "unverified_binding"


class IntegrityError(ContentStoreError):
    code = "integrity_error"


class Conflict(ContentStoreError):
    code = "conflict"


class Forbidden(ContentStoreError):
    code = "forbidden"


class NotFound(ContentStoreError):
    code = "not_found"


class Busy(ContentStoreError):
    code = "busy"


class Unavailable(ContentStoreError):
    code = "unavailable"
