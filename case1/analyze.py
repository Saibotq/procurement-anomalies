import pandas as pd, numpy as np
pd.set_option('display.width',250,'display.max_colwidth',200,'display.max_rows',300)
df=pd.read_csv('students.csv',encoding='utf-8-sig')
df['ts']=pd.to_datetime(df.Timestamp,utc=True).dt.tz_convert('Etc/GMT-3')
df=df.sort_values(['ProcessInstanceId','EventIndex']).reset_index(drop=True)
CUT=pd.Timestamp('2026-07-01 00:00',tz='Etc/GMT-3')
print('events after cut',(df.ts>CUT).sum(), 'max',df.ts.max())
ab={'Проверка заявки':'CHK','Согласование руководителем':'MGR','Согласование бюджета':'BUD','Проверка договора':'LEG','Исполнение заявки':'EXE','Доработка заявки':'REW','Внеплановая проверка':'AUD','Регистрация заявки':'REG','Завершение':'END'}
df['A']=df.ActivityName.map(ab)
print(df.groupby('A').ActivityId.nunique())
print(pd.crosstab(df.A,df.Role))
# tasks
cr=df[df.EventType=='task_created'].set_index('TaskId')
co=df[df.EventType=='task_completed'].set_index('TaskId')
tasks=cr[['ProcessInstanceId','A','ts','EventIndex','RequestType','Amount']].rename(columns={'ts':'t0','EventIndex':'i0'}).join(co[['ts','Role','UserId','Result','EventIndex']].rename(columns={'ts':'t1','EventIndex':'i1'}))
print('tasks',len(tasks),'closed',tasks.t1.notna().sum())
print('dup taskid in created',cr.index.duplicated().sum(),co.index.duplicated().sum())
tasks['dur_h']=(tasks.t1-tasks.t0).dt.total_seconds()/3600
print(tasks.groupby(['A','RequestType']).dur_h.describe().round(1))
# work hours calc
def workhours(a,b):
    if pd.isna(b): return np.nan
    tot=0; d=a.normalize()
    while d<=b:
        if d.weekday()<5:
            s=max(a,d+pd.Timedelta(hours=9)); e=min(b,d+pd.Timedelta(hours=18))
            if e>s: tot+=(e-s).total_seconds()
        d+=pd.Timedelta(days=1)
    return tot/3600
tasks['wh']=[workhours(a,b) for a,b in zip(tasks.t0,tasks.t1)]
print(tasks.groupby(['A','RequestType']).wh.describe().round(2))
tasks.to_pickle('tasks.pkl'); df.to_pickle('df.pkl')
# roles per activity
print(pd.crosstab(tasks.A,tasks.Role.fillna('NA')))
# users per role
u=df.dropna(subset=['UserId']).groupby('Role').UserId.nunique(); print(u)
print(df[df.EventType=='task_completed'].groupby('UserId').size().sort_values().head(15))
print(df.groupby('Role').UserId.apply(lambda s:s.value_counts().to_dict()).head(0))
# starter distribution
print(df[df.EventType=='process_started'].UserId.value_counts())
print(df[df.EventType=='process_started'].Role.value_counts())
print(df.groupby('RequestType').Amount.describe())
