# Fatura Dedektifi (Bill Detective)

Samsung Innovation Campus, Artificial Intelligence Course, Capstone Group 14

An electricity bill shows one total. It does not show which appliance used how much. This project estimates the consumption of the fridge, the washing machine, the dishwasher, the kettle and the microwave from the total power signal of a home, with no extra meter on any appliance. The task is known as non-intrusive load monitoring (NILM).

The project relates to SDG 7, Affordable and Clean Energy, mainly target 7.3 on energy efficiency.

![One day in REFIT House 2: the household total and the monitored appliances](01_idea_proposal/analysis/figures/house2_day.png)

The grey line is what the meter sees. The coloured areas are what each appliance drew on the same day. The model has to recover the colours from the grey line alone. On this day the dishwasher used 2.72 of the home's 10.34 kWh.

## Türkçe özet

Elektrik faturasında tek bir toplam yazar, hangi cihazın ne kadar harcadığı yazmaz. Bu proje, evin toplam güç sinyaline bakarak buzdolabı, çamaşır makinesi, bulaşık makinesi, su ısıtıcı ve mikrodalganın tüketimini tahmin etmeyi amaçlıyor. Cihazlara ayrı sayaç takmak gerekmiyor. Proje SDG 7 (Erişilebilir ve Temiz Enerji) ile, özellikle enerji verimliliği hedefiyle (7.3) ilgili. Belgelerin Türkçe sürümleri aşağıdaki tabloda.

## Assignments

| No | Assignment | Files |
|---|---|---|
| 01 | Idea proposal | [Proposal (EN)](01_idea_proposal/Fatura_Dedektifi_Group14_Idea_Proposal_EN.pdf), [Fikir önerisi (TR)](01_idea_proposal/Fatura_Dedektifi_Grup14_Fikir_Onerisi_TR.pdf), [Slides (EN)](01_idea_proposal/slides/Fatura_Dedektifi_Group14_Slides_EN.pdf), [Slaytlar (TR)](01_idea_proposal/slides/Fatura_Dedektifi_Group14_Slides_TR.pdf), [first analysis](01_idea_proposal/analysis/) |

Later assignments will get their own numbered folders.

## First results

These come from [01_idea_proposal/analysis/first_look.py](01_idea_proposal/analysis/first_look.py). Two simple baselines were trained on House 2 and tested on House 5 at 1-minute resolution. The score is the mean absolute error in watts, so lower is better.

| Appliance | Predict the mean | Gradient boosting |
|---|---|---|
| Kettle | 44.9 | 17.6 |
| Dishwasher | 107.1 | 67.6 |
| Washing machine | 44.3 | 43.6 |
| Microwave | 30.2 | 30.0 |
| Fridge-freezer | 55.6 | 48.0 |

Gradient boosting on window statistics helps for the kettle and the dishwasher. It barely helps for the washing machine and the microwave. The planned model is a small 1D convolutional network per appliance (sequence-to-point), and the target is to beat gradient boosting for at least four of the five appliances on homes the model has not seen.

These numbers use one training home and one test home, so they are a starting point and will change when more homes are used.

## Data

REFIT Electrical Load Measurements (Cleaned), University of Strathclyde, CC BY 4.0. It has 20 UK homes recorded between 2013 and 2015, with the household total and nine appliance channels about every 8 seconds, 119.5 million rows in total. The data files are not stored in this repository. [The analysis README](01_idea_proposal/analysis/README.md) explains how to download them.

Murray, D., Stankovic, L. and Stankovic, V. (2017). An electrical load measurements dataset of United Kingdom households from a two-year longitudinal study. Scientific Data 4, 160122. https://doi.org/10.1038/sdata.2016.122

The homes are British and there is no Turkish data to test on, so cost figures in lira will be an illustration.

## Repository layout

```
01_idea_proposal/
  Fatura_Dedektifi_Group14_Idea_Proposal_EN.pdf, .docx    one-page proposal
  Fatura_Dedektifi_Grup14_Fikir_Onerisi_TR.pdf, .docx     the same proposal in Turkish
  slides/                                                 slide deck and narration text, EN and TR
  analysis/                                               script, results and figure for the first numbers
```

## Team

Mert Güngör ([mert-gng-99](https://github.com/mert-gng-99))
