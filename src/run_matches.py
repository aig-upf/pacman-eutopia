import json
import sys
from contest import capture

with open("matches.json","r") as f:
  matches = f.read()
  
matches = json.loads(matches)
capture.run(matches[sys.argv[1]])

