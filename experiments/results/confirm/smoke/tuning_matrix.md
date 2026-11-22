# Tuning matrix

Run `experiments\results\confirm\smoke`; budget T = 4, seeds [0, 1], gate window y1, gate criterion V. Development data only.

| base | method | inputs | model | training loss | training rows / years | validation years | criterion | early stopping | trials | seeds | mean train rows (tuning folds) | trial s | deploy s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| lgbm | BASE | B0+R (-Z set), rank-transformed; base score: no | LightGBM regression | squared error on within-day rank of fwd H-day open-to-open return | all candidate rows from 2015 with label window ending before the validation / deployment year (day <= first day - 2H - 2) | 2017 | mean daily RankIC over (seed, year) folds | none (n_estimators is a hyper-parameter) | 4 | 2 | 31329 | 82.77 | 93.3 |
| lgbm | BASE-V | B0+R (-Z set), rank-transformed; base score: no | LightGBM regression | squared error on within-day rank of fwd H-day open-to-open return | all candidate rows from 2015 with label window ending before the validation / deployment year (day <= first day - 2H - 2) | 2017 | pooled V of own top 15 eligible names / day, pooled over validation days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 31329 | 82.77 | 93.3 |
| lgbm | LOSS(+Z_H) | -Z +Z_H + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 138.71 | 50.79 |
| lgbm | LOSS(+Z_H+Z_O*) | -Z +Z_H+Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 146.74 | 52.68 |
| lgbm | LOSS(+Z_O) | -Z +Z_O + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 145.32 | 26.37 |
| lgbm | LOSS(+Z_O*) | -Z +Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 142.36 | 51.99 |
| lgbm | LOSS(+perm Z_H) | -Z +perm Z_H + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 132.32 | 49.48 |
| lgbm | LOSS(+perm Z_O*) | -Z +perm Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 137.81 | 67.68 |
| lgbm | LOSS(-Z) | -Z + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 134.96 | 50.28 |
| lgbm | LOSS-LR(-Z) | -Z + base rank: yes; population top-K_tr = 90 of the base | logistic regression (LOGIT_SPACE) | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | n/a | 4 | 2 | 34231 | 83.36 | 15.75 |
| lgbm | NET-K(+Z_H) | -Z +Z_H + base rank: yes; population top-K_tr = 90 of the base | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 123.23 | 59.9 |
| lgbm | NET-K(+Z_O*) | -Z +Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 131.38 | 34.01 |
| lgbm | NET-K(-Z) | -Z + base rank: yes; population top-K_tr = 90 of the base | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 120.95 | 57.67 |
| lgbm | NET-U(-Z) | -Z + base rank: yes; population all candidates C_t | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through Y-2 (purged before Y-1; labels known before Y-1) | 2020 | mean theta_sel over (seed, year) folds | none (n_estimators is a hyper-parameter) | 4 | 2 | 16450 | 124.96 | 50.29 |
| lgbm | NET-U15(-Z) | -Z + base rank: yes; population all candidates C_t | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 144.34 | 21.41 |
| lgbm | PERF | lagged base RankIC series | rule (grid) | n/a | n/a | 2020 | mean AR over tuning years x seeds (deployment backtest) | n/a | 4 | 2 | n/a | 0.0 | n/a |
| lgbm | TREND | equal-weight index of the universe | rule (grid) | n/a | n/a | 2020 | mean AR over tuning years x seeds (deployment backtest) | n/a | 4 | 2 | n/a | 0.0 | n/a |
| ridge | BASE | B0+R (-Z set), rank-transformed; base score: no | ridge / elastic net (LINEAR_SPACE) | squared error on within-day rank of fwd H-day open-to-open return | all candidate rows from 2015 with label window ending before the validation / deployment year (day <= first day - 2H - 2) | 2017 | mean daily RankIC over (seed, year) folds | n/a | 4 | 1 (deterministic) | 31329 | 11.709999999999999 | 20.2 |
| ridge | BASE-V | B0+R (-Z set), rank-transformed; base score: no | ridge / elastic net (LINEAR_SPACE) | squared error on within-day rank of fwd H-day open-to-open return | all candidate rows from 2015 with label window ending before the validation / deployment year (day <= first day - 2H - 2) | 2017 | pooled V of own top 15 eligible names / day, pooled over validation days per seed, mean over seeds | n/a | 4 | 1 (deterministic) | 31329 | 11.709999999999999 | 19.6 |
| ridge | LOSS(+Z_H) | -Z +Z_H + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 132.54 | 23.1 |
| ridge | LOSS(+Z_H+Z_O*) | -Z +Z_H+Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 131.6 | 54.14 |
| ridge | LOSS(+Z_O) | -Z +Z_O + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 133.74 | 66.32 |
| ridge | LOSS(+Z_O*) | -Z +Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 131.61 | 51.05 |
| ridge | LOSS(+perm Z_H) | -Z +perm Z_H + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 130.64 | 32.28 |
| ridge | LOSS(+perm Z_O*) | -Z +perm Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 130.13 | 51.84 |
| ridge | LOSS(-Z) | -Z + base rank: yes; population top-K_tr = 90 of the base | LightGBM binary | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34231 | 145.63 | 22.82 |
| ridge | LOSS-LR(-Z) | -Z + base rank: yes; population top-K_tr = 90 of the base | logistic regression (LOGIT_SPACE) | log loss on O1 loss label (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | n/a | 4 | 2 | 34231 | 94.35000000000001 | 15.06 |
| ridge | NET-K(+Z_H) | -Z +Z_H + base rank: yes; population top-K_tr = 90 of the base | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 118.46000000000001 | 48.07 |
| ridge | NET-K(+Z_O*) | -Z +Z_O* + base rank: yes; population top-K_tr = 90 of the base | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 119.86 | 36.36 |
| ridge | NET-K(-Z) | -Z + base rank: yes; population top-K_tr = 90 of the base | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 118.16 | 58.45 |
| ridge | NET-U(-Z) | -Z + base rank: yes; population all candidates C_t | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through Y-2 (purged before Y-1; labels known before Y-1) | 2020 | mean theta_sel over (seed, year) folds | none (n_estimators is a hyper-parameter) | 4 | 2 | 16450 | 96.07000000000001 | 37.33 |
| ridge | NET-U15(-Z) | -Z + base rank: yes; population all candidates C_t | LightGBM regression | squared error on rho (filled orders) | base out-of-sample rows from 2018 through the purge point before Y (labels known before Y) | 2020 | pooled V of submitted orders over tuning days per seed, mean over seeds | none (n_estimators is a hyper-parameter) | 4 | 2 | 34222 | 97.84 | 39.44 |
| ridge | PERF | lagged base RankIC series | rule (grid) | n/a | n/a | 2020 | mean AR over tuning years x seeds (deployment backtest) | n/a | 4 | 2 | n/a | 0.0 | n/a |
| ridge | TREND | equal-weight index of the universe | rule (grid) | n/a | n/a | 2020 | mean AR over tuning years x seeds (deployment backtest) | n/a | 4 | 2 | n/a | 0.0 | n/a |

## Best criterion value after n trials (trial order = draw order)

| base | method | criterion | n=5 | n=10 | n=20 | n=30 | n=T | chosen trial |
|---|---|---|---|---|---|---|---|---|
| lgbm | BASE | mean validation RankIC | n/a | n/a | n/a | n/a | 0.0521739 | 1 |
| lgbm | BASE-V | V | n/a | n/a | n/a | n/a | -0.00314884 | 1 |
| lgbm | LOSS(+Z_H) | V | n/a | n/a | n/a | n/a | 0.00369813 | 2 |
| lgbm | LOSS(+Z_H+Z_O*) | V | n/a | n/a | n/a | n/a | 0.00327256 | 2 |
| lgbm | LOSS(+Z_O) | V | n/a | n/a | n/a | n/a | 0.0030679 | 1 |
| lgbm | LOSS(+Z_O*) | V | n/a | n/a | n/a | n/a | 0.00298719 | 2 |
| lgbm | LOSS(+perm Z_H) | V | n/a | n/a | n/a | n/a | 0.00357768 | 2 |
| lgbm | LOSS(+perm Z_O*) | V | n/a | n/a | n/a | n/a | 0.00354542 | 3 |
| lgbm | LOSS(-Z) | V | n/a | n/a | n/a | n/a | 0.0037515 | 2 |
| lgbm | LOSS-LR(-Z) | V | n/a | n/a | n/a | n/a | 0.00386903 | 2 |
| lgbm | NET-K(+Z_H) | V | n/a | n/a | n/a | n/a | 0.00384498 | 3 |
| lgbm | NET-K(+Z_O*) | V | n/a | n/a | n/a | n/a | 0.00306283 | 1 |
| lgbm | NET-K(-Z) | V | n/a | n/a | n/a | n/a | 0.00365195 | 3 |
| lgbm | NET-U(-Z) | theta_sel | n/a | n/a | n/a | n/a | 0.00031297 | 3 |
| lgbm | NET-U15(-Z) | V | n/a | n/a | n/a | n/a | 0.00311962 | 1 |
| lgbm | PERF | mean AR over tuning years x seeds | n/a | n/a | n/a | n/a | 0.0976562 | 2 |
| lgbm | TREND | mean AR over tuning years x seeds | n/a | n/a | n/a | n/a | 0.050072 | 0 |
| ridge | BASE | mean validation RankIC | n/a | n/a | n/a | n/a | 0.059221 | 0 |
| ridge | BASE-V | V | n/a | n/a | n/a | n/a | -0.002302 | 1 |
| ridge | LOSS(+Z_H) | V | n/a | n/a | n/a | n/a | 0.00403785 | 1 |
| ridge | LOSS(+Z_H+Z_O*) | V | n/a | n/a | n/a | n/a | 0.0042948 | 2 |
| ridge | LOSS(+Z_O) | V | n/a | n/a | n/a | n/a | 0.00401972 | 3 |
| ridge | LOSS(+Z_O*) | V | n/a | n/a | n/a | n/a | 0.0044302 | 2 |
| ridge | LOSS(+perm Z_H) | V | n/a | n/a | n/a | n/a | 0.00404487 | 0 |
| ridge | LOSS(+perm Z_O*) | V | n/a | n/a | n/a | n/a | 0.00426597 | 2 |
| ridge | LOSS(-Z) | V | n/a | n/a | n/a | n/a | 0.00393437 | 1 |
| ridge | LOSS-LR(-Z) | V | n/a | n/a | n/a | n/a | 0.00505005 | 2 |
| ridge | NET-K(+Z_H) | V | n/a | n/a | n/a | n/a | 0.00422566 | 3 |
| ridge | NET-K(+Z_O*) | V | n/a | n/a | n/a | n/a | 0.00342009 | 2 |
| ridge | NET-K(-Z) | V | n/a | n/a | n/a | n/a | 0.00385662 | 3 |
| ridge | NET-U(-Z) | theta_sel | n/a | n/a | n/a | n/a | 0.000426873 | 2 |
| ridge | NET-U15(-Z) | V | n/a | n/a | n/a | n/a | 0.00229786 | 3 |
| ridge | PERF | mean AR over tuning years x seeds | n/a | n/a | n/a | n/a | 0.110487 | 1 |
| ridge | TREND | mean AR over tuning years x seeds | n/a | n/a | n/a | n/a | 0.0577131 | 2 |
