#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 09:50:10 2019

@author: rob

!!rewrite this 

Produces more generalised diagnostic over multiple runs using multiple
numbers of agents for arc_ukf.py only. This produces a chloropleth style map 
showing the grand median error over both time and agents for various fixed numbers of agents 
and proportions observed.


import data from arc with following in bash terminal
scp medrclaa@arc3.leeds.ac.uk:/nobackup/medrclaa/dust/Projects/ABM_DA/experiments/ukf_experiments/ukf_results/agg* /home/rob/dust/Projects/ABM_DA/experiments/ukf_experiments/ukf_results/.
change to relevant directories

"""

import pickle
import sys
#sys.path.append("../../stationsim")
sys.path.append("../..")

from ukf_plots import L2s as L2_parser

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.cm as cm
import matplotlib.patheffects as pe
import matplotlib.colors as colors
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.lines as lines

import glob
import seaborn as sns
import pandas as pd


#%%
class grand_plots:
    
    
    """class for results of multiple ukf runs
    
    """

    def __init__(self,params, save, restrict = None, **kwargs):
        """initialise plot class
        
        Parameters
        ------
        params : dict
            `params` dictionary defines 2 parameters to extract data over 
            and a file source.
            
            e.g.
            depickle_params = {
                    "agents" :  [10,20,30],
                    "bin" : [5,10,25,50],
                    "source" : "/media/rob/ROB1/ukf_results/ukf_",
            }
            Searches for files with 10,20, and 30 "agents" (population size) 
            and 5, 10, 25, and 50 experiment 2 square grid size "bin".
            It extracts theres files from the source.
            Please be careful with this as it 
        
        save : bool
            `save` plots?
            
        restrict : func
            `restrict` function allows you to split up the distances data you
            plot. For example, in experiment 1 we have an observed/unobserved data
            split. This function allows you to restrict the plotting to observed
            or unobserved plotting only so we can properly observe the split. 
            
            The aim is to get this working with obs_array for new pickles 
            such that one can plot unobserved/ aggregate/observed depickle plots
            all separately.
            
        **kwargs : **kwargs
            `kwargs` keywords arguements for restrict function. For example,
            ex1_restrict is the restrict function for experiment 1. It needs a 
            boolean determining whether to plot observed/unobserved. This is 
            just a generalised version so we can hopefully work with both this
            current version for old pickles and the obs_array stuff for new pickles.
        """
        self.param_keys = [key for key in params.keys()]
        self.p1 = params[self.param_keys[0]]
        self.p2 = params[self.param_keys[1]]
        self.source = params["source"]
        self.save = save
        self.restrict = restrict
        self.kwargs = kwargs
     
    def numpy_parser(self):
        """ if data is in numpy form (see experiment 0)
        do the same thing as depickle_data_parser but with numpy arrays
        """
        keys = self.param_keys
        errors = {}
        for i in self.p1:
            
            errors[i] = {}
            
            for j in self.p2:
                
                f_name = self.source + f"{keys[0]}_{i}_{keys[1]}_{j}*"
                files = glob.glob(f_name)
                
                errors[i][j] = []
                
                for file in files:
                    errors[i][j].append(np.load(file))
                    
                
        return errors
    
    def numpy_extractor(self, L2s):
        "convert L2s from numpy arrays into pandas table"
        keys = self.param_keys
        columns = [keys[0],keys[1],"obs","forecasts","ukf"]
        frame = pd.DataFrame(columns = columns)
        for i in self.p1:
            for j in self.p2:
                data = L2s[i][j]
                for item in data:
                    new_row = pd.DataFrame([[float(i),float(j)]+list(item)], columns = columns)
                    frame = pd.concat([frame,new_row])
        
        "aggregate by rate then noise using median"
        frame = frame.groupby(by = ["rate","noise"]).median()
        best = frame.idxmin(axis=1) #which estiamtes are closest to the truth
        
        best.loc[best=="obs"] = 0
        best.loc[best=="forecasts"] = 1
        best.loc[best=="ukf"] = 2
        
        frame["best"] = best
        
        best_array= np.zeros(shape = (len(self.p1),len(self.p2)))
        for i , x in enumerate(self.p1):
            for j, y in enumerate(self.p2):
                best_array[i,j] = int(L2_frame.loc[x].loc[y]["best"])
                
        return frame, best_array
                
    def comparison_choropleth(self, n, data, xlabel, ylabel, title):
        """plot choropleth style for which is best our obs forecasts and ukf
    
        Parameters
        ------
        data2,best_array : array_like
            `data2` and `best_array` defined above
        
        n,rates,noises: list
            `n` `rates` `list` lists of each parameter defined above
        save : bool
            `save` plot?
        """
        
        f,ax = plt.subplots(figsize=(8,8))
        "cbar axis"
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right",size="5%",pad=0.05)
        colours = ["yellow","orangered","skyblue"]
        "custom discrete 3 colour map"
        cmap = colors.ListedColormap(colours)
        cmaplist = [cmap(i) for i in range(cmap.N)]
        cmap = colors.LinearSegmentedColormap.from_list("custom_map",cmaplist,cmap.N)
        bounds = [0,1,2,3]
        norm = colors.BoundaryNorm(bounds,cmap.N)
        
        "imshow plot and colourbar"
        im = ax.imshow(data,origin="lower",cmap = cmap,norm=norm)
        #"""alternative continous contour plot idea for more "spatially real" mapping"""
        #grid = np.meshgrid(noises,rates)
        #im = plt.contourf(grid[0],grid[1],best_array,cmap=cmap,levels=[0,1,2,3])
        plt.ylim([0,2])
        cbar = plt.colorbar(im,cax=cax,ticks=np.arange(0,len(bounds)-1,1)+0.5,boundaries = [0,1,2,3])
        cbar.set_label("Best Error")
        cbar.set_alpha(1)
        cbar.draw_all()
        
        "labelling"
        cbar.set_ticklabels(("Obs","Preds","UKF"))
        ax.set_xticks(np.arange(len(self.p2)))
        ax.set_yticks(np.arange(len(self.p1)))
        ax.set_xticklabels(self.p2)
        ax.set_yticklabels(self.p1)
        ax.set_xticks(np.arange(-.5,len(self.p2),1),minor=True)
        ax.set_yticks(np.arange(-.5,len(self.p1),1),minor=True)
        ax.grid(which="minor",color="k",linestyle="-",linewidth=2)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        if self.save:
            plt.savefig("plots/" + f"{n}_base_config_test.pdf")

    def comparisons_3d(self, n, data, best_array):
        
        
        """3d version of plots 2 based on Minh's code
        
            Parameters
            ------
            data2,best_array : array_like
                `data2` and `best_array` defined above
            
            n,rates,noises: list
                `n` `rates` `list` lists of each parameter defined above
            save : bool
                `save` plot?
            """
        #first make list of plots
        colours = ["yellow","orangered","skyblue"]
    
        "init and some labelling"
        fig = plt.figure(figsize = (12,12))
        ax = fig.add_subplot(111,projection='3d')
        ax.set_xlabel('Observation Noise', labelpad = 20,fontsize = 22)
        ax.set_ylabel("Assimilation Rate", labelpad = 20)
        ax.set_zlabel('Grand L2 Error')
        ax.view_init(30,225)
        
        "take each rate plot l2 error over each noise for preds obs and ukf"
        for i,rate in enumerate(self.p1):
            sub_data = data.loc[rate]
            preds=list(sub_data["forecasts"])
            ukf=list(sub_data["ukf"])
            obs=list(sub_data["obs"])
            
            xs = np.arange(len(self.p2))
            ys = [i]*len(self.p2)
            l1=ax.plot(xs= xs, ys=ys, zs=obs,color=colours[0], linewidth=4,
                    path_effects=[pe.Stroke(linewidth=6, foreground='k',alpha=1), pe.Normal()],alpha=0.8)
            
            l2=ax.plot(xs= xs, ys= ys,zs=preds,color=colours[1],linewidth=4,
                       linestyle = "-.", path_effects=[pe.Stroke(linewidth=6, foreground='k'
                        ,alpha=1), pe.Normal()],alpha=0.6)
            l3=ax.plot(xs= xs, ys= ys, zs=ukf, color=colours[2], linewidth=4,
                       linestyle = "--",path_effects=[pe.Stroke(offset=(2,0),linewidth=6,
                        foreground='k',alpha=1), pe.Normal()],alpha=1)
                 
        "placeholder dummies for legend"
        s1=lines.Line2D([-1],[-1],color=colours[0],label="obs",linewidth=4,linestyle = "-",
                    path_effects=[pe.Stroke(linewidth=6, foreground='k',alpha=1), pe.Normal()])
        s2 = lines.Line2D([-1],[-1],color=colours[1],label="preds",linewidth=4,linestyle = "-.",
                    path_effects=[pe.Stroke(linewidth=6, foreground='k',alpha=1), pe.Normal()])
        s3 = lines.Line2D([-1],[-1],color=colours[2],label="ukf",linewidth=4,linestyle = "--",
                    path_effects=[pe.Stroke(offset=(2,0),linewidth=6, foreground='k',alpha=1), pe.Normal()])
    
        "rest of labelling"
        ax.set_xticks(np.arange(0,len(self.p2)))
        ax.set_xticklabels(self.p2)
        ax.set_yticks(np.arange(0,len(self.p1)))
        ax.set_yticklabels(self.p1)
        ax.legend([s1,s2,s3],["obs","preds","ukf"])
        plt.tight_layout()
        "save?"
        if self.save:
            plt.savefig("plots/" + f"3d_{n}_error_trajectories.pdf")

    
    def depickle_data_parser(self,instance):
        
        
        """simplified version of ukf.data_parser. just pulls truths/preds
        
        Returns
        ------
            
        truth : array_like
            `a` noisy observations of agents positions
        preds : array_like
            `b` ukf predictions of said agent positions
        """
        
        """pull actual data. note a and b dont have gaps every sample_rate
        measurements. Need to fill in based on truths (d).
        """
        truth =  np.vstack(instance.truths) 
        preds2 = np.vstack(instance.ukf_histories)
        
        "full 'd' size placeholders"
        preds= np.zeros((truth.shape[0],instance.pop_total*2))*np.nan
        
        "fill in every sample_rate rows with ukf estimates and observation type key"
        "!!theres probably an easier way to do this"
        for j in range(int(preds.shape[0]//instance.sample_rate)):
            preds[j*instance.sample_rate,:] = preds2[j,:]
        
        nan_array = np.ones(shape = truth.shape,)*np.nan
        for i, agent in enumerate(instance.base_model.agents):
            array = np.array(agent.history_locations)
            index = np.where(array !=None)[0]
            nan_array[index,2*i:(2*i)+2] = 1
        
        return truth*nan_array, preds*nan_array
    
    
    def data_extractor(self):
        """pull multiple class runs into arrays for analysis
        
        This is function looks awful... because it is. 
        Heres what it does:
            
        - build grand dictionary L2
        - loop over first parameter e.g. population size
            - create sub dictionary for given i L2[i]
            - loop over second parameter e.g. proportion observed (prop)
                - create placeholder list sub_L2 to store data for given i and j.
                - load each ukf pickle with the given i and j.
                - for each pickle extract the data, calculate L2s, and put the 
                    grand median L2 into sub_L2.
                - put list sub_L2 as a bnpy array into 
                dictionary L2[i] with key j.
        
        This will output a dictionary where for every pair of keys i and j , we accquire
        an array of grand medians.
        """
        "names of first and second parameters. e.g. agents and prop"
        keys = self.param_keys
        "placeholder dictionary for all parameters" 
        L2 = {}
        "loop over first parameter. usually agents."
        for i in self.p1:
            print(i)
            "sub dictionary for parameter i"
            L2[i] = {} 
            for j in self.p2:
                "file names for glob to find. note wildcard * is needed"
                f_name = self.source + f"{keys[0]}_{i}_{keys[1]}_{j}-*"
                "find all files with given i and j"
                files = glob.glob(f_name)
                "placeholder list for grand medians of UKF runs with parameters i and j"
                sub_L2=[]
                for file in files:
                    "open pickle"
                    f = open(file,"rb")
                    u = pickle.load(f)
                    f.close()
                    "pull raw data"
                    truth, preds = self.depickle_data_parser(u)
                    "find L2 distances"
                    distances = L2_parser(truth[::u.sample_rate,:], 
                                          preds[::u.sample_rate,:])
                    if self.restrict is not None:
                        distances = self.restrict(distances, u, self.kwargs)
                    
                    "add grand median to sub_L2"
                    sub_L2.append(np.nanmedian(np.nanmedian(distances,axis=0)))
                    "stack list of grand medians as an nx1 vector array"
                    "put array into grand dictionary with keys i and j"
                L2[i][j] = np.hstack(sub_L2)
           
        return L2
    
    def data_framer(self,L2):
        sub_frames = []
        keys = self.param_keys
        for i in self.p1:
            for j in self.p2:
                "extract L2s from L2 dictionary with corresponding i and j."
                L2s = L2[i][j]
                sub_frames.append(pd.DataFrame([[i]*len(L2s),[j]*len(L2s),L2s]).T)
    
        "stack into grand frames and label columns"
        error_frame = pd.concat(sub_frames)
        error_frame.columns = [keys[0], keys[1], "Grand Median L2s"]
    
        self.error_frame = error_frame

    def choropleth_array(self):
        
        
        """converts pandas frame into generalised numpy array for choropleth
        
        """
        error_frame2 = self.error_frame.groupby(by =[str(self.param_keys[0]),str(self.param_keys[1])]).mean()
        error_array = np.ones((len(self.p1),len(self.p2)))*np.nan
        
        for  i, x  in enumerate(self.p1):
            for  j, y in enumerate(self.p2):
                error_array[i,j] = error_frame2.loc[(x,y),][0]
    
        self.error_array = error_array

    def choropleth_plot(self, xlabel, ylabel, title):
       
        
        """choropleth style plot for grand medians
        
        Parameters
        ------
        data : array_like
            L2 `data` matrix from grand_L2_matrix
        n,bin_size : float
            population `n` and square size `bin_size`
        save : bool
            `save` plot?
    
        """    
        "rotate  so population on x axis"
        data = np.rot90(self.error_array,k=1) 
        "flip so proportion goes upwards so imshow `origin=lower` is true"
        data = np.flip(data,axis=0)
        "put nan values to white"
        data2 = np.ma.masked_where(np.isnan(data),data)

        "initiate plot"
        f,ax=plt.subplots(figsize=(8,8))
        "colourmap"
        cmap = cm.viridis
        "set nan values for 100% unobserved to white (not black because black text)"
        cmap.set_bad("white") 
        
        im=ax.imshow(data2,interpolation="nearest",cmap=cmap,origin="lower")
        
        
        "text on top of squares for clarity"
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                plt.text(j,i,str(data[i,j].round(2)),ha="center",va="center",color="w",
                         path_effects=[pe.Stroke(linewidth = 0.7,foreground='k')])
        
        
        "colourbar alignment and labelling"
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right",size="5%",pad=0.05)
        cbar=plt.colorbar(im,cax,cax)
        
        "labelling"
        ax.set_xticks(np.arange(len(self.p1)))
        ax.set_yticks(np.arange(len(self.p2)))
        ax.set_xticklabels(self.p1)
        ax.set_yticklabels(self.p2)
        ax.set_xticks(np.arange(-.5,len(self.p1),1),minor=True)
        ax.set_yticks(np.arange(-.5,len(self.p2),1),minor=True)
        ax.grid(which="minor",color="k",linestyle="-",linewidth=2)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.title = title + " Choropleth"
        cbar.set_label(title + " Grand Median L2s")
        
        "save"
        if self.save:
            plt.savefig("plots/" + title + "_Choropleth.pdf")
        
    def boxplot(self, xlabel, ylabel, title):
        """produces grand median boxplot for all 30 ABM runs for choropleth plot
        
           
        Parameters
        ------
        frame : array_like
            L2 `data` matrix from grand_L2_matrix
        n,bin_size : float
            population `n` and square size `bin_size`
        save,seperate : bool
            `save` plot?
            `seperate` box plots by population or have one big catplot?
        
        """       
        keys = self.param_keys
        data = self.error_frame
        f_name = title  + "_boxplot.pdf"
        y_name = "Grand Median L2s"
        
        f = plt.figure()
        cat = sns.catplot(x=str(keys[1]),y=y_name,col=str(keys[0]),kind="box", data=data)
        plt.tight_layout()
        
        for i, ax in enumerate(cat.axes.flatten()):
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(str(keys[0]).capitalize() + " = " + str(self.p1[i]))
        plt.title = title
        if self.save:
            plt.savefig("plots/" + f_name)
       
        
      
        
        
"""parameter dictionary
parameter1: usually number of "agents"

parameter2: proportion observed "prop" or size of aggregate squares "bin" 
    int 1 here because I named the results files poorly.!! fix later using grep?"

source : "where files are loaded from plus some file prefix such as "ukf" or "agg_ukf" e.g. dust repo or a USB


"""


def ex0_grand():
    n = 30 #population size
    file_params = {
            "rate" :  [1.0, 2.0, 5.0, 10.0],
            "noise" : [0., 0.25, 0.5, 1.0, 2.0, 5.0],
            #"source" : "/home/rob/dust/Projects/ABM_DA/experiments/ukf_experiments/ukf_results/agg_ukf_",
            "source" : f"/home/rob/ukf_config_test/config_agents_{str(n).zfill(3)}_",
            }
    
    g_plts = grand_plots(file_params, True)
    L2 = g_plts.numpy_parser()
    L2_frame, best_array = g_plts.numpy_extractor(L2)
    g_plts.comparison_choropleth(n,best_array,"Observation Noise Standard Deviation",
                                 "Assimilation Rate","")
    g_plts.comparisons_3d(n, L2_frame, best_array)
    
def ex1_restrict(distances,instance, *kwargs):
    "split L2s for separate observed unobserved plots."
    try:
        observed = kwargs[0]["observed"]
    except:
        observed = kwargs["observed"] 
    index = instance.index
    
    if observed:
        distances = distances[:,index]
    elif not observed:
        "~ doesnt seem to work here for whatever reason. using delete instead"
        distances = np.delete(distances,index,axis=1)
        
    return distances
    
def ex1_grand():

    file_params = {
            "agents" :  [10,20, 30],
            "prop" : [0.25, 0.5, 0.75, int(1)],
            #"source" : "/home/rob/dust/Projects/ABM_DA/experiments/ukf_experiments/ukf_results/agg_ukf_",
            "source" : "/media/rob/ROB1/ukf_results/ukf_",
            }
    "plot observed/unobserved plots"
    obs_bools = [True, False]
    obs_titles = ["Observed", "Unobserved"]
    for i in range(len(obs_bools)):
        "initialise plot for observed/unobserved agents"
        g_plts = grand_plots(file_params, True, restrict = ex1_restrict, observed = obs_bools[i])
        "make dictionary"
        L2 = g_plts.data_extractor()
        "make pandas dataframe for seaborn"
        g_plts.data_framer(L2)
        "make choropleth numpy array"
        g_plts.choropleth_array()
        "make choropleth"
        g_plts.choropleth_plot("Numbers of Agents", "Proportion Observed",obs_titles[i])
        "make boxplot"
        g_plts.boxplot("Proportion Observed", "Grand Median L2s",obs_titles[i])
        
        
def ex2_grand():

    file_params = {
            "agents" :  [10, 20, 30],
            "bin" : [5,10,25,50],
            #"source" : "/home/rob/dust/Projects/ABM_DA/experiments/ukf_experiments/ukf_results/agg_ukf_",
            "source" : "/media/rob/ROB1/ukf_results_100_2/agg_ukf_",
            }

    "init plot class"
    g_plts = grand_plots(file_params,True)
    "make dictionary"
    L2 = g_plts.data_extractor()
    "make pandas dataframe for seaborn"
    g_plts.data_framer(L2)
    "make choropleth numpy array"
    g_plts.choropleth_array()
    "make choropleth"
    g_plts.choropleth_plot("Numbers of Agents", "Proportion Observed","Aggregate")
    "make boxplot"
    g_plts.boxplot("Grid Square Size", "Grand Median L2s", "Aggregate")

#%%
if __name__ == "__main__":
    ex0_grand()
    #ex1_grand()
    #ex2_grand()
    