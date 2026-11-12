#!/usr/bin/env python3
"""Build the Fatura Dedektifi slide deck as one HTML file per language.

    python build_slides.py            # Turkish, writes slides_tr.html
    python build_slides.py --lang en  # English, writes slides_en.html
    DECK_LANG=en python build_slides.py

Open the file with ?s=<slide>&b=<beat> to see one slide at 1920x1080 with its
elements revealed up to that beat (b=99 shows everything). Without ?s every
slide is shown, one per page, which is what the PDF export prints.

The charts are drawn from ../../analysis/chart_day.json and results.json.
"""

import argparse
import json
import os
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent.parent / "analysis"
N_SLIDES = 11

# --------------------------------------------------------------------------
# Text. Every string the slides show lives here once, Turkish first.
# --------------------------------------------------------------------------

S = {
    # cover
    "name": ("Mert Güngör", "Mert Güngör"),
    "course": ("Samsung Innovation Campus, Yapay Zekâ Kursu<br>Capstone Idea Proposal",
               "Samsung Innovation Campus, Artificial Intelligence Course<br>Capstone Idea Proposal"),
    "project": ("Fatura<br>Dedektifi", "Fatura<br>Dedektifi"),
    "project_en": ("", "Bill Detective"),
    "question": ("Evde elektriği hangi<br>cihaz harcıyor?",
                 "Which appliance uses<br>the electricity at home?"),
    "footer": ("Fatura Dedektifi, Idea Proposal, Mert Güngör",
               "Fatura Dedektifi, Idea Proposal, Mert Güngör"),
    # appliances
    "fridge": ("Buzdolabı", "Fridge"),
    "washer": ("Çamaşır makinesi", "Washing machine"),
    "washer_short": ("Çamaşır", "Washer"),
    "dish": ("Bulaşık makinesi", "Dishwasher"),
    "kettle": ("Su ısıtıcı", "Kettle"),
    "micro": ("Mikrodalga", "Microwave"),
    "washer_cell": ("Çamaşır<br>makinesi", "Washing<br>machine"),
    "dish_cell": ("Bulaşık<br>makinesi", "Dishwasher"),
    # slide 2
    "t2": ("Faturada tek bir sayı var", "The bill shows one number"),
    "bill": ("Elektrik faturası", "Electricity bill"),
    "total": ("Toplam", "Total"),
    "one_number": ("tek bir sayı,<br>kWh olarak", "one number,<br>in kWh"),
    "bill_note": ("Hangi cihazın ne kadar harcadığı yazmaz.",
                  "It does not say how much each appliance used."),
    "cold_fig": ("%19,5", "19.5%"),
    "cold": ("Türkiye’de nüfusun bu kadarı evini<br>yeterince ısıtamıyor.",
             "of people in Türkiye cannot keep their<br>home warm enough."),
    "cold_src": ("Eurostat, 2025", "Eurostat, 2025"),
    "meters": ("Her cihaza ayrı sayaç takmak pahalı<br>ve zahmetli.",
               "A separate meter on every appliance is<br>expensive and impractical."),
    # slide 3
    "t3": ("Gerçek bir evin bir günü", "One day in a real home"),
    "src3": ("REFIT veri seti, Ev 2, 17 Haziran 2014, 5 dakikalık ortalamalar",
             "REFIT dataset, House 2, 17 June 2014, 5-minute means"),
    "meter_total": ("Sayacın gördüğü toplam", "Total the meter sees"),
    "clipped": ("10,3 kW’a çıkıyor, kırpıldı", "peaks at 10.3 kW, clipped"),
    "quarter": ("O gün elektriğin dörtte biri bulaşık makinesine gitti",
                "The dishwasher used a quarter of that day’s energy"),
    "others": ("Diğer cihazlar", "Other appliances"),
    "day_total": ("Günün toplamı", "Day total"),
    # slide 4
    "t4": ("Gri çizgiden renkleri bulmak", "Colours from the grey line"),
    "model": ("Yapay zekâ<br>modeli", "AI<br>model"),
    "input": ("Girdi: sayacın toplam sinyali", "Input: the meter’s total signal"),
    "output": ("Çıktı: cihaz bazında tüketim", "Output: use per appliance"),
    "same_time": ("Cihazlar aynı anda çalışıyor.", "Appliances run at the<br>same time."),
    "alike": ("Güçleri birbirine benziyor.", "Their power levels look alike."),
    "wm_heater": ("Çamaşır makinesi ısıtıcısı", "Washing machine heater"),
    "dw_heater": ("Bulaşık makinesi ısıtıcısı", "Dishwasher heater"),
    # slide 5
    "t5": ("Kalkınma amaçları", "Sustainable development"),
    "sdg7": ("Erişilebilir ve<br>temiz enerji", "Affordable and<br>clean energy"),
    "target73": ("Enerji verimliliği", "Energy efficiency"),
    "see": ("İnsanlar ancak görebildikleri<br>tüketimi azaltabilir.",
            "People can only reduce the<br>consumption they can see."),
    "indirect": ("Dolaylı katkı", "Indirect contribution"),
    "sdg12": ("Sorumlu üretim ve tüketim", "Responsible consumption<br>and production"),
    "sdg13": ("İklim eylemi", "Climate action"),
    # slide 6
    "t6": ("İki temel çalışma", "Two key studies"),
    "kelly": ("Kelly ve<br>Knottenbelt, 2015", "Kelly and<br>Knottenbelt, 2015"),
    "kelly_txt": ("Derin sinir ağları klasik yöntemleri geçti.",
                  "Deep neural networks beat classical methods."),
    "kelly_src": ("“Neural NILM”, ACM BuildSys", "“Neural NILM”, ACM BuildSys"),
    "zhang": ("Zhang ve ark., 2018", "Zhang et al., 2018"),
    "zhang_txt": ("Sinyalin bir penceresinden tek bir cihazın o<br>andaki gücü.",
                  "From a window of the signal, one appliance’s power<br>at that moment."),
    "zhang_src": ("“Sequence-to-point learning”, AAAI", "“Sequence-to-point learning”, AAAI"),
    "missing": ("İki özette de olmayan", "Missing from both abstracts"),
    "tool": ("Ev halkı için<br>bir araç", "A tool for<br>households"),
    "cost": ("Maliyet hesabı", "A cost calculation"),
    "this_project": ("Bu proje: hiç görülmemiş<br>evlerde test, sonuç kWh ve<br>TL olarak.",
                     "This project: tested on<br>homes it has never seen,<br>results in kWh and lira."),
    # slide 7
    "t7": ("REFIT veri seti", "The REFIT dataset"),
    "homes": ("20 ev", "20 homes"),
    "homes_l": ("İngiltere, 2013-2015", "UK, 2013-2015"),
    "licence": ("CC BY 4.0", "CC BY 4.0"),
    "licence_l": ("Açık lisans, ücretsiz", "Open licence, free"),
    "sec": ("8 sn", "8 sec"),
    "sec_l": ("Yaklaşık bu aralıkla:<br>toplam güç ve 9 cihaz", "About this often: total<br>power, 9 appliances"),
    "rows": ("119,5 milyon", "119.5 million"),
    "rows_l": ("Satır, yaklaşık 6,9 GB", "Rows, about 6.9 GB"),
    "how_many": ("Kaç evde ölçülmüş", "Measured in how many homes"),
    "gap_fig": ("%25", "25%"),
    "gap": ("Bir evde dakikaların dörtte birinde veri yok.",
            "A quarter of one home’s minutes have no data."),
    "plan": ("Plan: boşlukları ayıkla, evleri eğitim ve test<br>olarak ayır.",
             "Plan: clean the gaps, split the homes into<br>training and test sets."),
    # slide 8
    "t8": ("Yöntem ve ilk kıyas", "Method and first test"),
    "dl": ("Derin<br>öğrenme", "Deep<br>learning"),
    "raw": ("Girdi ham bir zaman serisi.", "Input: a raw time series."),
    "cnn": ("Her cihaz için küçük bir<br>evrişimli sinir ağı<br>(sequence-to-point).",
            "A small convolutional neural<br>network for each appliance<br>(sequence-to-point)."),
    "target": ("Hedef: beş cihazın en<br>az dördünde klasik<br>yöntemden düşük hata.",
               "Target: lower error than<br>the classical method<br>for at least four of the<br>five appliances."),
    "mae": ("Ortalama mutlak hata (watt)", "Mean absolute error (watts)"),
    "mae_sub": ("Ev 2’de eğitim, Ev 5’te test", "Trained on House 2, tested on House 5"),
    "pred_mean": ("Ortalamayı<br>tahmin etmek", "Predicting the<br>average"),
    "classic": ("Klasik makine<br>öğrenmesi", "Classical machine<br>learning"),
    "dl_here": ("Derin öğrenmenin<br>fark yaratması beklenen yer",
                "Where deep learning<br>is expected to help"),
    # slide 9 (new)
    "t9": ("Türkiye’de fatura: gece gündüz tarifesi", "The bill in <span lang=\"tr\">Türkiye</span>: day and night tariff"),
    "three_rate": ("Üç zamanlı tarife, TL/kWh", "Three-rate tariff, TL per kWh"),
    "single_rate": ("Tek zamanlı, TL/kWh", "Single-rate, TL per kWh"),
    "night": ("Gece", "Night"),
    "day": ("Gündüz", "Day"),
    "peak": ("Puant", "Peak"),
    "upto8": ("günde 8 kWh’e kadar", "up to 8 kWh a day"),
    "above8": ("üstü", "above"),
    "src9": ("Fiyatlar: EPDK mesken tarifesi, 4 Nisan 2026’dan itibaren geçerli, vergiler dahil hesaplandı.",
             "Prices: EPDK residential tariff valid from 4 April 2026, taxes included by calculation."),
    "same_day": ("Slayt 3’teki gün, {kwh} kWh, iki tarifeyle", "The day from slide 3, {kwh} kWh, on both tariffs"),
    "bill_single": ("Tek zamanlı", "Single-rate"),
    "bill_three": ("Üç zamanlı", "Three-rate"),
    "bill_shift": ("Üç zamanlı, bulaşık<br>ve çamaşır geceye", "Three-rate, dishwasher<br>and wash at night"),
    "saving": ("günde {tl} TL az", "{tl} TL less a day"),
    "moved": ("{kwh} kWh geceye", "{kwh} kWh moved to night"),
    "verdict": ("Bu ev için tek zamanlı tarife daha ucuz. Demo bu karşılaştırmayı her ev için yapacak.",
                "For this home the single-rate tariff is cheaper. The demo makes this comparison for every home."),
    # slide 10 (new)
    "t10": ("İngiltere verisinden Türkiye’ye", "From UK data to <span lang=\"tr\">Türkiye</span>"),
    "grid_same": ("İngiltere’de de Türkiye’de de aynı şebeke", "The same grid in the UK and in Türkiye"),
    "five_here": ("Beş hedef cihaz Türk evlerinde de var", "The five target appliances are in Turkish homes too"),
    "st1": ("İkinci veri setinde test", "Test on a second dataset"),
    "st1_txt": ("REFIT ile eğitilen modelin hatası", "Error of a model trained on REFIT"),
    "st1_src": ("D’Incecco, Squartini ve Zhong, 2019", "D’Incecco, Squartini and Zhong, 2019"),
    "ukdale": ("UK-DALE, İngiltere", "UK-DALE, UK"),
    "redd": ("REDD, ABD", "REDD, US"),
    "redd_self": ("REDD ile eğitilen, REDD", "Trained on REDD, REDD"),
    "st2": ("Türk evine özgü yükler", "Loads of Turkish homes"),
    "st2_txt": ("REFIT’te yok, eğitim verisine yapay olarak eklenecek",
                "Missing in REFIT, added to the training data artificially"),
    "ac": ("Klima", "Air conditioner"),
    "boiler": ("Termosifon", "Water heater"),
    "tea": ("Çay makinesi", "Tea maker"),
    "st3": ("Saatlik veride ölçüm", "Measure on hourly data"),
    "st3_txt": ("Türkiye’de akıllı sayaçlar saatlik veri veriyor",
                "Smart meters in Türkiye give hourly data"),
    "res": (("1 dk", "15 dk", "1 saat"), ("1 min", "15 min", "1 hour")),
    "st4": ("Bir Türk evinde ölçüm", "Measure one Turkish home"),
    "st4_txt": ("Akıllı prizlerle birkaç hafta", "Smart plugs for a few weeks"),
    "st4_box": ("Hata, gerçek Türk verisinde raporlanacak", "The error, reported on real Turkish data"),
    # slide 11
    "t11": ("Demo ve sınırlar", "Demo and limits"),
    "demo": ("Dönem sonunda<br>tarayıcıdan açılan demo", "At the end of the term<br>a demo in the browser"),
    "uploaded": ("Yüklenen", "Uploaded"),
    "uploaded_txt": ("Bir günün<br>sayaç verisi", "One day of<br>meter data"),
    "shown": ("Görünen", "Shown"),
    "shown_txt": ("Cihaz bazında kWh ve TL, iki<br>tarifenin karşılaştırması,<br>geceye kaydırma önerisi",
                  "kWh and lira per appliance,<br>the two tariffs compared,<br>what to move to the night"),
    "limit": ("Sınır", "Limit"),
    "limit_txt": ("Türkiye’den etiketli açık veri<br>bulamadım. Kendi ölçümüm<br>küçük bir kontrol olacak.",
                  "I found no open labelled data<br>from Türkiye. My own<br>measurement will be a small check."),
    "closing": ("Faturanın nereye gittiğini gören ev,<br>tasarrufa nereden başlayacağını bilir",
                "Seeing the dishwasher’s share,<br>a family can run it less often"),
    "thanks": ("Teşekkürler", "Thank you"),
}

LANG = "tr"


def L(key, **kw):
    """The string for the current language."""
    v = S[key][0 if LANG == "tr" else 1]
    return v.format(**kw) if kw else v


def V(tr, en):
    """A layout value that differs between the languages."""
    return tr if LANG == "tr" else en


def num(x, nd=2):
    """A number with a decimal comma in Turkish and a point in English."""
    s = f"{x:.{nd}f}"
    return s.replace(".", ",") if LANG == "tr" else s


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

def load_data():
    day = json.loads((ANALYSIS / "chart_day.json").read_text())
    res = json.loads((ANALYSIS / "results.json").read_text())
    return day, res


# EPDK regulated tariff for low-voltage residential customers, valid from
# 4 April 2026, kuruş per kWh without taxes.
DIST = 242.49
ENERGY = {"low": 49.4065, "high": 189.5808, "day": 195.0640, "peak": 374.7551, "night": 51.3656}
BANDS = (("night", 0, 6), ("day", 6, 17), ("peak", 17, 22), ("night", 22, 24))


def all_in(energy_kurus):
    """TL per kWh with the 5% consumption tax on energy and 10% VAT on everything."""
    return (energy_kurus * 1.05 + DIST) * 1.10 / 100


PRICE = {k: all_in(v) for k, v in ENERGY.items()}


def band_of(hhmm):
    h = int(hhmm[:2])
    for name, a, b in BANDS:
        if a <= h < b:
            return name
    return "night"


def tariff_numbers(day):
    step = 5 / 60 / 1000  # 5-minute mean in W to kWh
    bands = [band_of(t) for t in day["t"]]
    kwh = {"day": 0.0, "peak": 0.0, "night": 0.0}
    for b, w in zip(bands, day["aggregate"]):
        kwh[b] += w * step
    total = sum(kwh.values())
    single = min(total, 8) * PRICE["low"] + max(total - 8, 0) * PRICE["high"]
    three = sum(kwh[b] * PRICE[b] for b in kwh)
    moved = 0.0
    for b, dw, wm in zip(bands, day["Dishwasher"], day["Washing Machine"]):
        if b != "night":
            moved += (dw + wm) * step
    shifted = dict(kwh)
    for b in ("day", "peak"):
        part = sum((dw + wm) * step for bb, dw, wm in zip(bands, day["Dishwasher"], day["Washing Machine"]) if bb == b)
        shifted[b] -= part
    shifted["night"] += moved
    three_shift = sum(shifted[b] * PRICE[b] for b in shifted)
    out = dict(total=total, kwh=kwh, single=single, three=three, three_shift=three_shift,
               moved=moved, saving=three - three_shift)
    # The numbers quoted in the narration and the spec.
    assert round(total, 2) == 10.34 and round(single, 2) == 37.28
    assert round(three, 2) == 49.95 and round(three_shift, 2) == 45.74
    assert round(moved, 2) == 2.54 and round(three - three_shift, 2) == 4.21
    return out


# --------------------------------------------------------------------------
# Layout helpers. Coordinates are pixels on the 1920x1080 slide; text is
# placed by its first baseline so the type sits where the grid wants it.
# --------------------------------------------------------------------------

HALF = {"j": (1.07 - 0.375) / 2, "k": (0.917 - 0.252) / 2}


def txt(html, x, base, size, face="k", weight=400, lh=None, color="ink", w=None,
        align="left", b=None, cls="", style=""):
    lh = lh or round(size * (1.0 if face == "j" else 1.3), 2)
    top = base - (lh / 2 + HALF[face] * size)
    pos = f"left:{x}px;" if align == "left" else f"right:{1920 - x}px;text-align:right;"
    if align == "center":
        pos = f"left:{x - w / 2}px;text-align:center;"
    width = f"width:{w}px;" if w else ""
    fam = "var(--font-display)" if face == "j" else "var(--font-body)"
    cl = "t" + (" up" if face == "j" else "") + (f" {cls}" if cls else "")
    db = f' data-b="{b}"' if b else ""
    return (f'<div class="{cl}"{db} style="{pos}top:{top:.2f}px;{width}font-family:{fam};'
            f'font-size:{size}px;line-height:{lh}px;font-weight:{weight};color:var(--color-{color});{style}">{html}</div>')


def box(x, y, w, h, fill=None, border=None, bw=4, b=None, cls="", style="", inner=""):
    st = f"left:{x}px;top:{y}px;width:{w}px;height:{h}px;"
    if fill:
        st += f"background:var(--color-{fill});"
    if border:
        st += f"border:{bw}px solid var(--color-{border});"
    db = f' data-b="{b}"' if b else ""
    return f'<div class="r {cls}"{db} style="{st}{style}">{inner}</div>'


def rule(x1, x2, y, th=4, color="ink", b=None):
    return box(x1, y, x2 - x1, th, fill=color, b=b)


def group(b, *parts):
    return f'<div data-b="{b}">' + "".join(parts) + "</div>"


def svg(b, body):
    db = f' data-b="{b}"' if b else ""
    return f'<svg class="layer"{db} viewBox="0 0 1920 1080" aria-hidden="true">{body}</svg>'


def title(key, size=96, base=170):
    return txt(L(key), 120, base, size, "j", 700, lh=size, b=1, cls="title")


def footer(n):
    return (rule(120, 1800, 984, 3)
            + txt(L("footer"), 120, 1041, 24, "k", 600, color="ink-2")
            + txt(f"{n} / {N_SLIDES}", 1800, 1041, 24, "k", 600, color="ink-2", align="right"))


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

STACK = (("Fridge-Freezer", "ink"), ("Washing Machine", "red"), ("Dishwasher", "blue"), ("Kettle", "yellow"))


def xs(n, x0, x1):
    return [x0 + i * (x1 - x0) / (n - 1) for i in range(n)]


def stacked_areas(day, x0, x1, y0, kw_px):
    n = len(day["t"])
    X = xs(n, x0, x1)
    base = [0.0] * n
    out = []
    for key, col in STACK:
        top = [base[i] + day[key][i] for i in range(n)]
        up = " ".join(f"{X[i]:.1f},{y0 - top[i] / 1000 * kw_px:.1f}" for i in range(n))
        down = " ".join(f"{X[i]:.1f},{y0 - base[i] / 1000 * kw_px:.1f}" for i in reversed(range(n)))
        out.append(f'<polygon class="f-{col}" points="{up} {down}"/>')
        base = top
    return "".join(out)


def total_line(day, x0, x1, y0, kw_px, width=5):
    n = len(day["t"])
    X = xs(n, x0, x1)
    pts = " ".join(f"{X[i]:.1f},{y0 - day['aggregate'][i] / 1000 * kw_px:.1f}" for i in range(n))
    return f'<polyline class="s-meter" style="stroke-width:{width}px" points="{pts}"/>'


def clip(cid, x, y, w, h):
    return f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'


def marker(x, y):
    return f'<circle class="mark" cx="{x}" cy="{y}" r="7"/>'


def leader(x1, y1, x2, y2):
    return f'<line class="lead" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'


# --------------------------------------------------------------------------
# Slides
# --------------------------------------------------------------------------

def slide1(D):
    p = []
    p.append(txt(L("name"), 120, 134, 52, "k", 500, b=1))
    p.append(txt(L("course"), 120, 194, 34, "k", 400, lh=46, color="muted", b=2))
    p.append(rule(120, 1800, 317, 4))
    extra = ""
    if LANG == "en":
        extra = txt(L("project_en"), 1101, 701, 40, "k", 600, color="muted")
    p.append(group(3, txt(L("project"), 120, 517, 184, "j", 700, lh=184, cls="cover"), extra))
    p.append(group(4, box(120, 729, 1680, 221, fill="ink"),
                   txt(L("question"), 160, 827, 68, "j", 700, lh=71, color="paper")))
    return "".join(p)


def slide2(D):
    p = [title("t2")]
    rows = [("fridge", "ink"), ("washer", "red"), ("dish", "blue"), ("kettle", "yellow"), ("micro", "light")]
    bill = [box(120, 293, 860, 657, border="ink", bw=4),
            txt(L("bill"), 148, 342, 28, "k", 600, color="muted"),
            box(124, 368, 852, 3, fill="ink"),
            box(124, 371, 852, 112, fill="meter"),
            txt(L("total"), 148, 453, 72, "j", 700, color="accent-ink"),
            txt(L("one_number"), 952, 418, 34, "k", 500, lh=41, color="accent-ink", align="right")]
    p.append(group(1, *bill))
    r = []
    for i, (k, col) in enumerate(rows):
        y = 510 + 70 * i
        if col == "light":
            r.append(box(148, y, 32, 32, fill="light", border="ink", bw=3))
        else:
            r.append(box(148, y, 32, 32, fill=col))
        r.append(txt(L(k), 204, y + 27, 34, "k", 400))
        r.append(txt("?", 952, y + 33, 52, "j", 700, color="muted", align="right"))
        r.append(box(148, y + 50, 804, 2, fill="rule"))
    r.append(txt(L("bill_note"), 148, 908, 34, "k", 600))
    p.append(group(2, *r))
    p.append(group(3, rule(1076, 1800, 356, 4),
                   txt(L("cold_fig"), 1076, 558, V(197, 200), "j", 700, cls="fig tn"),
                   txt(L("cold"), 1076, 627, 40, "k", 400, lh=52),
                   txt(L("cold_src"), 1076, 728, 24, "k", 400, color="muted")))
    p.append(group(4, rule(1076, 1800, 802, 4), txt(L("meters"), 1076, 885, 40, "k", 400, lh=52)))
    p.append(footer(2))
    return "".join(p)


def slide3(D):
    day = D["day"]
    p = [title("t3")]
    x0, x1, y0, k = 216, 1792, 691, 134
    axes = []
    for kw in (1, 2, 3):
        y = y0 - kw * k
        axes.append(f'<rect class="f-rule" x="{x0}" y="{y - 1}" width="{x1 - x0}" height="2"/>')
    axes.append(f'<rect class="f-ink" x="{x0 - 1}" y="{y0 - 2}" width="{x1 - x0 + 2}" height="3"/>')
    for i in range(5):
        x = x0 + i * (x1 - x0) / 4
        axes.append(f'<rect class="f-ink" x="{x - 1.5}" y="{y0 - 2}" width="3" height="11"/>')
    lab = [txt(f"{kw} kW", 199, y0 - kw * k + 11, 29, "k", 400, color="muted", align="right") for kw in (1, 2, 3)]
    for i, hh in enumerate(("00:00", "06:00", "12:00", "18:00", "24:00")):
        x = x0 + i * (x1 - x0) / 4
        al = "left" if i == 0 else ("right" if i == 4 else "center")
        xx = x if i in (0, 4) else x
        lab.append(txt(hh, xx + (1 if i == 0 else 0), 734, 28, "k", 400, color="muted", align=al, w=120 if al == "center" else None))
    lab.append(txt(L("src3"), 1791, 234, 24.4, "k", 500, color="muted", align="right", cls="pn"))
    p.append(group(1, svg(None, "".join(axes)), *lab))
    cl = clip("c3", x0 - 5, 220, x1 - x0 + 10, y0 - 220 + 4)
    line = svg(None, f'<defs>{cl}</defs><g clip-path="url(#c3)">{total_line(day, x0, x1, y0, k)}</g>'
               + leader(615, 253, 698, 253) + marker(705, 253))
    p.append(group(2, line, txt(L("meter_total"), 602, 264, 34.5, "k", 500, align="right"),
                   txt(L("clipped"), 730, 244, 25.7, "k", 400, color="muted", cls="pn")))
    areas = svg(None, f'<defs>{clip("c3b", x0, 216, x1 - x0 + 10, y0 - 216)}</defs>'
                f'<g clip-path="url(#c3b)">{stacked_areas(day, x0, x1, y0, k)}</g>')
    p.insert(2, group(3, areas))  # areas sit under the grey line
    p.append(group(3, svg(None, leader(548, 363, 678, 464) + marker(684, 468)
                          + leader(372, 571, 320, 681) + marker(317, 688)
                          + leader(1291, 381, 1239, 541) + marker(1236, 548)
                          + leader(1632, 331, 1736, 525) + marker(1740, 531)),
                   txt(L("washer"), 535, 371, 34.5, "k", 500, align="right"),
                   txt(L("fridge"), 385, 582, 34, "k", 500),
                   txt(L("kettle"), 1305, 390, 34.5, "k", 500),
                   txt(L("dish"), 1618, 340, 34.5, "k", 500, align="right")))
    kwh = day["kwh"]
    parts = [("Dishwasher", "blue", "accent-ink", "dish"), ("Washing Machine", "red", "accent-ink", "washer_short"),
             ("Fridge-Freezer", "ink", "paper", "fridge"), ("Kettle", "yellow", "ink", "kettle")]
    total = kwh["Aggregate"]
    other = round(total - sum(kwh[k] for k, *_ in parts), 2)
    x = 120.0
    bar = []
    for i, (key, col, tc, lk) in enumerate(parts + [(None, "meter", "accent-ink", "others")]):
        v = kwh[key] if key else other
        w = v / total * 1680
        bar.append(box(round(x, 1), 849, round(w + 0.6, 1), 55, fill=col))
        label = num(v) + (" kWh" if i == 0 else "")
        bar.append(txt(label, x + 8, 886, 27, "k", 700, color=tc, cls="pn"))
        bar.append(txt(L(lk), x + (40 if key is None else 0), 946, 28, "k", 600))
        x += w
    bar.append(txt(f'{L("day_total")} {num(total)} kWh', 1799, 946, 28, "k", 600, align="right"))
    p.append(group(4, txt(L("quarter"), 120, 825, 52, "j", 700), *bar))
    p.append(footer(3))
    return "".join(p)


ARROW = ('<svg class="arrow" width="59" height="27" viewBox="0 0 59 27" aria-hidden="true">'
         '<path d="M0 13.5H56M43.5 1L56 13.5L43.5 26" fill="none" stroke="currentColor" stroke-width="3"/></svg>')


def slide4(D):
    day = D["day"]
    p = [title("t4")]
    k = 258 / 3.5
    inp = svg(None, f'<defs>{clip("c4a", 110, 230, 640, 262)}</defs><g clip-path="url(#c4a)">'
              f'{total_line(day, 121, 740, 488.5, k)}</g><rect class="f-ink" x="120" y="489" width="620" height="3"/>')
    out = svg(None, f'<defs>{clip("c4b", 1180, 230, 620, 260)}</defs><g clip-path="url(#c4b)">'
              f'{stacked_areas(day, 1180, 1800, 490, k)}</g><rect class="f-ink" x="1180" y="489" width="620" height="3"/>')
    mid = (f'<div class="flow" style="top:292px;height:145px">'
           f'{ARROW}<div class="modelbox up">{L("model")}</div>{ARROW}</div>')
    p.append(group(1, inp, out, mid,
                   txt(L("input"), 120, 537, 28, "k", 600, color="ink-2"),
                   txt(L("output"), 1180, 537, 28, "k", 600, color="ink-2")))
    cells = [("fridge", "ink", "paper"), ("washer_cell", "red", "accent-ink"), ("dish_cell", "blue", "accent-ink"),
             ("kettle", "yellow", "ink"), ("micro", "light", "ink")]
    c = [box(120, 587, 1680, 113, border="ink", bw=3)]
    for i, (key, col, tc) in enumerate(cells):
        x = 120 + i * 336
        c.append(box(x, 587, 336 + (0 if i < 4 else 0), 113, fill=col, border="ink", bw=3))
        two = "<br>" in L(key)
        c.append(txt(L(key), x + 28, 655 if not two else 635, 34, "j", 700, lh=39, color=tc))
    p.append(group(2, *c))
    p.append(group(3, rule(120, 714, V(780, 740), 4),
                   txt(L("same_time"), 120, V(837, 798), 40.5, "k", 500, lh=50),
                   box(120, V(866, 876), 594, 2, fill="rule"),
                   txt(L("alike"), 120, V(921, 932), 40.5, "k", 500)))
    def fig(x, val, lk, col):
        return (txt(val, x, V(885, 896), 112, "j", 700)
                + txt("kW", x + 188, V(885, 896), 40, "k", 500)
                + box(x, V(916, 926), 28, 28, fill=col)
                + txt(L(lk), x + 40, V(941, 951), 28.4, "k", 500))
    p.append(group(4, rule(810, 1800, V(768, 778), 4), fig(810, num(2.1, 1), "wm_heater", "red"),
                   fig(1325, num(2.2, 1), "dw_heater", "blue")))
    p.append(footer(4))
    return "".join(p)


def slide5(D):
    p = [title("t5")]
    p.append(group(1, box(120, 250, 560, 700, fill="ink"),
                   txt("7", 160, 590, 400, "j", 700, color="paper"),
                   txt(L("sdg7"), 160, V(900, 900) - 52, 52, "j", 700, lh=52, color="paper")))
    p.append(group(2, rule(776, 1800, 250, 4),
                   txt("7.3", 776, 442, 130, "j", 700, cls="tn"),
                   txt(L("target73"), 1023, 442.5, 72, "j", 700),
                   txt(L("see"), 776, 564, 52, "k", 400, lh=64)))
    r0 = V(769, 713)
    p.append(group(3, txt(L("indirect"), 778, r0 - 22, 28, "k", 600, color="muted"),
                   rule(776, 1800, r0, 3),
                   txt("SDG 12", 776, r0 + 60, 52, "j", 700, cls="tn"),
                   txt(L("sdg12"), 1048, r0 + 61, 40, "k", 400, lh=56),
                   box(776, 860, 1024, 2, fill="rule"),
                   txt("SDG 13", 776, 919, 52, "j", 700, cls="tn"),
                   txt(L("sdg13"), 1048, 920, 40, "k", 400)))
    p.append(footer(5))
    return "".join(p)


def slide6(D):
    p = [title("t6")]
    p.append(group(2, rule(120, 1064, 266, 4), txt(L("kelly"), 120, 355, 72, "j", 700, lh=72, cls="tn"),
                   txt(L("kelly_txt"), 120, 495, 40, "k", 400),
                   txt(L("kelly_src"), 120, 550, 28, "k", 400, color="muted")))
    p.append(group(3, rule(120, 1064, 653, 4), txt(L("zhang"), 120, 743, 72, "j", 700, lh=72, cls="tn"),
                   txt(L("zhang_txt"), 120, 809, 40, "k", 400, lh=52),
                   txt(L("zhang_src"), 120, 915, 28, "k", 400, color="muted")))
    p.append(group(4, box(1160, 266, 640, 566, border="ink", bw=4),
                   txt(L("missing"), 1204, 324, 28, "k", 600, color="muted"),
                   box(1164, 345, 632, 2, fill="rule"),
                   txt(L("tool"), 1204, 415, 50, "j", 700, lh=52),
                   box(1164, 497, 632, 2, fill="rule"),
                   txt(L("cost"), 1204, 568, 50, "j", 700)))
    p.append(group(5, box(1160, 598, 640, 234, fill="ink"),
                   txt(L("this_project"), 1204, 677, 40.5, "k", 500, lh=50, color="paper")))
    p.append(footer(6))
    return "".join(p)


def slide7(D):
    p = [title("t7")]
    cuts = V((486, 866, 1265), (525, 905, 1277))
    xs_ = (120,) + cuts
    cells = [("homes", "homes_l"), ("licence", "licence_l"), ("sec", "sec_l"), ("rows", "rows_l")]
    p.append(box(120, 226, 1680, 217, border="ink", bw=4))
    for i, (a, bkey) in enumerate(cells):
        x = xs_[i]
        parts = []
        if i:
            parts.append(box(x, 230, 3, 209, fill="ink"))
        parts.append(txt(L(a), x + 28, 321, 63.8, "j", 700, cls="tn"))
        parts.append(txt(L(bkey), x + 28, 369, 28, "k", 600, lh=36, color="ink-2"))
        p.append(group(i + 1, *parts))
    p[-4] = p[-4]  # keep order
    homes = [("fridge", "ink", 20), ("washer", "red", 19), ("micro", "light", 16), ("dish", "blue", 15), ("kettle", "yellow", 15)]
    bars = [txt(L("how_many"), 120, 600, 28, "k", 600, color="muted")]
    for i, (k, col, n) in enumerate(homes):
        y = 620 + 66 * i
        bars.append(box(120, y, 824, 2, fill="rule"))
        if col == "light":
            bars.append(box(416, y + 14, n * 20.8, 40, fill="light", border="ink", bw=3))
        else:
            bars.append(box(416, y + 14, n * 20.8, 40, fill=col))
        bars.append(txt(L(k), 120, y + 43, 28, "k", 600))
        bars.append(txt(str(n), 943, y + 45, 34, "j", 700, align="right", cls="tn"))
    p.append(group(4, *bars))
    p.append(group(5, rule(1040, 1800, 528, 4), txt(L("gap_fig"), 1040, 671, 131, "j", 700, cls="tn"),
                   txt(L("gap"), 1040, 728, 34, "k", 400),
                   box(1040, 757, 760, 40, fill="light", border="ink", bw=3),
                   box(1043, 760, 566, 34, fill="meter", style="border-right:3px solid var(--color-ink)")))
    p.append(group(6, box(1040, 837, 760, 2, fill="rule"), txt(L("plan"), 1040, 891, 34.4, "k", 500, lh=47)))
    p.append(footer(7))
    return "".join(p)


def slide8(D):
    res = D["res"]["baselines"]
    p = [title("t8")]
    p.append(group(1, rule(120, 580, 250, 4), txt(L("dl"), 120, 340, 72, "j", 700, lh=72),
                   txt(L("raw"), 120, 474, 34, "k", 400)))
    p.append(group(2, txt(L("cnn"), 120, 543, 34, "k", 400, lh=44)))
    p.append(group(3, rule(676, 1800, 250, 4), txt(L("mae"), 677, 314, 40, "k", 600),
                   txt(L("mae_sub"), 676, 360, 28, "k", 400, color="muted")))
    scale = 600 / res["Kettle"]["mae_mean"]

    def pair(y, key, col, name, d=0):
        m, g = res[key]["mae_mean"], res[key]["mae_gb"]
        out = [box(700, y, 36, 36, fill=col), txt(L(name), 754, y + 37, 52, "j", 700)]
        r = y + d
        out.append(txt(L("pred_mean"), 700, r + 86, 28, "k", 600, lh=32))
        out.append(box(974, r + 63, m * scale, 60, fill="light", border="ink", bw=3))
        out.append(txt(f'{num(m, 1)}<span class="unitw">W</span>', 974 + m * scale + 26, r + 111, 51, "j", 700, cls="wfig tn"))
        out.append(txt(L("classic"), 700, r + 166, 28, "k", 600, lh=32))
        out.append(box(974, r + 143, g * scale, 60, fill=col))
        out.append(txt(f'{num(g, 1)}<span class="unitw">W</span>', 974 + g * scale + 26, r + 191, 51, "j", 700, cls="wfig tn"))
        return out
    p.append(group(4, *pair(424, "Kettle", "yellow", "kettle")))
    p.append(group(5, *pair(718, "Washing Machine", "red", "washer", 6)))
    p.append(group(6, box(676, 678, 1124, 276, border="ink", bw=4),
                   txt(L("dl_here"), 1776, 728, 28, "k", 600, lh=33, align="right")))
    p.append(group(7, box(120, V(773, 729), 460, V(181, 225), fill="ink"),
                   txt(L("target"), 160, V(831, 787), 34.5, "k", 500, lh=44, color="paper")))
    p.append(footer(8))
    return "".join(p)


def slide9(D):
    T = D["tariff"]
    p = [txt(L("t9"), 120, 170, 74, "j", 700, lh=74, b=1, cls="title")]
    # b1: the three-rate day as a strip, to scale in hours (x) and in price (height).
    x0, x1, base, k = 120, 1344, 492, 18.0
    ph = (x1 - x0) / 24
    strip = []
    for name, a, b in BANDS:
        price = PRICE[name]
        h = price * k
        strip.append(box(round(x0 + a * ph, 1), round(base - h, 1), round((b - a) * ph + 0.5, 1), round(h, 1), fill="ink"))
        if not (name == "night" and a == 22):
            strip.append(txt(num(price), x0 + a * ph, base - h - 14, 52, "j", 700, cls="tn"))
        strip.append(txt(L(name), x0 + a * ph + 14, base - 18, 26, "k", 600, color="paper"))
    for hh in (0, 6, 17, 22):
        al = "left" if hh == 0 else "center"
        strip.append(txt(f"{hh:02d}:00", x0 + hh * ph, base + 36, 26, "k", 500, color="muted", align=al,
                         w=None if al == "left" else 100))
    p.append(group(1, rule(120, 1344, 250, 4), txt(L("three_rate"), 120, 292, 30, "k", 600), *strip,
                   txt(L("src9"), 120, 568, 24, "k", 400, color="muted")))
    # b2: the single-rate tariff on the same baseline and price scale; x is kWh in a day.
    sx0, lw, hw = 1440, 240, 120
    single = [rule(sx0, 1800, 250, 4), txt(L("single_rate"), sx0, 292, 30, "k", 600),
              box(sx0, round(base - PRICE["low"] * k, 1), lw, round(PRICE["low"] * k, 1), fill="ink"),
              box(sx0 + lw, round(base - PRICE["high"] * k, 1), hw, round(PRICE["high"] * k, 1), fill="ink"),
              txt(num(PRICE["low"]), sx0, base - PRICE["low"] * k - 14, 52, "j", 700, cls="tn"),
              txt(num(PRICE["high"]), sx0 + lw, base - PRICE["high"] * k - 14, 52, "j", 700, cls="tn"),
              txt(L("upto8"), sx0, base + 36, 26, "k", 500, color="muted"),
              txt(L("above8"), sx0 + lw + 14, base - 18, 26, "k", 600, color="paper")]
    p.append(group(2, *single))
    # b3, b4: the day from slide 3 priced both ways, bars to scale in TL.
    bx = 430
    scale = 680 / T["three"]
    y0 = 662
    g3 = [rule(120, 1800, 604, 4), txt(L("same_day", kwh=num(T["total"])), 120, 646, 30, "k", 600)]
    g4 = []
    rows = (("bill_single", T["single"]), ("bill_three", T["three"]), ("bill_shift", T["three_shift"]))
    for i, (lk, val) in enumerate(rows):
        y = y0 + i * 66
        tgt = g4 if i == 2 else g3
        two = "<br>" in L(lk)
        tgt.append(txt(L(lk), 120, y + (20 if two else 36), 26 if two else 28, "k", 600, lh=28))
        tgt.append(box(bx, y, val * scale, 50, fill="meter"))
        if i == 2:
            gap = (T["three"] - val) * scale
            tgt.append(box(bx + val * scale, y, gap, 50, fill="light", border="ink", bw=3))
        vx = bx + T["three"] * scale + 24 if i == 2 else bx + val * scale + 24
        tgt.append(txt(f'{num(val)} TL', vx, y + 43, 48, "j", 700, cls="tn"))
        if i == 2:
            sx = vx + 236
            tgt.append(txt(L("saving", tl=num(T["saving"])), sx, y + 20, 26, "k", 600, lh=28))
            tgt.append(box(sx, y + 31, 20, 20, fill="blue"))
            tgt.append(box(sx + 26, y + 31, 20, 20, fill="red"))
            tgt.append(txt(L("moved", kwh=num(T["moved"])), sx + 56, y + 48, 26, "k", 600, color="ink-2"))
    p.append(group(3, *g3))
    p.append(group(4, *g4))
    p.append(group(5, box(120, 874, 1680, 76, fill="ink"),
                   txt(L("verdict"), 160, 923, 32, "k", 600, color="paper")))
    p.append(footer(9))
    return "".join(p)


def chips(x, y, labels, h=64, size=28, last_ink=False, b=None):
    """A row of ruled cells sized to their words, left to right."""
    cells = "".join(
        f'<div class="chip up{" chip-ink" if last_ink and i == len(labels) - 1 else ""}" '
        f'style="height:{h}px;font-size:{size}px">{lab}</div>' for i, lab in enumerate(labels))
    return f'<div class="chips" style="left:{x}px;top:{y}px">{cells}</div>'


def slide10(D):
    p = [title("t10", size=V(92, 96))]
    # b1: what is the same in both countries.
    sw = "".join(box(1110 + i * 46, 286, 34, 34, fill=c, border="ink" if c == "light" else None, bw=3)
                 for i, c in enumerate(("ink", "red", "blue", "yellow", "light")))
    p.append(group(1, box(120, 226, 1680, 176, border="ink", bw=4),
                   txt("230", 148, 321, 63.8, "j", 700, cls="tn"),
                   txt("V", 288, 321, 40, "k", 500),
                   txt("50", 380, 321, 63.8, "j", 700, cls="tn"),
                   txt("Hz", 478, 321, 40, "k", 500),
                   txt(L("grid_same"), 148, 369, 28, "k", 600, color="ink-2"),
                   box(1004, 230, 3, 168, fill="ink"),
                   txt("5", 1032, 321, 63.8, "j", 700, cls="tn"), sw,
                   txt(L("five_here"), 1032, 369, 28, "k", 600, color="ink-2")))
    tops = (436, 600, 717, 834)

    def head(i, tk, dk):
        y = tops[i]
        return [rule(120, 1800, y, 4 if i == 0 else 2, color="ink" if i == 0 else "rule"),
                txt(str(i + 1), 120, y + 94, 92, "j", 700, cls="tn"),
                txt(L(tk), 220, y + 50, 40, "j", 700), txt(L(dk), 220, y + 90, 28, "k", 400)]
    # step 1: error on other datasets, to scale in watts.
    y = tops[0]
    sc = 300 / 32.1
    bars = [txt(L("st1_src"), 220, y + 128, 24, "k", 400, color="muted")]
    for j, (lk, val, fill) in enumerate((("ukdale", 11.8, "ink"), ("redd", 32.1, "ink"), ("redd_self", 23.7, "light"))):
        yy = y + 22 + j * 42
        bars.append(txt(L(lk), 1300, yy + 25, 26, "k", 600, align="right"))
        bars.append(box(1324, yy, val * sc, 34, fill=fill, border="ink" if fill == "light" else None, bw=3))
        bars.append(txt(f'{num(val, 1)} W', 1324 + val * sc + 16, yy + 30, 34, "j", 700, cls="tn"))
    p.append(group(2, *head(0, "st1", "st1_txt"), *bars))
    y = tops[1]
    p.append(group(3, *head(1, "st2", "st2_txt"),
                   chips(1004, y + 26, [L("ac"), L("boiler"), L("tea")])))
    y = tops[2]
    p.append(group(4, *head(2, "st3", "st3_txt"),
                   chips(1004, y + 26, list(S["res"][0 if LANG == "tr" else 1]), last_ink=True)))
    y = tops[3]
    p.append(group(5, *head(3, "st4", "st4_txt"), box(1004, y + 26, 796, 64, fill="ink"),
                   txt(L("st4_box"), 1032, y + 68, 28, "k", 600, color="paper")))
    p.append(footer(10))
    return "".join(p)


def slide11(D):
    p = [title("t11")]
    cut = 520
    p.append(group(1, box(120, 250, 911, 380, border="ink", bw=4),
                   txt(L("demo"), 164, 336, 52, "j", 700, lh=52)))
    p.append(group(2, box(124, 428, 903, 3, fill="ink"), box(cut, 431, 3, 195, fill="ink"),
                   txt(L("uploaded"), 164, 484, 34, "k", 600, color="muted"),
                   txt(L("uploaded_txt"), 164, 530, 32, "k", 400, lh=40),
                   txt(L("shown"), cut + 44, 484, 34, "k", 600, color="muted"),
                   txt(L("shown_txt"), cut + 44, 530, 32, "k", 400, lh=40)))
    p.append(group(3, rule(1127, 1800, 250, 4), txt(L("limit"), 1127, 317, 40.6, "k", 500, color="muted"),
                   txt(L("limit_txt"), 1127, 393, 36, "k", 400, lh=52)))
    p.append(group(4, rule(120, 1800, 681, 4), txt(L("closing"), 120, 761, 60, "j", 700, lh=62)))
    p.append(group(5, txt(L("thanks"), 1800, 925, 96, "j", 700, align="right")))
    p.append(footer(11))
    return "".join(p)


SLIDES = [slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9, slide10, slide11]

# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

CSS = """
@font-face { font-family: "Jost"; src: url("fonts/Jost-VariableFont_wght.ttf") format("truetype"); font-weight: 100 900; font-display: block; }
@font-face { font-family: "Karla"; src: url("fonts/Karla-VariableFont_wght.ttf") format("truetype"); font-weight: 200 800; font-display: block; }
:root {
  --color-paper: oklch(84% 0.024 82);
  --color-light: oklch(89.5% 0.018 84);
  --color-ink: oklch(18% 0.008 60);
  --color-ink-2: oklch(27% 0.01 60);
  --color-muted: oklch(39% 0.014 62);
  --color-rule: oklch(58% 0.022 72);
  --color-meter: oklch(50% 0.007 75);
  --color-blue: oklch(46% 0.2 264);
  --color-red: oklch(50% 0.19 31);
  --color-yellow: oklch(85% 0.165 92);
  --color-accent-ink: oklch(96% 0.012 82);
  --font-display: "Jost", "Futura", sans-serif;
  --font-body: "Karla", ui-sans-serif, system-ui, sans-serif;
  --tracking-display: -0.005em;
}
@page { size: 1920px 1080px; margin: 0; }
html, body { margin: 0; padding: 0; background: var(--color-paper); overflow-x: clip; }
body { -webkit-print-color-adjust: exact; print-color-adjust: exact; font-synthesis: none; }
.slide { position: relative; width: 1920px; height: 1080px; overflow: hidden; background: var(--color-paper);
  break-after: page; font-kerning: normal; }
.slide[hidden] { display: none; }
.t { position: absolute; white-space: nowrap; font-variant-numeric: lining-nums tabular-nums; }
.up { font-variant-numeric: lining-nums; }
.up { text-transform: uppercase; letter-spacing: var(--tracking-display); }
.r { position: absolute; box-sizing: border-box; }
.layer { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: visible; }
.pending { opacity: 0; }
.unit { font-family: var(--font-body); font-weight: 500; font-size: 40px; text-transform: none; letter-spacing: 0; margin-left: 20px; }
.unitw { font-family: var(--font-body); font-weight: 600; font-size: 28px; text-transform: none; letter-spacing: 0; margin-left: 8px; }
.flow { position: absolute; left: -3px; width: 1920px; display: flex; justify-content: center; align-items: center; }
.flow .arrow:first-child { margin-right: 21px; } .flow .arrow:last-child { margin-left: 16px; }
.pn { font-variant-numeric: lining-nums proportional-nums; }
.tn { font-variant-numeric: lining-nums tabular-nums; }
.arrow { display: block; flex-shrink: 0; color: var(--color-ink); }
.modelbox { box-sizing: border-box; height: 145px; display: flex; align-items: center; justify-content: center; text-align: center;
  padding: 0 25px; border: 4px solid var(--color-ink); font-family: var(--font-display); font-weight: 700; font-size: 40px;
  line-height: 44px; color: var(--color-ink); }
.chips { position: absolute; display: flex; gap: 16px; }
.chip { box-sizing: border-box; display: flex; align-items: center; padding: 0 18px; border: 3px solid var(--color-ink);
  font-family: var(--font-display); font-weight: 700; line-height: 1; color: var(--color-ink); white-space: nowrap; }
.chip-ink { background: var(--color-ink); color: var(--color-paper); }
.f-ink { fill: var(--color-ink); } .f-red { fill: var(--color-red); } .f-blue { fill: var(--color-blue); }
.f-yellow { fill: var(--color-yellow); } .f-rule { fill: var(--color-rule); } .f-light { fill: var(--color-light); }
.s-meter { fill: none; stroke: var(--color-meter); stroke-linejoin: round; stroke-linecap: round; }
.lead { stroke: var(--color-ink); stroke-width: 3px; }
.mark { fill: var(--color-light); stroke: var(--color-ink); stroke-width: 3px; }
"""

JS = """
(function () {
  var q = new URLSearchParams(location.search);
  var s = parseInt(q.get('s') || '0', 10);
  var b = q.has('b') ? parseInt(q.get('b'), 10) : 99;
  var slides = document.querySelectorAll('.slide');
  if (s) slides.forEach(function (el, i) { el.hidden = (i + 1 !== s); });
  document.querySelectorAll('[data-b]').forEach(function (el) {
    if (parseInt(el.getAttribute('data-b'), 10) > b) el.classList.add('pending');
  });
})();
"""


def build(lang):
    global LANG
    LANG = lang
    day, res = load_data()
    D = {"day": day, "res": res, "tariff": tariff_numbers(day)}
    body = "\n".join(f'<section class="slide" id="s{i + 1}">{f(D)}</section>' for i, f in enumerate(SLIDES))
    title_ = "Fatura Dedektifi, Idea Proposal"
    return (f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=1920">\n<title>{escape(title_)}</title>\n'
            f'<style>{CSS}</style>\n</head>\n<body>\n{body}\n<script>{JS}</script>\n</body>\n</html>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", choices=("tr", "en"), default=os.environ.get("DECK_LANG", "tr"))
    args = ap.parse_args()
    out = HERE / f"slides_{args.lang}.html"
    out.write_text(build(args.lang), encoding="utf-8")
    print(out.name)


if __name__ == "__main__":
    main()
