import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_colwidth',120,'display.max_rows',400,'display.max_columns',30)
df=pd.read_pickle('df.pkl'); tasks=pd.read_pickle('tasks.pkl').reset_index()
CUT=pd.Timestamp('2026-07-01 00:00',tz='Etc/GMT-3')
# relabel budget-vs-manager: order within process of MGR tasks
tasks=tasks.sort_values(['ProcessInstanceId','i0'])
# Budget stage name: ActivityName 'Согласование бюджета' -> BUD (already mapped by ActivityName!). A map was by name so MGR/BUD distinct.
def route(g): return ' > '.join((g.A+'/'+g.Result.fillna('open')).tolist())
R=tasks.groupby('ProcessInstanceId').apply(route)
T=tasks.groupby('ProcessInstanceId').RequestType.first()
end=df[df.EventType=='process_completed'].set_index('ProcessInstanceId').Result
V=pd.DataFrame({'r':R,'t':T,'end':end}); V['end']=V.end.fillna('OPEN')
vc=V.groupby(['t','r','end']).size().sort_values(ascending=False)
# compress repeated loops
import re
def comp(s): 
    return re.sub(r'(?:CHK/accept > MGR/return > REW/accept > ){2,}','[LOOP x n] ',s)
V['rc']=V.r.map(comp)
print(V.groupby(['t','rc','end']).size().sort_values(ascending=False).to_string())
V.to_pickle('V.pkl')
