"""يقرأ موقع وزارة الأوقاف ويضيف إلى data.json فاتح كل شهر هجري جديد معلن.

يبحث عن عبارة مثل: «فاتح جمادى الآخرة 1448هـ — الأربعاء 11 نونبر 2026م».
لا يضيف شهرا إلا إذا كان فاتحه بعد 29 أو 30 يوما من فاتح الشهر السابق المحفوظ.
"""
import datetime as dt, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data.json"
URLS = ["https://www.habous.gov.ma/", "https://habous.gov.ma/"]

HIJRI = {
    "محرم": 1, "صفر": 2, "ربيع الأول": 3, "ربيع الاول": 3, "ربيع الآخر": 4, "ربيع الاخر": 4, "ربيع الثاني": 4,
    "جمادى الأولى": 5, "جمادى الاولى": 5, "جمادى الأول": 5, "جمادى الآخرة": 6, "جمادى الاخرة": 6, "جمادى الثانية": 6,
    "رجب": 7, "شعبان": 8, "رمضان": 9, "شوال": 10, "ذو القعدة": 11, "ذي القعدة": 11, "ذو الحجة": 12, "ذي الحجة": 12,
}
GREG = {
    "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ابريل": 4, "ماي": 5, "مايو": 5, "يونيو": 6, "يونيه": 6,
    "يوليوز": 7, "يوليو": 7, "غشت": 8, "أغسطس": 8, "اغسطس": 8, "شتنبر": 9, "سبتمبر": 9, "أكتوبر": 10, "اكتوبر": 10,
    "نونبر": 11, "نوفمبر": 11, "دجنبر": 12, "ديسمبر": 12,
}
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def alt(words):
    return "|".join(sorted((re.escape(w) for w in words), key=len, reverse=True))


PATTERN = re.compile(
    rf"فاتح\s+(?:شهر\s+)?(?P<hm>{alt(HIJRI)})(?:\s+المعظم|\s+الحرام)?\s+(?:لعام\s+|لسنة\s+)?(?P<hy>1[3-5]\d\d)\s*(?:هـ|ه)?"
    rf"[^0-9]{{0,40}}?(?P<gd>\d{{1,2}})\s+(?P<gm>{alt(GREG)})\s+(?P<gy>20\d\d)"
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (hijri-maroc calendar bot)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def clean(html):
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.translate(DIGITS).replace("ـ", "")  # tatweel
    return re.sub(r"\s+", " ", text)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    months = {(r["y"], r["m"]): r for r in data["months"]}
    found = []
    for url in URLS:
        try:
            text = clean(fetch(url))
        except Exception as e:  # الموقع في الصيانة أو يحجب الطلب
            print(f"تعذرت قراءة {url}: {e}")
            continue
        for mt in PATTERN.finditer(text):
            try:
                start = dt.date(int(mt["gy"]), GREG[mt["gm"]], int(mt["gd"]))
            except ValueError:
                continue
            found.append((int(mt["hy"]), HIJRI[mt["hm"]], start, url))
        if found:
            break

    added = []
    for hy, hm, start, url in sorted(set(found)):
        if (hy, hm) in months:
            continue
        prev = months.get((hy, hm - 1) if hm > 1 else (hy - 1, 12))
        if not prev:
            print(f"تجاهل {hy}-{hm}: لا يوجد فاتح الشهر السابق للتحقق")
            continue
        gap = (start - dt.date.fromisoformat(prev["start"])).days
        if gap not in (29, 30):
            print(f"تجاهل {hy}-{hm} {start}: الفارق {gap} يوما")
            continue
        months[(hy, hm)] = {"y": hy, "m": hm, "start": start.isoformat(), "source": url}
        added.append(f"{hy}-{hm:02d} = {start}")

    if added:  # لا نكتب شيئا إن لم يجد جديدا، تفاديا لإيداع كل نصف ساعة
        data["checked"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["months"] = [months[k] for k in sorted(months)]
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("أضيف: " + ", ".join(added) if added else "لا جديد")


if __name__ == "__main__":
    sys.exit(main())
