import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

con.sql("""CREATE OR REPLACE TEMP TABLE inc AS
 SELECT * FROM read_csv('incidents.csv', delim=';', header=true, all_varchar=true)""")
con.sql("""CREATE OR REPLACE TEMP TABLE i2 AS
 SELECT CAST(user_id AS BIGINT) AS user_id, app_version,
  CAST(n_error AS DOUBLE) AS n_error, CAST(host_lookup AS DOUBLE) AS host_lookup,
  CAST(tun_refused AS DOUBLE) AS tun_refused, CAST(day AS DATE) AS day
 FROM inc WHERE note = '' OR note IS NULL""")
con.sql("""CREATE OR REPLACE TEMP TABLE paid AS
 SELECT DISTINCT user_id FROM orders WHERE status='paid' AND NOT trial""")

print("1. Платящие и бесплатные среди пользователей с инцидентами")
q("""SELECT (p.user_id IS NOT NULL) AS paid_user, count(DISTINCT i.user_id) AS users,
 median(host_lookup) AS med_host_lookup, median(n_error) AS med_errors
 FROM i2 i LEFT JOIN paid p USING (user_id) GROUP BY 1""")

print("2. Последняя активность после инцидента (дни до последней сессии)")
q("""WITH last_s AS (SELECT user_id, max(created_at) AS last_at FROM sessions GROUP BY 1),
 firsti AS (SELECT user_id, min(day) AS first_inc FROM i2 GROUP BY 1)
 SELECT count(*) AS users,
  count_if(date_diff('day', f.first_inc, l.last_at) <= 1) AS gone_within_1d,
  count_if(date_diff('day', f.first_inc, l.last_at) > 7) AS active_after_week
 FROM firsti f JOIN last_s l USING (user_id)""")

print("3. Версии приложения: инциденты, ошибки на инцидент")
q("""SELECT app_version, count(*) AS n, round(median(n_error)) AS med_err,
 round(median(host_lookup)) AS med_dns FROM i2
 GROUP BY 1 ORDER BY 2 DESC LIMIT 6""")