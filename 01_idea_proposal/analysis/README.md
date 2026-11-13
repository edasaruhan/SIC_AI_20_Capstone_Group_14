# First look at the REFIT data

`first_look.py` produces the first numbers quoted in the project proposal. It uses
two homes from the REFIT Electrical Load Measurements (Cleaned) dataset and does three things:

1. Describes House 2: number of rows, how many minutes have data, and how much of the
   total energy the nine monitored appliances account for.
2. Picks one complete day in House 2 where the washing machine, dishwasher, kettle and
   microwave all run (17 June 2014), saves it as `chart_day.json` (5-minute means) and draws
   `figures/house2_day.png`.
3. Trains two simple baselines on House 2 and tests them on House 5, at 1-minute resolution,
   for the five appliances both homes have: predicting the training mean, and a gradient
   boosting regressor on features of the household total. The score is mean absolute error in watts.

![House 2 on 17 June 2014](figures/house2_day.png)

## Getting the data

Download `CLEAN_REFIT_081116.7z` (about 514 MB) from the dataset page with a normal browser:
https://pureportal.strath.ac.uk/en/datasets/refit-electrical-load-measurements-cleaned/

The portal sometimes blocks scripted downloads. Houses 1, 2, 3, 4, 5 and 11 can also be downloaded one
by one from Zenodo (https://doi.org/10.5281/zenodo.5063428).

The archive holds 20 CSV files (about 6.9 GB unpacked). Only two are needed:

```
mkdir data
7z e CLEAN_REFIT_081116.7z -odata CLEAN_House2.csv CLEAN_House5.csv
```

## Running

```
pip install -r requirements.txt
python first_look.py --data-dir data --out-dir .
```

It writes `results.json`, `chart_day.json` and `figures/house2_day.png`. A run takes one to two
minutes on a laptop. The random seed is fixed, so the
numbers below should come out the same.

## Results

House 2:

| Quantity | Value |
|---|---|
| Rows in CLEAN_House2.csv | 5,733,526 |
| Minutes with data (first to last reading) | 75.4% |
| Share of total energy, all nine monitored appliances | 32.1% |
| Share of total energy, dishwasher | 13.1% |
| 17 June 2014, total energy | 10.34 kWh |
| 17 June 2014, dishwasher energy | 2.72 kWh |

Baselines, trained on House 2 and tested on House 5, mean absolute error in W
(lower is better):

| Appliance | Predict the mean | Gradient boosting |
|---|---|---|
| Kettle | 44.9 | 17.6 |
| Dishwasher | 107.1 | 67.6 |
| Washing machine | 44.3 | 43.6 |
| Microwave | 30.2 | 30.0 |
| Fridge-freezer | 55.6 | 48.0 |

For reference, the whole archive has 119,495,879 data rows across the 20 CSV files
(counted separately, not by this script).

## Caveats

- The baselines use one home for training and one for testing. Results on other pairs of
  homes can be quite different, so these numbers only show that the task is learnable for some
  appliances (the kettle and dishwasher) and hard for others.
- All REFIT homes are in the UK (Loughborough area, 2013 to 2015). Appliances, wiring and
  habits differ elsewhere, so the results may not carry over to other countries.

## Tariff cost analysis

`tariff_cost.py` prices the example day with Türkiye's regulated residential tariffs. It
needs only `chart_day.json`, so it runs without the REFIT download:

```
python tariff_cost.py --chart-day chart_day.json --out-dir .
```

It writes `tariff_results.json` and `figures/house2_day_tariff.png`.

The script compares two tariffs from the EPDK table for low-voltage residential customers
(mesken, AG), valid from 4 April 2026. The single-rate tariff charges a low energy price for
the first 8 kWh per day on average and a higher price for the rest. The three-rate tariff has
one price for each time band: day (06:00 to 17:00), peak (17:00 to 22:00) and night (22:00 to
06:00). Both add a distribution charge of 242.49 kuruş per kWh. We add the 5% consumption
tax (BTV) on the energy part and then 10% VAT (KDV) on the whole, which gives the all-in price:
(energy × 1.05 + distribution) × 1.10.

The script splits the day's energy into the three bands, for the household total and for each
of the five appliances, and works out three bills. The third one moves the dishwasher and
washing machine energy that falls in the day and peak bands (2.54 kWh) to the night band, as if
the household had started both machines after 22:00.

![House 2 on 17 June 2014 with the three tariff bands](figures/house2_day_tariff.png)

All-in prices, TL per kWh:

| Tariff | Price |
|---|---|
| Single-rate, first 8 kWh per day | 3.238 |
| Single-rate, above 8 kWh per day | 4.857 |
| Three-rate, day | 4.920 |
| Three-rate, peak | 6.996 |
| Three-rate, night | 3.261 |

House 2 on 17 June 2014, energy in each band (kWh) and cost on the three-rate tariff (TL):

| | Day | Peak | Night | Total kWh | Three-rate cost |
|---|---|---|---|---|---|
| Household total | 6.66 | 1.39 | 2.30 | 10.34 | 49.95 |
| Dishwasher | 1.39 | 0.00 | 1.33 | 2.72 | 11.18 |
| Washing machine | 1.15 | 0.00 | 0.00 | 1.15 | 5.65 |
| Fridge-freezer | 0.50 | 0.22 | 0.26 | 0.98 | 4.86 |
| Kettle | 0.56 | 0.11 | 0.00 | 0.67 | 3.54 |
| Microwave | 0.00 | 0.05 | 0.00 | 0.05 | 0.33 |

Bills for the whole day:

| Case | Bill (TL) |
|---|---|
| Single-rate | 37.28 |
| Three-rate | 49.95 |
| Three-rate, dishwasher and washing machine moved to night | 45.74 |

Moving the two machines saves 4.21 TL on the three-rate tariff. On this day the household
would still pay less on the single-rate tariff. About two thirds of its energy falls in the day
band, and even the night price (3.261 TL) is slightly above the single-rate low tier (3.238 TL).
The script applies the 8 kWh limit to this one day; on a real bill it is an average over the
billing period.

Caveats for this part:

- The prices are the regulated tariff valid from 4 April 2026. EPDK revises the table several
  times a year, so the constants at the top of `tariff_cost.py` need updating before the
  numbers are reused.
- The tax add-on is our calculation from the published tax rates and should be checked against
  a real Turkish electricity bill.
- The day comes from a UK home in 2014. It shows the method; Turkish homes use electricity at
  different hours and with different appliances, so the bills say little about a Turkish
  household.

## Dataset licence and citation

The REFIT data is published by the University of Strathclyde under the Creative Commons
Attribution 4.0 licence (CC BY 4.0). The CSV files are not included in this repository.

Murray, D., Stankovic, L. and Stankovic, V. (2017). An electrical load measurements dataset
of United Kingdom households from a two-year longitudinal study. Scientific Data 4, 160122.
https://doi.org/10.1038/sdata.2016.122

Dataset: REFIT: Electrical Load Measurements (Cleaned). University of Strathclyde.
https://doi.org/10.15129/9ab14b0e-19ac-4279-938f-27f643078cec
