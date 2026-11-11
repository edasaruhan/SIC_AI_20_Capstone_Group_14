"""First look at the REFIT cleaned dataset (Houses 2 and 5).

Prints and saves:
  - basic facts about House 2 (rows, data coverage, energy share of each appliance)
  - the energy use of House 2 on one example day, and a figure of that day
  - two simple baselines trained on House 2 and tested on House 5

Usage:
  python first_look.py --data-dir data --out-dir .
where data/ holds CLEAN_House2.csv and CLEAN_House5.csv from the REFIT archive.
"""
import argparse
import json
import os

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
    5: ["Fridge-Freezer", "Tumble Dryer", "Washing Machine", "Dishwasher", "Desktop Computer",
        "Television", "Microwave", "Kettle", "Toaster"],
}
# Appliances that exist in both houses, so we can train on one and test on the other.
COMMON = ["Fridge-Freezer", "Washing Machine", "Dishwasher", "Microwave", "Kettle"]
SEED = 0


def load_house(path, house):
    """Read one house CSV and average it to 1-minute resolution."""
    cols = ["Time", "Aggregate"] + [f"Appliance{i}" for i in range(1, 10)]
    df = pd.read_csv(path, usecols=cols, parse_dates=["Time"], index_col="Time")
    raw_rows = len(df)
    df = df.rename(columns={f"Appliance{i + 1}": name for i, name in enumerate(APPLIANCES[house])})
    # Raw samples come every ~8 s with gaps; 1-minute means give a regular time grid.
    minutes = df.resample("1min").mean()
    # Share of minutes between the first and last reading that have any data.
    coverage = minutes["Aggregate"].notna().mean()
    minutes = minutes.dropna(subset=["Aggregate"])
    return minutes, raw_rows, coverage


def make_features(minutes):
    """Features computed only from the household total (the one meter we would have)."""
    total = minutes["Aggregate"]
    f = pd.DataFrame({"total": total})
    # Rolling windows describe the shape around each minute (an appliance cycle lasts minutes).
    for w in (5, 15, 31, 61):
        r = total.rolling(w, center=True, min_periods=1)
        f[f"mean{w}"] = r.mean()
        f[f"max{w}"] = r.max()
        f[f"min{w}"] = r.min()
        f[f"std{w}"] = r.std().fillna(0)
    # Step changes show when something switches on or off.
    f["diff_prev"] = total.diff().fillna(0)
    f["diff_next"] = total.diff(-1).fillna(0)
    f["hour"] = minutes.index.hour + minutes.index.minute / 60
    return f


def pick_chart_day(m):
    """Pick a complete House 2 day where the four intermittent appliances all run.

    Score = share of the day's energy explained by the five common appliances,
    minus the share of minutes where the appliances add up to clearly more than the total
    (a sign of bad data).
    """
    best_day, best_score = None, None
    for day, x in m.groupby(m.index.date):
        if len(x) < 1430:  # allow at most 10 missing minutes
            continue
        active = [(x[a] > 20).sum() for a in ["Washing Machine", "Dishwasher", "Kettle", "Microwave"]]
        if min(active) < 3:
            continue
        residual = x["Aggregate"] - x[APPLIANCES[2]].sum(axis=1)
        score = x[COMMON].sum().sum() / x["Aggregate"].sum() - (residual < -50).mean()
        if best_score is None or score > best_score:
            best_day, best_score = day, score
    return best_day


def draw_day(day_5min, day, path):
    """Total load as a grey line, the five common appliances as stacked areas."""
    hours = day_5min.index.hour + day_5min.index.minute / 60
    kw = day_5min / 1000
    layers = [  # bottom to top: always-on fridge first, then the large cycles
        ("Fridge-Freezer", "#222222"),
        ("Dishwasher", "#1f6fd1"),
        ("Washing Machine", "#d62728"),
        ("Kettle", "#f2c200"),
        ("Microwave", "#9ecae1"),
    ]
    ymax = 3.5

    fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    ax.stackplot(hours, [kw[n] for n, _ in layers], colors=[c for _, c in layers],
                 alpha=0.9, linewidth=0)
    ax.plot(hours, kw["Aggregate"].clip(upper=ymax), color="grey", linewidth=1.6)

    # Label each layer directly. Positions are picked by hand for this day so that
    # no label sits on top of another layer: (hour to point at, label x, label y in kW).
    label_spots = {
        "Fridge-Freezer": (2.75, 1.0, 0.55),
        "Dishwasher": (22.45, 19.6, 2.55),
        "Washing Machine": (7.05, 3.4, 2.1),
        "Kettle": (15.5, 16.2, 1.35),
        "Microwave": (18.67, 16.6, 0.75),
    }
    bottom = np.zeros(len(kw))
    for name, color in layers:
        values = kw[name].to_numpy()
        hour, tx, ty = label_spots[name]
        i = int(np.argmin(np.abs(hours - hour)))  # nearest 5-minute slot
        ax.annotate(name, xy=(hours[i], bottom[i] + values[i] / 2), xytext=(tx, ty),
                    fontsize=14, color="black",
                    arrowprops=dict(arrowstyle="-", color="black", lw=0.8))
        bottom += values

    ax.text(19.85, 0.45, "Household total", fontsize=14, color="dimgray")

    # The total line is clipped, so say how high it really goes.
    peak = kw["Aggregate"].idxmax()
    peak_h = peak.hour + peak.minute / 60
    ax.annotate(f"Total reaches {kw['Aggregate'].max():.1f} kW at {peak:%H:%M}\n"
                "(an appliance that is\nnot monitored).\nAxis clipped at 3.5 kW.",
                xy=(peak_h, ymax), xytext=(peak_h - 0.7, 2.75), va="bottom", ha="right",
                fontsize=13, color="dimgray",
                arrowprops=dict(arrowstyle="->", color="dimgray", lw=1))

    ax.set_xlim(0, 24)
    ax.set_ylim(0, ymax)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 2)], fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.set_xlabel("Time of day", fontsize=14)
    ax.set_ylabel("Power (kW, 5-minute mean)", fontsize=14)
    ax.set_title(f"REFIT House 2 on {day}: household total and five monitored appliances",
                 fontsize=17, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default="data", help="folder with CLEAN_House2.csv and CLEAN_House5.csv")
    parser.add_argument("--out-dir", default=".", help="where results.json, chart_day.json and figures/ go")
    args = parser.parse_args()
    os.makedirs(os.path.join(args.out_dir, "figures"), exist_ok=True)
    results = {}

    # 1. House 2 facts
    houses = {}
    for h in (2, 5):
        m, rows, coverage = load_house(os.path.join(args.data_dir, f"CLEAN_House{h}.csv"), h)
        houses[h] = m
        if h == 2:
            kwh = m.sum() / 60 / 1000  # 1-minute means in W -> kWh
            share = (kwh.drop("Aggregate") / kwh["Aggregate"] * 100).round(1)
            results["house2"] = {
                "rows": rows,
                "minutes_with_data_pct": round(coverage * 100, 1),
                "total_kwh": round(float(kwh["Aggregate"]), 1),
                "monitored_share_pct": round(float(share.sum()), 1),
                "appliance_share_pct": share.sort_values(ascending=False).to_dict(),
            }
            print(f"House 2: {rows:,} rows, {coverage:.1%} of minutes have data")
            print(f"  nine appliances = {share.sum():.1f}% of total energy, dishwasher {share['Dishwasher']}%")

    # 2. Example day
    m2 = houses[2]
    day = pick_chart_day(m2)
    x = m2[m2.index.date == day]
    x5 = x.resample("5min").mean()
    chart = {"day": str(day), "t": [t.strftime("%H:%M") for t in x5.index],
             "aggregate": x5["Aggregate"].round(0).tolist()}
    for a in COMMON:
        chart[a] = x5[a].round(0).tolist()
    chart["kwh"] = {k: round(float(v), 2) for k, v in (x.sum() / 60 / 1000).items()}
    with open(os.path.join(args.out_dir, "chart_day.json"), "w") as f:
        json.dump(chart, f)
    results["chart_day"] = {"day": str(day), "total_kwh": chart["kwh"]["Aggregate"],
                            "dishwasher_kwh": chart["kwh"]["Dishwasher"],
                            "peak_5min_kw": round(float(x5["Aggregate"].max()) / 1000, 2)}
    print(f"Chart day {day}: total {chart['kwh']['Aggregate']} kWh, dishwasher {chart['kwh']['Dishwasher']} kWh")
    draw_day(x5, str(day), os.path.join(args.out_dir, "figures", "house2_day.png"))

    # 3. Baselines: train on House 2, test on House 5, 1-minute resolution.
    X_train, X_test = make_features(houses[2]), make_features(houses[5])
    results["baselines"] = {}
    print("MAE in W (House 2 -> House 5):  predict-mean   gradient-boosting")
    for a in COMMON:
        y_train, y_test = houses[2][a].fillna(0), houses[5][a].fillna(0)
        mean_pred = np.full(len(y_test), y_train.mean())
        # A 600k-minute random sample keeps training to about a minute; fixed seed for repeatability.
        idx = np.random.RandomState(SEED).choice(len(X_train), 600000, replace=False)
        model = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, random_state=SEED)
        model.fit(X_train.iloc[idx], y_train.iloc[idx])
        gb_pred = np.clip(model.predict(X_test), 0, None)  # power cannot be negative
        results["baselines"][a] = {
            "true_mean_W": round(float(y_test.mean()), 1),
            "mae_mean": round(float(np.abs(y_test - mean_pred).mean()), 1),
            "mae_gb": round(float(np.abs(y_test - gb_pred).mean()), 1),
            # signal aggregate error: how far off the total energy over the test period is
            "sae_mean": round(float(abs(mean_pred.sum() - y_test.sum()) / y_test.sum()), 2),
            "sae_gb": round(float(abs(gb_pred.sum() - y_test.sum()) / y_test.sum()), 2),
        }
        r = results["baselines"][a]
        print(f"  {a:16s} {r['mae_mean']:8.1f} {r['mae_gb']:12.1f}")

    with open(os.path.join(args.out_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=1)


if __name__ == "__main__":
    main()
