import duckdb, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")
q = lambda s: con.sql(s).show()

print("1. Масштаб программы")
q("""SELECT count(*) AS used_codes,
 count(DISTINCT referer_user_id) AS referrers,
 count(DISTINCT referal_user_id) AS referred FROM referral_code_used""")

print("2. Приглашённые vs остальные: триал и покупка")
q("""WITH r AS (SELECT DISTINCT TRY_CAST(referal_user_id AS BIGINT) AS user_id
   FROM referral_code_used),
 paid AS (SELECT DISTINCT user_id FROM orders WHERE status='paid' AND NOT trial),
 tr AS (SELECT DISTINCT user_id FROM orders WHERE status='paid' AND trial)
 SELECT (r.user_id IS NOT NULL) AS referred, count(*) AS users,
  round(100.0*count_if(t.user_id IS NOT NULL)/count(*), 2) AS pct_trial,
  round(100.0*count_if(p.user_id IS NOT NULL)/count(*), 2) AS pct_bought
 FROM users u LEFT JOIN r ON r.user_id = u.id
 LEFT JOIN paid p ON p.user_id = u.id LEFT JOIN tr t ON t.user_id = u.id
 GROUP BY 1""")

print("3. Начисления рефереру")
q("""SELECT count(*) AS accruals, count(DISTINCT referrer_id) AS referrers_paid,
 round(sum(accrual), 2) AS total, round(avg(accrual), 2) AS avg_accrual,
 round(avg(percentage), 1) AS avg_pct FROM referral_history""")

print("4. Доля топ-10 рефереров в начислениях")
q("""WITH s AS (SELECT referrer_id, sum(accrual) AS a FROM referral_history GROUP BY 1),
 r AS (SELECT a, row_number() OVER (ORDER BY a DESC) AS rn FROM s)
 SELECT round(100.0*sum(a) FILTER (WHERE rn <= 10)/sum(a), 1) AS top10_pct FROM r""")

print("5. Реферер и приглашённый на одном устройстве (признак накрутки)")
q("""WITH d AS (SELECT device_identifier FROM devices WHERE device_identifier IS NOT NULL
   GROUP BY 1 HAVING count(DISTINCT user_id) BETWEEN 2 AND 10),
 ud AS (SELECT DISTINCT user_id, device_identifier FROM devices JOIN d USING (device_identifier))
 SELECT count(*) AS pairs,
  count_if(EXISTS (SELECT 1 FROM ud a JOIN ud b USING (device_identifier)
   WHERE a.user_id = TRY_CAST(r.referer_user_id AS BIGINT)
     AND b.user_id = TRY_CAST(r.referal_user_id AS BIGINT))) AS same_device
 FROM referral_code_used r""")