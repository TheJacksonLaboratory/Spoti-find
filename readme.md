## Spoti-find

### Version
0.024  
+ Feature added: Removing Anaconda dependency

## 📌 Installation
Your environment policy allows installation either using Python’s built-in virtual environment (`venv`) with pip or **Miniforge3** (with channels: `conda-forge`, `bioconda`). Both methods are described below.

### Option 1: PyApp Binaries (recomended)

Included in this repo are binaries packaged with [PyApp](https://ofek.dev/pyapp/latest/) that will automaticaly install a virtual enviroment and launch spotifind when executed.

Windows: Spoti-Find.exe
MacOS: Spoti-Find.command
Linux: Spoti-Find (no extension)

This may require adding execution permisions in linux
```bash
chmod +x ./Spoti-Find
```

These are unsigned binaries and may initiate a system warning that needs to be bypassed. If you are uncomfortable or unable to do so (e.g. lacking the required privileges) you can follow instalation options 2 or 3 bellow and see the "Running the Application" section to launch the program.

---

### Option 2: Using Miniforge3 (conda-forge channel)

This method is compliant with JAX's allowed environment policies.

**Step 1: Install Miniforge3**

- Download Miniforge3 from:  
[Miniforge3 Installer](https://github.com/conda-forge/miniforge/releases/latest)

- **macOS/Linux Example (terminal):**
```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

- **Windows Example:**  
Download and run the executable installer from above link, following on-screen instructions.

**Step 2: Create and activate conda environment**
```bash
mamba create -f .\spoti_find_enviroment.yaml
```


**Important**: Confirm your conda environment is correctly set to use only `conda-forge`:

```bash
mamba config --remove channels defaults
mamba config --add denylist_channels defaults
```

---
### Option 3: Using Python's built-in venv + pip 

1. **Install Python 3.11**  
   Download from the official website: [python.org](https://www.python.org/downloads/).

2. **Create & Activate Virtual Environment**  

**macOS/Linux:**
```bash
python -m venv .env_vsa
source .env_vsa/bin/activate
```

**Windows:**
```powershell
python -m venv .env_vsa
.env_vsa\Scripts\Activate.ps1
```

3. **Install Dependencies (via pip)**  
```bash
pip install -r requirements_pip.txt
```
---

## 🚀 Running the Application

After activating your selected virtual environment:

**macOS/Linux:**
```bash
python -m spoti_find
```

**Windows:**
```powershell
python -m spoti_find
```
