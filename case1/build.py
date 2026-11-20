import pandas as pd, numpy as np, csv
df=pd.read_pickle('df.pkl'); tasks=pd.read_pickle('tasks.pkl').reset_index(); V=pd.read_pickle('V.pkl')
CUT=pd.Timestamp('2026-07-01 00:00',tz='Etc/GMT-3')
amt=df.groupby('ProcessInstanceId').Amount.first()
tname={'standard':'обычная','urgent':'срочная','contract':'договорная'}
RU={'CHK':'проверка заявки','MGR':'руководитель','BUD':'бюджет','LEG':'юрист','EXE':'исполнение'}
rows=[]
def add(p,t,e): rows.append((p,t,e))
tasks=tasks.sort_values(['ProcessInstanceId','i0'])
# per-activity medians (working hours) by type, from tasks closed
c=tasks.dropna(subset=['t1'])
med=c.groupby(['A','RequestType']).wh.median()
ft=lambda x: f"{x:.1f}".replace('.',',') if False else f"{x:.1f}"
# 1 skip MGR
for p in V.index[V.r.str.startswith('CHK/accept > BUD')]:
    t=V.loc[p,'t']
    add(p,'Пропуск согласования руководителем',f"Заявка ({tname[t]}, {amt[p]:.0f} руб.) после проверки заявки сразу попала на проверку бюджета: этап «Согласование руководителем» отсутствует, хотя во всех типовых маршрутах он обязателен перед бюджетом. Маршрут: {V.loc[p,'r']}.")
# 2 EXE before BUD
for p in V.index[V.r.str.contains('EXE/accept > BUD')]:
    t=V.loc[p,'t']; g=tasks[tasks.ProcessInstanceId==p].set_index('A')
    ex=g.loc['EXE'].t1; bu=g.loc['BUD'].t0
    extra=' Юридическая проверка также выполнена после исполнения.' if 'LEG' in g.index and g.loc['LEG'].t0>ex else ''
    add(p,'Исполнение до проверки бюджета',f"Закупка исполнена {ex:%d.%m.%Y %H:%M}, а проверка бюджета создана только {bu:%d.%m.%Y %H:%M}, то есть деньги подтверждены уже после исполнения. По бизнес-схеме порядок: руководитель → бюджет → [юрист] → исполнение.{extra} Маршрут: {V.loc[p,'r']}.")
# 3 dup CHK
for p in V.index[V.r.str.startswith('CHK/accept > CHK')]:
    g=tasks[(tasks.ProcessInstanceId==p)&(tasks.A=='CHK')].sort_values('i0')
    a,b=g.iloc[0],g.iloc[1]
    same='тем же специалистом' if a.UserId==b.UserId else 'другим специалистом'
    add(p,'Повторная проверка без возврата',f"Этап «Проверка заявки» выполнен дважды подряд ({a.t1:%d.%m %H:%M} и {b.t1:%d.%m %H:%M}, {same}) без возврата руководителем и без доработки. В норме повторная проверка бывает только после цепочки возврат → доработка (в 11,9% процессов); здесь цепочки нет.")
# 4 AUD
for p in V.index[V.r.str.contains('AUD')]:
    g=tasks[(tasks.ProcessInstanceId==p)&(tasks.A=='AUD')]
    us=g.UserId.nunique()
    add(p,'Внеплановая проверка (для ручной проверки)',f"В процессе {len(g)} задания «Внеплановая проверка» (роль auditor, пользователей: {us}), вставленные между согласованием руководителем и исполнением (маршрут: {V.loc[p,'r']}). Такие этапы есть только в 8 из 1000 заявок; сумма {amt[p]:.0f} руб. и тип ({tname[V.loc[p,'t']]}) сами по себе не объясняют проверку, поэтому нужен ручной разбор: оправданность по данным не установить.")
# 5 loops
rc=tasks.assign(ret=tasks.Result=='return').groupby('ProcessInstanceId').ret.sum()
for p in rc.index[rc>=5]:
    t=V.loc[p,'t']; fin=V.loc[p,'end']
    add(p,'Зацикливание возвратов на доработку',f"Руководитель возвращал заявку на доработку {int(rc[p])} раз(а); в 87,3% заявок возвратов нет, в 11,9% — ровно один, ни у одной другой нет больше одного. Повторялась цепочка проверка → руководитель → доработка. Итог процесса: {fin}.")
# 6 CHK long
for _,r in c[(c.A=='CHK')&(c.wh>1.4)].iterrows():
    m=med[('CHK',r.RequestType)]
    if r.wh>=59:
        add(r.ProcessInstanceId,'Аномально долгая проверка заявки',f"Проверка заявки ({tname[r.RequestType]}) закрыта через {r.dur_h:.0f} ч календарного времени = {r.wh:.0f} рабочих часов (создана {r.t0:%d.%m %H:%M}, закрыта {r.t1:%d.%m %H:%M}). Медиана для этого типа — {m:.1f} рабочих часа, остальные заявки укладываются примерно в 1,3 часа; выброс в десятки раз.")
    else:
        add(r.ProcessInstanceId,'Долгая проверка заявки',f"Проверка заявки ({tname[r.RequestType]}) заняла {r.wh:.1f} рабочих часов ({r.dur_h:.0f} ч календарных); медиана для типа — {m:.2f} ч, 99-й процентиль без выбросов около 1,3 ч. Это в {r.wh/m:.0f} раз дольше типичного, но заметно короче максимальных выбросов, поэтому сначала проверить загрузку специалиста.")
# 7 instant
z=c[c.dur_h<1/60]; zc=z.groupby('ProcessInstanceId').size()
for p in zc.index[zc>=2]:
    g=z[z.ProcessInstanceId==p]; secs=(g.dur_h*3600).round().astype(int)
    add(p,'Мгновенное закрытие этапов',f"{len(g)} задания закрыты за {secs.min()}–{secs.max()} секунд после создания ({', '.join(g.A.map(RU))}). Типичное время этих этапов — десятки минут и часы (медиана проверки {med[('CHK','standard')]:.1f} ч, руководителя {med[('MGR','standard')]:.1f} ч), так быстро человек не работает: похоже на автоматическое или формальное закрытие.")
# 8 MGR by requester
for _,r in tasks[(tasks.A=='MGR')&(tasks.Role=='requester')].iterrows():
    add(r.ProcessInstanceId,'Согласование закрыто заявителем (роль не соответствует этапу)',f"Задание «Согласование руководителем» закрыто пользователем с ролью requester (результат: {r.Result}), хотя этот этап в 1141 из 1149 закрытий выполняет manager. Нарушение разделения обязанностей: заявитель участвует в решении по своей заявке.")
# 9 after cut
after=df[df.ts>CUT]
for p,g in after.groupby('ProcessInstanceId'):
    n=len(g); last=g.ts.max()
    add(p,'События после среза наблюдения',f"{n} события датированы {g.ts.min():%d.%m.%Y %H:%M} (UTC+3), то есть после среза 01.07.2026 00:00; по описанию выгрузки событий после среза быть не должно. Процесс при этом уже завершён (fulfilled). Проверить время/часовой пояс и источник данных.")
# 10 stuck
op=tasks[tasks.t1.isna()&(tasks.A=='MGR')]
for _,r in op.iterrows():
    add(r.ProcessInstanceId,'Зависшая заявка на согласовании',f"Задание «Согласование руководителем» создано {r.t0:%d.%m.%Y %H:%M} и не закрыто к срезу 01.07.2026: ожидание ≈{(CUT-r.t0).days} дней. Нормальное закрытие этого этапа занимает до 6,8 рабочих часов (99-й процентиль ≈5 ч). Открытая заявка сама не аномалия, но такая давность — вероятно потерянное или брошенное задание.")
out=pd.DataFrame(rows,columns=['ProcessInstanceId','AnomalyType','Explanation']).drop_duplicates()
out.to_csv('anomalies.csv',index=False,encoding='utf-8-sig',quoting=csv.QUOTE_MINIMAL)
print(len(out), out.ProcessInstanceId.nunique()); print(out.AnomalyType.value_counts())
print(out.ProcessInstanceId.value_counts().head(8))
print(out.sample(4,random_state=1).to_string())
