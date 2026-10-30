"""Kvitteringsrobot for ENK.

Henter kvitteringer fra en Gmail-etikett (valgfritt) og fra mappen innboks/,
arkiverer dem som bilag med fast filnavn og fører en rad i fanen Utgifter i
ENK-regnskap-2027.xlsx. Alle rader merkes "AUTO – kontroller" slik at du
godkjenner dem selv (du er fortsatt ansvarlig for bokføringen).

Bruk:
    python kvittering_robot.py            # kjør én gang
    python kvittering_robot.py --test     # vis hva som ville skjedd, endrer ingenting
"""
import argparse
import datetime as dt
import email
import email.utils
import html
import imaplib
import json
import os
import re
import shutil
import sys
from email.header import decode_header, make_header
from pathlib import Path

from openpyxl import load_workbook

HER = Path(__file__).resolve().parent
FILTYPER = {".pdf", ".jpg", ".jpeg", ".png", ".heic", ".html"}
FORSTE_RAD, SISTE_RAD = 2, 401


def last_config():
    p = HER / "config.json"
    if not p.exists():
        sys.exit("Fant ikke config.json – kopier config.example.json til config.json og fyll inn.")
    cfg = json.loads(p.read_text(encoding="utf-8"))
    for k in ("regneark", "innboks", "bilag", "backup", "status"):
        cfg[k] = (HER / cfg[k]).resolve()
    return cfg


def last_status(cfg):
    if cfg["status"].exists():
        return json.loads(cfg["status"].read_text(encoding="utf-8"))
    return {"meldinger": []}


def trygt_navn(tekst):
    tekst = re.sub(r"[^\w\-]+", "-", tekst.strip().lower(), flags=re.UNICODE)
    return tekst.strip("-")[:40] or "ukjent"


# ---------- Tolking av kvitteringstekst ----------

BELOP = re.compile(
    r"(?:totalt|total|sum|å betale|a betale|beløp|amount paid|amount due|grand total)"
    r"[^\d\n]{0,25}?(?P<val>NOK|kr|USD|\$|EUR|€)?\s*(?P<tall>\d{1,3}(?:[ . ]\d{3})*(?:[.,]\d{2})?|\d+(?:[.,]\d{2})?)"
    r"\s*(?P<val2>NOK|kr|USD|EUR|€)?",
    re.IGNORECASE,
)
DATO = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](20\d{2})\b|\b(20\d{2})-(\d{2})-(\d{2})\b")


def til_tall(s):
    s = s.replace(" ", " ").replace(" ", "")
    if "," in s and "." in s:          # 1.299,00 eller 1,299.00
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    return float(s)


def finn_belop(tekst):
    """Returnerer (beløp, valuta). Tar det største 'total'-beløpet i teksten."""
    funn = []
    for m in BELOP.finditer(tekst):
        try:
            v = til_tall(m.group("tall"))
        except ValueError:
            continue
        val = (m.group("val") or m.group("val2") or "NOK").upper()
        val = {"KR": "NOK", "$": "USD", "€": "EUR"}.get(val, val)
        funn.append((v, val))
    if not funn:
        return None, None
    return max(funn, key=lambda f: f[0])


def finn_dato(tekst):
    m = DATO.search(tekst)
    if not m:
        return None
    try:
        if m.group(1):
            return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        return dt.date(int(m.group(4)), int(m.group(5)), int(m.group(6)))
    except ValueError:
        return None


def tekst_fra_fil(p):
    if p.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join((s.extract_text() or "") for s in PdfReader(p).pages)
        except Exception:
            return ""
    if p.suffix.lower() == ".html":
        rå = p.read_text(encoding="utf-8", errors="ignore")
        return html.unescape(re.sub(r"<[^>]+>", " ", rå))
    return ""  # bilder: ingen tekstlesing, fylles inn manuelt


def gjett_kategori(cfg, leverandor, tekst):
    hay = f"{leverandor} {tekst[:2000]}".lower()
    for regel in cfg.get("regler", []):
        if any(re.search(rf"\b{re.escape(o.lower())}\b", hay) for o in regel["ord"]):
            return regel["kategori"], regel.get("næringsandel")
    return "", None


# ---------- Gmail ----------

def dekod(h):
    return str(make_header(decode_header(h or "")))


def hent_gmail(cfg, status, test):
    g = cfg.get("gmail") or {}
    if not g.get("aktiv"):
        return
    passord = os.environ.get("ENK_GMAIL_APP_PASSORD")
    if not passord:
        print("Gmail: ENK_GMAIL_APP_PASSORD er ikke satt – hopper over e-post.")
        return
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(g["adresse"], passord)
    imap.select(f'"{g["etikett"]}"', readonly=True)
    _, data = imap.search(None, "ALL")
    for num in data[0].split():
        _, msgdata = imap.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msgdata[0][1])
        mid = msg.get("Message-ID", f"uten-id-{num.decode()}")
        if mid in status["meldinger"]:
            continue
        lagre_epost(cfg, msg, test)
        if not test:
            status["meldinger"].append(mid)
    imap.logout()


def lagre_epost(cfg, msg, test):
    """Legger vedlegg (eller selve e-posten som HTML) i innboks/ med metadata i filnavnet."""
    avsender = email.utils.parseaddr(dekod(msg.get("From")))
    leverandor = trygt_navn(avsender[0] or avsender[1].split("@")[-1].split(".")[0])
    try:
        dato = email.utils.parsedate_to_datetime(msg.get("Date")).date()
    except Exception:
        dato = dt.date.today()
    prefix = f"{dato.isoformat()}_{leverandor}"
    lagret = False
    html_del = None
    for del_ in msg.walk():
        navn = del_.get_filename()
        if navn and Path(dekod(navn)).suffix.lower() in FILTYPER:
            mål = cfg["innboks"] / f"{prefix}{Path(dekod(navn)).suffix.lower()}"
            print(f"Gmail: vedlegg → {mål.name}")
            if not test:
                skriv_unik(mål, del_.get_payload(decode=True))
            lagret = True
        elif del_.get_content_type() == "text/html" and html_del is None:
            html_del = del_
    if not lagret and html_del is not None:  # mange abonnementer sender kvittering kun i e-postteksten
        mål = cfg["innboks"] / f"{prefix}.html"
        print(f"Gmail: e-posttekst → {mål.name}")
        if not test:
            skriv_unik(mål, html_del.get_payload(decode=True))


def skriv_unik(mål, data):
    mål.parent.mkdir(parents=True, exist_ok=True)
    i = 2
    while mål.exists():
        mål = mål.with_name(f"{mål.stem.rsplit('__', 1)[0]}__{i}{mål.suffix}")
        i += 1
    mål.write_bytes(data)
    return mål


# ---------- Innboks → bilag + regneark ----------

def tolk_filnavn(p):
    """2027-01-03_openart.pdf → (dato, 'openart'). Ellers filens endringsdato og filnavnet."""
    m = re.match(r"(20\d{2}-\d{2}-\d{2})_([^_]+?)(?:__\d+)?$", p.stem)
    if m:
        return dt.date.fromisoformat(m.group(1)), m.group(2), True
    return dt.date.fromtimestamp(p.stat().st_mtime), trygt_navn(p.stem), False


def behandle_innboks(cfg, test):
    filer = sorted(f for f in cfg["innboks"].glob("*") if f.suffix.lower() in FILTYPER)
    if not filer:
        print("Innboks: ingen nye kvitteringer.")
        return []
    rader = []
    for f in filer:
        dato, leverandor, dato_fra_navn = tolk_filnavn(f)
        tekst = tekst_fra_fil(f)
        if not dato_fra_navn:
            dato = finn_dato(tekst) or dato
        belop, valuta = finn_belop(tekst)
        kategori, andel = gjett_kategori(cfg, leverandor, tekst)
        merknad = ["AUTO – kontroller"]
        if belop is None:
            merknad.append("fant ikke beløp")
        if valuta and valuta != "NOK":
            merknad.append(f"{valuta} {belop:.2f} – før NOK-beløpet fra bankutskriften")
            belop = None
        if not kategori:
            merknad.append("velg kategori")
        mål = cfg["bilag"] / str(dato.year) / f"{dato.isoformat()}_{leverandor}{f.suffix.lower()}"
        print(f"{f.name} → {dato} | {leverandor} | {belop} | {kategori or '?'}")
        if not test:
            mål = skriv_unik(mål, f.read_bytes())
            f.unlink()
        rader.append([dato, f"Kvittering {leverandor}", leverandor, kategori, belop, andel,
                      mål.name, "Firmakonto", "; ".join(merknad)])
    return rader


def skriv_til_regneark(cfg, rader):
    ark_fil = cfg["regneark"]
    cfg["backup"].mkdir(parents=True, exist_ok=True)
    shutil.copy2(ark_fil, cfg["backup"] / f"{ark_fil.stem}_{dt.datetime.now():%Y%m%d-%H%M%S}.xlsx")
    wb = load_workbook(ark_fil)
    ws = wb["Utgifter"]
    ledige = [r for r in range(FORSTE_RAD, SISTE_RAD + 1)
              if ws.cell(r, 1).value is None and ws.cell(r, 2).value is None]
    if len(ledige) < len(rader):
        sys.exit("Fanen Utgifter er full – utvid arket før du kjører igjen.")
    for r, (dato, beskr, lev, kat, belop, andel, bilag, betalt, merknad) in zip(ledige, rader):
        # Kolonner: A dato, B beskrivelse, C leverandør, D kategori, E beløp, F andel, J bilag, K betalt fra, L merknad
        for kol, verdi in ((1, dato), (2, beskr), (3, lev), (4, kat or None), (5, belop),
                           (6, andel), (10, bilag), (11, betalt), (12, merknad)):
            ws.cell(r, kol).value = verdi
    wb.calculation.fullCalcOnLoad = True  # Excel/LibreOffice regner om formlene ved åpning
    try:
        wb.save(ark_fil)
    except PermissionError:
        sys.exit("Regnearket er åpent i Excel – lukk det og kjør igjen. Bilagene ligger trygt i innboks/.")
    print(f"Førte {len(rader)} rad(er) i {ark_fil.name}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="vis hva som skjer uten å endre noe")
    test = ap.parse_args().test
    cfg = last_config()
    cfg["innboks"].mkdir(parents=True, exist_ok=True)
    status = last_status(cfg)
    hent_gmail(cfg, status, test)
    if test:
        # I testmodus ligger e-postvedleggene ikke i innboks, så vi viser bare filene som allerede er der.
        behandle_innboks(cfg, test=True)
        return
    rader = behandle_innboks(cfg, test=False)
    if rader:
        skriv_til_regneark(cfg, rader)
    cfg["status"].write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
