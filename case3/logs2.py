import zipfile, io, os, re, collections
os.chdir(os.path.dirname(os.path.abspath(__file__)))
z = zipfile.ZipFile("data/logs.zip")
inner = zipfile.ZipFile(io.BytesIO(z.read("logs/1003739/DARSSGUJM8.zip")))
ip = re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b")
tok = re.compile(r"[A-Za-z0-9_\-]{25,}")
def clean(s): return tok.sub("<tok>", ip.sub("x.x.x.x", s))[:220]

for name in ["vpn_access_log.txt", "vpn_error_log.txt", "peepster_logs.txt"]:
    print("=====", name)
    with inner.open(name) as f:
        for _, line in zip(range(6), f):
            print(clean(line.decode("utf-8", "replace").rstrip()))

levels = collections.Counter()
cnt = collections.Counter()
for i in inner.infolist():
    if i.filename.strip().endswith(".log"):
        for line in inner.read(i).decode("utf-8", "replace").splitlines():
            m = re.match(r"\[(.*?)\]\s+\S+\s+\S+\s+\[(\w)\]\s+(.*)", line)
            if m:
                levels[m.group(2)] += 1
                if m.group(2) in "EW":
                    msg = re.sub(r"\d+", "N", clean(m.group(3)))[:120]
                    cnt[(m.group(2), m.group(1), msg)] += 1
print("=====", dict(levels))
for k, v in cnt.most_common(12):
    print(v, k)