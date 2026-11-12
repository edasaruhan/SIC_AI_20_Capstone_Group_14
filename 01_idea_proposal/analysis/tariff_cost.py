"""Price one day of electricity with Türkiye's single-rate and three-rate (day/peak/night) tariffs.

Uses the example day saved by first_look.py (REFIT House 2, 17 June 2014, 5-minute means)
and prints and saves:
  - the all-in price per kWh in each tariff band
  - the day's energy in each time band, for the household total and for five appliances
  - the bill on the single-rate tariff and on the three-rate tariff
  - what each appliance costs on the three-rate tariff
  - a "shift" scenario: the dishwasher and washing machine run at night instead

Usage:
  python tariff_cost.py --chart-day chart_day.json --out-dir .
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")  # draw to a file, no window needed
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Tariff constants
# Source: EPDK regulated national tariff table, low-voltage residential customers
# (mesken, AG), valid from 4 April 2026. Prices exclude taxes, in kurus per kWh.
# These change several times a year, so check the current table before reusing them.
DISTRIBUTION = 242.49           # same for every band and tier
SINGLE_LOW = 49.4065            # single-rate energy, up to an average of 8 kWh per day
SINGLE_HIGH = 189.5808          # single-rate energy, the part above 8 kWh per day
SINGLE_LIMIT_KWH_PER_DAY = 8    # the tier is marginal: only the kWh above 8 pay the high price
THREE_RATE = {                  # three-rate energy, no tiers
    "day": 195.0640,            # gunduz
    "peak": 374.7551,           # puant
    "night": 51.3656,           # gece
}
# Time bands, the same every day of the year: (start hour, end hour).
BANDS = {"day": [(6, 17)], "peak": [(17, 22)], "night": [(22, 24), (0, 6)]}
# Taxes. This formula is our own calculation from the published rates, not part of the
# EPDK table: 5% consumption tax (BTV) on the energy part only, then 10% VAT (KDV) on
# energy + distribution + BTV.
BTV = 0.05
KDV = 0.10
# ---------------------------------------------------------------------------

APPLIANCES = ["Fridge-Freezer", "Washing Machine", "Dishwasher", "Microwave", "Kettle"]
# The two appliances whose start time a household can usually choose.
SHIFTABLE = ["Dishwasher", "Washing Machine"]


def all_in_tl(energy_kurus):
    """Price per kWh in TL with distribution and both taxes added."""
    return (energy_kurus * (1 + BTV) + DISTRIBUTION) * (1 + KDV) / 100


def band_of(hhmm):
    """Name of the tariff band an 'HH:MM' label falls in."""
    hour = int(hhmm[:2]) + int(hhmm[3:]) / 60
    for name, spans in BANDS.items():
        for start, end in spans:
            if start <= hour < end:
                return name


def kwh_per_band(times, watts, step_minutes):
    """Add up the energy of one series in each band. Mean watts over a step -> kWh."""
    out = {name: 0.0 for name in BANDS}
    for t, w in zip(times, watts):
        if w is not None:  # a missing 5-minute slot adds nothing
            out[band_of(t)] += w * step_minutes / 60 / 1000
    return out


def single_rate_bill(kwh, days, prices):
    """Single-rate bill: the first 8 kWh per day at the low price, the rest at the high one."""
    limit = SINGLE_LIMIT_KWH_PER_DAY * days
    low = min(kwh, limit)
    return low * prices["single_low"] + (kwh - low) * prices["single_high"]


def three_rate_bill(band_kwh, prices):
    return sum(band_kwh[b] * prices[b] for b in BANDS)


def draw(chart, prices, bills, path):
    """The day's total and stacked appliances, with the three tariff bands shaded behind."""
    hours = np.array([int(t[:2]) + int(t[3:]) / 60 for t in chart["t"]])
    kw = {k: np.array([v or 0 for v in chart[k]]) / 1000 for k in ["aggregate"] + APPLIANCES}
    layers = [  # same order and colours as figures/house2_day.png
        ("Fridge-Freezer", "#222222"),
        ("Dishwasher", "#1f6fd1"),
        ("Washing Machine", "#d62728"),
        ("Kettle", "#f2c200"),
        ("Microwave", "#9ecae1"),
    ]
    band_style = {"day": ("#fdf3d0", "Day"), "peak": ("#fadbd2", "Peak"), "night": ("#dde5f2", "Night")}
    ymax = 3.5

    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")

    # Shade the bands and label them just above the plot, with hours and all-in price.
    for name, spans in BANDS.items():
        color, label = band_style[name]
        for start, end in spans:
            ax.axvspan(start, end, color=color, zorder=0, linewidth=0)
        start = spans[0][0]
        last_end = spans[-1][1]
        text = f"{label} {start:02d}:00-{last_end:02d}:00\n{prices[name]:.3f} TL/kWh"
        for s, e in spans:
            # The two-hour night slice before midnight only has room for the band name.
            ax.text((s + e) / 2, ymax * 1.012, text if e - s >= 4 else label,
                    ha="center", va="bottom", fontsize=13)

    ax.stackplot(hours, [kw[n] for n, _ in layers], colors=[c for _, c in layers],
                 alpha=0.9, linewidth=0, zorder=2)
    ax.plot(hours, kw["aggregate"].clip(max=ymax), color="grey", linewidth=1.6, zorder=3)

    # Hand-placed labels for this day: (hour to point at, label x, label y in kW).
    label_spots = {
        "Fridge-Freezer": (2.75, 1.0, 0.55),
        "Dishwasher": (13.1, 14.3, 2.75),
        "Washing Machine": (7.05, 3.4, 2.1),
        "Kettle": (15.5, 15.9, 1.35),
        "Microwave": (18.67, 17.3, 1.05),
    }
    bottom = np.zeros(len(hours))
    for name, color in layers:
        hour, tx, ty = label_spots[name]
        i = int(np.argmin(np.abs(hours - hour)))
        ax.annotate(name, xy=(hours[i], bottom[i] + kw[name][i] / 2), xytext=(tx, ty),
                    fontsize=14, color="black", zorder=4,
                    arrowprops=dict(arrowstyle="-", color="black", lw=0.8))
        bottom += kw[name]
    ax.text(3.4, 0.24, "Household total", fontsize=14, color="dimgray", zorder=4)

    i = int(np.argmax(kw["aggregate"]))
    ax.annotate(f"Total reaches {kw['aggregate'][i]:.1f} kW at {chart['t'][i]}\n"
                "(an appliance that is\nnot monitored).\nAxis clipped at 3.5 kW.",
                xy=(hours[i], ymax), xytext=(hours[i] - 0.7, 2.6), va="bottom", ha="right",
                fontsize=13, color="dimgray", zorder=4,
                arrowprops=dict(arrowstyle="->", color="dimgray", lw=1))

    # The three bills in a small box inside the peak band, where the curves stay low.
    box = (f"Bill for this day ({bills['total_kwh']:.2f} kWh)\n"
           f"Single-rate:  {bills['single_rate']:.2f} TL\n"
           f"Three-rate:  {bills['three_rate']:.2f} TL\n"
           f"Three-rate, dishwasher and\nwashing machine run at night:  {bills['three_rate_shifted']:.2f} TL")
    ax.text(17.2, 3.3, box, ha="left", va="top", fontsize=13, linespacing=1.5, zorder=5,
            bbox=dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#999999"))

    ax.set_xlim(0, 24)
    ax.set_ylim(0, ymax)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)], fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.set_xlabel("Time of day", fontsize=14)
    ax.set_ylabel("Power (kW, 5-minute mean)", fontsize=14)
    ax.set_title(f"REFIT House 2 on {chart['day']} priced with Türkiye's three-rate tariff "
                 "(prices incl. taxes, from 4 April 2026)", fontsize=17, loc="left", pad=52)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", zorder=1)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chart-day", default="chart_day.json", help="day saved by first_look.py")
    parser.add_argument("--out-dir", default=".", help="where tariff_results.json and figures/ go")
    args = parser.parse_args()
    os.makedirs(os.path.join(args.out_dir, "figures"), exist_ok=True)

    with open(args.chart_day) as f:
        chart = json.load(f)
    # Step between samples in minutes, read from the first two time labels (5 for this file).
    t0, t1 = chart["t"][0], chart["t"][1]
    step = (int(t1[:2]) * 60 + int(t1[3:])) - (int(t0[:2]) * 60 + int(t0[3:]))

    # 1. All-in prices
    prices = {"single_low": all_in_tl(SINGLE_LOW), "single_high": all_in_tl(SINGLE_HIGH)}
    for b, p in THREE_RATE.items():
        prices[b] = all_in_tl(p)
    print("All-in price, TL per kWh:")
    for k, v in prices.items():
        print(f"  {k:12s} {v:.3f}")

    # 2. Energy per band
    total = kwh_per_band(chart["t"], chart["aggregate"], step)
    per_app = {a: kwh_per_band(chart["t"], chart[a], step) for a in APPLIANCES}
    total_kwh = sum(total.values())
    print(f"\nEnergy on {chart['day']}, kWh:      day   peak  night  total")
    for name, k in [("Household total", total)] + list(per_app.items()):
        print(f"  {name:16s} {k['day']:6.2f} {k['peak']:6.2f} {k['night']:6.2f} {sum(k.values()):6.2f}")

    # 3. Bills for the household total
    single = single_rate_bill(total_kwh, 1, prices)
    three = three_rate_bill(total, prices)

    # 4. Cost of each appliance on the three-rate tariff
    app_cost = {a: three_rate_bill(k, prices) for a, k in per_app.items()}

    # 5. Shift: dishwasher and washing machine energy in the day and peak bands moves to night.
    # We move energy only; the appliance's power profile and the rest of the day stay the same.
    moved = sum(per_app[a]["day"] + per_app[a]["peak"] for a in SHIFTABLE)
    shifted = dict(total)
    for a in SHIFTABLE:
        shifted["day"] -= per_app[a]["day"]
        shifted["peak"] -= per_app[a]["peak"]
    shifted["night"] += moved
    three_shifted = three_rate_bill(shifted, prices)

    print(f"\nBill for the day ({total_kwh:.2f} kWh):")
    print(f"  single-rate                      {single:6.2f} TL")
    print(f"  three-rate                       {three:6.2f} TL")
    print(f"  three-rate, {moved:.2f} kWh moved to night {three_shifted:6.2f} TL"
          f"  (saves {three - three_shifted:.2f} TL)")
    print("\nAppliance cost on the three-rate tariff:")
    for a, c in app_cost.items():
        print(f"  {a:16s} {c:5.2f} TL")

    results = {
        "source": "EPDK regulated tariff, low-voltage residential (mesken, AG), valid from 2026-04-04",
        "tax_note": "all-in = (energy x 1.05 + distribution) x 1.10; our calculation, check against a real bill",
        "day": chart["day"],
        "price_tl_per_kwh": {k: round(v, 3) for k, v in prices.items()},
        "kwh_per_band": {"Household total": {k: round(v, 2) for k, v in total.items()}}
                        | {a: {k: round(v, 2) for k, v in d.items()} for a, d in per_app.items()},
        "total_kwh": round(total_kwh, 2),
        "bill_tl": {
            "single_rate": round(single, 2),
            "three_rate": round(three, 2),
            "three_rate_shifted": round(three_shifted, 2),
            "shift_saving": round(three - three_shifted, 2),
        },
        "shifted_kwh": round(moved, 2),
        "appliance_cost_three_rate_tl": {a: round(c, 2) for a, c in app_cost.items()},
    }
    with open(os.path.join(args.out_dir, "tariff_results.json"), "w") as f:
        json.dump(results, f, indent=1)

    bills = {"total_kwh": total_kwh, "single_rate": single, "three_rate": three,
             "three_rate_shifted": three_shifted}
    draw(chart, prices, bills, os.path.join(args.out_dir, "figures", "house2_day_tariff.png"))


if __name__ == "__main__":
    main()
