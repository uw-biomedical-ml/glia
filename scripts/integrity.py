import glia
import matplotlib.pyplot as plt
import numpy as np
from functools import partial
from warnings import warn

def plot_spike_trains(axis_gen,data,prepend_start_time=1,append_lifespan=1):
    ax = next(axis_gen)
    trial = 0
    for v in data:
        # print(type(v))
        stimulus, spike_train = (v["stimulus"], v["spikes"])
        lifespan = stimulus['lifespan'] / 120
        if lifespan > 20:
            print("skipping stimulus longer than 20 seconds")
            continue
        if spike_train.size>0:
            glia.draw_spikes(ax, spike_train, ymin=trial+0.3,ymax=trial+1)
        
        stimulus_end = prepend_start_time + lifespan
        duration = stimulus_end + append_lifespan
        ax.fill([0,prepend_start_time,prepend_start_time,0],
                [trial,trial,trial+1,trial+1],
                facecolor="gray", edgecolor="none", alpha=0.1)
        ax.fill([stimulus_end,duration,duration,stimulus_end],
                [trial,trial,trial+1,trial+1],
                facecolor="gray", edgecolor="none", alpha=0.1)
        trial += 1
        
    ax.set_title("Unit spike train per SOLID")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("trials")


def save_unit_spike_trains(units, stimulus_list, c_add_unit_figures, c_add_retina_figure, prepend, append):
    print("Creating solid unit spike trains")
    
    get_solid = glia.compose(
        glia.f_create_experiments(stimulus_list,prepend_start_time=prepend,append_lifespan=append),
        glia.f_has_stimulus_type(["SOLID"]),
    )
    response = glia.apply_pipeline(get_solid,units)
    plot_function = partial(plot_spike_trains,prepend_start_time=prepend,append_lifespan=append)
    result = glia.plot_units(plot_function,response,ncols=1,ax_xsize=10, ax_ysize=5)
    c_add_unit_figures(result)
    glia.close_figs([fig for the_id,fig in result])