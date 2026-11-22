import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

con.sql("""CREATE OR REPLACE TEMP TABLE t AS
 SELECT user_id,
  min(CASE WHEN trial THEN created_at END) AS trial_at,
  min(CASE WHEN NOT trial THEN created_at END) AS buy_at
 FROM orders WHERE status = 'paid' GROUP BY user_id""")

print("1. Структура платящих")
q("""SELECT count(*) AS users_paid_any,
 count(trial_at) AS had_trial,
 count(buy_at) AS bought,
 count_if(trial_at IS NOT NULL AND buy_at >= trial_at) AS trial_then_bought,
 count_if(trial_at IS NULL AND buy_at IS NOT NULL) AS bought_no_trial,
 count_if(trial_at IS NOT NULL AND buy_at IS NULL) AS trial_only
 FROM t""")

print("2. Дни от регистрации до первой покупки")
q("""SELECT (trial_at IS NOT NULL) AS had_trial, count(*) AS n,
 median(date_diff('day', u.created_at, buy_at)) AS med_days,
 quantile_cont(date_diff('day', u.created_at, buy_at), 0.75) AS p75,
 quantile_cont(date_diff('day', u.created_at, buy_at), 0.9) AS p90
 FROM t JOIN users u ON u.id = t.user_id
 WHERE buy_at IS NOT NULL GROUP BY 1""")

print("3. Дни от триала до покупки")
q("""SELECT count(*) AS n,
 median(date_diff('day', trial_at, buy_at)) AS med_days,
 quantile_cont(date_diff('day', trial_at, buy_at), 0.9) AS p90
 FROM t WHERE trial_at IS NOT NULL AND buy_at >= trial_at""")