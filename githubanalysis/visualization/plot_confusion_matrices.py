"""Plot a confusion matrix from ML classification results"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

from utilities.rse_persona_info_utils import RSE_personas_info


def confusion_matrix_plotter(
    y_test: pd.Series,
    y_pred: pd.Series | np.ndarray,
    model_abbrv: str,
    tuning_method: str,
    added_noise: bool,
    x_noise: float,
    y_noise: float,
    noiseSDscale: float,
    seed_no: int,
    image_write_location: str | Path,
    current_date_info: str,
    saveout_args_dpi: int = 400,
    saveout_args_format: str = "pdf",
    saveout_args_bboxin: str = "tight",
):
    # savefig kwargs
    saveout_args = dict(
        dpi=saveout_args_dpi,
        format=saveout_args_format,
        bbox_inches=saveout_args_bboxin,
    )

    if added_noise is True:
        noisestr = f"Xnoise={round(x_noise * 100)}%, ynoise={round(y_noise * 100)}%, noiseSD={(noiseSDscale * 100)}%"
    else:
        noisestr = "No Noise"

    # Plot non-normalized confusion matrix
    titles_options = [
        (
            f"{model_abbrv} with {tuning_method}: no normalization (Ntest={len(y_test)}, seed={seed_no}, {noisestr})",
            None,
        ),
        (
            f"{model_abbrv}with {tuning_method}: normalized (Ntest={len(y_test)}, seed={seed_no}, {noisestr})",
            "true",
        ),  # normalise on True value pcs
    ]

    persona_order = RSE_personas_info.cat_labels  # full names
    persona_labels = RSE_personas_info.persona_abbrevs  # abbreviated names for plotting

    files_generated = []

    for title, normalize in titles_options:
        disp = ConfusionMatrixDisplay.from_predictions(
            np.vectorize(lambda x: RSE_personas_info.name_palette.get(x))(y_test),
            np.vectorize(lambda x: RSE_personas_info.name_palette.get(x))(
                y_pred
            ),  # can't use apply as it's taking np.ndarray in...
            labels=persona_order,  # personas listed in increasing MRC order
            sample_weight=None,
            normalize=normalize,  # 'all': total N samples; 'pred': over predictions; 'true': over true; None: default
            display_labels=persona_labels,
            include_values=True,
            xticks_rotation="vertical",
            values_format=None,
            cmap=plt.cm.Blues,  # pyright: ignore[reportAttributeAccessIssue]
            # code seems to work regardless, but it relates to a colour matrix from somewhere inside matplotlib I think?
            ax=None,
            colorbar=False,
            im_kw=None,
            text_kw=None,
        )
        disp.ax_.set_title(title)
        saveout_name = Path(
            image_write_location,
            f"{model_abbrv}_{tuning_method}_seed{seed_no}_confusion_matrix_normalise{normalize}_N{len(y_test)}_{noisestr}_{current_date_info}.pdf",
        )
        plt.savefig(
            saveout_name,
            **saveout_args,
        )
        files_generated.append(saveout_name)
        plt.show()

    return files_generated
