##How to Run?

1. Create the virtual Environment

```bash
conda create -n travel python=3.14 -y
```

2. Activate the environment
```bash
conda activate travel
```

3. Install the Requirements

```bash

pip install -r requirement.txt
```

Alternative (no conda available) — create a venv using the system Python

```powershell
# Create the venv named 'travel'
python -m venv travel

# Activate (PowerShell)
.\travel\Scripts\Activate.ps1

# Or activate for cmd.exe
.\travel\Scripts\activate.bat

# Upgrade pip and install requirements
python -m pip install --upgrade pip
python -m pip install -r requirement.txt
```



external db url in render ps sql
postgresql://hari:eoh8MrhEz718LZQ4GPIHO5LLohUiCm3v@dpg-d9van9u7bikc73d40gvg-a.ohio-postgres.render.com/agentmemory_dq2y