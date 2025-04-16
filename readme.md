## VSA - Voiding Spot Analysis

### Version
0.024  
+ Feature added: Removing Anaconda dependency

## 📌 Installation
Your environment policy allows installation either using Python’s built-in virtual environment (`venv`) with pip or **Miniforge3** (with channels: `conda-forge`, `bioconda`). Both methods are described below.

### Option 1: Using Python's built-in venv + pip (recommended)

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
conda create -n vsa python=3.11 numpy=1.24.2 -c conda-forge
conda activate vsa
```

**Step 3: Install remaining dependencies via pip**
```bash
pip install -r requirements_pip.txt
```

**Important**: Confirm your conda environment is correctly set to use only `conda-forge`:

```bash
conda config --remove channels defaults
conda config --add denylist_channels defaults
```

---

## 🚀 Running the Application

After activating your selected virtual environment:

**macOS/Linux:**
```bash
python src/vsa_gui.py
```

**Windows:**
```powershell
python src/vsa_gui.py
```
