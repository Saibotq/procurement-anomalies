import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

print("1. Идентификаторы с самым большим числом аккаунтов")
q("""SELECT substr(device_identifier, 1, 16) AS ident, count(DISTINCT user_id) AS accounts
 FROM devices WHERE device_identifier IS NOT NULL
 GROUP BY device_identifier ORDER BY 2 DESC LIMIT 8""")

con.sql("""CREATE OR REPLACE TEMP TABLE d AS
 SELECT device_identifier FROM devices WHERE device_identifier IS NOT NULL
 GROUP BY 1 HAVING count(DISTINCT user_id) BETWEEN 2 AND 10""")
con.sql("""CREATE OR REPLACE TEMP TABLE tr AS
 SELECT DISTINCT user_id FROM orders WHERE trial AND status = 'paid'""")

print("2. Только устройства с 2-10 аккаунтами")
q("""SELECT count(DISTINCT x.user_id) AS users, count(DISTINCT tr.user_id) AS with_trial
 FROM (SELECT DISTINCT user_id, device_identifier FROM devices) x
 JOIN d USING (device_identifier) LEFT JOIN tr ON tr.user_id = x.user_id""")

print("3. Устройства, где несколько аккаунтов брали платный триал")
q("""WITH x AS (SELECT d.device_identifier, count(DISTINCT tr.user_id) AS trials
  FROM d JOIN (SELECT DISTINCT user_id, device_identifier FROM devices) u
   USING (device_identifier)
  LEFT JOIN tr ON tr.user_id = u.user_id GROUP BY 1)
 SELECT count(*) AS devices, count_if(trials >= 2) AS multi_trial_devices,
  sum(greatest(trials - 1, 0)) AS extra_trials FROM x""")