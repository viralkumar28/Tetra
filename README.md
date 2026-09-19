**THIS IS AN AI-GENERATED GAME. NO HUMAN WORK WAS INVOLVED IN ITS CREATION.**

# Tetra Setup Guide

This project is a small Tetris-style game written in Python using Pygame.

## Requirements

- Windows 10 or 11
- Python 3.11 or newer
- Internet access to install dependencies

## 1) Install Python

Download and install Python from:

https://www.python.org/downloads/

During installation, make sure to check:

- Add Python to PATH
- Install launcher for all users

After installation, verify it works:

```powershell
python --version
```

If `python` is not recognized, try:

```powershell
py --version
```

## 2) Open a terminal in the project folder

```powershell
cd "C:\Users\ASUS\Desktop\Tertis"
```

## 3) Create a virtual environment (recommended)

```powershell
python -m venv .venv
```

## 4) Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 5) Install the game dependency

```powershell
pip install pygame-ce
```

## 6) Run the game

```powershell
python tetra.py
```

## Troubleshooting

### If `pip` is not recognized

Use:

```powershell
python -m pip install pygame-ce
```

### If the virtual environment cannot be activated

Try:

```powershell
.\.venv\Scripts\python.exe -m pip install pygame-ce
```

Then run:

```powershell
.\.venv\Scripts\python.exe tetra.py
```

### If the game still will not start

Make sure the dependency is installed in the same environment you are running from, and that you are executing the file from the project folder.

## Controls

- Left / Right: move
- Down: soft drop
- Up or X: rotate clockwise
- Z: rotate counter-clockwise
- Space: hard drop
- C or Shift: hold
- P or Esc: pause
- R: restart

## Notes

This project is intentionally simple and is designed to run with the pygame-ce package on modern Windows systems.
