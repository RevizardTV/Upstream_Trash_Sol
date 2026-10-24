# razorpay.pyi
from typing import Any, Dict, Type

class SignatureVerificationError(Exception):
    ...

class _ErrorsNamespace:
    SignatureVerificationError: Type[SignatureVerificationError]

errors: _ErrorsNamespace

class Client:
    def __init__(self, auth: tuple[str, str]) -> None: ...
    
    class _Order:
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    order: _Order

    class _Utility:
        def verify_payment_signature(self, parameters: Dict[str, Any]) -> bool: ...
    utility: _Utility

    class _Contact:
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    contact: _Contact

    class _FundAccount:
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    fund_account: _FundAccount

    class _Payout:
        def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    payout: _Payout