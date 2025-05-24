from typing import Any, List, Optional, Sequence

from fastapi._compat import ErrorWrapper
from fastapi.exceptions import RequestErrorModel
from pydantic import TypeAdapter, ValidationError
from pydantic_core import ErrorDetails
from typing_extensions import Annotated, Doc

error_details_adapter = TypeAdapter(ErrorDetails)


def _normalize_to_validationerrors(errors: Sequence[Any]) -> List[ValidationError]:
    use_errors: List[Any] = []
    for error in errors:
        if isinstance(error, ErrorWrapper):
            ve = ValidationError(  # type: ignore[call-arg]
                errors=[error], model=RequestErrorModel
            )
            use_errors.append(ve)
        elif isinstance(error, list):
            use_errors.extend(_normalize_to_validationerrors(error))
        else:
            is_ed = False
            try:
                ed = error_details_adapter.validate_python(error)
                is_ed = True
            except ValidationError:
                pass
            if is_ed:
                ve = ValidationError.from_exception_data(  # type: ignore[call-arg]
                    "", [ed]
                )
                use_errors.append(ve)
            else:
                use_errors.append(error)
    return use_errors


class RequestErrors:
    """
    This is a special class that you can use as a dependency anywhere
    in the dependency chain to collect errors raised therein.

    The use of this class implies `raise_from_deps`=`False` for the
    dependency chain.

    Parameters must be optional for control to be passed to the path
    operation function, otherwise ValidationErrors will escape.
    """

    def __init__(
        self,
        errors: Annotated[
            Optional[Sequence[Any]],
            Doc(
                """
                This will be filled by FastAPI.
                """
            ),
        ] = None,
    ):
        self._errors: Annotated[
            List[ValidationError],
            Doc(
                """
                The list of all the exceptions raised by dependencies.
                """
            ),
        ] = _normalize_to_validationerrors(errors)

    def errors(self):
        return [ed for e in self._errors for ed in e.errors(include_url=False)]
