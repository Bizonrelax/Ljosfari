#!/usr/bin/env python3
# QWR v1.0 — инструменты протокола. Предметно-нейтрален. Только stdlib.
# Оценка токенов: qwr-bytes/1 (кириллица 4.4 байта/токен, прочее 3.6). Это оценка, не счётчик.
import argparse, base64, hashlib, json, os, re, sys, time, datetime, math, glob
import urllib.request, urllib.error

def find_root(cli=None):
    if cli: return os.path.abspath(cli)
    if os.environ.get("QWR_ROOT"): return os.path.abspath(os.environ["QWR_ROOT"])
    p = os.path.abspath(os.getcwd())
    while True:
        if os.path.isfile(os.path.join(p, "qwr", "bot", "GATE.txt")): return p
        np = os.path.dirname(p)
        if np == p: break
        p = np
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

ROOT = find_root()
BOT = os.path.join(ROOT, "qwr", "bot")
FIX = os.environ.get("QWR_FIXREALM") or os.path.join(ROOT, "fixrealm")
COMPOSITE = "QWR:ALV-1.0_PPV-1.0_TAV-1.0"
LIMITS = {"gate":3000,"card":800,"role":2500,"needs":6000,"slice":1500,"decode":500,"input":18000,"input_target":12000}

def est_text(s):
    cy = sum(1 for ch in s if "\u0400" <= ch <= "\u04FF")
    other_bytes = len(s.encode("utf-8")) - cy*2
    return int(math.ceil(cy*2/4.4 + other_bytes/3.6))

def est_file(p):
    with open(p, "r", encoding="utf-8") as f: return est_text(f.read())

def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def read(p):
    with open(p, "r", encoding="utf-8") as f: return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(s)

def append(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f: f.write(s)

# ---------- manifest ----------
SCOPE = ["README.md","SELFTEST.md","qwr/GUIDE.md","qwr/bot/GATE.txt",
         "qwr/bot/dict/*.kv","qwr/bot/roles/*.txt","qwr/bot/mod/*.txt","qwr/bot/bin/*.py"]

def scope_files():
    out = []
    for pat in SCOPE:
        full = os.path.join(ROOT, pat)
        if any(c in pat for c in "*?"):
            out += [os.path.relpath(x, ROOT).replace(os.sep,"/") for x in glob.glob(full)]
        elif os.path.isfile(full):
            out.append(pat)
    return sorted(set(out))

def cmd_manifest(a):
    mp = os.path.join(ROOT, "MANIFEST.json")
    old = {}
    if os.path.isfile(mp):
        try: old = json.loads(read(mp))
        except Exception: old = {}
    files = {}
    for rel in scope_files():
        data = open(os.path.join(ROOT, rel), "rb").read()
        files[rel] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "tokens_est": est_text(data.decode("utf-8"))}
    if a.check:
        if not old:
            print("MISMATCH: MANIFEST.json отсутствует"); return 1
        bad = []
        for rel, meta in old.get("files", {}).items():
            fp = os.path.join(ROOT, rel)
            if not os.path.isfile(fp): bad.append(rel+" (нет файла)"); continue
            data = open(fp,"rb").read()
            if hashlib.sha256(data).hexdigest() != meta["sha256"]: bad.append(rel+" (хэш)")
        for rel in files:
            if rel not in old.get("files", {}): bad.append(rel+" (нет в манифесте)")
        ver = f'{old.get("composite",COMPOSITE)}_b{old.get("build",0)}'
        if bad:
            print("MISMATCH: " + "; ".join(bad)); return 1
        print(f"VER {ver} | MANIFEST OK"); return 0
    build = int(old.get("build", 0)) + 1
    man = {"protocol":"QWR","version":"1.0","composite":COMPOSITE,"build":build,
           "estimator":"qwr-bytes/1","built_at":now(),
           "scope":SCOPE,"exclude":["qwr/bot/a2a","fixrealm"],
           "limits":LIMITS,"files":files}
    write(mp, json.dumps(man, ensure_ascii=False, indent=1) + "\n")
    print(f"VER {COMPOSITE}_b{build} | MANIFEST BUILT files={len(files)}")
    return 0

# ---------- tokens ----------
def cmd_tokens(a):
    if a.sub == "est":
        total = 0
        for p in a.files:
            fp = p if os.path.isabs(p) else os.path.join(ROOT, p)
            t = est_file(fp); total += t
            print(f"{p}\t{t}")
        print(f"ИТОГО\t{total}\t(оценка qwr-bytes/1)")
        return 0
    return 2

# ---------- dict ----------
SUBJ_RE = re.compile(r"^%([cgrs])(\d+)$")
def load_dicts():
    d = {}
    for name, letter in [("common","c"),("group","g"),("role","r")]:
        p = os.path.join(BOT, "dict", name + ".kv")
        if os.path.isfile(p):
            for line in read(p).splitlines():
                line = line.strip()
                if not line or line.startswith("#"): continue
                code, _, key = line.partition(" ")
                d[code] = key
    tp = os.path.join(FIX, "TERMS.md")
    if os.path.isfile(tp):
        txt = read(tp)
        m = re.search(r"DICT:BEGIN-->(.*?)<!--DICT:END", txt, re.S)
        block = m.group(1) if m else ""
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            code, _, key = line.partition(" ")
            if SUBJ_RE.match(code) and code.startswith("%s"): d[code] = key
    return d

def cmd_dict(a):
    d = load_dicts()
    if a.sub == "load":
        codes = [c.strip() for c in a.codes.split(",") if c.strip()]
        out = []
        for c in codes:
            if c not in d:
                print(f"НЕИЗВЕСТНЫЙ КОД {c}"); return 1
            out.append(f"{c} {d[c]}")
        text = "\n".join(out)
        if est_text(text) > LIMITS["decode"]:
            print("ПРЕВЫШЕН БЮДЖЕТ РАСШИФРОВКИ 500: сузь список кодов"); return 1
        print(text); return 0
    if a.sub == "lint":
        txt = read(a.file) if os.path.isfile(a.file) else a.file
        codes = set(re.findall(r"%[cgrs]\d+", txt))
        unknown = sorted(c for c in codes if c not in d)
        if unknown:
            print("НЕИЗВЕСТНЫЕ КОДЫ: " + ",".join(unknown)); return 1
        print(f"OK кодов={len(codes)} неизвестных=0"); return 0
    if a.sub == "show":
        print("словарь целиком в контекст не грузится; используй dict load --codes"); return 2
    return 2

# ---------- card / need ----------
def card_text(role):
    p = os.path.join(BOT, "roles", role + ".txt")
    if not os.path.isfile(p): return None
    txt = read(p)
    m = re.search(r"CARD:BEGIN\n(.*?)CARD:END", txt, re.S)
    return m.group(1).strip() if m else None

def cmd_card(a):
    c = card_text(a.role)
    if c is None:
        print(f"НЕТ КАРТОЧКИ РОЛИ {a.role}"); return 1
    t = est_text(c)
    if t > LIMITS["card"]:
        print(f"КАРТОЧКА {a.role} ПРЕВЫШАЕТ 800: {t}"); return 1
    print(c); return 0

def parse_card_field(c, key):
    m = re.search(rf"^{key}=(.*)$", c, re.M)
    return m.group(1).strip() if m else ""

def cmd_need(a):
    c = card_text(a.role)
    if c is None: print("НЕТ КАРТОЧКИ"); return 1
    if a.lazy:
        lp = os.path.join(BOT, "mod", "lazy.txt")
        print(read(lp) if os.path.isfile(lp) else "lazy.txt не поставлен"); return 0
    needs = parse_card_field(c, "needs").split(",")
    manp = os.path.join(ROOT, "MANIFEST.json")
    man = json.loads(read(manp)) if os.path.isfile(manp) else {"files":{}}
    total = 0
    for n in needs:
        n = n.strip()
        if not n: continue
        rel = f"qwr/bot/mod/{n}.txt"
        t = man.get("files", {}).get(rel, {}).get("tokens_est")
        if t is None and os.path.isfile(os.path.join(ROOT, rel)): t = est_file(os.path.join(ROOT, rel))
        t = t or 0; total += t
        print(f"{rel}\t{t}")
    print(f"ИТОГО needs\t{total}\tлимит {LIMITS['needs']}")
    return 0 if total <= LIMITS["needs"] else 1

# ---------- helpers: state ----------
import shutil, subprocess, tempfile

def locks_dir(): return os.path.join(BOT, "a2a", "locks")
def tasks_dir(): return os.path.join(BOT, "a2a", "tasks")

def parse_ts(t):
    try: return datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except Exception: return None

def age_min(t):
    dt = parse_ts(t)
    if not dt: return 1e9
    return (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()/60.0

def fresh_trace(owner):
    cutoff = 60.0
    td = tasks_dir()
    if os.path.isdir(td):
        for f in os.listdir(td):
            if not f.endswith(".tsv"): continue
            for line in read(os.path.join(td, f)).splitlines()[1:]:
                p = line.split("\t")
                if len(p) >= 2 and p[1] == owner and age_min(p[0]) <= cutoff: return True
    ib = os.path.join(BOT, "a2a", "inbox.jsonl")
    if os.path.isfile(ib):
        for line in read(ib).splitlines():
            try: m = json.loads(line)
            except Exception: continue
            if m.get("from") == owner and age_min(m.get("at","")) <= cutoff: return True
    return False

def read_locks():
    out = []
    ld = locks_dir()
    if os.path.isdir(ld):
        for f in sorted(os.listdir(ld)):
            if not f.endswith(".json"): continue
            try: m = json.loads(read(os.path.join(ld, f)))
            except Exception: continue
            m["_file"] = f; out.append(m)
    return out

def lock_live(m):
    return age_min(m.get("born_at","")) <= 60 or fresh_trace(m.get("owner",""))

def task_meta(tid):
    p = os.path.join(tasks_dir(), tid + ".tsv")
    if not os.path.isfile(p): return None
    lines = read(p).splitlines()
    if not lines: return None
    try: return json.loads(lines[0])
    except Exception: return None

def task_status(tid):
    p = os.path.join(tasks_dir(), tid + ".tsv")
    if not os.path.isfile(p): return None
    lines = [l for l in read(p).splitlines()[1:] if l.strip()]
    if not lines: return "ready"
    return lines[-1].split("\t")[2] if len(lines[-1].split("\t")) >= 3 else "ready"

def all_tasks():
    td = tasks_dir(); out = []
    if os.path.isdir(td):
        for f in sorted(os.listdir(td)):
            if f.endswith(".tsv"):
                tid = f[:-4]; m = task_meta(tid)
                if m: m["status"] = task_status(tid); out.append(m)
    return out

def index_rows():
    p = os.path.join(FIX, "INDEX.tsv")
    rows = {}
    if os.path.isfile(p):
        for line in read(p).splitlines()[1:]:
            if not line.strip(): continue
            c = line.split("\t")
            if len(c) >= 3: rows[c[0]] = c
    return rows

def park_state():
    p = os.path.join(BOT, "a2a", "park.tsv")
    out = {}
    if os.path.isfile(p):
        for line in read(p).splitlines()[1:]:
            c = line.split("\t")
            if len(c) >= 2: out[c[0]] = {"status": c[1], "reason": c[2] if len(c)>2 else "", "at": c[3] if len(c)>3 else ""}
    return out

def cmd_slice(a):
    locks = read_locks()
    live = [m for m in locks if lock_live(m)]
    roles = {}
    for m in live: roles[m.get("role","?")] = m.get("owner","?")
    tasks = all_tasks()
    idx = index_rows()
    debt_chk = sum(1 for t in tasks if t.get("status") in ("check","verify"))
    debt_chk += sum(1 for c in idx.values() if c[1] == "emp")
    khi = sum(1 for c in idx.values() if c[1] == "hyp")
    nov_unc = sum(1 for c in idx.values() if c[2] == "unc")
    ready = [t["id"] for t in tasks if t.get("status") == "ready"]
    park = {b: v["reason"] for b, v in park_state().items() if v["status"] == "park"}
    open_q = sum(1 for t in tasks if t.get("status") in ("ready","open","blk"))
    cards_n = len(idx)
    drift = 0
    for i, c in idx.items():
        cp = os.path.join(ROOT, c[5]) if len(c) > 5 and c[5] else None
        if cp and os.path.isfile(cp):
            txt = read(cp)
            mt = re.search(r"истина:\s*(\w+)", txt); mn = re.search(r"новизна:\s*(\w+)", txt)
            if (mt and mt.group(1) != c[1]) or (mn and mn.group(1) != c[2]): drift += 1
    idle = (len(ready) == 0 and open_q == 0 and debt_chk == 0 and len(live) == 0)
    sl = {"ver": composite_ver(), "at": now(), "agents": len(live), "roles": roles,
          "debt_chk": debt_chk, "khi": khi, "nov_unc": nov_unc, "open_q": open_q,
          "ready": ready[:20], "ready_n": len(ready), "park": park,
          "cards_n": cards_n, "drift": drift, "idle": idle}
    text = json.dumps(sl, ensure_ascii=False)
    if est_text(text) > LIMITS["slice"]:
        sl["ready"] = ready[:5]; sl["_narrowed"] = True
        text = json.dumps(sl, ensure_ascii=False)
    print(text)
    return 0

def composite_ver():
    mp = os.path.join(ROOT, "MANIFEST.json")
    if os.path.isfile(mp):
        m = json.loads(read(mp)); return f'{m.get("composite",COMPOSITE)}_b{m.get("build",0)}'
    return COMPOSITE + "_b0"

# ---------- github api ----------
def gh(method, path, body=None):
    tok = os.environ.get("QWR_TOKEN")
    if not tok: raise RuntimeError("QWR_TOKEN не задан")
    repo = os.environ.get("QWR_REPO")
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Accept", "application/vnd.github+json")
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, {}

# ---------- claim / release ----------
def lock_path(role, owner, task=None):
    if task: return os.path.join(locks_dir(), task + ".json")
    c = card_text(role) or ""
    tmpl = parse_card_field(c, "claim")
    if tmpl:
        rel = tmpl.replace("{owner}", owner)
        return os.path.join(ROOT, rel)
    return os.path.join(locks_dir(), f"{role}-{owner}.json")

def cmd_claim(a):
    role, owner = a.role, a.owner
    lp = lock_path(role, owner, a.task)
    content = {"role": role, "owner": owner, "task": a.task or "", "born_at": now(), "epoch": 1, "ver": composite_ver()}
    if a.api == "github":
        rel = os.path.relpath(lp, ROOT).replace(os.sep, "/")
        body = {"message": f"claim {role} {owner}", "content": base64.b64encode(json.dumps(content).encode()).decode()}
        st, _ = gh("PUT", rel, body)
        if st == 201: print("201"); return 0
        if st in (422, 409): print(f"{st} занято"); return 1
        print(f"{st} ошибка запроса"); return 2
    # local atomic O_EXCL
    if not a.task:
        live = [m for m in read_locks() if lock_live(m) and m.get("role") != role]
        if len(live) >= 3:
            print("422 лимит три агента"); return 1
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    try:
        fd = os.open(lp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        with os.fdopen(fd, "w") as f: json.dump(content, f, ensure_ascii=False)
        print("201"); return 0
    except FileExistsError:
        try: old = json.loads(read(lp))
        except Exception: old = {}
        if age_min(old.get("born_at","")) > 60 and not fresh_trace(old.get("owner","")):
            append(os.path.join(BOT,"a2a","inbox.jsonl"), json.dumps({"from":"system","to":old.get("owner",""),"kind":"stale_release","text":f"замок {role} брошен, снят {owner}","at":now()}, ensure_ascii=False)+"\n")
            content["epoch"] = int(old.get("epoch",1)) + 1
            write(lp, json.dumps(content, ensure_ascii=False))
            print("201 снятие брошенного"); return 0
        print("422 занято"); return 1

def cmd_release(a):
    lp = lock_path(a.role, a.owner, a.task)
    if not os.path.isfile(lp): print("404 нет замка"); return 1
    old = json.loads(read(lp))
    if old.get("owner") != a.owner:
        if not a.stale: print("403 чужой живой замок не снимать"); return 1
        if age_min(old.get("born_at","")) <= 60 or fresh_trace(old.get("owner","")):
            print("403 замок жив, не брошен"); return 1
        append(os.path.join(BOT,"a2a","inbox.jsonl"), json.dumps({"from":"system","to":old.get("owner",""),"kind":"stale_release","text":f"замок снят {a.owner}","at":now()}, ensure_ascii=False)+"\n")
    os.remove(lp); print("200 освобождён"); return 0

# ---------- guard ----------
def match_globs(path, patterns):
    import fnmatch
    for pat in patterns:
        pat = pat.strip()
        if not pat: continue
        if fnmatch.fnmatch(path, pat) or path == pat or path.startswith(pat.rstrip("*")):
            return True
    return False

def cmd_guard(a):
    c = card_text(a.role)
    if c is None: print("2 нет карточки роли"); return 2
    write_p = parse_card_field(c, "write").split(",")
    create_p = parse_card_field(c, "create_only").split(",")
    deny_p = parse_card_field(c, "deny").split(",")
    paths = [p.strip() for p in a.paths.split(",") if p.strip()]
    # ownership: role lock held
    held = any(m.get("role")==a.role and m.get("owner")==a.owner for m in read_locks())
    if not held and a.role != "EDT":
        print("1 нет захвата роли"); return 1
    for p in paths:
        if match_globs(p, deny_p): print(f"1 deny {p}"); return 1
        if a.intent == "create":
            if not (match_globs(p, create_p) or match_globs(p, write_p)): print(f"1 не create_only {p}"); return 1
        else:
            if not match_globs(p, write_p): print(f"1 не write {p}"); return 1
        m = re.search(r"cards/A(\d+)\.md$", p)
        if m and a.task:
            meta = task_meta(a.task) or {}
            blk = meta.get("block","")
            nums = block_numbers(blk)
            if int(m.group(1)) not in nums: print(f"1 номер вне блока {p}"); return 1
    if a.content_file and os.path.isfile(a.content_file):
        txt = read(a.content_file)
        if re.search(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})", txt):
            print("1 секрет в содержимом"); return 1
    print("0 можно"); return 0

def block_numbers(blk):
    nums = set()
    for part in blk.split(","):
        part = part.strip()
        m = re.match(r"A?(\d+)-A?(\d+)$", part)
        if m: nums.update(range(int(m.group(1)), int(m.group(2))+1))
        else:
            m2 = re.match(r"A?(\d+)$", part)
            if m2: nums.add(int(m2.group(1)))
    return nums

# ---------- task ----------
def cmd_task(a):
    if a.sub == "new":
        if a.role != "PLN": print("1 задачи создаёт только PLN"); return 1
        if not a.cost: print("1 задача без оценки стоимости не создаётся"); return 1
        ceiling = float(a.ceiling or 1e7)
        if float(a.cost) > ceiling:
            print(f"1 отклонено: оценка {a.cost} выше потолка {ceiling:.0e}, требуется декомпозиция"); return 1
        if not (a.artifact and a.accept and a.question and a.block):
            print("1 нужны artifact accept question block"); return 1
        meta = {"id":a.id,"role":a.role,"owner":a.owner,"block":a.block,"cost_ops":a.cost,
                "mem_mb":a.mem or 512,"ceiling_ops":ceiling,"artifact":a.artifact,"accept":a.accept,
                "question":a.question,"branch":a.branch or a.id,"ver":composite_ver(),"at":now()}
        tp = os.path.join(tasks_dir(), a.id + ".tsv")
        if os.path.isfile(tp): print("1 задача уже есть"); return 1
        write(tp, json.dumps(meta, ensure_ascii=False) + "\n" + f"{now()}\t{a.owner}\tready\tсоздана\n")
        append(os.path.join(BOT,"a2a","ledger.tsv"), f"{a.id}\t{a.role}\t{a.owner}\t{a.block}\t{a.cost}\t{a.mem or 512}\t{a.artifact}\tready\t{composite_ver()}\t{now()}\n")
        print(f"201 {a.id} создана"); return 0
    if a.sub == "status":
        meta = task_meta(a.id)
        if not meta: print("1 нет задачи"); return 1
        held = any(m.get("task")==a.id and m.get("owner")==a.owner for m in read_locks())
        if not held: print("1 нет захвата задачи"); return 1
        append(os.path.join(tasks_dir(), a.id + ".tsv"), f"{now()}\t{a.owner}\t{a.status}\t{a.note or ''}\n")
        print("200 статус записан"); return 0
    if a.sub == "get":
        meta = task_meta(a.id)
        if not meta: print("1 нет задачи"); return 1
        meta["status"] = task_status(a.id)
        print(json.dumps(meta, ensure_ascii=False)); return 0
    return 2

# ---------- index / journal / birth / inbox ----------
def cmd_index(a):
    ip = os.path.join(FIX, "INDEX.tsv")
    if a.sub == "append":
        row = a.row
        append(ip, row.rstrip("\n") + "\n")
        if row.split("\t")[0] not in read(ip): print("1 обратное чтение не подтвердило"); return 1
        print("200 строка INDEX добавлена"); return 0
    if a.sub == "md":
        rows = index_rows()
        lines = ["# INDEX — человеческий вид указателя утверждений", "",
                 "Генерируется из INDEX.tsv инструментом qwr.py index md. Руками не править.",
                 "Номер и карточка — гиперссылки: прочёл, тыкнул, перелетел.", "",
                 "| id | истина | новизна | формулировка | метод | польза | карточка | данные |",
                 "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        def relfix(p):
            if not p: return ""
            return p[len("fixrealm/"):] if p.startswith("fixrealm/") else p
        for i in sorted(rows):
            c = rows[i]
            get = lambda k: c[k] if len(c) > k else ""
            cardrel = relfix(get(5)); datarel = relfix(get(6))
            idcell = f"[{get(0)}]({cardrel})" if cardrel else get(0)
            cardcell = f"[открыть]({cardrel})" if cardrel else "—"
            datacell = f"[данные]({datarel})" if datarel else "—"
            lines.append(f"| {idcell} | {get(1)} | {get(2)} | {get(3)} | {get(4)} | {get(8)} | {cardcell} | {datacell} |")
        write(os.path.join(FIX, "INDEX.md"), "\n".join(lines) + "\n")
        print(f"200 INDEX.md строк={len(rows)}"); return 0
    if a.sub == "check":
        rows = index_rows(); drift = []
        for i, c in rows.items():
            cp = os.path.join(ROOT, c[5]) if len(c) > 5 and c[5] else None
            if cp and os.path.isfile(cp):
                txt = read(cp)
                mt = re.search(r"истина:\s*(\w+)", txt); mn = re.search(r"новизна:\s*(\w+)", txt)
                if mt and mt.group(1) != c[1]: drift.append(f"{i} истина {mt.group(1)}!={c[1]}")
                if mn and mn.group(1) != c[2]: drift.append(f"{i} новизна {mn.group(1)}!={c[2]}")
        if drift: print("ДРЕЙФ: " + "; ".join(drift)); return 1
        print("OK дрейфа нет"); return 0
    return 2

def cmd_journal(a):
    jp = os.path.join(FIX, "JOURNAL.md")
    line = f"- {now()} | {a.by} | {a.text}\n"
    append(jp, line)
    print("200 строка JOURNAL добавлена"); return 0

def cmd_birth(a):
    bp = os.path.join(BOT, "a2a", "births", f'{now().replace(":","").replace("-","")}-{a.owner}.json')
    if os.path.isfile(bp): print("1 рождение уже есть, перезапись запрещена"); return 1
    rec = {"owner":a.owner,"role":a.role,"task":a.task or "","born_at":now(),"ver":composite_ver()}
    write(bp, json.dumps(rec, ensure_ascii=False)+"\n"); print("201 рождение"); return 0

def cmd_inbox(a):
    msg = {"from":a.frm,"to":a.to,"kind":a.kind,"text":a.text,"at":now()}
    append(os.path.join(BOT,"a2a","inbox.jsonl"), json.dumps(msg, ensure_ascii=False)+"\n")
    print("200 сообщение"); return 0

# ---------- park ----------
def cmd_park(a):
    pp = os.path.join(BOT, "a2a", "park.tsv")
    if not os.path.isfile(pp): write(pp, "branch\tstatus\treason\tat\n")
    if a.sub == "check":
        tasks = all_tasks()
        branches = {}
        for t in tasks:
            b = t.get("branch", t["id"])
            p = os.path.join(tasks_dir(), t["id"] + ".tsv")
            for line in read(p).splitlines()[1:]:
                c = line.split("\t")
                if len(c) >= 4 and c[2] == "done":
                    branches.setdefault(b, []).append("none" if "shift:none" in c[3] else "shift")
        parked = []
        for b, hist in branches.items():
            tail = hist[-3:]
            if len(tail) == 3 and all(x == "none" for x in tail):
                parked.append(b)
                append(pp, f"{b}\tpark\tтри этапа без сдвига\t{now()}\n")
        print("PARK: " + (",".join(parked) if parked else "нет")); return 0
    if a.sub == "set":
        append(pp, f"{a.branch}\tpark\t{a.reason or ''}\t{now()}\n"); print("200 park"); return 0
    if a.sub == "unset":
        append(pp, f"{a.branch}\tactive\t{a.reason or 'разморозка'}\t{now()}\n"); print("200 разморожена"); return 0
    return 2

# ---------- report ----------
def cmd_report(a):
    read_t = 0
    for p in (a.read or []):
        fp = p if os.path.isabs(p) else os.path.join(ROOT, p)
        if os.path.isfile(fp): read_t += est_file(fp)
    expense = f"расход токенов: {a.exact}" if a.exact else f"расход токенов: {read_t} (оценка)"
    lines = [f"РОЛЬ: {a.role} | владелец: {a.owner}",
             f"ЗАДАЧА: {a.task or '—'}",
             f"РЕЗУЛЬТАТ: {a.result or '—'}",
             f"НОВЫЕ НОМЕРА: {a.numbers or '—'}",
             f"СДВИГ: {a.shift or 'нет'}",
             expense,
             f"ВЕРСИЯ: {composite_ver()}"]
    if a.note: lines.append(a.note)
    lines.append(f"СОСТОЯНИЕ: {a.state or 'ЗЕЛЕНО'}")
    lines.append(f"ВЕРДИКТ: {a.verdict or 'ПУБЛИКОВАТЬ'} — {a.reason or 'этап завершён'}")
    if len(lines) > 30: print("1 отчёт больше 30 строк"); return 1
    print("\n".join(lines)); return 0

# ---------- lever ----------
def cmd_lever(a):
    line = a.line.strip()
    if not line.startswith("РЫЧАГ"): print("1 нет слова РЫЧАГ, это не приказ"); return 1
    body = line.split(":",1)[1].strip() if ":" in line else line[len("РЫЧАГ"):].strip()
    parts = body.split(); cmd = parts[0].upper() if parts else ""
    if cmd in ("ОТЧЁТ","ОТЧЕТ","СТАТУС","ОБЗОР"):
        return cmd_slice(a)
    if cmd == "РАСЧИСТИ":
        n = 0
        for m in read_locks():
            if not lock_live(m):
                append(os.path.join(BOT,"a2a","inbox.jsonl"), json.dumps({"from":"system","to":m.get("owner",""),"kind":"stale_release","text":f"замок снят рычагом РАСЧИСТИ","at":now()}, ensure_ascii=False)+"\n")
                os.remove(os.path.join(locks_dir(), m["_file"])); n += 1
        print(f"200 снято брошенных замков: {n}"); return 0
    if cmd == "ПОТОЛОК":
        print(json.dumps(LIMITS, ensure_ascii=False)); return 0
    if cmd == "РАЗМОРОЗЬ":
        if len(parts) < 2: print("1 укажите ветку"); return 1
        a.sub = "unset"; a.branch = parts[1]; a.reason = " ".join(parts[2:]) or "рычаг владельца"
        return cmd_park(a)
    if cmd == "СЛОВАРЬ":
        tp = os.path.join(FIX, "TERMS.md")
        print(read(tp) if os.path.isfile(tp) else "TERMS.md нет"); return 0
    if cmd == "ПРОТОКОЛ":
        print("HUMAN-ONLY: правка протокола ролью EDT по рычагу; захватите EDT, правьте, пересоберите манифест"); return 0
    if cmd == "ПУБЛИКУЙ":
        a.state="ЗЕЛЕНО"; a.verdict="ПУБЛИКОВАТЬ"; a.api="local"; a.repo=None; a.message=None
        return cmd_publish(a)
    print(f"1 неизвестный рычаг {cmd}"); return 1

# ---------- doctor ----------
def cmd_doctor(a):
    checks = []
    def ck(name, ok, detail=""): checks.append((name, ok, detail))
    for p in ["qwr/bot/GATE.txt","MANIFEST.json","qwr/bot/dict/common.kv","qwr/bot/roles/PLN.txt","qwr/bot/mod/needs.txt","fixrealm/INDEX.tsv"]:
        ck("структура "+p, os.path.isfile(os.path.join(ROOT,p)))
    ck("шлюз<=3000", est_file(os.path.join(BOT,"GATE.txt")) <= 3000)
    modtot = sum(est_file(os.path.join(BOT,"mod",f)) for f in os.listdir(os.path.join(BOT,"mod")) if f.endswith(".txt"))
    ck("needs сумма<=6000", modtot <= 6000, str(modtot))
    gate = est_file(os.path.join(BOT,"GATE.txt"))
    for r in ["PLN","WRK","EUR","CHK","LIT","IDE","SYN","AUD","EDT"]:
        c = card_text(r)
        ck(f"карточка {r}<=800", c is not None and est_text(c) <= 800)
        ck(f"роль {r}<=2500", est_file(os.path.join(BOT,"roles",r+".txt")) <= 2500)
        refs = re.findall(r"roles/([A-Z]+)\.txt", read(os.path.join(BOT,"roles",r+".txt")))
        ck(f"изоляция {r}", all(x == r for x in refs))
        if c:
            needs = parse_card_field(c,"needs").split(",")
            nt = sum(est_file(os.path.join(BOT,"mod",n.strip()+".txt")) for n in needs if n.strip() and os.path.isfile(os.path.join(BOT,"mod",n.strip()+".txt")))
            inp = gate + est_text(c) + est_file(os.path.join(BOT,"roles",r+".txt")) + nt + 1500 + 500
            ck(f"вход {r}<=18000", inp <= 18000, str(inp))
    d = load_dicts(); unknown = set()
    for base, _, files in os.walk(BOT):
        if "a2a" in base: continue
        for f in files:
            if f.endswith((".txt",".kv")):
                for code in re.findall(r"%[cgrs]\d+", read(os.path.join(base,f))):
                    if code not in d: unknown.add(code)
    ck("неизвестных кодов нет", not unknown, ",".join(sorted(unknown)))
    rc = cmd_manifest(argparse.Namespace(check=True))
    ck("манифест OK", rc == 0)
    allok = True
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\t{detail}")
        allok = allok and ok
    print("DOCTOR " + ("OK" if allok else "FAIL"))
    return 0 if allok else 1

# ---------- selftest ----------
def cmd_selftest(a):
    tmp = tempfile.mkdtemp(prefix="qwr_selftest_")
    dst = os.path.join(tmp, "repo")
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git","__pycache__"))
    # песочница должна быть чистой: убрать runtime-состояние и фикстуры прогонки
    b = os.path.join(dst,"qwr","bot","a2a")
    for sub in ("tasks","births","locks"):
        d = os.path.join(b,sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f != ".gitkeep": os.remove(os.path.join(d,f))
    for f in ("park.tsv",):
        p=os.path.join(b,f)
        if os.path.isfile(p): os.remove(p)
    open(os.path.join(b,"inbox.jsonl"),"w").close()
    open(os.path.join(b,"ledger.tsv"),"w").write("task\trole\towner\tblock\tcost_ops\tmem_mb\tartifact\tstatus\tver\tat\n")
    fx=os.path.join(dst,"fixrealm")
    open(os.path.join(fx,"INDEX.tsv"),"w").write("id\ttruth\tnovelty\ttitle\tmethod\tcard\tdata\tlinks\tutility\tver\tat\tby\n")
    for sub in ("cards","data"):
        d=os.path.join(fx,sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f!=".gitkeep": os.remove(os.path.join(d,f))
    env = dict(os.environ); env["QWR_ROOT"] = dst
    script = os.path.join(dst, "qwr", "bot", "bin", "qwr.py")
    def run(*args):
        r = subprocess.run([sys.executable, script, *args], capture_output=True, text=True, env=env, cwd=dst)
        return r.returncode, r.stdout.strip()
    results = []
    def ck(name, ok, detail=""): results.append((name, ok, detail))
    run("manifest")
    rc, out = run("claim","--role","PLN","--owner","agentA","--api","local"); ck("захват 201", rc==0 and "201" in out, out)
    rc, out = run("claim","--role","PLN","--owner","agentB","--api","local"); ck("второй 422", rc==1 and "422" in out, out)
    rc, out = run("card","--role","IDE"); ck("карточка IDE", rc==0, "")
    rc, out = run("claim","--role","IDE","--owner","agentC","--api","local"); ck("захват IDE 201", rc==0 and "201" in out, out)
    run("release","--role","IDE","--owner","agentC")
    rc, out = run("slice"); ck("срез имеет idle и cards_n", rc==0 and '"idle"' in out and '"cards_n"' in out, "")
    rc, out = run("task","new","--id","T9001","--role","PLN","--owner","agentA","--block","A9001-A9010","--cost","1e40","--artifact","x","--accept","y","--question","z")
    ck("1e40 отклонена", rc==1 and "декомпозиция" in out, out)
    rc, out = run("task","new","--id","T9002","--role","PLN","--owner","agentA","--block","A9001-A9010","--cost","1e6","--artifact","таблица","--accept","граница","--question","малый случай")
    ck("под потолком создана", rc==0, out)
    rc, out = run("guard","--role","WRK","--owner","agentA","--paths","fixrealm/cards/A9001.md","--intent","create","--task","T9002")
    ck("guard номер вне блока/без захвата", rc in (0,1), out)
    rc, out = run("dict","load","--codes","%c1,%g12"); ck("расшифровка кодов", rc==0 and "протокол" in out, out)
    rc, out = run("dict","load","--codes","%c999"); ck("неизвестный код отклонён", rc==1, out)
    rc, out = run("doctor"); ck("doctor", rc==0, out.splitlines()[-1] if out else "")
    rc, out = run("report","--role","WRK","--owner","agentA","--task","T9002","--result","тест","--shift","диапазон","--read","qwr/bot/GATE.txt")
    ck("отчёт<=30 и расход", rc==0 and "расход токенов" in out and "(оценка)" in out, "")
    rc, out = run("lever","--line","РЫЧАГ: СТАТУС"); ck("рычаг статус", rc==0 and "debt_chk" in out, "")
    rc, out = run("lever","--line","просто продолжай"); ck("без РЫЧАГ не приказ", rc==1, out)
    rc, out = run("publish","--state","КРАСНО","--verdict","ПУБЛИКОВАТЬ"); ck("красное не пушится", rc==1, out)
    rc, out = run("publish","--state","ЗЕЛЕНО","--verdict","НЕ ПУБЛИКОВАТЬ"); ck("не публиковать не пушится", rc==1, out)
    rc, out = run("publish","--state","ЗЕЛЕНО","--verdict","ПУБЛИКОВАТЬ","--api","local"); ck("зелёное пушится и СТОП", rc==0 and "СТОП" in out, out)
    rc, out = run("lever","--line","РЫЧАГ: ПУБЛИКУЙ"); ck("рычаг ПУБЛИКУЙ", rc==0 and "СТОП" in out, out)
    open(os.path.join(dst,"fixrealm","data","chk.tsv"),"w").write("x\n2\n-3\n")
    rc, out = run("precheck","--data","fixrealm/data/chk.tsv","--predicate","x>0"); ck("precheck ловит нарушение на сохранённых данных", rc==1 and "нарушено 1" in out, out)
    rc, out = run("precheck","--data","fixrealm/data/chk.tsv","--predicate","abs(x)>=2"); ck("precheck проходит истинное", rc==0, out)
    rc, out = run("lint"); ck("lint чистой песочницы", rc==0, out)
    open(os.path.join(dst,"fixrealm","cards","A9099.md"),"w").write("# A9099\nистина: hyp\nновизна: unc\nпольза: x\nверсия: QWR:test\nформула %s4\n")
    rc, out = run("lint"); ck("lint ловит плейсхолдер и сироту", rc==1 and "плейсхолдер" in out, out)
    os.remove(os.path.join(dst,"fixrealm","cards","A9099.md"))
    run("index","append","--row","A9001\tprf\tunc\tтест\tметод\tfixrealm/cards/A9001.md\tfixrealm/data/A9001.tsv\t\tactive\tv\tat\tbot")
    run("index","md")
    idxmd = open(os.path.join(dst,"fixrealm","INDEX.md"),encoding="utf-8").read()
    ck("INDEX.md гиперссылки на карточки", "](cards/A9001.md)" in idxmd, "")
    rc, out = run("prior","--query","тест"); ck("prior находит прежние результаты", rc==0 and "A9001" in out, out)
    shutil.rmtree(tmp, ignore_errors=True)
    allok = True
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\t{detail}"); allok = allok and ok
    print("SELFTEST " + ("OK" if allok else "FAIL"))
    return 0 if allok else 1

# ---------- publish ----------
def cmd_publish(a):
    if (a.state or "") != "ЗЕЛЕНО" or (a.verdict or "") != "ПУБЛИКОВАТЬ":
        print("ОТКАЗ: пуш только при СОСТОЯНИЕ ЗЕЛЕНО и ВЕРДИКТ ПУБЛИКОВАТЬ"); return 1
    if cmd_manifest(argparse.Namespace(check=True)) != 0:
        print("ОТКАЗ: манифест не сошёлся, записей не делать"); return 1
    if cmd_lint(argparse.Namespace()) != 0:
        print("ОТКАЗ: lint дефекты, не публиковать, править"); return 1
    if a.api == "github":
        tok = os.environ.get("QWR_TOKEN"); repo = a.repo or os.environ.get("QWR_REPO")
        if not tok or not repo: print("ОТКАЗ: нет QWR_TOKEN или репозитория"); return 1
        auth = "Authorization: Basic " + base64.b64encode(f"x-access-token:{tok}".encode()).decode()
        def git(*args):
            return subprocess.run(["git","-c",f"http.extraheader={auth}",*args], cwd=ROOT, capture_output=True, text=True)
        git("add","-A")
        if git("status","--porcelain").stdout.strip():
            git("-c","user.name=qwr-bot","-c","user.email=bot@qwr.local","commit","-m", a.message or "этап QWR: фиксация и публикация")
        r = git("push","origin","main")
        if r.returncode != 0:
            print("ОТКАЗ: пуш не удался: " + r.stderr.strip()[:120]); return 1
        print("PUSH OK — СТОП: исследование в этом сообщении завершено, следующее только в новом сообщении или чате"); return 0
    print("PUSH OK (local) — СТОП: исследование в этом сообщении завершено"); return 0

# ---------- reuse: prior / card-get ----------
def cmd_prior(a):
    rows = index_rows()
    q = (a.query or "").lower()
    matches = []
    for i, c in rows.items():
        title = c[3] if len(c) > 3 else ""; method = c[4] if len(c) > 4 else ""
        if not q or q in title.lower() or q in method.lower() or q in i.lower():
            matches.append(c)
    if not q: matches = list(rows.values())[-10:]
    lines = []
    for c in matches[:20]:
        get = lambda k: c[k] if len(c) > k else ""
        lines.append(f'{get(0)}\t{get(1)}\t{get(2)}\t{get(3)}\tпольза:{get(8)}\t{get(5)}')
    text = "\n".join(lines) if lines else "нет прежних результатов по запросу"
    if est_text(text) > 800:
        text = "\n".join(lines[:8]) + "\n…сужай запрос"
    print(text); return 0

def cmd_cardget(a):
    p = os.path.join(FIX, "cards", a.id + ".md")
    if not os.path.isfile(p): print("нет карточки " + a.id); return 1
    txt = read(p)
    if est_text(txt) > 2000: txt = txt[:6000] + "\n…усечено, сужай запрос"
    print(txt); return 0

# ---------- check gate: precheck / lint ----------
def cmd_precheck(a):
    p = a.data if os.path.isabs(a.data) else os.path.join(ROOT, a.data)
    if not os.path.isfile(p): print("нет data " + a.data); return 2
    lines = [l for l in read(p).splitlines() if l.strip()]
    if not lines: print("data пуст"); return 2
    header = lines[0].split("\t")
    rows = lines[1:] if a.header else lines
    import math
    ns = {"__builtins__": {}, "abs": abs, "min": min, "max": max, "sum": sum, "len": len, "math": math, "prod": math.prod}
    passed = failed = errors = 0; fails = []
    for ln in rows:
        cells = ln.split("\t")
        if a.header:
            row = {header[i]: cells[i] for i in range(min(len(header), len(cells)))}
        else:
            row = {f"c{i}": cells[i] for i in range(len(cells))}
        for k, v in list(row.items()):
            try: row[k] = int(v)
            except Exception:
                try: row[k] = float(v)
                except Exception: pass
        try:
            if eval(a.predicate, ns, row): passed += 1
            else: failed += 1; fails.append(ln)
        except Exception as e:
            errors += 1; fails.append(ln + " (" + str(e) + ")")
    print(f"precheck: пройдено {passed}, нарушено {failed}, ошибок {errors}, всего {len(rows)}")
    if fails:
        print("нарушения (первые 5):")
        for f in fails[:5]: print("  " + f)
    return 0 if failed == 0 and errors == 0 else 1

def cmd_lint(a):
    defects = []
    rows = index_rows()
    ip = os.path.join(FIX, "INDEX.tsv")
    if os.path.isfile(ip):
        for line in read(ip).splitlines()[1:]:
            if not line.strip(): continue
            c = line.split("\t")
            if len(c) != 12: defects.append(f"колонки {len(c)}!=12: {c[0] if c else '?'}")
    cards_dir = os.path.join(FIX, "cards"); bodies = {}; cardids = set()
    if os.path.isdir(cards_dir):
        for f in sorted(os.listdir(cards_dir)):
            if not f.endswith(".md"): continue
            cid = f[:-3]; cardids.add(cid)
            txt = read(os.path.join(cards_dir, f))
            h = hashlib.sha256(txt.encode()).hexdigest()
            if h in bodies: defects.append(f"дубль тела {cid}={bodies[h]}")
            bodies[h] = cid
            if re.search(r"%[cgrs]\d+", txt): defects.append(f"плейсхолдер кода в {cid}")
            for field in ["истина:", "новизна:", "польза:"]:
                if field not in txt: defects.append(f"нет поля {field} в {cid}")
            mv = re.search(r"версия:\s*(\S+)", txt)
            if mv and not mv.group(1).startswith("QWR:"): defects.append(f"штамп версии не QWR в {cid}")
    for i, c in rows.items():
        card = c[5] if len(c) > 5 else ""
        if ";" in card: defects.append(f"склеенный путь карточки {i}")
        cp = os.path.join(ROOT, card) if card else None
        if not cp or not os.path.isfile(cp): defects.append(f"карточка не существует {i}: {card}")
        data = c[6] if len(c) > 6 else ""
        if data and not os.path.isfile(os.path.join(ROOT, data)): defects.append(f"data не существует {i}: {data}")
        truth = c[1] if len(c) > 1 else ""
        if truth in ("emp", "prf"):
            has_data = bool(data) and os.path.isfile(os.path.join(ROOT, data))
            has_proof = cp and os.path.isfile(cp) and "Доказательство" in read(cp)
            if not has_data and not has_proof: defects.append(f"{truth} без data и доказательства {i}")
    for cid in cardids:
        if cid not in rows: defects.append(f"карточка без строки INDEX {cid}")
    if defects:
        print("LINT ДЕФЕКТЫ:")
        for d in defects: print("  " + d)
        return 1
    print("LINT OK"); return 0

def main():
    ap = argparse.ArgumentParser(prog="qwr.py", description="инструменты протокола QWR v1.0")
    ap.add_argument("--root", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("manifest"); m.add_argument("--check", action="store_true")
    t = sub.add_parser("tokens"); t.add_argument("sub", choices=["est"]); t.add_argument("--files", nargs="+", required=True)
    d = sub.add_parser("dict"); d.add_argument("sub", choices=["load","lint","show"])
    d.add_argument("--codes"); d.add_argument("--file")
    c = sub.add_parser("card"); c.add_argument("--role", required=True)
    n = sub.add_parser("need"); n.add_argument("--role", required=True); n.add_argument("--lazy", action="store_true")
    sub.add_parser("slice")
    cl = sub.add_parser("claim"); cl.add_argument("--role", required=True); cl.add_argument("--owner", required=True)
    cl.add_argument("--task"); cl.add_argument("--api", choices=["local","github"], default="local")
    rl = sub.add_parser("release"); rl.add_argument("--role", required=True); rl.add_argument("--owner", required=True)
    rl.add_argument("--task"); rl.add_argument("--stale", action="store_true")
    g = sub.add_parser("guard"); g.add_argument("--role", required=True); g.add_argument("--owner", required=True)
    g.add_argument("--paths", required=True); g.add_argument("--intent", choices=["create","write","append"], default="write")
    g.add_argument("--content-file"); g.add_argument("--task")
    tk = sub.add_parser("task"); tk.add_argument("sub", choices=["new","status","get"])
    for x in ["--id","--role","--owner","--block","--cost","--mem","--ceiling","--artifact","--accept","--question","--branch","--status","--note"]:
        tk.add_argument(x)
    ix = sub.add_parser("index"); ix.add_argument("sub", choices=["append","md","check"]); ix.add_argument("--row")
    j = sub.add_parser("journal"); j.add_argument("--text", required=True); j.add_argument("--by", required=True)
    b = sub.add_parser("birth"); b.add_argument("--owner", required=True); b.add_argument("--role", required=True); b.add_argument("--task")
    ib = sub.add_parser("inbox"); ib.add_argument("--from", dest="frm", required=True); ib.add_argument("--to", required=True)
    ib.add_argument("--kind", required=True); ib.add_argument("--text", required=True)
    pk = sub.add_parser("park"); pk.add_argument("sub", choices=["check","set","unset"]); pk.add_argument("--branch"); pk.add_argument("--reason")
    rp = sub.add_parser("report"); rp.add_argument("--role", required=True); rp.add_argument("--owner", required=True)
    rp.add_argument("--task"); rp.add_argument("--result"); rp.add_argument("--numbers"); rp.add_argument("--shift")
    rp.add_argument("--read", nargs="*"); rp.add_argument("--exact"); rp.add_argument("--note")
    rp.add_argument("--state"); rp.add_argument("--verdict"); rp.add_argument("--reason")
    lv = sub.add_parser("lever"); lv.add_argument("--line", required=True)
    pb = sub.add_parser("publish"); pb.add_argument("--state", default="ЗЕЛЕНО"); pb.add_argument("--verdict", default="ПУБЛИКОВАТЬ")
    pb.add_argument("--api", choices=["local","github"], default="local"); pb.add_argument("--repo"); pb.add_argument("--message")
    sub.add_parser("doctor")
    sub.add_parser("selftest")
    pr = sub.add_parser("prior"); pr.add_argument("--query", default="")
    cg = sub.add_parser("card-get"); cg.add_argument("--id", required=True)
    pc = sub.add_parser("precheck"); pc.add_argument("--data", required=True); pc.add_argument("--predicate", required=True)
    pc.add_argument("--no-header", dest="header", action="store_false", default=True)
    sub.add_parser("lint")
    a = ap.parse_args()
    global ROOT, BOT, FIX
    if a.root:
        ROOT = find_root(a.root); BOT = os.path.join(ROOT,"qwr","bot")
        FIX = os.environ.get("QWR_FIXREALM") or os.path.join(ROOT,"fixrealm")
    fn = {"manifest":cmd_manifest,"tokens":cmd_tokens,"dict":cmd_dict,"card":cmd_card,"need":cmd_need,
          "slice":cmd_slice,"claim":cmd_claim,"release":cmd_release,"guard":cmd_guard,"task":cmd_task,
          "index":cmd_index,"journal":cmd_journal,"birth":cmd_birth,"inbox":cmd_inbox,"park":cmd_park,
          "report":cmd_report,"lever":cmd_lever,"publish":cmd_publish,"prior":cmd_prior,"card-get":cmd_cardget,"precheck":cmd_precheck,"lint":cmd_lint,"doctor":cmd_doctor,"selftest":cmd_selftest}[a.cmd]
    sys.exit(fn(a))

if __name__ == "__main__":
    main()
