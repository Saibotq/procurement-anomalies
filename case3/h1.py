import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

print("1. Сколько аккаунтов на одном устройстве")
q("""SELECT accounts, count(*) AS devices FROM (
 SELECT device_identifier, count(DISTINCT user_id) AS accounts
 FROM devices WHERE device_identifier IS NOT NULL GROUP BY 1)
 GROUP BY 1 ORDER BY 1 LIMIT 15""")

print("2. Платные триалы: общие устройства vs одиночные")
q("""WITH d AS (SELECT device_identifier, count(DISTINCT user_id) AS accounts
  FROM devices WHERE device_identifier IS NOT NULL GROUP BY 1),
 ud AS (SELECT DISTINCT user_id, device_identifier FROM devices
  WHERE device_identifier IS NOT NULL),
 tr AS (SELECT DISTINCT user_id FROM orders WHERE trial AND status = 'paid')
 SELECT (d.accounts > 1) AS shared_device,
  count(DISTINCT ud.user_id) AS users,
  count(DISTINCT tr.user_id) AS with_trial
 FROM ud JOIN d USING (device_identifier)
 LEFT JOIN tr ON tr.user_id = ud.user_id GROUP BY 1""")