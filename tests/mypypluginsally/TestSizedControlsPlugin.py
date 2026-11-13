"""
Unit and integration tests for ``mypypluginsally.SizedControlsPlugin``.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable
from typing import Optional
from unittest import TestCase
from unittest import main

from mypy import api as mypyApi
from mypy.options import Options
from mypy.plugin import ClassDefContext
from mypy.plugin import Plugin

from mypypluginsally.SizedControlsPlugin import SizedControlsPlugin
from mypypluginsally.SizedControlsPlugin import TARGET_SIZER_ITEM_CLASS
from mypypluginsally.SizedControlsPlugin import TARGET_WINDOW_CLASS
from mypypluginsally.SizedControlsPlugin import plugin

STUB_WX_INIT: str = ''
STUB_WX_CORE: str = """
class Window:
    pass


class Panel(Window):
    pass


class SizerItem:
    pass
"""


class TestSizedControlsPlugin(TestCase):
    """
    Verify hook dispatch and end-to-end mypy type checking for SizedControlsPlugin.
    """

    def testPluginEntryPointReturnsPluginClass(self):
        """
        Verify mypy's ``plugin(version)`` factory returns ``SizedControlsPlugin``.
        """
        pluginClass: type[Plugin] = plugin('2.3.1')
        self.assertIs(pluginClass, SizedControlsPlugin)

    def testHookTargetsOnlySizedControlsClasses(self):
        """
        Verify ``get_customize_class_mro_hook`` matches only ``wx.core.Window``
        and ``wx.core.SizerItem``.
        """
        instance: SizedControlsPlugin = SizedControlsPlugin(Options())

        windowHook: Optional[Callable[[ClassDefContext], None]] = (
            instance.get_customize_class_mro_hook(TARGET_WINDOW_CLASS)
        )
        sizerItemHook: Optional[Callable[[ClassDefContext], None]] = (
            instance.get_customize_class_mro_hook(TARGET_SIZER_ITEM_CLASS)
        )
        unrelatedHook: Optional[Callable[[ClassDefContext], None]] = (
            instance.get_customize_class_mro_hook('wx.core.Button')
        )

        self.assertIsNotNone(windowHook)
        self.assertIsNotNone(sizerItemHook)
        self.assertIsNone(unrelatedHook)

    def testMypyAcceptsInjectedWindowAndSizerItemMethods(self):
        """
        Run mypy end-to-end with the plugin enabled and verify all injected
        methods on ``wx.core.Window`` subclasses and ``wx.core.SizerItem``
        type-check cleanly.
        """
        sampleSource: str = """
from wx.core import Panel
from wx.core import SizerItem


def exercise(panel: Panel, item: SizerItem):
    panel.SetSizerProps(expand=True, proportion=1)
    props = panel.GetSizerProps()
    panel.SetSizerProp('expand', True)
    panel.SetDefaultSizerProps()
    higBorder: int = panel.GetDefaultHIGBorder()
    dialogBorder: int = panel.GetDialogBorder()

    item.SetHGrow(1)
    hGrow: int = item.GetHGrow()
    item.SetVGrow(2)
    vGrow: int = item.GetVGrow()
    _ = (props, higBorder, dialogBorder, hGrow, vGrow)
"""
        stdout, stderr, exitStatus = self._runMypyOnSample(sampleSource=sampleSource)
        self.assertEqual(exitStatus, 0, msg=f'stdout:\n{stdout}\nstderr:\n{stderr}')

    def testMypyStillFlagsInvalidMethodAndReturnTypeMismatch(self):
        """
        Verify the plugin does not suppress genuine type errors on
        ``wx.core.Window`` subclasses.
        """
        invalidSource: str = """
from wx.core import Panel


def exerciseInvalid(panel: Panel):
    wrongType: str = panel.GetDefaultHIGBorder()
    panel.NonExistentSizerMethod()
    _ = wrongType
"""
        stdout, _stderr, exitStatus = self._runMypyOnSample(sampleSource=invalidSource)
        self.assertNotEqual(exitStatus, 0)
        self.assertIn('NonExistentSizerMethod', stdout)
        self.assertIn('Incompatible types in assignment', stdout)

    def _runMypyOnSample(self, sampleSource: str) -> tuple[str, str, int]:
        """
        Write a temporary ``wx.core`` stub, mypy config, and target module,
        then execute ``mypy.api.run`` against it.
        """
        with TemporaryDirectory() as tempDirName:
            tempDir: Path = Path(tempDirName)
            wxDir: Path = tempDir / 'wx'
            wxDir.mkdir()
            (wxDir / '__init__.py').write_text(STUB_WX_INIT, encoding='utf-8')
            (wxDir / 'core.py').write_text(STUB_WX_CORE, encoding='utf-8')

            configFile: Path = tempDir / 'mypy.ini'
            configFile.write_text(
                '[mypy]\nplugins = mypypluginsally.SizedControlsPlugin\n',
                encoding='utf-8',
            )

            sampleFile: Path = tempDir / 'sample.py'
            sampleFile.write_text(sampleSource, encoding='utf-8')

            result: tuple[str, str, int] = mypyApi.run(
                [
                    '--config-file',
                    str(configFile),
                    '--no-incremental',
                    str(sampleFile),
                ]
            )
            return result


if __name__ == '__main__':
    main()
