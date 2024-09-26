## VSA - Voiding Spot Analysis

# Version
0.2.3
 + Feature added: Save all functionality.

# Intallation
This application requires the following:
* Python 3.3 or later
* numpy
* OpenCV 
* QT

After you install <a href="https://www.python.org/downloads/">Python</a>, the commands below will create a Python virtual environment in which to run the application, and install the packages above in the new virtual environment.

```
python -m venv .env_vsa
source .env_vsa/bin/activate
pip install -r requirements_pip.txt
```

# Running
To run the application the Python virtual environment must be activated at the start of the session with the first command below.  The application is then run with the second command below.
```
source .env_vsa/bin/activate
python src/vsa_gui.py
```

