from typing import List, Optional
from pydantic import ValidationError
from typing_extensions import Annotated, Doc


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
            Optional[List[ValidationError]],
            Doc(
                """
                This will be filled by FastAPI.
                """
            ),
        ] = None,
    ):
        self.errors: Annotated[
            List[ValidationError],
            Doc(
                """
                The list of all the exceptions raised by dependencies.
                """
            ),
        ] = errors or []