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
      data = json.loads(data)
    except json.JSONDecodeError as e:
      print(f, e)
      continue
    try:
      data = {
        v['name']: v['present']
        for v in data
      }
      results[f] = data
    except TypeError as e:
      print(e)
results = pd.DataFrame(results)
idx = results.sum(axis=1).sort_values(ascending=False).index
results = results.loc[idx]
sns.heatmap(results)
plt.tight_layout()
plt.show()