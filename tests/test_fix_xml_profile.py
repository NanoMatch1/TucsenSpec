#!/usr/bin/env python
# coding: utf-8
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
XML_NAME = "Dhyana 400BSI_PIDe408_KBS40B1907011.xml"
XML_PATH = os.path.join(HERE, XML_NAME)

# Accept override via argv for different paths
if len(sys.argv) > 1:
    XML_PATH = sys.argv[1]

assert os.path.exists(XML_PATH), f"XML not found: {XML_PATH}"

print(f"Checking XML: {XML_PATH}")

tree = ET.parse(XML_PATH)
root = tree.getroot()

# Navigate to ParameterSets/DftParameter/LNExposure
param = root.find(".//ParameterSets[@Name='DftParameter']")
if param is None:
    raise SystemExit("Could not find ParameterSets Name='DftParameter'")

ln = param.find("LNExposure")
if ln is None:
    raise SystemExit("Could not find LNExposure element")

try:
    val = int(ln.text.strip())
except Exception:
    val = 1

print(f"Current LNExposure={val}")

# Consider values > 200 suspicious for tests; set to 1
if val > 200 or val <= 0:
    ln.text = "1"
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=False)
    print("Adjusted LNExposure to 1 and saved.")
else:
    print("LNExposure is within safe range; no change.")

#TODO: 
# 1. Create check on startup
# 2. create try-except to identify timeout issue and fix automatically