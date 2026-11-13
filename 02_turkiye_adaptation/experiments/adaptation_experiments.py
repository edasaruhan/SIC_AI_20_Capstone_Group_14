"""Three adaptation experiments on REFIT Houses 2, 3, 5 and 11.

Trains on Houses 2 and 3 and tests on Houses 5 and 11, so the test homes are never seen
in training. Uses only the two baselines from 01_idea_proposal/analysis/first_look.py
(predict the training mean, and gradient boosting on window features of the total).

  1. Resolution: the same baselines at 1-minute, 15-minute and 60-minute resolution.
  2. Turkish loads: synthetic air conditioner, water heater (termosifon) and tea maker
     (cay makinesi) signals added to the household totals.
  3. Bills: a year of bills on Turkiye's single-rate and three-rate tariffs from the
     measured appliance channels (no model).

Usage:
  python adaptation_experiments.py --data-dir data --cache-dir cache --out-dir .
where data/ holds CLEAN_House2.csv, CLEAN_House3.csv, CLEAN_House5.csv and CLEAN_House11.csv.
"""
import argparse
import json
import os
import time

import matplotlib
matplotlib.use("Agg")  # draw to a file, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

# Appliance1..Appliance9 mean different things in each house (see the REFIT metadata).
APPLIANCES = {
    2: ["Fridge-Freezer", "Washing Machine", "Dishwasher", "Television", "Microwave",
        "Toaster", "Hi-Fi", "Kettle", "Overhead Fan"],
    3: ["Toaster", "Fridge-Freezer", "Freezer", "Tumble Dryer", "Dishwasher",
        "Washing Machine", "Television", "Microwave", "Kettle"],
    5: ["Fridge-Freezer", "Tumble Dryer", "Washing Machine", "Dishwasher", "Desktop Computer",
        "Television", "Microwave", "Kettle", "Toaster"],
    # House 11 has a separate fridge; Appliance2 (Fridge-Freezer) is the target.
    11: ["Fridge", "Fridge-Freezer", "Washing Machine", "Dishwasher", "Computer Site",
         "Microwave", "Kettle", "Router", "Hi-Fi"],
}
TRAIN_HOUSES = [2, 3]
TEST_HOUSES = [5, 11]
# The five appliances all four homes have.
COMMON = ["Fridge-Freezer", "Washing Machine", "Dishwasher", "Microwave", "Kettle"]
COLORS = {  # same colours as the figures in 01_idea_proposal/analysis
    "Fridge-Freezer": "#222222",
    "Dishwasher": "#1f6fd1",
    "Washing Machine": "#d62728",
    "Kettle": "#f2c200",
    "Microwave": "#9ecae1",
}
SEED = 0
RESOLUTIONS = [1, 15, 60]  # minutes
# Rolling windows for the features, counted in samples at each resolution.
# 1 minute: 5 min to 1 hour, as in first_look.py. 15 minutes: 45 min to 6 h. 60 minutes: 3 h to 25 h.
WINDOWS = {1: (5, 15, 31, 61), 15: (3, 5, 9, 25), 60: (3, 5, 9, 25)}
TRAIN_ROWS = 600_000      # random training rows at 1 minute, as in first_look.py
MIN_BIN_COVERAGE = 0.8    # a 15 or 60 minute bin needs 80% of its minutes to count
MIN_DAY_COVERAGE = 0.9    # a test day needs 90% of its minutes for the daily energy error
MIN_MONTH_COVERAGE = 0.8  # a month needs 80% of its minutes to get a bill (experiment 3)

# ---------------------------------------------------------------------------
# Synthetic loads for experiment 2.
# These are ASSUMED signatures, written from typical rated powers and habits.
# They are not measurements of Turkish homes. Change them here and nowhere else.
# Ranges (lo, hi) are drawn uniformly per event (or per day for the air conditioner).
SYNTH = {
    "Air conditioner": {
        # Chance that a day in this month is warm enough to run it (UK calendar of the test homes).
        "day_prob_by_month": {5: 0.1, 6: 0.4, 7: 0.6, 8: 0.6, 9: 0.3},
        "start_hour": (13.0, 19.0),     # the run starts on a warm afternoon or evening
        "run_hours": (3.0, 6.0),        # and lasts several hours
        "compressor_w": (900, 1300),    # compressor power, fixed for the day
        "on_min": (8, 20),              # compressor on, minutes
        "off_min": (5, 12),             # compressor off between cycles, minutes
        "fan_w": 40,                    # indoor fan runs during the whole run
    },
    "Water heater": {
        "power_w": 2000,                # resistive element, one block per heating
        "duration_min": (20, 50),
        # (earliest start hour, latest start hour, chance per day)
        "sessions": [(6.0, 8.5, 0.7), (18.0, 22.0, 0.8)],
    },
    "Tea maker": {
        "boil_w": (1600, 1800),
        "boil_min": (4, 7),
        "sessions_per_day": (2, 4),
        "start_windows": [(7.0, 9.0), (15.0, 17.5), (19.0, 22.5)],
        "keep_warm_min": (30, 90),      # how long the tea is kept warm after the boil
        "pulse_every_min": (8, 12),     # one keep-warm pulse every 8 to 12 minutes
        "pulse_min": 1,                 # each pulse is one minute at the boil power
    },
}
SYNTH_COLORS = {"Air conditioner": "#1b9e77", "Water heater": "#7b3fa0", "Tea maker": "#e6812f"}
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tariff constants for experiment 3, copied from 01_idea_proposal/analysis/tariff_cost.py.
# Source: EPDK regulated national tariff table, low-voltage residential customers
# (mesken, AG), valid from 4 April 2026. Prices exclude taxes, in kurus per kWh.
DISTRIBUTION = 242.49
SINGLE_LOW = 49.4065            # single-rate energy, up to an average of 8 kWh per day
SINGLE_HIGH = 189.5808          # single-rate energy, the part above (marginal)
SINGLE_LIMIT_KWH_PER_DAY = 8
THREE_RATE = {"day": 195.0640, "peak": 374.7551, "night": 51.3656}
BAND_HOURS = {"day": 11, "peak": 5, "night": 8}  # 06-17, 17-22, 22-06, every day
# Our calculation, not part of the EPDK table: 5% consumption tax on energy, then 10% VAT.
BTV = 0.05
KDV = 0.10
# Appliances a household can usually start later. The bill shift moves only the first two.
SHIFTABLE = ["Dishwasher", "Washing Machine", "Tumble Dryer", "Washer Dryer"]
SHIFTED = ["Dishwasher", "Washing Machine"]
# ---------------------------------------------------------------------------


def all_in_tl(energy_kurus):
    """Price per kWh in TL with distribution and both taxes added."""
    return (energy_kurus * (1 + BTV) + DISTRIBUTION) * (1 + KDV) / 100


PRICES = {"single_low": all_in_tl(SINGLE_LOW), "single_high": all_in_tl(SINGLE_HIGH)}
PRICES.update({b: all_in_tl(p) for b, p in THREE_RATE.items()})


# ----------------------------------------------------------------- data loading

def read_minutes(path, house):
    """Read one REFIT CSV in chunks and average it to a regular 1-minute grid.

    The Unix column is the Time column (UK clock time) written as seconds, so it gives the
    local clock time directly and is much lighter to parse than the text column.
    Minutes without any reading stay as NaN rows.
    """
    cols = ["Unix", "Aggregate"] + [f"Appliance{i}" for i in range(1, 10)]
    dtypes = {c: "float32" for c in cols[1:]} | {"Unix": "int64"}
    sums, counts = [], []
    for chunk in pd.read_csv(path, usecols=cols, dtype=dtypes, chunksize=1_000_000):
        minute = pd.to_datetime(chunk.pop("Unix"), unit="s").dt.floor("min").to_numpy()
        g = chunk.groupby(minute)
        sums.append(g.sum())
        counts.append(g.count())
    # A minute can be split across two chunks, so add sums and counts before dividing.
    s = pd.concat(sums).groupby(level=0).sum()
    n = pd.concat(counts).groupby(level=0).sum()
    m = (s / n.where(n > 0)).astype("float32")
    m = m.reindex(pd.date_range(m.index[0], m.index[-1], freq="min"))
    m = m.rename(columns={f"Appliance{i + 1}": name for i, name in enumerate(APPLIANCES[house])})
    present = m["Aggregate"].notna()
    m.loc[present] = m.loc[present].fillna(0)
    return m


def load_house(data_dir, cache_dir, house):
    """1-minute grid for one house, cached so later runs skip the slow CSV read."""
    cache = os.path.join(cache_dir, f"house{house}_1min.pkl")
    if os.path.exists(cache):
        return pd.read_pickle(cache)
    m = read_minutes(os.path.join(data_dir, f"CLEAN_House{house}.csv"), house)
    os.makedirs(cache_dir, exist_ok=True)
    m.to_pickle(cache)
    return m


def at_resolution(grid, minutes):
    """Average power over longer bins (keeps energy). Thin bins become NaN."""
    if minutes == 1:
        return grid
    g = grid.resample(f"{minutes}min")
    out = g.mean()
    out.loc[g["Aggregate"].count() < MIN_BIN_COVERAGE * minutes] = np.nan
    return out


def good_days(grid):
    """Dates with enough 1-minute data for a fair daily energy comparison."""
    have = grid["Aggregate"].notna().groupby(grid.index.date).mean()
    return set(have[have >= MIN_DAY_COVERAGE].index)


# ----------------------------------------------------------------- baselines

def make_features(total, windows):
    """Features from the household total only (the one meter we would have).

    total is a regular grid with NaN for missing samples; rolling windows skip the NaN.
    Returns rows where the total itself is present.
    """
    f = pd.DataFrame({"total": total})
    for w in windows:
        r = total.rolling(w, center=True, min_periods=1)
        f[f"mean{w}"] = r.mean()
        f[f"max{w}"] = r.max()
        f[f"min{w}"] = r.min()
        f[f"std{w}"] = r.std().fillna(0)
    f["diff_prev"] = total.diff().fillna(0)
    f["diff_next"] = total.diff(-1).fillna(0)
    f["hour"] = total.index.hour + total.index.minute / 60
    return f.loc[total.notna()].astype("float32")


def fit_models(train_grids, windows, n_rows, extra=None):
    """One gradient boosting model per appliance, plus the training means.

    extra: optional list of synthetic watts to add to each training total.
    """
    X, Y = [], []
    for i, g in enumerate(train_grids):
        total = g["Aggregate"] if extra is None else g["Aggregate"] + extra[i]
        X.append(make_features(total, windows))
        Y.append(g.loc[g["Aggregate"].notna(), COMMON].astype("float32"))
    X, Y = pd.concat(X), pd.concat(Y)
    rng = np.random.RandomState(SEED)
    # Subsample like first_look.py to keep training to about a minute per model.
    idx = rng.choice(len(X), n_rows, replace=False) if len(X) > n_rows else np.arange(len(X))
    models, means = {}, {}
    for a in COMMON:
        means[a] = float(Y[a].mean())
        model = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=SEED)
        model.fit(X.iloc[idx], Y[a].iloc[idx])
        models[a] = model
    return models, means


def predict(models, means, test_grids, windows, extra=None):
    """Per test house: a frame with the true and predicted watts of each appliance."""
    out = []
    for i, g in enumerate(test_grids):
        total = g["Aggregate"] if extra is None else g["Aggregate"] + extra[i]
        X = make_features(total, windows)
        frame = pd.DataFrame(index=X.index)
        for a in COMMON:
            frame[f"{a}|true"] = g.loc[X.index, a].to_numpy()
            frame[f"{a}|mean"] = means[a]
            frame[f"{a}|gb"] = np.clip(models[a].predict(X), 0, None)  # power cannot be negative
        out.append(frame)
    return out


def score(frames, days_per_house):
    """MAE in W over all test samples, and the error in daily energy over good test days."""
    res = {}
    allf = pd.concat(frames)
    for a in COMMON:
        r = {}
        y = allf[f"{a}|true"]
        r["true_mean_W"] = round(float(y.mean()), 1)
        for m in ("mean", "gb"):
            r[f"mae_{m}_W"] = round(float((allf[f"{a}|{m}"] - y).abs().mean()), 1)
        # Daily energy: mean power over the samples of the day times 24 h. Using the mean
        # keeps the comparison fair when a day has a few missing samples.
        daily = []
        for f, days in zip(frames, days_per_house):
            d = f[[f"{a}|true", f"{a}|mean", f"{a}|gb"]].groupby(f.index.date).mean() * 24 / 1000
            daily.append(d[d.index.isin(days)])
        daily = pd.concat(daily)
        true_kwh = daily[f"{a}|true"]
        r["test_days"] = int(len(daily))
        r["true_daily_kwh"] = round(float(true_kwh.mean()), 3)
        for m in ("mean", "gb"):
            err = (daily[f"{a}|{m}"] - true_kwh).abs()
            r[f"daily_err_median_kwh_{m}"] = round(float(err.median()), 3)
            r[f"daily_err_pct_{m}"] = round(float(err.mean() / true_kwh.mean() * 100), 1)
        res[a] = r
    return res


# ----------------------------------------------------------------- synthetic loads

def synthetic_loads(index, rng):
    """Synthetic watts of the three assumed loads on a regular 1-minute index."""
    n = len(index)
    out = {name: np.zeros(n, dtype="float32") for name in SYNTH}
    first = index[0]

    def put(name, day_start, start_min, length, watts):
        s = day_start + int(start_min)
        e = s + int(length)
        s, e = max(s, 0), min(e, n)
        if s < e:
            out[name][s:e] += watts

    ac, wh, tea = SYNTH["Air conditioner"], SYNTH["Water heater"], SYNTH["Tea maker"]
    for day in pd.date_range(first.normalize(), index[-1].normalize(), freq="D"):
        base = int((day - first) / pd.Timedelta("1min"))  # minute offset of midnight

        # Air conditioner: on some summer days, compressor cycles plus a fan for a few hours.
        if rng.random() < ac["day_prob_by_month"].get(day.month, 0.0):
            start = rng.uniform(*ac["start_hour"]) * 60
            end = start + rng.uniform(*ac["run_hours"]) * 60
            power = rng.uniform(*ac["compressor_w"])
            put("Air conditioner", base, start, end - start, ac["fan_w"])
            t = start
            while t < end:
                on = rng.integers(ac["on_min"][0], ac["on_min"][1] + 1)
                put("Air conditioner", base, t, min(on, end - t), power)
                t += on + rng.integers(ac["off_min"][0], ac["off_min"][1] + 1)

        # Water heater: one block in the morning and one in the evening, each with some chance.
        for lo, hi, p in wh["sessions"]:
            if rng.random() < p:
                dur = rng.integers(wh["duration_min"][0], wh["duration_min"][1] + 1)
                put("Water heater", base, rng.uniform(lo, hi) * 60, dur, wh["power_w"])

        # Tea maker: a boil, then short keep-warm pulses, a few times a day.
        k = rng.integers(tea["sessions_per_day"][0], tea["sessions_per_day"][1] + 1)
        for _ in range(k):
            lo, hi = tea["start_windows"][rng.integers(len(tea["start_windows"]))]
            start = rng.uniform(lo, hi) * 60
            power = rng.uniform(*tea["boil_w"])
            boil = rng.integers(tea["boil_min"][0], tea["boil_min"][1] + 1)
            put("Tea maker", base, start, boil, power)
            warm_end = start + boil + rng.integers(tea["keep_warm_min"][0], tea["keep_warm_min"][1] + 1)
            t = start + boil + rng.integers(tea["pulse_every_min"][0], tea["pulse_every_min"][1] + 1)
            while t < warm_end:
                put("Tea maker", base, t, tea["pulse_min"], power)
                t += rng.integers(tea["pulse_every_min"][0], tea["pulse_every_min"][1] + 1)
    return pd.DataFrame(out, index=index)


# ----------------------------------------------------------------- bills

def band_of_hour(hours):
    """Tariff band for each clock hour: day 06-17, peak 17-22, night 22-06."""
    return np.where((hours >= 6) & (hours < 17), "day", np.where((hours >= 17) & (hours < 22), "peak", "night"))


def single_rate_bill(kwh, days):
    """First 8 kWh per day on average at the low price, the rest at the high one."""
    low = min(kwh, SINGLE_LIMIT_KWH_PER_DAY * days)
    return low * PRICES["single_low"] + (kwh - low) * PRICES["single_high"]


def three_rate_bill(band_kwh):
    return sum(band_kwh[b] * PRICES[b] for b in THREE_RATE)


def house_bills(grid, house):
    """Band shares and monthly bills for one home from its measured channels."""
    g = grid[grid["Aggregate"].notna()]
    band = band_of_hour(g.index.hour)
    shiftable = [a for a in SHIFTABLE if a in APPLIANCES[house]]
    cols = ["Aggregate"] + shiftable

    energy = g[cols].groupby(band).sum()  # W-minutes, only the ratio matters here
    shares = {("Household total" if c == "Aggregate" else c):
              {b: round(float(energy.loc[b, c] / energy[c].sum() * 100), 1) for b in THREE_RATE}
              for c in cols}
    daily_kwh = {("Household total" if c == "Aggregate" else c): round(float(g[c].mean() * 24 / 1000), 3)
                 for c in cols}

    # Monthly bills. Per band: mean power over the minutes we have in that band, times the
    # band's hours per day, times the days in the month. This fills gaps with the month's
    # own average for that time of day instead of counting them as zero.
    months, skipped = [], []
    for period, x in grid.groupby(grid.index.to_period("M")):
        days = period.days_in_month
        coverage = x["Aggregate"].notna().sum() / (days * 1440)
        if coverage < MIN_MONTH_COVERAGE:
            skipped.append(f"{period} ({coverage:.0%})")
            continue
        x = x[x["Aggregate"].notna()]
        b = band_of_hour(x.index.hour)
        mean_w = x[["Aggregate"] + SHIFTED].groupby(b).mean()
        kwh = {c: {bb: float(mean_w.loc[bb, c]) * BAND_HOURS[bb] / 1000 * days for bb in THREE_RATE}
               for c in mean_w.columns}
        total = kwh["Aggregate"]
        moved = sum(kwh[a]["day"] + kwh[a]["peak"] for a in SHIFTED)
        shifted = {"day": total["day"] - sum(kwh[a]["day"] for a in SHIFTED),
                   "peak": total["peak"] - sum(kwh[a]["peak"] for a in SHIFTED),
                   "night": total["night"] + moved}
        month_kwh = sum(total.values())
        months.append({
            "month": str(period), "coverage_pct": round(coverage * 100, 1),
            "kwh": round(month_kwh, 1), "daily_kwh": round(month_kwh / days, 2),
            "single_rate_tl": round(single_rate_bill(month_kwh, days), 2),
            "three_rate_tl": round(three_rate_bill(total), 2),
            "three_rate_shifted_tl": round(three_rate_bill(shifted), 2),
            "shifted_kwh": round(moved, 1),
        })
    mdf = pd.DataFrame(months)
    return {
        "first_day": str(grid.index[0].date()), "last_day": str(grid.index[-1].date()),
        "minutes_with_data_pct": round(float(grid["Aggregate"].notna().mean() * 100), 1),
        "average_daily_kwh": daily_kwh,
        "band_share_pct": shares,
        "months_used": int(len(mdf)),
        "months_skipped": skipped,
        "average_monthly": {
            "kwh": round(float(mdf["kwh"].mean()), 1),
            "single_rate_tl": round(float(mdf["single_rate_tl"].mean()), 2),
            "three_rate_tl": round(float(mdf["three_rate_tl"].mean()), 2),
            "three_rate_shifted_tl": round(float(mdf["three_rate_shifted_tl"].mean()), 2),
            "shifted_kwh": round(float(mdf["shifted_kwh"].mean()), 1),
            "months_single_rate_cheaper": int((mdf["single_rate_tl"] < mdf["three_rate_tl"]).sum()),
            "months_single_rate_cheaper_than_shifted": int((mdf["single_rate_tl"] < mdf["three_rate_shifted_tl"]).sum()),
        },
        "months": months,
    }


# ----------------------------------------------------------------- figures

def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=12)


def draw_resolution(res, path):
    """Two panels: MAE in W and daily energy error, both against resolution."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    x = np.arange(len(RESOLUTIONS))
    keys = [f"{r}min" for r in RESOLUTIONS]
    panels = [("mae_{}_W", "Mean absolute error (W, at that resolution)"),
              ("daily_err_pct_{}", "Daily energy error (% of true daily mean)")]
    for ax, (key, ylabel) in zip(axes, panels):
        ends = []
        for a in COMMON:
            gb = [res[k][a][key.format("gb")] for k in keys]
            mean = [res[k][a][key.format("mean")] for k in keys]
            ax.plot(x, mean, color=COLORS[a], lw=1.2, ls="--", alpha=0.8)
            ax.plot(x, gb, color=COLORS[a], lw=2.4, marker="o", ms=8,
                    markeredgecolor="white", markeredgewidth=1.5)
            ends.append([gb[-1], a])
        # Direct labels at the right end; nudge them apart so they do not overlap.
        ends.sort()
        top = max(max(res[k][a][key.format(m)] for k in keys for a in COMMON) for m in ("gb", "mean"))
        gap = top * 0.045
        last = -1e9
        for v, a in ends:
            y = max(v, last + gap)
            ax.annotate(a, xy=(x[-1], v), xytext=(x[-1] + 0.12, y), va="center", fontsize=12,
                        arrowprops=dict(arrowstyle="-", color="#999999", lw=0.6))
            last = y
        ax.set_xticks(x)
        ax.set_xticklabels(["1 minute", "15 minutes", "60 minutes"])
        ax.set_xlim(-0.2, len(x) - 1 + 0.75)
        ax.set_ylim(0, top * 1.1)
        ax.set_xlabel("Resolution of the household total and the targets", fontsize=13)
        ax.set_ylabel(ylabel, fontsize=13)
        style(ax)
    axes[0].plot([], [], color="#555555", lw=2.4, marker="o", label="Gradient boosting")
    axes[0].plot([], [], color="#555555", lw=1.2, ls="--", label="Predict the training mean")
    axes[0].legend(loc="upper left", fontsize=12, frameon=False)
    fig.suptitle("Experiment 1: trained on REFIT Houses 2 and 3, tested on Houses 5 and 11",
                 fontsize=17, x=0.01, ha="left")
    fig.text(0.01, 0.915, "Watt errors at different resolutions are not directly comparable, because averaging "
             "smooths the signal. The daily energy error (right) is the fair comparison.",
             fontsize=13, color="dimgray")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def draw_turkish_loads(cases, example, path):
    """Left: one test day with the synthetic loads. Right: GB error for the three cases."""
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    ax1 = fig.add_axes((0.06, 0.12, 0.38, 0.68))
    ax2 = fig.add_axes((0.53, 0.12, 0.45, 0.68))

    day, base, synth = example
    hours = base.index.hour + base.index.minute / 60
    names = list(SYNTH)
    ax1.stackplot(hours, [base.to_numpy() / 1000] + [synth[n].to_numpy() / 1000 for n in names],
                  colors=["#d9d9d9"] + [SYNTH_COLORS[n] for n in names], linewidth=0)
    ax1.set_xlim(0, 24)
    ax1.set_xticks(range(0, 25, 4))
    ax1.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 4)])
    ax1.set_xlabel("Time of day", fontsize=13)
    ax1.set_ylabel("Power (kW, 5-minute mean)", fontsize=13)
    ax1.set_title(f"House 5 on {day}: measured total (grey)\nplus the three synthetic loads",
                  fontsize=14, loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ["#d9d9d9"] + [SYNTH_COLORS[n] for n in names]]
    ax1.legend(handles, ["Measured total"] + [f"{n} (synthetic)" for n in names],
               loc="upper left", fontsize=11, frameon=False)
    style(ax1)

    labels = ["Clean test homes", "Synthetic loads added,\nmodel never saw them",
              "Synthetic loads added,\nmodel retrained with them"]
    width = 0.26
    x = np.arange(len(COMMON))
    for j, key in enumerate(["clean", "unseen", "retrained"]):
        vals = [cases[key][a]["mae_gb_W"] for a in COMMON]
        for i, a in enumerate(COMMON):
            kw = dict(color=COLORS[a], edgecolor="white", linewidth=2)
            if key == "unseen":
                kw = dict(facecolor="white", edgecolor=COLORS[a], hatch="///", linewidth=1.5)
            elif key == "retrained":
                kw = dict(color=COLORS[a], alpha=0.5, edgecolor="white", linewidth=2)
            ax2.bar(x[i] + (j - 1) * width, vals[i], width, **kw)
            ax2.text(x[i] + (j - 1) * width, vals[i] + 2, f"{vals[i]:.0f}", ha="center", fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels([a.replace(" ", "\n").replace("-", "-\n") for a in COMMON], fontsize=12)
    ax2.set_ylabel("Mean absolute error, gradient boosting (W)", fontsize=13)
    ax2.set_title("Error per appliance in the three cases (1-minute data)", fontsize=14, loc="left")
    proxies = [plt.Rectangle((0, 0), 1, 1, color="#555555"),
               plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="#555555", hatch="///"),
               plt.Rectangle((0, 0), 1, 1, color="#555555", alpha=0.5)]
    ax2.legend(proxies, labels, loc="upper left", fontsize=11, frameon=False)
    style(ax2)
    fig.suptitle("Experiment 2: loads common in Turkish homes but missing in REFIT (assumed signatures)",
                 fontsize=17, x=0.01, y=0.97, ha="left")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def draw_bills(bills, path):
    """Left: share of energy in each tariff band. Right: average monthly bill per home."""
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    ax1 = fig.add_axes((0.17, 0.1, 0.33, 0.72))
    ax2 = fig.add_axes((0.6, 0.1, 0.38, 0.72))
    band_colors = {"day": "#e9b949", "peak": "#d0603f", "night": "#4f6fa8"}

    rows = []
    for h in sorted(bills):
        for c in ["Household total"] + SHIFTED:
            rows.append((h, c, bills[h]["band_share_pct"][c]))
    y = np.arange(len(rows))[::-1].astype(float)
    y += np.repeat(np.arange(len(bills)) * 0.6, 3)[::-1]  # small gap between homes
    for yi, (h, c, s) in zip(y, rows):
        left = 0
        for b in THREE_RATE:
            ax1.barh(yi, s[b], left=left, color=band_colors[b], edgecolor="white", linewidth=2, height=0.8)
            if s[b] >= 7:
                ax1.text(left + s[b] / 2, yi, f"{s[b]:.0f}%", ha="center", va="center", fontsize=10,
                         color="white" if b != "day" else "black")
            left += s[b]
    ax1.set_yticks(y)
    ax1.set_yticklabels([f"House {h}  {c}" if c == "Household total" else c for h, c, _ in rows], fontsize=11)
    for tick, (_, c, _) in zip(ax1.get_yticklabels(), rows):
        if c in COLORS:
            tick.set_color(COLORS[c])
    ax1.set_xlim(0, 100)
    ax1.set_xlabel("Share of energy in each band (%)", fontsize=13)
    ax1.set_title("When the energy is used (clock time)", fontsize=14, loc="left")
    ax1.spines[["top", "right"]].set_visible(False)
    hb = [plt.Rectangle((0, 0), 1, 1, color=band_colors[b]) for b in THREE_RATE]
    ax1.legend(hb, ["Day 06-17", "Peak 17-22", "Night 22-06"], ncol=3, fontsize=11, frameon=False,
               loc="lower left", bbox_to_anchor=(0, 1.04))

    houses = sorted(bills)
    x = np.arange(len(houses))
    width = 0.26
    cases = [("single_rate_tl", "Single-rate", "#8c8c8c"), ("three_rate_tl", "Three-rate", "#d0603f"),
             ("three_rate_shifted_tl", "Three-rate, dishwasher and\nwashing machine moved to night", "#4f6fa8")]
    for j, (k, label, color) in enumerate(cases):
        vals = [bills[h]["average_monthly"][k] for h in houses]
        ax2.bar(x + (j - 1) * width, vals, width, color=color, edgecolor="white", linewidth=2, label=label)
        for i, v in enumerate(vals):
            ax2.text(x[i] + (j - 1) * width, v + 8, f"{v:.0f}", ha="center", fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"House {h}\n{bills[h]['average_daily_kwh']['Household total']:.1f} kWh/day"
                         for h in houses], fontsize=12)
    ax2.set_ylabel("Average monthly bill (TL, taxes included)", fontsize=13)
    ax2.set_title("Average monthly bill on the April 2026 tariffs", fontsize=14, loc="left")
    ax2.legend(fontsize=11, frameon=False, loc="upper left")
    style(ax2)
    ax2.set_ylim(0, max(bills[h]["average_monthly"]["three_rate_tl"] for h in houses) * 1.3)
    fig.suptitle("Experiment 3: measured REFIT homes priced with Türkiye's regulated residential tariffs",
                 fontsize=17, x=0.01, y=0.97, ha="left")
    fig.savefig(path, facecolor="white")
    plt.close(fig)


# ----------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default="data", help="folder with the four CLEAN_HouseN.csv files")
    parser.add_argument("--cache-dir", default="cache", help="where the 1-minute grids are cached")
    parser.add_argument("--out-dir", default=".", help="where results.json and figures/ go")
    args = parser.parse_args()
    os.makedirs(os.path.join(args.out_dir, "figures"), exist_ok=True)
    t_start = time.time()

    grids = {}
    for h in TRAIN_HOUSES + TEST_HOUSES:
        t = time.time()
        grids[h] = load_house(args.data_dir, args.cache_dir, h)
        print(f"House {h}: {len(grids[h]):,} minutes, {grids[h]['Aggregate'].notna().mean():.1%} with data "
              f"({time.time() - t:.0f} s)")
    train = [grids[h] for h in TRAIN_HOUSES]
    test = [grids[h] for h in TEST_HOUSES]
    days = [good_days(g) for g in test]
    results = {"train_houses": TRAIN_HOUSES, "test_houses": TEST_HOUSES,
               "settings": {"train_rows_1min": TRAIN_ROWS, "windows": {str(k): v for k, v in WINDOWS.items()},
                            "min_bin_coverage": MIN_BIN_COVERAGE, "min_day_coverage": MIN_DAY_COVERAGE,
                            "min_month_coverage": MIN_MONTH_COVERAGE, "seed": SEED}}

    # 1. Resolution
    results["experiment1_resolution"] = {}
    for r in RESOLUTIONS:
        t = time.time()
        tr = [at_resolution(g, r) for g in train]
        te = [at_resolution(g, r) for g in test]
        models, means = fit_models(tr, WINDOWS[r], TRAIN_ROWS)
        frames = predict(models, means, te, WINDOWS[r])
        results["experiment1_resolution"][f"{r}min"] = score(frames, days)
        if r == 1:
            models_1min, means_1min = models, means
        print(f"\nExperiment 1, {r} min ({time.time() - t:.0f} s)")
        for a, s in results["experiment1_resolution"][f"{r}min"].items():
            print(f"  {a:16s} MAE mean {s['mae_mean_W']:6.1f} gb {s['mae_gb_W']:6.1f} W   "
                  f"daily err gb {s['daily_err_median_kwh_gb']:.3f} kWh median, {s['daily_err_pct_gb']:5.1f}%"
                  f"  (mean {s['daily_err_pct_mean']:5.1f}%)")
    draw_resolution(results["experiment1_resolution"], os.path.join(args.out_dir, "figures", "exp1_resolution.png"))

    # 2. Turkish loads. Different seeds for training and test homes, so the retrained
    # model sees the same kind of load, never the same events.
    t = time.time()
    synth_test = [synthetic_loads(g.index, np.random.default_rng(SEED + 1000 + h))
                  for g, h in zip(test, TEST_HOUSES)]
    synth_train = [synthetic_loads(g.index, np.random.default_rng(SEED + 2000 + h))
                   for g, h in zip(train, TRAIN_HOUSES)]
    extra_test = [s.sum(axis=1) for s in synth_test]
    extra_train = [s.sum(axis=1) for s in synth_train]
    cases = {"clean": results["experiment1_resolution"]["1min"]}
    cases["unseen"] = score(predict(models_1min, means_1min, test, WINDOWS[1], extra_test), days)
    models_aug, means_aug = fit_models(train, WINDOWS[1], TRAIN_ROWS, extra_train)
    cases["retrained"] = score(predict(models_aug, means_aug, test, WINDOWS[1], extra_test), days)
    synth_kwh = {}
    for g, s, h in zip(test, synth_test, TEST_HOUSES):
        present = g["Aggregate"].notna()
        synth_kwh[f"House {h}"] = {n: round(float(s.loc[present, n].mean() * 24 / 1000), 2) for n in SYNTH}
        synth_kwh[f"House {h}"]["measured total"] = round(float(g["Aggregate"].mean() * 24 / 1000), 2)
    results["experiment2_turkish_loads"] = {
        "note": "synthetic loads are assumed signatures, not measurements",
        "parameters": SYNTH, "synthetic_daily_kwh_test_homes": synth_kwh, "cases": cases}
    print(f"\nExperiment 2 ({time.time() - t:.0f} s), GB MAE in W: clean / unseen / retrained")
    for a in COMMON:
        print(f"  {a:16s} {cases['clean'][a]['mae_gb_W']:6.1f} {cases['unseen'][a]['mae_gb_W']:6.1f} "
              f"{cases['retrained'][a]['mae_gb_W']:6.1f}   daily % {cases['clean'][a]['daily_err_pct_gb']:5.1f} "
              f"{cases['unseen'][a]['daily_err_pct_gb']:5.1f} {cases['retrained'][a]['daily_err_pct_gb']:5.1f}")
    print("  synthetic daily kWh:", synth_kwh)

    # Example day for the figure: a complete House 5 day in July that has all three loads.
    g5, s5 = test[0], synth_test[0]
    pick = None
    for d in sorted(days[0]):
        x = s5[s5.index.date == d]
        if d.month == 7 and (x > 0).any().all():
            pick = d
            break
    if pick is None:  # fall back to the first good day
        pick = sorted(days[0])[0]
    sel = g5.index.date == pick
    base = g5.loc[sel, "Aggregate"].resample("5min").mean()
    synth5 = s5.loc[sel].resample("5min").mean()
    draw_turkish_loads(cases, (str(pick), base, synth5),
                       os.path.join(args.out_dir, "figures", "exp2_turkish_loads.png"))

    # 3. Bills from the measured channels
    results["experiment3_bills"] = {
        "tariff": "EPDK regulated tariff, low-voltage residential (mesken, AG), valid from 2026-04-04",
        "tax_note": "all-in = (energy x 1.05 + distribution) x 1.10; our calculation, check against a real bill",
        "price_tl_per_kwh": {k: round(v, 3) for k, v in PRICES.items()},
        "month_rule": f"a calendar month is billed only if at least {MIN_MONTH_COVERAGE:.0%} of its minutes "
                      "have data; gaps are filled with that month's mean power in the same band",
        "houses": {},
    }
    bills = {}
    for h in TRAIN_HOUSES + TEST_HOUSES:
        bills[h] = house_bills(grids[h], h)
        results["experiment3_bills"]["houses"][f"House {h}"] = bills[h]
        am = bills[h]["average_monthly"]
        print(f"\nHouse {h}: {bills[h]['average_daily_kwh']['Household total']} kWh/day, "
              f"{bills[h]['months_used']} months used, skipped {bills[h]['months_skipped']}")
        print(f"  bands {bills[h]['band_share_pct']['Household total']}")
        print(f"  monthly: single {am['single_rate_tl']} three {am['three_rate_tl']} "
              f"shifted {am['three_rate_shifted_tl']} TL, {am['shifted_kwh']} kWh moved")
    draw_bills(bills, os.path.join(args.out_dir, "figures", "exp3_bills.png"))

    results["runtime_s"] = round(time.time() - t_start)
    with open(os.path.join(args.out_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    print(f"\nTotal runtime {results['runtime_s']} s")


if __name__ == "__main__":
    main()
