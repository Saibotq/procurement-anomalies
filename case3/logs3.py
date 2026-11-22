import zipfile, io, os, re, csv
os.chdir(os.path.dirname(os.path.abspath(__file__)))
z = zipfile.ZipFile("data/logs.zip")
run = re.compile(r"Running on Os\.(\w+); OS version ([^;]+); App version (\S+)")
line_re = re.compile(r"\[(.*?)\]\s+\S+\s+\S+\s+\[(\w)\]\s+(.*)")
FIELDS = ["user_id","code","day","size_mb","os","os_version","app_version",
 "n_info","n_warn","n_error","n_fatal","host_lookup","network_exc","timeout",
 "push_unavail","auth_verify","vpn_err_total","tun_refused","dns_pending",
 "access_lines","note"]
out = open("incidents.csv", "w", newline="", encoding="utf-8")
w = csv.DictWriter(out, fieldnames=FIELDS, delimiter=";")
w.writeheader()
entries = [i for i in z.infolist() if i.filename.endswith(".zip")]
LV = {"I": "n_info", "W": "n_warn", "E": "n_error", "F": "n_fatal"}

for n, e in enumerate(entries, 1):
    _, uid, fn = e.filename.split("/")
    row = dict.fromkeys(FIELDS, 0)
    row.update(user_id=uid, code=fn[:-4], day="%04d-%02d-%02d" % e.date_time[:3],
               size_mb=round(e.file_size / 1e6, 1), os="", os_version="",
               app_version="", note="")
    if e.file_size > 200e6:
        row["note"] = "skipped_big"
        w.writerow(row)
        continue
    try:
        inner = zipfile.ZipFile(io.BytesIO(z.read(e)))
        for i in inner.infolist():
            name = i.filename.strip()
            if name.endswith(".log"):
                for line in inner.open(i):
                    s = line.decode("utf-8", "replace")
                    if not row["os"]:
                        m = run.search(s)
                        if m:
                            row["os"], row["os_version"], row["app_version"] = m.groups()
                    m = line_re.match(s)
                    if not m:
                        continue
                    lvl, msg = m.group(2), m.group(3)
                    if lvl in LV:
                        row[LV[lvl]] += 1
                    if lvl in "EWF":
                        if "Failed host lookup" in msg: row["host_lookup"] += 1
                        if "Network Exception" in msg: row["network_exc"] += 1
                        if "imeout" in msg: row["timeout"] += 1
                        if "Cloud messaging service is not available" in msg: row["push_unavail"] += 1
                        if "auth/verify" in msg: row["auth_verify"] += 1
            elif name == "vpn_error_log.txt":
                for line in inner.open(i):
                    s = line.decode("utf-8", "replace")
                    row["vpn_err_total"] += 1
                    if "connection was refused" in s: row["tun_refused"] += 1
                    if "pending request" in s: row["dns_pending"] += 1
            elif name == "vpn_access_log.txt":
                with inner.open(i) as f:
                    while chunk := f.read(1 << 20):
                        row["access_lines"] += chunk.count(b"\n")
    except Exception as ex:
        row["note"] = "error:" + str(ex)[:40]
    w.writerow(row)
    if n % 25 == 0:
        out.flush()
        print(n, "из", len(entries), flush=True)
out.close()
print("готово")