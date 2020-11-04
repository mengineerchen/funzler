#!usr/bin/Python3
"""
Some helper functions for functional deficiency diagnosis.
"""
import numpy as np


def convert_obs_user_to_obs(obs_user):
    """
    Converter of the user input observation to the observation vector required by the inference algorithm.
    :param obs_user: valued by {"certainly present": 1, "unkonwn": 0, "certainly absent": -1}
    :return obs: valued by {"certainly present": [1, 0], "unkonwn": [0, 0], "certainly absent": [0, 1]}
    """
    n_ev = obs_user.shape[0]
    obs = np.zeros((1, 2*n_ev))
    for i in range(n_ev):
        obs[0, i*2] = max(0, obs_user[i])
        obs[0, i*2 + 1] = abs(min(0, obs_user[i]))
    return obs


def transpose_obs(obs):
    """
    Function for manupulating observation vector, which is used for computing consistency index.
    :param obs: observation array with the shape (1, n_ev*2)
    :returen obsT: "plus" and "minus" columns in obs matrix are exchanged
    """
    n_ev = int(obs.shape[1] / 2)
    obsT = np.zeros((1, 2*n_ev))
    for i in range(n_ev):
        obsT[0, i*2] = obs[0, i*2+1]
        obsT[0, i*2+1] = obs[0, i*2]
    return obsT


def prepare_2combi(csa_int):
    """
    Generate a relation matrix for double boundary combinations from the single boundary relation matrix.
    This is preparation for double boundary inference.
    :param csa_int: adapted causal relation matrix (with intensity matrix)
    :return csa_2combi: causal relation matrix for all boundary combinations
    :return bouc_2combi: mapping between bouc combination id (in csa_2combi) and bouc id (in csa)
    """
    n_ev = int(csa_int.shape[1]/2)
    n_bouc = csa_int.shape[0]
    n_bouc_2combi = int((n_bouc*n_bouc - n_bouc)/2)
    bouc_2combi = np.zeros((n_bouc_2combi, 2))
    csa_2combi = np.zeros((n_bouc_2combi, 2*n_ev))

    # consruct relation matrix based purely on max/min operation
    row_count = 0
    for i in range(n_bouc-1):
        for j in range(i+1, n_bouc):
            for z in range(n_ev):
                csa_2combi[row_count, 2 *
                           z] = max(csa_int[i, 2*z], csa_int[j, 2*z])
                csa_2combi[row_count, 2*z +
                           1] = min(csa_int[i, 2*z+1], csa_int[j, 2*z+1])
            bouc_2combi[row_count, 0] = i
            bouc_2combi[row_count, 1] = j
            row_count = row_count + 1

    return csa_2combi, bouc_2combi


def advise_boucmeas(input_df, output_df):
    """
    Analyze two dataframes and add impact of boundary measurement into output_df
    :param input_df: input data for inference
    :param output_df: output data from inference
    """
    thres_boucmeas_advice = input_df["configs"][2]["thres_boucmeas_advice"]
    n_bouc = input_df["bo in uc"].shape[0]
    meas_type = input_df.meas_type.values
    plausibility = output_df.plausibility.values
    double_done = "plausibility_2combi" in output_df.columns
    if double_done:
        plausibility_2combi = output_df.plausibility_2combi.values
        n_bouc_2combi = output_df["plausibility_2combi"].shape[0]
        bouc_2combi_left = output_df["2combi_bouc_left"].values
        bouc_2combi_right = output_df["2combi_bouc_right"].values
    output_df.insert(5, "impact_boucmeas", None)

    # given a boundary, analyze all solutions including this boundary
    for i in range(n_bouc):
        if meas_type[i] != "default":
            continue
        # get relevant single boundary solution plausi sum
        impact_single = plausibility[i]
        check_enough_plausi = (impact_single >= thres_boucmeas_advice)
        # get relevant double boundary solution plausi sum
        impact_double = 0
        if double_done:
            for j in range(n_bouc_2combi):
                if bouc_2combi_left[j] == i or bouc_2combi_right[j] == i:
                    impact_double = impact_double + plausibility_2combi[j]
                    check_enough_plausi = check_enough_plausi or \
                        (plausibility_2combi[j] >= thres_boucmeas_advice)
        impact_boucmeas = (impact_single + impact_double) * check_enough_plausi
        output_df.impact_boucmeas.iloc[i] = impact_boucmeas


def visualize(input_df, output_df):
    """ print some info to terminal for user inspection."""

    label = output_df.label[0]

    # n_showhypo = input_df.configs[2]["n_showhypo"]
    n_advisemeas = input_df.configs[2]["n_advisemeas"]
    # thres_showhypo = input_df.configs[2]["thres_showhypo"]

    bouc_description = input_df["bo in uc"].values

    meas_suggestion_data = output_df[["bouc_id", "impact_boucmeas"]]\
        .sort_values(by="impact_boucmeas", ascending=False).values

    done_2combi = "plausibility_2combi" in output_df.columns
    max_plausi = output_df.plausibility_2combi.max(axis=0) if done_2combi \
        else output_df.plausibility.max(axis=0)
    idx_max = output_df.plausibility_2combi.idxmax(axis=0) if done_2combi \
        else output_df.plausibility.idxmax(axis=0)
    bouc_ids = [output_df["2combi_bouc_left"][idx_max], output_df["2combi_bouc_right"][idx_max]] if done_2combi\
        else output_df["bouc_id"][idx_max]

    print("****************Results***************")
    print(label)
    if label == "fail known":
        if done_2combi:
            print("The most plausible solution: plausi=%g, %s (id %d) & %s (id %d)" % (max_plausi, bouc_description[int(bouc_ids[0])],
                                                                                       bouc_ids[0], bouc_description[int(bouc_ids[1])], bouc_ids[1]))
        else:
            print("The most plausible solution: plausi=%g, %s (id %d)" %
                  (max_plausi, bouc_description[int(bouc_ids)], bouc_ids))
    elif label == "fail pending":
        print("measurement suggestion:")
        for i in range(n_advisemeas):
            if meas_suggestion_data[i, 1] == 0:
                break
            print("id {}, worthiness {}: ".format(int(meas_suggestion_data[i, 0]), round(meas_suggestion_data[i, 1],2)) \
                + bouc_description[int(meas_suggestion_data[i, 0])])
    print("******************End*****************")
