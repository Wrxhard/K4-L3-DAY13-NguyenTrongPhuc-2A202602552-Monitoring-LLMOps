import os
import sys
from pathlib import Path

# Ensure temp directory uses a clean local path to bypass Windows Temp permission lock
LOCAL_TEMP = Path(__file__).resolve().parent / ".pytest_temp"
LOCAL_TEMP.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(LOCAL_TEMP)
os.environ["TMP"] = str(LOCAL_TEMP)

def pytest_configure(config):
    config.option.basetemp = str(LOCAL_TEMP)
