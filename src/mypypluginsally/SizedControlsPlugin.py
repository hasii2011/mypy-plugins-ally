"""
Mypy plugin for ``wx.lib.sized_controls`` dynamic extensions.

At runtime, importing ``wx.lib.sized_controls`` monkey-patches layout helper
methods directly onto ``wx.Window`` (``wx.core.Window``) and ``wx.SizerItem``
(``wx.core.SizerItem``). Because these methods are attached dynamically at
import time rather than declared in class bodies, static type stubs shipped
with wxPython (4.3.2+) do not include them.

Without this plugin, mypy reports ``[attr-defined]`` errors on calls such as
``sizedPanel.SetSizerProps(expand=True, proportion=1)`` or
``notebook.SetSizerProps(...)``.

Usage in ``.mypi.ini`` or ``mypy.ini``::

    [mypy]
    plugins = mypypluginsally.SizedControlsPlugin
"""
from typing import Callable
from typing import Optional

from mypy.nodes import Var
from mypy.nodes import ARG_STAR
from mypy.nodes import ARG_STAR2
from mypy.nodes import Argument

from mypy.plugin import Plugin
from mypy.plugin import ClassDefContext
from mypy.plugins.common import add_method_to_class

from mypy.types import Type
from mypy.types import AnyType
from mypy.types import Instance
from mypy.types import NoneType
from mypy.types import TypeOfAny

TARGET_WINDOW_CLASS: str = 'wx.core.Window'
TARGET_SIZER_ITEM_CLASS: str = 'wx.core.SizerItem'


def _buildStarArguments(anyType: AnyType) -> list[Argument]:
    """
    Build ``*args: Any, **kwargs: Any`` parameter definitions for injected methods.

    ``wx.lib.sized_controls`` methods accept flexible keyword and positional
    sizer options (for example, ``expand=True``, ``proportion=1``, ``border=...``).
    Using ``*args, **kwargs`` typed as ``Any`` keeps call sites ergonomic
    without duplicating wxPython's internal option-validation dictionary.
    """
    starArgs: Argument = Argument(
        variable=Var('args', anyType),
        type_annotation=anyType,
        initializer=None,
        kind=ARG_STAR,
    )
    starKwargs: Argument = Argument(
        variable=Var('kwargs', anyType),
        type_annotation=anyType,
        initializer=None,
        kind=ARG_STAR2,
    )
    return [starArgs, starKwargs]


def _injectMethodSpecs(
    ctx: ClassDefContext,
    methodSpecs: list[tuple[str, list[Argument], Type]],
):
    """
    Register a sequence of synthetic method signatures on ``ctx.cls``.

    Each entry in ``methodSpecs`` is ``(methodName, arguments, returnType)``.
    """
    for methodName, arguments, returnType in methodSpecs:
        add_method_to_class(
            api=ctx.api,
            cls=ctx.cls,
            name=methodName,
            args=arguments,
            return_type=returnType,
        )


class SizedControlsPlugin(Plugin):
    """
    Teach mypy about methods monkey-patched by ``wx.lib.sized_controls``.
    """

    def get_customize_class_mro_hook(
        self,
        fullname: str,
    ) -> Optional[Callable[[ClassDefContext], None]]:
        """
        Return a class-customization hook for wxPython classes patched by
        ``wx.lib.sized_controls``.

        Mypy invokes ``get_customize_class_mro_hook`` during semantic analysis
        when building a class's MRO, before subclass bodies and call sites are
        type-checked. Injecting methods onto ``wx.core.Window`` and
        ``wx.core.SizerItem`` here ensures all subclasses (such as
        ``SizedPanel``, ``SizedFrame``, ``SizedDialog``, and ``wx.Notebook``)
        automatically inherit the patched methods.
        """
        if fullname == TARGET_WINDOW_CLASS:
            return self._customizeWindowClass
        if fullname == TARGET_SIZER_ITEM_CLASS:
            return self._customizeSizerItemClass
        return None

    def _customizeWindowClass(self, ctx: ClassDefContext):
        """
        Inject ``wx.lib.sized_controls`` methods onto ``wx.core.Window``.

        Injected methods and why they exist:
        - ``SetSizerProps(*args, **kwargs) -> None``: Sets multiple sizer flags
          on the window's parent sizer item (e.g., ``expand``, ``proportion``).
        - ``GetSizerProps() -> Any``: Returns the dict of current sizer
          properties applied to this window.
        - ``SetSizerProp(*args, **kwargs) -> None``: Sets a single named sizer
          property (``prop``, ``value``) on this window.
        - ``SetDefaultSizerProps() -> None``: Resets/applies default HIG sizer
          properties for the window type.
        - ``GetDefaultHIGBorder() -> int``: Returns platform-appropriate HIG
          border spacing in pixels.
        - ``GetDialogBorder() -> int``: Returns standard dialog border spacing
          in pixels.
        """
        anyType: AnyType = AnyType(TypeOfAny.special_form)
        starArguments: list[Argument] = _buildStarArguments(anyType=anyType)
        intType: Instance = ctx.api.named_type('builtins.int')
        noneType: NoneType = NoneType()

        windowMethodSpecs: list[tuple[str, list[Argument], Type]] = [
            ('SetSizerProps', starArguments, noneType),
            ('GetSizerProps', [], anyType),
            ('SetSizerProp', starArguments, noneType),
            ('SetDefaultSizerProps', [], noneType),
            ('GetDefaultHIGBorder', [], intType),
            ('GetDialogBorder', [], intType),
        ]
        _injectMethodSpecs(ctx=ctx, methodSpecs=windowMethodSpecs)

    def _customizeSizerItemClass(self, ctx: ClassDefContext):
        """
        Inject ``wx.lib.sized_controls`` methods onto ``wx.core.SizerItem``.

        Injected methods and why they exist:
        - ``SetHGrow(*args, **kwargs) -> None`` / ``GetHGrow() -> int``:
          Gets or sets horizontal growth proportion/factor on a ``SizerItem``.
        - ``SetVGrow(*args, **kwargs) -> None`` / ``GetVGrow() -> int``:
          Gets or sets vertical growth proportion/factor on a ``SizerItem``.
        """
        anyType: AnyType = AnyType(TypeOfAny.special_form)
        starArguments: list[Argument] = _buildStarArguments(anyType=anyType)
        intType: Instance = ctx.api.named_type('builtins.int')
        noneType: NoneType = NoneType()

        sizerItemMethodSpecs: list[tuple[str, list[Argument], Type]] = [
            ('SetHGrow', starArguments, noneType),
            ('GetHGrow', [], intType),
            ('SetVGrow', starArguments, noneType),
            ('GetVGrow', [], intType),
        ]
        _injectMethodSpecs(ctx=ctx, methodSpecs=sizerItemMethodSpecs)


def plugin(_version: str) -> type[Plugin]:
    """
    Entry point discovered by mypy when loading ``mypypluginsally.SizedControlsPlugin``.
    """
    return SizedControlsPlugin
