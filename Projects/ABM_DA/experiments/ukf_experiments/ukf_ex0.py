#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 11:49:27 2019

Experiment 0 module. Similar ideas to experiment 1 but keep prop fixed at 1
and vary noise/sample_rate

@author: rob
"""

import sys

from ukf_fx import fx
from ukf_plots import L2s
from default_ukf_configs import model_params,ukf_params
from ukf_ex1 import obs_key_func, omission_index, hx1
sys.path.append("../../stationsim")
from ukf2 import ukf_ss, pickler, depickler
from stationsim_model import Model

import numpy as np
from math import floor

def ex0_params(n, noise, sample_rate, model_params = model_params, ukf_params=ukf_params):
    
    
    """update ukf_params with fx/hx and their parameters for experiment 1
    
    Parameters
    ------
    ukf_params : dict
        
    Returns
    ------
    ukf_params : dict
    """
    model_params["pop_total"] = n
    ukf_params["noise"] = noise
    ukf_params["sample_rate"] = sample_rate
    
    ukf_params["p"] = np.eye(2 * n) #inital guess at state covariance
    ukf_params["q"] = np.eye(2 * n)
    ukf_params["r"] = np.eye(2 * n)#sensor noise
    
    ukf_params["fx"] = fx
    ukf_params["hx"] = hx0    
    ukf_params["obs_key_func"] = None
    
    ukf_params["file_name"] = f"config_agents_{n}_rate_{sample_rate}_noise_{noise}"
    ukf_params["do_forecasts"] = True
    
    return model_params, ukf_params

def hx0(state, model_params, ukf_params):
    "do nothing for hx. two states are the same."
    return state


def ex0_save(instance,source):
    
    obs,preds,forecasts,truths,nan_array= instance.data_parser()
    truths *= nan_array
    preds *= nan_array
    forecasts *= nan_array
    
    truths = truths[::instance.sample_rate,:]
    preds = preds[::instance.sample_rate,:]
    forecasts = forecasts[::instance.sample_rate,:]

    errors = {}
    errors["obs"] = L2s(truths,obs)
    obs_error = np.nanmedian(np.nanmedian(errors["obs"],axis=0))
    errors["forecasts"] = L2s(truths,forecasts)
    forecast_error = np.nanmedian(np.nanmedian(errors["forecasts"],axis=0))
    errors["ukf"] = L2s(truths,preds)
    ukf_error =  np.nanmedian(np.nanmedian(errors["ukf"],axis=0))
    
    mean_array = np.array([obs_error, forecast_error, ukf_error])
    np.save(source + ukf_params["file_name"], mean_array)
    
def ex0_main():

    n= 5
    noise = 0.5
    sampling_rate = 5
    model_params, ukf_params = ex0_params(n, noise, sampling_rate)
    print(model_params)
    print(ukf_params)
    
    base_model = Model(**model_params)
    u = ukf_ss(model_params,ukf_params,base_model)
    u.main()
    ex0_save(u,"")
  
#%%  
    
if __name__ == "__main__":
    ex0_main()
    
    
    
    