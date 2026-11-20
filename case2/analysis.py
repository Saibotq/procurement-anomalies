import pandas as pd, collections, os
from pathlib import Path
# Папка с данными и результатами: students.csv лежит здесь же, результаты пишутся сюда
BASE=Path(r"C:\Users\user\Desktop\case2")
out=BASE
if not (BASE/'students.csv').exists(): raise SystemExit(f'Не найден {BASE/"students.csv"}')
d=pd.read_csv(BASE/'students.csv',encoding='utf-8-sig')
d=d.sort_values(['ProcessInstanceId','EventIndex'])   # числовая сортировка
N=d.ProcessInstanceId.nunique()
g=d.groupby('ProcessInstanceId')
routes=g.ActivityName.apply(lambda s:' > '.join(s))
vc=routes.value_counts()
v=pd.DataFrame({'Variant':[f'V{i+1}' for i in range(len(vc))],'Route':vc.index,'NumberOfCases':vc.values})
v['Share']=(v.NumberOfCases/N).round(4)
v.to_csv(out/'variants.csv',index=False,encoding='utf-8')
# transitions
pairs=collections.Counter()
for _,s in g.ActivityName:
    l=list(s)
    for a,b in zip(l,l[1:]): pairs[(a,b)]+=1
t=pd.DataFrame([(a,b) for (a,b) in pairs],columns=['SourceActivity','TargetActivity'])
t.to_csv(out/'student_transitions.csv',index=False,encoding='utf-8')
print(v.to_string()); 
for (a,b),c in sorted(pairs.items(),key=lambda x:-x[1]): print(c,a,'->',b)
# checks
print('start',d[d.EventIndex==1].ActivityName.value_counts().to_dict())
print('end',g.ActivityName.last().value_counts().to_dict())
info=g.agg(route=('ActivityName',lambda s:list(s)),amt=('Amount','first'))
comp=info[info.route.apply(lambda l:l[-1]=='Заявка выполнена')]
ex=comp.route.apply(lambda l:'Дополнительное согласование' in l)
print('extra amt min',comp[ex].amt.min(),'non-extra max',comp[~ex].amt.max(), 'n',ex.sum(),(~ex).sum())
# returns per instance
nret=info.route.apply(lambda l:l.count('Доработка заявки'))
print(nret.value_counts().to_dict())
# terminal outcomes after rework?
def after_rework_terminal(l):
    if 'Доработка заявки' not in l: return None
    return l[-1]
print(info[nret>0].route.apply(lambda l:l[-1]).value_counts().to_dict())
# rejections/cancels amounts
for k in ['Заявка отклонена','Заявка отменена']:
    print(k,info[info.route.apply(lambda l:l[-1]==k)].amt.describe()[['min','50%','max']].to_dict())
# rework independence from amount
print(info.assign(r=nret>0).groupby('r').amt.median().to_dict())
# who does what
print(d.groupby('ActivityName').Role.unique().to_dict())
# same user repeated? time stats (calendar hours between consecutive)
d['ts']=pd.to_datetime(d.Timestamp.str[:19])
d['dt']=d.groupby('ProcessInstanceId').ts.diff().dt.total_seconds()/3600
print(d.groupby('ActivityName').dt.median().round(1).to_dict())
print('reject-result of task-level vs final:',d[d.Result.isin(['reject','rejected','cancel','cancelled'])].groupby(['ActivityName','EventType','Result']).size().to_dict())
