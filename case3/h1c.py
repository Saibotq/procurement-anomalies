import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

con.sql("""CREATE OR REPLACE TEMP TABLE tt AS
 SELECT user_id, min(created_at) AS trial_at FROM orders
 WHERE trial AND status = 'paid' GROUP BY 1""")
con.sql("""CREATE OR REPLACE TEMP TABLE d AS
 SELECT device_identifier FROM devices WHERE device_identifier IS NOT NULL
 GROUP BY 1 HAVING count(DISTINCT user_id) BETWEEN 2 AND 10""")

print("1. Пауза между триалами на одном устройстве (дни)")
q("""WITH x AS (
 SELECT u.device_identifier, tt.trial_at,
  lag(tt.trial_at) OVER (PARTITION BY u.device_identifier ORDER BY tt.trial_at) AS prev
 FROM d JOIN (SELECT DISTINCT user_id, device_identifier FROM devices) u USING (device_identifier)
 JOIN tt ON tt.user_id = u.user_id)
 SELECT count(*) AS pairs,
  quantile_cont(date_diff('day', prev, trial_at), 0.25) AS p25,
  median(date_diff('day', prev, trial_at)) AS med,
  quantile_cont(date_diff('day', prev, trial_at), 0.75) AS p75,
  count_if(date_diff('day', prev, trial_at) <= 7) AS within_week
 FROM x WHERE prev IS NOT NULL""")

print("2. То же по общему push-токену FCM")
q("""WITH p AS (SELECT fcm_push_token AS t FROM devices WHERE fcm_push_token IS NOT NULL
  GROUP BY 1 HAVING count(DISTINCT user_id) BETWEEN 2 AND 10)
 SELECT count(*) AS tokens, count_if(trials >= 2) AS multi_trial_tokens,
  sum(greatest(trials - 1, 0)) AS extra_trials
 FROM (SELECT p.t, count(DISTINCT tt.user_id) AS trials FROM p
  JOIN devices dv ON dv.fcm_push_token = p.t
  LEFT JOIN tt ON tt.user_id = dv.user_id GROUP BY 1)""")