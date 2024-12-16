import glob
import json
import pprint
import pandas as pd
import re

for f in glob.glob('summaries/*.txt'):
  with open(f, 'r') as file:
    data = file.read()
    data = re.sub(r'.*</metric_evaluation>\n*', '', data, flags=re.DOTALL)
    try:
      data = json.loads(data)
    except json.JSONDecodeError as e:
      print(f, e)
      continue
    try:
      if 'metrics' in data:
        data = data['metrics']
      #pprint.pprint(data[0])
    except TypeError as e:
      print(e)