import zipfile, io, os, re, duckdb
os.chdir(os.path.dirname(os.path.abspath(__file__)))
z = zipfile.ZipFile("data/logs.zip")
ids = sorted({int(m.group(1)) for n in z.namelist()
              if (m := re.match(r"logs/(\d+)/", n))})
print("пользователей в logs:", len(ids))

con = duckdb.connect("practice.duckdb")
con.sql("CREATE OR REPLACE TEMP TABLE lid(id BIGINT)")
con.executemany("INSERT INTO lid VALUES (?)", [(i,) for i in ids])
con.sql("""SELECT count(*) AS found_in_users,
 count_if(id IN (SELECT user_id FROM orders WHERE status='paid')) AS with_paid
 FROM lid WHERE id IN (SELECT id FROM users)""").show()

inner = zipfile.ZipFile(io.BytesIO(z.read("logs/1003739/DARSSGUJM8.zip")))
files = [i for i in inner.infolist() if not i.filename.endswith("/")]
for i in files:
    print(i.filename, i.file_size)
print("-----")
print(inner.read(files[0])[:2500].decode("utf-8", errors="replace"))