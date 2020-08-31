#!usr/bin/Python3

import pandas as pd
import numpy as np
from .helpers import convert_obs_user_to_obs, transpose_obs, prepare_2combi

class FunzlerInference(object):
    def __init__(self, df):
        self.observation = df.observation[df.observation.notnull()].values
        self.measurement = df.measurement.values
        self.csa = df.filter(regex='u_ev', axis=1).values
        self.params = df.configs[2]
        self._get_intensity_matrix()
        self.csa_2combi = []
        self.bouc_2combi = []
        self.df = pd.DataFrame()
    
    def run(self):
        """
        run the inference: search for single boundary solution,
        and double boundary solution, if needed
        """
        # prepare observation row vector
        obs = convert_obs_user_to_obs(self.observation)
        
        # search for single boundary solution
        indices_single = self.compute_indices(obs)
        self.df = pd.DataFrame(indices_single)
        self.df["bouc_id"] = self.df.index

        # search for double boundary solution, if needed
        if np.amax(indices_single["plausibility"]) < self.params["thres_find_double_bouc"]:
            self.csa_2combi, self.bouc_2combi = prepare_2combi(self.csa * self.int_1_single)
            self._get_intensity_matrix("double")
            indices_double = self.compute_indices(obs, "double")
            df_2combi=pd.DataFrame(indices_double)
            self.df = self.df.join(df_2combi, how='right', rsuffix='_2combi')
            self.df["2combi_bouc_left"] = self.bouc_2combi[:,0]
            self.df["2combi_bouc_right"] = self.bouc_2combi[:,1]
    
    def _get_intensity_matrix(self, inf_type="single"):
        """
        analyze measurement and generate intensity matrix based on inf_type
        :param inf_type: single, double
        """
        n_bouc = self.measurement.shape[0]
        n_ev = self.observation.shape[0]

        if inf_type == "single":  # int_0 and int_1 created based on csa and meas
            int_0 = np.zeros(self.csa.shape)
            int_1 = int_0 + 1
            for i in range(n_bouc):
                for j in range(n_ev):
                    if self.csa[i, 2*j] > 0:
                        int_0[i, 2*j:(2*j+2)] = self.measurement[i,]
                        int_1[i, 2*j:(2*j+2)] = int_0[i, 2*j:(2*j+2)]
            self.int_0_single = int_0
            self.int_1_single = int_1

        elif inf_type == "double":  # int_0 and int_1 created based on csa, but no meas
            int_0 = np.zeros((int((n_bouc*n_bouc-n_bouc)/2),n_ev*2))
            int_1 = int_0 + 1
            for i in range(int_0.shape[0]):
                for j in range(n_ev):
                    if self.csa_2combi[i, 2*j] > 0:
                        int_0[i, 2*j:(2*j+2)] = 1
            self.int_0_double = int_0
            self.int_1_double = int_1
    
    def compute_indices(self,obs,inf_type="single"):
        """
        Main method for computing plausibility
        :return indices: dict of output indices
        """
        # prepare adapted relation matrix (csa)
        if inf_type == "single":
            csa_int_0 = self.csa * self.int_0_single
            csa_int_1 = self.csa * self.int_1_single
        elif inf_type == "double":
            csa_int_0 = self.csa_2combi * self.int_0_double
            csa_int_1 = self.csa_2combi * self.int_1_double

        # calculate consistency index
        obsT = transpose_obs(obs)
        min_csa_obsT = np.minimum(csa_int_1, obsT)
        cons = 1 - np.amax(min_csa_obsT, axis=1)
        # calculate relevance index
        min_csa_obs = np.minimum(csa_int_0, obs)
        rel = np.minimum(cons, np.amax(min_csa_obs, axis=1))
        # calculate cover index
        compare_csa_obs = np.maximum(csa_int_1, csa_int_1>=obs)
        cov = np.minimum(cons, np.amin(compare_csa_obs, axis=1))
        # calculate plausibility
        plausi= (cons + rel + cov)/3
        indices = {"plausibility":plausi, "consistency":cons, "relevance":rel, "cover":cov}
        
        return indices