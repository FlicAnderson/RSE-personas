"""Functions to add statistically appropriate noise to data for evaluation experiments."""

import numpy as np


def noised_X_train(
    X_train: np.ndarray,  # matrix of columns of RSE interactions data Repository Contibutions values, each column has different means and std deviations and represents different variable
    random_seed: int = 42,
    percent_of_data_to_noise: float = 0.0,  # this applies to the whole dataset, but will be applied columnwise.
    std_dev_scale: float = 1.0,  # the amount to multiply standard deviation of each column by (default:1 = 100% of existing stddev)
):
    random_generator = np.random.default_rng(random_seed)
    print(
        f"Using random number generator: {random_generator} with random seed {random_seed}"
    )

    n_to_change = round(len(X_train) * percent_of_data_to_noise)
    print(
        f"Adding noise to: {n_to_change} rows in each column; columns have {len(X_train)} rows in total."
    )

    for column in range(X_train.shape[1]):
        # for each column in all the df's 10 columns:

        # get the column's standard deviation and mean
        col = X_train[:, column]

        col_mean = col.mean()
        print(f"Mean of column {column} is: {col_mean}")

        col_std = col.std()
        print(f"StdDev of column is: {col_std}")

        # randomly choose row indices to change by adding random values
        replace_these_indices = random_generator.choice(
            len(col), size=n_to_change, replace=False
        )
        # X_train[column][indices] will be the index of the cell to replace each time
        # print(f"Replace indices: {replace_these_indices}")

        generated_noise = random_generator.normal(
            # this generates data with a normal distribution with mean matching column, and scale match
            loc=col_mean,  #  μ (mean),
            scale=col_std
            * std_dev_scale,  # σ (standard dev) multiplied by a scaler value float supplied as arg,
            size=n_to_change,  # size = number of values to generate (equivalent to len(replace_these_indices))
        )
        # use the generated noise values to overwrite the current values.
        # replace all indices identified with generated noise
        col[replace_these_indices] = generated_noise[
            :
        ]  # this OVERWRITES/updates X_train values!!

        col_mean = col.mean()
        print(f"NEW Mean of column {column} is: {col_mean}")
        col_std = col.std()
        print(f"NEW StdDev of column is: {col_std}")

    print("Noise generation loop completed")

    return X_train
