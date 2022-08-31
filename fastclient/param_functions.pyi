from typing import Any, Callable, Optional, TypeVar, overload

T = TypeVar("T")

@overload
def Header(alias: Optional[str] = None, *, required: bool = False) -> Any: ...
@overload
def Header(alias: Optional[str] = None, *, default: T, required: bool = False) -> T: ...
@overload
def Header(
    alias: Optional[str] = None,
    *,
    default_factory: Callable[[], T],
    required: bool = False,
) -> T: ...
@overload
def Query(alias: Optional[str] = None, *, required: bool = False) -> Any: ...
@overload
def Query(alias: Optional[str] = None, *, default: T, required: bool = False) -> T: ...
@overload
def Query(
    alias: Optional[str] = None,
    *,
    default_factory: Callable[[], T],
    required: bool = False,
) -> T: ...
@overload
def Path(alias: Optional[str] = None, *, required: bool = False) -> Any: ...
@overload
def Path(alias: Optional[str] = None, *, default: T, required: bool = False) -> T: ...
@overload
def Path(
    alias: Optional[str] = None,
    *,
    default_factory: Callable[[], T],
    required: bool = False,
) -> T: ...
@overload
def Cookie(alias: Optional[str] = None, *, required: bool = False) -> Any: ...
@overload
def Cookie(alias: Optional[str] = None, *, default: T, required: bool = False) -> T: ...
@overload
def Cookie(
    alias: Optional[str] = None,
    *,
    default_factory: Callable[[], T],
    required: bool = False,
) -> T: ...
@overload
def Body(alias: Optional[str] = None, *, required: bool = False) -> Any: ...
@overload
def Body(alias: Optional[str] = None, *, default: T, required: bool = False) -> T: ...
@overload
def Body(
    alias: Optional[str] = None,
    *,
    default_factory: Callable[[], T],
    required: bool = False,
) -> T: ...
def Headers() -> Any: ...
def Queries() -> Any: ...
def Cookies() -> Any: ...
@overload
def Depends(*, use_cache: bool = True) -> Any: ...
@overload
def Depends(dependency: Callable[..., T], /, *, use_cache: bool = True) -> T: ...
@overload
def Promise() -> Any: ...
@overload
def Promise(promised_type: T, /) -> T: ...
