import duckdb, glob, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect("practice.duckdb")

def make_view(view, pattern, table):
    with open(f"data/db_structure/{table}.csv", encoding="utf-8-sig") as f:
        names = f.readline().strip().split(";")
    con.execute(f"""CREATE OR REPLACE VIEW {view} AS
        SELECT * FROM read_csv('{pattern}', delim=';', header=false,
        names={names}, sample_size=20000, null_padding=true,
        strict_mode=false)""")

for f in glob.glob("data/*.csv"):
    name = os.path.splitext(os.path.basename(f))[0]
    if name.startswith("user_connection_logs"):
        continue
    try:
        make_view(name, f.replace("\\", "/"), name)
        print("ok:", name)
    except Exception as e:
        print("ПРОПУЩЕН:", name, "|", str(e)[:100].replace("\n", " "))

try:
    make_view("user_connection_logs", "data/user_connection_logs*.csv", "user_connection_logs")
    print("ok: user_connection_logs")
except Exception as e:
    print("ПРОПУЩЕН: user_connection_logs |", str(e)[:150].replace("\n", " "))
print("готово")