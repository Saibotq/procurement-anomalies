import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

con.sql("""CREATE OR REPLACE TEMP TABLE c AS
 SELECT TRY_CAST(l.user_id AS BIGINT) AS user_id,
  CAST(TRY_CAST(l.created_at AS TIMESTAMP) AS DATE) AS day,
  (s.id IS NULL) AS is_free, count(*) AS n
 FROM user_connection_logs l
 LEFT JOIN subscribe s ON TRY_CAST(l.subscribe_id AS BIGINT) = s.id
 WHERE TRY_CAST(l.created_at AS TIMESTAMP) IS NOT NULL
 GROUP BY ALL""")
con.sql("""CREATE OR REPLACE TEMP TABLE adv AS
 SELECT TRY_CAST(user_id AS BIGINT) AS user_id,
  CAST(TRY_CAST(created_at AS TIMESTAMP) AS DATE) AS day, count(*) AS views
 FROM adv_view_history
 WHERE TRY_CAST(user_id AS BIGINT) IS NOT NULL
   AND TRY_CAST(created_at AS TIMESTAMP) IS NOT NULL GROUP BY 1,2""")

print("1. Дни подключения: free или платный, и доля дней с рекламой")
q("""SELECT c.is_free, count(*) AS user_days,
  round(100.0*count_if(a.views IS NOT NULL)/count(*), 1) AS pct_with_ads,
  median(c.n) AS med_conn, quantile_cont(c.n,0.9) AS p90_conn
 FROM c LEFT JOIN adv a USING (user_id, day) GROUP BY 1""")

print("2. Free: подключения в день по числу просмотров рекламы")
q("""SELECT CASE WHEN a.views IS NULL THEN '0' WHEN a.views<=3 THEN '1-3'
  WHEN a.views<=10 THEN '4-10' ELSE '11+' END AS ads_that_day,
  count(*) AS user_days, median(c.n) AS med_conn, quantile_cont(c.n,0.9) AS p90_conn
 FROM c LEFT JOIN adv a USING (user_id, day) WHERE c.is_free
 GROUP BY 1 ORDER BY 1""")

print("3. Free: сколько дней подряд пользователи остаются на free до первой покупки")
q("""WITH f AS (SELECT user_id, count(DISTINCT day) AS free_days
  FROM c WHERE is_free GROUP BY 1),
 paid AS (SELECT DISTINCT user_id FROM orders WHERE status='paid' AND NOT trial)
 SELECT CASE WHEN free_days<=3 THEN '1-3' WHEN free_days<=14 THEN '4-14'
  WHEN free_days<=60 THEN '15-60' ELSE '60+' END AS free_days_bucket,
  count(*) AS users, count_if(p.user_id IS NOT NULL) AS bought,
  round(100.0*count_if(p.user_id IS NOT NULL)/count(*), 2) AS pct
 FROM f LEFT JOIN paid p USING (user_id) GROUP BY 1 ORDER BY min(free_days)""")