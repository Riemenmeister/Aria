# Aria

Aria is a small cross-platform Python launcher created from a PyBridge template and prepared for local Windows/PC use.

## Requirements

- Python 3.9 or later
- Windows, macOS, or Linux

## Install Locally

From the project root:

```powershell
py -m pip install -e .
```

The package exposes the `aria` console command and can also be imported as `Aria`.

## Run

```powershell
py -m Aria
```

or, after installation:

```powershell
aria
```

## Verify

```powershell
py -m compileall Aria
py -c "import Aria; print('import-ok')"
py -m pip install -e . --dry-run --no-deps
```

Copyright (c) 2026 Andreas Paulus. All rights reserved.
