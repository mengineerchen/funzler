#!usr/bin/Python3
"""
This script prompts measurement update and reruns the inference which has already run by './funzler_start.py'.
Hence, prerequisite is that a run is already started and a _tmp_output.csv already generated in this folder.
"""

import warnings
import numpy as np
import pandas as pd
from pandas.core.common import SettingWithCopyWarning
warnings.simplefilter(action="ignore", category=SettingWithCopyWarning)
import yaml
from funzler_start import explanability_check, run


def prompt_and_update_meas(input_df):
    """
    Prompt user updates on measurement and update measurement column in input_df.
    :param input_df: input dataframe for measurement update process
    """
    # user input (new_meas_array) format: [id value id value id value ...]
    new_meas_array = np.fromstring(
        input("Enter updated boundary measurement:"), dtype=float, sep=' ')
    # TODO currently no exception handling
    n_meas = int(new_meas_array.shape[0]/2)
    meas = input_df[["measurement", "meas_type"]].values
    for i in range(n_meas):
        meas[int(new_meas_array[2*i]), :] = [new_meas_array[2*i+1], "manual"]
    input_df[["measurement", "meas_type"]] = meas


def update():
    """Execute a measurement update procedure."""
    # Load input and output dataframes from the last run
    input_df = pd.read_csv('_tmp_input.csv').drop(columns=['Unnamed: 0'])
    # Convert input configs into a dict
    param_dict = yaml.safe_load(input_df["configs"][2])
    input_df["configs"][2] = param_dict

    # Prompt user updates for measurement and re-run
    prompt_and_update_meas(input_df)
    run(input_df)


if __name__ == "__main__":
    update()
