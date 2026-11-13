"""Price a typical Turkish household on the single-rate and three-rate tariffs, using EPIAS load profiles.

EPIAS (the Turkish market operator) publishes hourly profile coefficients that suppliers use to
split a meter reading into hours for settlement. This script uses the 2025 coefficients for
low-voltage residential customers (Mesken - AG) in all 21 distribution companies and:
  - builds a national hourly load shape (share of daily energy in each hour of the day)
    for January, July and the whole year
  - works out the share of daily energy in the day, peak and night tariff bands
  - prices daily consumption of 4.9, 8, 10 and 15 kWh on both tariffs
  - finds the night share at which the three-rate tariff becomes the cheaper one

Two steps:
  1. Build the small processed CSV from the 12 monthly Excel files (about 21 MB each, not kept
     in the repository). --download fetches any that are missing into --raw-dir.
       python profile_cost.py --build --raw-dir raw --download
  2. Run the analysis from the processed CSV alone (works offline):
       python profile_cost.py --out-dir .
"""
import argparse
import datetime
import json
import os
import urllib.request

import matplotlib
matplotlib.use("Agg")  # draw to a file, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Data source
# Announcement page for the 2025 coefficients. The 2026 announcement
# (epias.com.tr/tum-duyurular/piyasa-duyurulari/elektrik/kayit-ve-uzlastirma/2026-yili-profil-katsayilari/)
# has no Excel files; it points to the transparency platform, whose service needs a login.
# So 2025 is the newest year published as open files.
SOURCE_PAGE = "https://www.epias.com.tr/genel/2025-yili-profil-katsayilari/"
FILE_BASE = "https://www.epias.com.tr/wp-content/uploads/2024/11/"
MONTH_FILES = [  # month number, file name as published (September was reissued as v2)
    (1, "Ocak-2025.xlsx"), (2, "Subat-2025.xlsx"), (3, "Mart-2025.xlsx"),
    (4, "Nisan-2025.xlsx"), (5, "Mayis-2025.xlsx"), (6, "Haziran-2025.xlsx"),
    (7, "Temmuz-2025.xlsx"), (8, "Agustos-2025.xlsx"),
    (9, "profil_katsayilari_eylul_2025_v2.xlsx"), (10, "Ekim-2025.xlsx"),
    (11, "Kasim-2025.xlsx"), (12, "Aralik-2025.xlsx"),
]
YEAR = 2025
GROUP = "Mesken - AG"                  # residential, low voltage
SINGLE_TYPE = "Tek Zamanlı"            # single-rate meter reading
THREE_TYPE = "Üç Zamanlı"              # three-rate meter reading
PROCESSED_CSV = "mesken_ag_hourly_2025.csv"

# ---------------------------------------------------------------------------
# Tariff constants
# Source: EPDK regulated national tariff table, low-voltage residential customers
# (mesken, AG), valid from 4 April 2026.
# Prices exclude taxes, in kurus per kWh.
DISTRIBUTION = 242.49           # same for every band and tier
SINGLE_LOW = 49.4065            # single-rate energy, up to an average of 8 kWh per day
SINGLE_HIGH = 189.5808          # single-rate energy, the part above 8 kWh per day
SINGLE_LIMIT_KWH_PER_DAY = 8    # the tier is marginal: only the kWh above 8 pay the high price
THREE_RATE = {"day": 195.0640, "peak": 374.7551, "night": 51.3656}
# Time bands, the same every day of the year: (start hour, end hour).
BANDS = {"day": [(6, 17)], "peak": [(17, 22)], "night": [(22, 24), (0, 6)]}
# Taxes. Our own calculation from the published rates, not part of the EPDK table:
# 5% consumption tax (BTV) on the energy part, then 10% VAT (KDV) on everything.
BTV = 0.05
KDV = 0.10
# ---------------------------------------------------------------------------

LEVELS = [4.9, 8, 10, 15]       # daily consumption levels to price, kWh per day
NIGHT_SCENARIOS = [0.4, 0.5, 0.6, 0.7, 0.8]  # night shares for the "what if" table
BILLING_DAYS = 30               # one billing month
SHAPES = {"January": [1], "July": [7], "Year": list(range(1, 13))}


def hour_band(hour):
    for name, spans in BANDS.items():
        for start, end in spans:
            if start <= hour < end:
                return name


# ---------------------------------------------------------------------------
# Step 1: raw Excel files -> small processed CSV

def download(raw_dir):
    os.makedirs(raw_dir, exist_ok=True)
    for _, name in MONTH_FILES:
        path = os.path.join(raw_dir, name)
        if not os.path.exists(path):
            print("downloading", name)
            req = urllib.request.Request(FILE_BASE + name, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as r, open(path, "wb") as f:
                f.write(r.read())


def read_month(path):
    """Rows of one monthly file for the residential low-voltage group only.

    The files have about 390,000 rows each, so we stream them and keep only what we need.
    """
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    header = next(rows)
    col = {name: i for i, name in enumerate(header)}
    keep = []
    for r in rows:
        if r[col["PROFIL_ABONE_GRUP"]] == GROUP:
            keep.append((r[col["ORG_AD"]], r[col["OKUMA_TIP"]], r[col["SAAT"]], r[col["CARPAN"]]))
    wb.close()
    return pd.DataFrame(keep, columns=["org", "read_type", "time", "coef"])


def build(raw_dir, out_csv):
    """Sum each company's hourly coefficients by hour of day, one month at a time."""
    parts, checks = [], []
    for month, name in MONTH_FILES:
        df = read_month(os.path.join(raw_dir, name))
        df["hour"] = df["time"].dt.hour
        df["band"] = df["hour"].map(hour_band)
        # Check what the coefficients mean before using them. Single-rate coefficients
        # should add up to 1 over the month; three-rate ones to 1 within each band.
        single = df[df.read_type == SINGLE_TYPE]
        three = df[df.read_type == THREE_TYPE]
        s_sum = single.groupby("org").coef.sum()
        t_sum = three.groupby(["org", "band"]).coef.sum()
        # Is the three-rate series just the single-rate one rescaled inside each band?
        s = single.set_index(["org", "time"])
        band_total = s.groupby(["org", "band"]).coef.transform("sum")
        rescaled = s.coef / band_total
        diff = (rescaled - three.set_index(["org", "time"]).coef.reindex(s.index)).abs().max()
        hours_per_org = single.groupby("org").size()
        checks.append({"month": month, "orgs": int(s_sum.size),
                       "hours": int(hours_per_org.iloc[0]),
                       "single_sum_range": [float(s_sum.min()), float(s_sum.max())],
                       "three_band_sum_range": [float(t_sum.min()), float(t_sum.max())],
                       "three_vs_rescaled_single_max_diff": float(diff)})
        print(f"month {month:2d}: {s_sum.size} companies, {hours_per_org.iloc[0]} hours, "
              f"single sums {s_sum.min():.6f}-{s_sum.max():.6f}, "
              f"three-rate band sums {t_sum.min():.6f}-{t_sum.max():.6f}, "
              f"three-rate minus rescaled single max {diff:.1e}")
        g = df.groupby(["org", "read_type", "hour"]).coef.sum().unstack("read_type")
        g = g.rename(columns={SINGLE_TYPE: "single_share", THREE_TYPE: "three_within_band"})
        g = g.reset_index()
        g.insert(0, "month", month)
        parts.append(g)
    out = pd.concat(parts)[["month", "org", "hour", "single_share", "three_within_band"]]
    today = datetime.date.today().isoformat()
    with open(out_csv, "w", encoding="utf-8") as f:
        f.write(f"# EPIAS weighted profile coefficients {YEAR}, group '{GROUP}', all distribution companies\n")
        f.write(f"# source page: {SOURCE_PAGE}\n")
        f.write(f"# files: {FILE_BASE}<month file>.xlsx (12 monthly files)\n")
        f.write(f"# downloaded: {today}\n")
        f.write("# single_share: sum over the month's days of the single-rate (Tek Zamanli) coefficient "
                "for this hour of day; adds to 1 over 24 hours\n")
        f.write("# three_within_band: same for the three-rate (Uc Zamanli) coefficient; adds to 1 "
                "inside each tariff band\n")
        out.to_csv(f, index=False, float_format="%.10f")
    with open(os.path.splitext(out_csv)[0] + "_checks.json", "w") as f:
        json.dump({"downloaded": today, "months": checks}, f, indent=1)


# ---------------------------------------------------------------------------
# Step 2: analysis

def all_in_tl(energy_kurus):
    """Price per kWh in TL with distribution and both taxes added."""
    return (energy_kurus * (1 + BTV) + DISTRIBUTION) * (1 + KDV) / 100


def national_shapes(df):
    """Share of daily energy in each hour, national, for each entry of SHAPES.

    Each company counts equally (the files give no consumption weights). For a period longer
    than a month, months are weighted by their number of days, which treats every day as
    using the same energy (the coefficients are normalised per month, so the seasonal level
    is not in the data).
    """
    by_month = df.groupby(["month", "hour"]).single_share.mean().unstack("hour")
    days = pd.Series({m: pd.Period(f"{YEAR}-{m:02d}").days_in_month for m in range(1, 13)})
    out = {}
    for name, months in SHAPES.items():
        w = days[months] / days[months].sum()
        out[name] = (by_month.loc[months].T * w).sum(axis=1).values
    return out


def company_shapes(df):
    """Year shape for each company separately, to show how much they differ."""
    days = pd.Series({m: pd.Period(f"{YEAR}-{m:02d}").days_in_month for m in range(1, 13)})
    d = df.copy()
    d["w"] = d.month.map(days) / days.sum()
    d["x"] = d.single_share * d.w
    return d.groupby(["org", "hour"]).x.sum().unstack("hour")


def band_shares(shape):
    out = {b: 0.0 for b in BANDS}
    for h in range(24):
        out[hour_band(h)] += shape[h]
    return out


def single_bill(kwh_per_day, days, prices):
    """The first 8 kWh per day (averaged over the period) at the low price, the rest high."""
    total = kwh_per_day * days
    low = min(total, SINGLE_LIMIT_KWH_PER_DAY * days)
    return low * prices["single_low"] + (total - low) * prices["single_high"]


def three_bill(kwh_per_day, days, shares, prices):
    return kwh_per_day * days * sum(shares[b] * prices[b] for b in BANDS)


def break_even_night(kwh_per_day, shares, prices):
    """Night share above which the three-rate bill is lower than the single-rate bill.

    The rest of the energy keeps the observed day to peak proportion. Returns None when even
    100% at night is not cheaper.
    """
    single_avg = single_bill(kwh_per_day, 1, prices) / kwh_per_day
    day_frac = shares["day"] / (shares["day"] + shares["peak"])
    rest_price = day_frac * prices["day"] + (1 - day_frac) * prices["peak"]
    n = (rest_price - single_avg) / (rest_price - prices["night"])
    return n if n <= 1 else None


def draw_shapes(shapes, spread, prices, path):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    ymax = 6
    band_style = {"day": ("#fdf3d0", "Day"), "peak": ("#fadbd2", "Peak"), "night": ("#dde5f2", "Night")}
    for name, spans in BANDS.items():
        color, label = band_style[name]
        for s, e in spans:
            ax.axvspan(s, e, color=color, zorder=0, linewidth=0)
            text = f"{label} {spans[0][0]:02d}:00-{spans[-1][1]:02d}:00\n{prices[name]:.3f} TL/kWh"
            ax.text((s + e) / 2, ymax * 1.01, text if e - s >= 4 else label,
                    ha="center", va="bottom", fontsize=13)

    x = np.arange(25)
    lo = np.append(spread.min().values, spread.min().values[-1]) * 100
    hi = np.append(spread.max().values, spread.max().values[-1]) * 100
    ax.fill_between(x, lo, hi, step="post", color="#9a9a9a", alpha=0.35, linewidth=0, zorder=1)
    styles = {"January": ("#1f5fbf", "--", 2.2), "July": ("#d9480f", "--", 2.2),
              "Year": ("#222222", "-", 3.0)}
    for name, shape in shapes.items():
        color, ls, lw = styles[name]
        y = np.append(shape, shape[-1]) * 100
        ax.step(x, y, where="post", color=color, linestyle=ls, linewidth=lw, zorder=3)

    # Direct labels, placed by hand where the lines are apart.
    ax.text(12.6, shapes["July"][12] * 100 + 0.25, "July", color="#d9480f", fontsize=15, zorder=4)
    ax.text(9.3, shapes["January"][9] * 100 - 0.55, "January", color="#1f5fbf", fontsize=15, zorder=4)
    ax.text(1.2, shapes["Year"][1] * 100 + 0.3, "Whole year", color="#222222", fontsize=15, zorder=4)
    ax.text(3.0, lo[4] - 0.55, "Grey: range of the 21 distribution companies (whole year)",
            color="dimgray", fontsize=13, zorder=4)

    rows = ["Share of daily energy   Day    Peak   Night"]
    for name, shape in shapes.items():
        b = band_shares(shape)
        rows.append(f"{name:<22s}{b['day']*100:5.1f}%{b['peak']*100:6.1f}%{b['night']*100:6.1f}%")
    ax.text(0.3, 5.85, "\n".join(rows), family="monospace", fontsize=12.5, va="top", zorder=5,
            bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#999999"))

    ax.set_xlim(0, 24)
    ax.set_ylim(0, ymax)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)], fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.set_xlabel("Hour of day", fontsize=14)
    ax.set_ylabel("Share of the day's energy in this hour (%)", fontsize=14)
    ax.set_title(f"Average Turkish residential load shape, EPİAŞ profile coefficients {YEAR} "
                 "(Mesken AG, single-rate), with 2026 three-rate prices", fontsize=16, loc="left", pad=52)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", zorder=1)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def draw_bills(year_shares, prices, path):
    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    kwh = np.linspace(0, 20, 401)
    day_frac = year_shares["day"] / (year_shares["day"] + year_shares["peak"])
    shifted = {"night": 0.6, "day": 0.4 * day_frac, "peak": 0.4 * (1 - day_frac)}
    single = np.array([single_bill(k, BILLING_DAYS, prices) for k in kwh])
    three = np.array([three_bill(k, BILLING_DAYS, year_shares, prices) for k in kwh])
    three_60 = np.array([three_bill(k, BILLING_DAYS, shifted, prices) for k in kwh])

    ax.plot(kwh, three, color="#d9480f", linewidth=3, zorder=3,
            label=f"Three-rate, national average shape ({year_shares['night']*100:.0f}% of energy at night)")
    ax.plot(kwh, three_60, color="#d9480f", linewidth=2, linestyle="--", zorder=3,
            label="Three-rate, if 60% of the energy is used at night")
    ax.plot(kwh, single, color="#1f5fbf", linewidth=3, zorder=3, label="Single-rate")

    rows = ["kWh/day   Single-rate   Three-rate   Night share needed"]
    for k in LEVELS:
        s = single_bill(k, BILLING_DAYS, prices)
        t = three_bill(k, BILLING_DAYS, year_shares, prices)
        be = break_even_night(k, year_shares, prices)
        ax.axvline(k, color="#bbbbbb", linestyle=":", zorder=1)
        ax.plot([k, k], [s, t], "o", color="black", markersize=7, zorder=4)
        rows.append(f"{k:>5g}     {s:9,.0f} TL  {t:8,.0f} TL   "
                    f"{'never' if be is None else f'{be*100:.0f}%':>10s}")
    # The table goes in the empty lower right corner, under both lines.
    ax.text(19.8, 80, "Monthly bill (30 days, taxes included)\n" + "\n".join(rows),
            family="monospace", fontsize=12.5, ha="right", va="bottom", multialignment="left",
            linespacing=1.5, zorder=5,
            bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#999999"))
    ax.annotate("8 kWh/day: single-rate price\nsteps up above here", xy=(8, single_bill(8, 30, prices)),
                xytext=(8.4, 330), fontsize=13, color="dimgray",
                arrowprops=dict(arrowstyle="->", color="dimgray", lw=1))

    ax.legend(loc="upper left", fontsize=14, frameon=False)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 3000)
    ax.set_xticks(range(0, 21, 2))
    ax.tick_params(labelsize=12)
    ax.set_xlabel("Average daily consumption (kWh per day)", fontsize=14)
    ax.set_ylabel(f"Bill for a {BILLING_DAYS}-day month (TL, taxes included)", fontsize=14)
    ax.set_title("Monthly bill on the single-rate and three-rate residential tariffs "
                 "(EPDK, from 4 April 2026)", fontsize=17, loc="left", pad=20)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", zorder=0)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def analyse(csv_path, out_dir):
    os.makedirs(os.path.join(out_dir, "figures"), exist_ok=True)
    meta = [line[2:].strip() for line in open(csv_path, encoding="utf-8") if line.startswith("# ")]
    df = pd.read_csv(csv_path, comment="#")

    prices = {"single_low": all_in_tl(SINGLE_LOW), "single_high": all_in_tl(SINGLE_HIGH)}
    prices.update({b: all_in_tl(p) for b, p in THREE_RATE.items()})

    # The three-rate coefficients only spread each band's metered energy over the band's
    # hours, so they cannot tell us how three-rate customers split energy between bands.
    # Check, from the CSV, that they are the single-rate shape rescaled inside each band.
    d = df.copy()
    d["band"] = d.hour.map(hour_band)
    d["rescaled"] = d.single_share / d.groupby(["month", "org", "band"]).single_share.transform("sum")
    three_diff = float((d.rescaled - d.three_within_band).abs().max())

    shapes = national_shapes(df)
    shares = {name: band_shares(s) for name, s in shapes.items()}
    comp = company_shapes(df)
    comp_night = comp.apply(lambda r: band_shares(r.values)["night"], axis=1)

    print("All-in price, TL per kWh:")
    for k, v in prices.items():
        print(f"  {k:12s} {v:.3f}")
    print(f"\nThree-rate coefficients minus rescaled single-rate: max {three_diff:.1e}")
    print("\nShare of daily energy:      day   peak  night")
    for name, b in shares.items():
        print(f"  {name:22s} {b['day']*100:5.1f} {b['peak']*100:5.1f} {b['night']*100:5.1f}")
    print(f"  night share across companies (year): {comp_night.min()*100:.1f}% "
          f"({comp_night.idxmin()}) to {comp_night.max()*100:.1f}% ({comp_night.idxmax()})")

    # Bills. The single-rate bill does not depend on the shape. The three-rate bill is worked
    # out with each single-rate shape; there is no separate three-rate customers' shape to use
    # (see the check above), so that case is recorded as missing.
    bills = {}
    print(f"\nBills (TL), {BILLING_DAYS}-day month; three-rate uses the single-rate customers' shape:")
    for k in LEVELS:
        s1 = single_bill(k, 1, prices)
        t1 = {name: three_bill(k, 1, shares[name], prices) for name in shares}
        be = {name: break_even_night(k, shares[name], prices) for name in shares}
        bills[str(k)] = {
            "single_rate_day": round(s1, 2),
            "single_rate_month": round(s1 * BILLING_DAYS, 2),
            "single_rate_avg_tl_per_kwh": round(s1 / k, 4),
            "three_rate_day_single_rate_shape": {n: round(v, 2) for n, v in t1.items()},
            "three_rate_month_single_rate_shape": {n: round(v * BILLING_DAYS, 2) for n, v in t1.items()},
            "three_minus_single_month_year_shape": round((t1["Year"] - s1) * BILLING_DAYS, 2),
            "three_rate_month_three_rate_customer_shape": None,
            "break_even_night_share": {n: (None if v is None else round(v, 4)) for n, v in be.items()},
        }
        bev = be["Year"]
        print(f"  {k:4g} kWh/day  single {s1:6.2f}/day {s1*BILLING_DAYS:8.2f}/month  "
              f"three {t1['Year']:6.2f}/day {t1['Year']*BILLING_DAYS:8.2f}/month  "
              f"(Jan {t1['January']*BILLING_DAYS:.2f}, Jul {t1['July']*BILLING_DAYS:.2f})  "
              f"break-even night share {'never' if bev is None else f'{bev*100:.1f}%'}")

    # What if a household moved more of its use to the night? Rest keeps the year day:peak ratio.
    day_frac = shares["Year"]["day"] / (shares["Year"]["day"] + shares["Year"]["peak"])
    scenarios = {}
    for n in NIGHT_SCENARIOS:
        sh = {"night": n, "day": (1 - n) * day_frac, "peak": (1 - n) * (1 - day_frac)}
        scenarios[f"{n:.0%}"] = {str(k): round(three_bill(k, BILLING_DAYS, sh, prices), 2) for k in LEVELS}
    print("\nThree-rate monthly bill (TL) if this share of energy is at night:")
    for n, row in scenarios.items():
        print(f"  {n:>4s}  " + "  ".join(f"{row[str(k)]:8.2f}" for k in LEVELS))

    results = {
        "profile_source": meta,
        "profile_group": GROUP,
        "profile_year": YEAR,
        "how_shapes_were_built": (
            "Single-rate (Tek Zamanli) coefficients of each company summed over the month's days by "
            "hour of day (share of the month's energy in each hour of day). National shape for a "
            "month = plain mean over the 21 distribution companies. Year shape = mean of the 12 "
            "monthly shapes weighted by days in month."),
        "three_rate_shape": {
            "available": False,
            "reason": ("Three-rate (Uc Zamanli) coefficients add up to 1 inside each band and equal "
                       "the single-rate coefficients rescaled inside each band, so they carry no "
                       "information on how three-rate customers split energy between bands."),
            "max_abs_diff_vs_rescaled_single": three_diff,
        },
        "tariff_source": "EPDK regulated tariff, low-voltage residential (mesken, AG), valid from 2026-04-04",
        "tax_note": "all-in = (energy x 1.05 + distribution) x 1.10 / 100; our calculation",
        "price_tl_per_kwh": {k: round(v, 4) for k, v in prices.items()},
        "hourly_shape_pct": {n: [round(x * 100, 3) for x in s] for n, s in shapes.items()},
        "band_share_pct": {n: {b: round(v * 100, 2) for b, v in s.items()} for n, s in shares.items()},
        "three_rate_avg_tl_per_kwh": {n: round(sum(s[b] * prices[b] for b in BANDS), 4)
                                      for n, s in shares.items()},
        "company_night_share_pct_year": {
            "min": round(comp_night.min() * 100, 2), "min_company": comp_night.idxmin(),
            "max": round(comp_night.max() * 100, 2), "max_company": comp_night.idxmax()},
        "billing_days": BILLING_DAYS,
        "bills_tl": bills,
        "bills_note": ("three_rate_*_single_rate_shape: three-rate bill if the household's energy "
                       "follows the national single-rate shape of that period. "
                       "three_rate_month_three_rate_customer_shape is null because the EPIAS files "
                       "have no separate load shape for three-rate customers."),
        "three_rate_month_by_night_share": scenarios,
        "night_scenario_note": "rest of the energy keeps the year shape's day to peak proportion",
        "break_even_note": ("Night share of daily energy above which three-rate is cheaper; the rest "
                            "keeps the shape's day to peak proportion; null = never cheaper"),
    }
    with open(os.path.join(out_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)

    draw_shapes(shapes, comp, prices, os.path.join(out_dir, "figures", "hourly_shape_bands.png"))
    draw_bills(shares["Year"], prices, os.path.join(out_dir, "figures", "bill_vs_consumption.png"))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true", help="rebuild the processed CSV from the Excel files")
    parser.add_argument("--download", action="store_true", help="with --build, fetch missing Excel files")
    parser.add_argument("--raw-dir", default="raw", help="folder with the 12 monthly Excel files")
    parser.add_argument("--csv", default=PROCESSED_CSV, help="processed hourly CSV")
    parser.add_argument("--out-dir", default=".", help="where results.json and figures/ go")
    args = parser.parse_args()
    np.random.seed(0)  # nothing here is random; fixed anyway so any later addition stays repeatable

    if args.build:
        if args.download:
            download(args.raw_dir)
        build(args.raw_dir, args.csv)
    analyse(args.csv, args.out_dir)


if __name__ == "__main__":
    main()
