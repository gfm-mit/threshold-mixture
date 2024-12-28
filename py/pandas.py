import glob
import json
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns


results = {}
for f in glob.glob('summaries/*.txt'):
  with open(f, 'r') as file:
    data = file.read()
    data = re.sub(r'.*</metric_evaluation>\n*', '', data, flags=re.DOTALL)
    try:
      data = re.findall('\[\s+\{.*?\}\s+\]', data, flags=re.DOTALL)[0]
    except IndexError as e:
      print(e)
      continue
    try:
      data = json.loads(data)
    except json.JSONDecodeError as e:
      print(f, e)
      continue
    ff = re.findall("/([a-z0-9_]+)", f)[0].split('_')
    ff = " ".join(ff[2:4])
    try:
      data = {
        v['name']: v['present']
        for v in data
      }
      results[ff] = data
    except TypeError as e:
      print(e)
results = pd.DataFrame(results).fillna(False)
print(results)
idx = results.sum(axis=1).sort_values(ascending=False).index
results = results.loc[idx]
idx = results.sum(axis=0).sort_values(ascending=False).index
results = results.loc[:, idx]
sns.heatmap(results)
plt.tight_layout()
plt.show()