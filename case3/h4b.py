import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

con.sql("""CREATE OR REPLACE TEMP TABLE inc AS
 SELECT * FROM read_csv('incidents.csv', delim=';', header=true, all_varchar=true)""")
con.sql("""CREATE OR REPLACE TEMP TABLE f AS
 SELECT CAST(user_id AS BIGINT) AS user_id, min(CAST(day AS DATE)) AS first_inc
 FROM inc GROUP BY 1""")

con.sql("""CREATE OR REPLACE TEMP TABLE a AS
 SELECT TRY_CAST(user_id AS BIGINT) AS user_id,
  min(CAST(TRY_CAST(created_at AS TIMESTAMP) AS DATE)) AS first_conn,
  max(CAST(TRY_CAST(created_at AS TIMESTAMP) AS DATE)) AS last_conn
 FROM user_connection_logs
 WHERE TRY_CAST(user_id AS BIGINT) IN (SELECT user_id FROM f)
   AND TRY_CAST(created_at AS TIMESTAMP) IS NOT NULL
 GROUP BY 1""")

print("Период подключений у этих пользователей")
q("SELECT min(first_conn), max(last_conn) FROM a")

print("Активность после первого инцидента")
q("""SELECT count(*) AS users,
  count_if(a.user_id IS NULL) AS never_connected,
  count_if(a.last_conn <= f.first_inc) AS none_after_incident,
  count_if(a.last_conn > f.first_inc + INTERVAL 7 DAY) AS active_after_week
 FROM f LEFT JOIN a USING (user_id)""")