# Fatura Dedektifi presentation script

## 1. Opening

Hello, I'm Mert Güngör.

In this video I will present my idea for the Samsung Innovation Campus capstone project.

The project is called Fatura Dedektifi. In English, Bill Detective.

It tries to answer one question. Which appliance uses the electricity at home?

## 2. Problem

An electricity bill shows only one total.

It does not show how much each appliance used, so we cannot tell where to save.

Energy costs are a serious burden in Türkiye. According to Eurostat, in 2025, 19.5 percent of the population could not afford to keep their home warm enough.

Putting a separate meter on every appliance is expensive and not practical.

## 3. One real day

This chart shows one day in a real home in the UK. I downloaded the data and drew it myself.

The grey line is the total power that the meter sees.

The coloured areas show the power of each appliance on the same day. The dishwasher, the washing machine, the kettle and the fridge.

On that day, one quarter of the home's electricity went to the dishwasher.

## 4. The idea

My idea is an AI model that looks only at the grey line and estimates the coloured areas.

From one meter it will separate five appliances. The fridge, the washing machine, the dishwasher, the kettle and the microwave.

A simple rule cannot do this, because appliances run at the same time and use similar power.

In this home the washing machine heater uses 2.1 kilowatts and the dishwasher heater uses 2.2. On the meter they look almost the same.

## 5. SDG

The project is connected to Sustainable Development Goal 7, affordable and clean energy.

It mainly serves the energy efficiency target, because people can only reduce the consumption they can see.

It also helps the goals on responsible consumption and climate action in an indirect way.

## 6. Literature

I found two main studies in the literature.

In 2015, Kelly and Knottenbelt used deep neural networks for this problem and got better results than classical methods.

In 2018, Zhang and his colleagues proposed a method that looks at a short part of the total signal and predicts the power of one appliance at that moment.

Both are research studies. They do not offer a tool for households or a cost calculation.

I want to test the model on homes it has never seen and show the result in kilowatt hours and in lira.

## 7. Data

The dataset is called REFIT. It was collected in 20 homes in the UK for almost two years.

It has an open licence and it is free.

In each home, the total power and the power of nine appliances were measured about every 8 seconds.

In total there are about 120 million rows.

I looked at two homes in detail. In one of them, a quarter of the minutes have no data.

I will clean these gaps first. I will also keep the test homes out of training.

## 8. Approach

I chose deep learning, because the input is a raw time series and the model has to learn the working cycle of each appliance.

I will train a small convolutional neural network for each appliance.

To compare, I first tried two simple methods. I trained on one home and tested on another home.

For the kettle, a model that always predicts the average has an error of 45 watts. Classical machine learning reduces this error to 18 watts.

For the washing machine, the classical method gives almost no improvement. The error stays at 44 watts.

The washing machine has a long cycle with several stages. This is where I expect deep learning to help.

My target is a lower error than the classical method for at least four of the five appliances.

## 9. The bill in Türkiye

I calculate the cost with the Turkish tariff. On the three-rate tariff, one kilowatt hour costs 3.26 lira at night, 4.92 lira in the daytime and 7 lira in the evening peak.

On the single-rate tariff it costs 3.24 lira up to 8 kilowatt hours a day, and 4.86 lira above that.

I priced the same day with both tariffs. It costs 37 lira on the single-rate tariff and 50 lira on the three-rate tariff.

If the midday dishwasher run and the morning wash move to the night, the three-rate bill falls to 46 lira.

So for this home the single-rate tariff is cheaper. The demo will make this comparison for every home and say which tariff and which hours are cheaper.

## 10. From UK data to Türkiye

The data come from the UK. But both countries use 230 volts and 50 hertz, and the five appliances I target are also found in Turkish homes.

In the first step I will also test the model on a second dataset. In the literature the error grows little inside one country and grows more in another country.

In the second step I will add loads that are common in Turkish homes, such as air conditioners, electric water heaters and tea makers, to the training data artificially.

In the third step I will also measure the model on hourly data, because smart meters in Türkiye give hourly data.

In the last step I will measure one Turkish home with smart plugs for a few weeks and report the model's error on real Turkish data.

## 11. Demo, limit and close

At the end of the term there will be a demo that opens in the browser.

You upload one day of meter data, and it shows the use of each appliance, the bill on both tariffs and the appliance that can move to the night.

There is one limit. I found no open labelled data from Türkiye, so my own measurement will be a small check.

A family that sees the dishwasher takes a quarter of their electricity can decide to run it less often.

Thank you for listening.
