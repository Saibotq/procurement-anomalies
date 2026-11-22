import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

con.sql("""CREATE OR REPLACE TEMP TABLE adv AS
 SELECT TRY_CAST(user_id AS BIGINT) AS user_id,
  CAST(TRY_CAST(created_at AS TIMESTAMP) AS DATE) AS day
 FROM adv_view_history
 WHERE TRY_CAST(user_id AS BIGINT) IS NOT NULL
   AND TRY_CAST(created_at AS TIMESTAMP) IS NOT NULL""")

print("0. Подписки по тарифам")
q("SELECT product_id, count(*) AS n FROM subscribe GROUP BY 1 ORDER BY 1")

print("1. Просмотры рекламы: период и охват")
q("SELECT count(*) AS views, count(DISTINCT user_id) AS users, min(day), max(day) FROM adv")

print("2. Просмотров рекламы на пользователя в день")
q("""WITH ud AS (SELECT user_id, day, count(*) AS n FROM adv GROUP BY 1,2)
 SELECT count(*) AS user_days, median(n) AS med,
  quantile_cont(n,0.75) AS p75, quantile_cont(n,0.9) AS p90,
  quantile_cont(n,0.99) AS p99, max(n) AS max FROM ud""")

print("3. Распределение по числу просмотров в день")
q("""WITH ud AS (SELECT user_id, day, count(*) AS n FROM adv GROUP BY 1,2)
 SELECT CASE WHEN n=1 THEN '1' WHEN n=2 THEN '2' WHEN n=3 THEN '3'
  WHEN n<=5 THEN '4-5' WHEN n<=10 THEN '6-10' WHEN n<=20 THEN '11-20'
  ELSE '21+' END AS views_per_day, count(*) AS user_days
 FROM ud GROUP BY 1 ORDER BY min(n)""")

print("4. Конверсия в покупку по числу просмотров рекламы за всё время")
q("""WITH u AS (SELECT user_id, count(*) AS views FROM adv GROUP BY 1),
 paid AS (SELECT DISTINCT user_id FROM orders WHERE status='paid' AND NOT trial)
 SELECT CASE WHEN views<=5 THEN '1-5' WHEN views<=20 THEN '6-20'
  WHEN views<=100 THEN '21-100' ELSE '100+' END AS bucket,
  count(*) AS users, count_if(p.user_id IS NOT NULL) AS bought,
  round(100.0*count_if(p.user_id IS NOT NULL)/count(*), 2) AS pct
 FROM u LEFT JOIN paid p USING (user_id) GROUP BY 1 ORDER BY min(views)""")

print("5. Подключения по тарифам (сырые логи, может идти несколько минут)")
con.sql("""CREATE OR REPLACE TEMP TABLE c AS
 SELECT TRY_CAST(l.user_id AS BIGINT) AS user_id,
  CAST(TRY_CAST(l.created_at AS TIMESTAMP) AS DATE) AS day,
  s.product_id, count(*) AS n
 FROM user_connection_logs l
 JOIN subscribe s ON TRY_CAST(l.subscribe_id AS BIGINT) = s.id
 WHERE TRY_CAST(l.created_at AS TIMESTAMP) IS NOT NULL
 GROUP BY ALL""")
q("""SELECT product_id, count(*) AS user_days, median(n) AS med,
  quantile_cont(n,0.9) AS p90, quantile_cont(n,0.99) AS p99
 FROM c GROUP BY 1 ORDER BY 1""")

print("6. Free-тариф: дни с рекламой и без")
q("""SELECT (a.user_id IS NOT NULL) AS watched_ad, count(*) AS user_days,
  median(n) AS med_conn, quantile_cont(n,0.9) AS p90_conn
 FROM c LEFT JOIN (SELECT DISTINCT user_id, day FROM adv) a USING (user_id, day)
 WHERE c.product_id = 1 GROUP BY 1""")