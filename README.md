[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/hasii2011/mypy-plugins-ally/graphs/commit-activity)
[![CI](https://github.com/hasii2011/mypy-plugins-ally/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/hasii2011/mypy-plugins-ally/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/mypy-plugins-ally.svg)](https://badge.fury.io/py/mypy-plugins-ally)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Copilot: No](https://img.shields.io/badge/GitHub_Copilot-No-red?logo=github&style=flat-square)](https://github.com/hasii2011/code-ally-basic/wiki/GitHub-Copilot)

# mypy-plugins-ally

Custom `mypy` plugins for wxPython and other projects.

## Overview

### `SizedControlsPlugin`

At runtime, importing `wx.lib.sized_controls` monkey-patches layout helper methods directly onto `wx.Window` (`wx.core.Window`) and `wx.SizerItem` (`wx.core.SizerItem`). Because these methods are attached dynamically at import time rather than declared in class bodies, static type stubs shipped with wxPython (4.3.2+) omit them, causing `mypy` to report `[attr-defined]` errors on calls such as `sizedPanel.SetSizerProps(expand=True, proportion=1)`.

`mypypluginsally.SizedControlsPlugin` hooks into `mypy` class MRO customization (`get_customize_class_mro_hook`) to register the dynamically added methods so all subclasses (such as `SizedPanel`, `SizedFrame`, `SizedDialog`, and `wx.Notebook`) inherit them during static type checking:

- **`wx.core.Window`**: `SetSizerProps`, `GetSizerProps`, `SetSizerProp`, `SetDefaultSizerProps`, `GetDefaultHIGBorder`, `GetDialogBorder`
- **`wx.core.SizerItem`**: `SetHGrow`, `GetHGrow`, `SetVGrow`, `GetVGrow`

## Requirements

- Python `>= 3.11`
- `mypy >= 2.4.1`

## Installation

```bash
pip install mypy-plugins-ally
```

## Usage

Enable `mypypluginsally.SizedControlsPlugin` in your `mypy` configuration:

**`mypy.ini` / `.mypi.ini`**

```ini
[mypy]
plugins = mypypluginsally.SizedControlsPlugin
```

**`pyproject.toml`**

```toml
[tool.mypy]
plugins = ["mypypluginsally.SizedControlsPlugin"]
```

___

Written by <a href="mailto:humberto.a.sanchez.ii@gmail.com?subject=Hello Humberto">Humberto A. Sanchez II</a> (C) 2026
___

## Note
For all kinds of problems, requests, enhancements, bug reports, etc., please drop me an e-mail.


> [!NOTE]
> **I do not consent to GitHub's use of this project's code in Copilot.** See our [GitHub Copilot Statement](https://github.com/hasii2011/code-ally-basic/wiki/GitHub-Copilot) for details.
