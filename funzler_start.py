#!usr/bin/python3
"""
This script starts functional deficiency diagnosis tool.
It is configured in ./config/funzler.yaml
"""

import numpy as np
import pandas as pd
import yaml
from src.funzler_inference import FunzlerInference
from src.helpers import advise_boucmeas, visualize


def load_input_data():
    """
    Load the following data based on configuration (./config/funzler.yaml)
    - causal relation matrix (aka. csa)
    - event description
    - boundary description
    - observation of events
    - measurement of boundaries
    """
    # Load configuration
    with open('./config/funzler.yaml') as config_file:
        config_dict = yaml.load(config_file)
    csa_dict = config_dict["csa"]
    input_dict = config_dict["input"]
    params_dict = config_dict["params"]
    # Create dataframe from config
    df = pd.read_excel(csa_dict["kb_path"],
                       sheet_name=csa_dict["kb_sheet"],
                       skip_rows=csa_dict["skip_rows"],
                       header=csa_dict["csa_range"]["header_row_index"],
                       usecols=(csa_dict["csa_range"]["columns"] + "," +
                                csa_dict["bouc_range"]["columns"] + "," +
                                csa_dict["ev_range"]["columns"]))
    df["configs"] = None
    df.at[0, "configs"] = csa_dict
    df.at[1, "configs"] = input_dict
    df.at[2, "configs"] = params_dict
    # Collect observation and pass to dataframe
    n_ev = df["trigger-event"].count()
    df["observation"] = None
    if input_dict["obs_mode"] == "manual":
        print("event: " + df["trigger-event"][0:n_ev].values)
        obs_user = np.fromstring(
            input("Enter observation of events:"), dtype=int, sep=' ')[np.newaxis, :]
        df["observation"].iloc[0:n_ev] = obs_user[0]
    # Collect measurement and pass to dataframe
    n_bouc = df["bo in uc"].count()
    if input_dict["meas_mode"] == "manual":
        meas = np.zeros((n_bouc, 1)) + 1.0
        df["measurement"] = meas
        df["meas_type"] = "default"
    return df


def explanability_check(output_df, threshold):
    """ check explainability and define label
    :param output_df:
    :param threshold:
    :return label:
    """
    plausibility_max = output_df.plausibility.max(axis=0)
    plausibility_2combi_max = output_df.plausibility_2combi.max(axis=0) if \
        "plausibility_2combi" in output_df.columns else None
    impact_boucmeas_max = output_df.impact_boucmeas.max(axis=0)
    label = ""
    if impact_boucmeas_max > 0:
        label = "fail pending"
    elif plausibility_max < threshold and plausibility_2combi_max < threshold:
        label = "fail unknown"
    else:
        label = "fail known"

    return label


def run(input_df):
    """wrapper for run"""
    # Create and run inference session
    funzler_inference = FunzlerInference(input_df)
    funzler_inference.run()
    output_df = funzler_inference.df

    # Rank measurement impact of boundaries
    advise_boucmeas(input_df, output_df)

    # Add explainability label to dataframe
    output_df.insert(0, "label", None)
    label = explanability_check(output_df, input_df.configs[2]["thres_plausi"])
    output_df["label"].iloc[0] = label

    # Visualize results
    visualize(input_df, output_df)

    # Write dataframes to csv files
    input_df.to_csv('_tmp_input.csv')
    output_df.to_csv('_tmp_output.csv')


def main():
    input_df = load_input_data()
    run(input_df)


if __name__ == "__main__":
    main()
