"""Functions to add statistically appropriate noise to data for evaluation experiments."""

import numpy as np


def generate_noise(original_matrix, noise_percentage: float):
    # Get stats and dimensions
    means = np.mean(original_matrix, axis=0)
    stds = np.std(original_matrix, axis=0)
    row_count, col_count = original_matrix.shape

    noise_cols = []

    # Calculate how many rows should remain UNCHANGED (0 noise)
    # If noise_percentage is 10, we want 90% of rows to be 0
    num_to_keep_clean = int(row_count * (1 - (noise_percentage / 100)))

    for i in range(col_count):
        # Generate full Gaussian noise for the column
        column_noise = np.random.normal(loc=means[i], scale=stds[i], size=row_count)

        # Pick random indices to "zero out" (the clean rows)
        clean_indices = np.random.choice(
            row_count, size=num_to_keep_clean, replace=False
        )

        column_noise[clean_indices] = 0
        noise_cols.append(column_noise)

    noise_matrix = np.column_stack(noise_cols)
    print()
    print(noise_matrix)
    print()

    # Return original matrix with random noise added
    return original_matrix + noise_matrix


matrix = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [0, 1, 2, 3]])
print()
print(matrix)
print(generate_noise(matrix, 0.1))
