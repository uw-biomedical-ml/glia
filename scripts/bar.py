import glia
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from functools import update_wrapper, partial

def f_get_key(i):
    return lambda item: item[i]


def plot_spike_trains(axis_gen,data):
    "assumes data is sorted by angle"
    # we will use a different axis for each speed_width & repetition
    axes = {}
    y = 0
    trial = 0
    current_angle = None
    for d in data:
        stimulus = d["stimulus"]
        spike_train = d['spikes']
        speed_width = (stimulus["speed"], stimulus["width"])
        angle = stimulus["angle"]

        if angle!=current_angle:
            trial = 0
            y += 1
            current_angle = angle
        else:
            # same angle, next trial
            trial+=1

        try:
            ax = axes[speed_width][trial]
        except:
            ax = next(axis_gen)
            if speed_width not in axes:
                axes[speed_width] = {}
            axes[speed_width][trial] = ax

        if spike_train.size>0:
            glia.draw_spikes(ax, spike_train, ymin=y+0.3,ymax=y+1)        
    for speed_width, trial in axes.items():
        for trial, ax in trial.items():
            ax.set_title("Trial: {}, Speed: {}, Width: {}".format(
                trial+1,speed_width[0], speed_width[1]))
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Bar Angle")
            ax.set_yticks(np.linspace(0,y+1,8))
            ax.set_yticklabels([0,"90°","45°","180°","225°","270°","315°","360°"])


def get_fr_dsi_osi(units, stimulus_list):

    get_bar_firing_rate = glia.compose(
        glia.f_create_experiments(stimulus_list),
        glia.f_has_stimulus_type(["BAR"]),
        glia.f_group_by_stimulus(),
        glia.f_calculate_firing_rate_by_stimulus(),
    )
    bar_firing_rate = glia.apply_pipeline(get_bar_firing_rate,units)

    get_bar_dsi = glia.compose(
        glia.by_speed_width_then_angle,
        glia.calculate_dsi_by_speed_width
    )
    bar_dsi = glia.apply_pipeline(get_bar_dsi,bar_firing_rate)

    get_bar_osi = glia.compose(
        glia.by_speed_width_then_angle,
        glia.calculate_osi_by_speed_width
    )
    bar_osi = glia.apply_pipeline(get_bar_osi,bar_firing_rate)


    return (bar_firing_rate, bar_dsi, bar_osi)


def plot_unit_response_by_angle(axis_gen, data):
    """Plot the average for each speed and width."""
    # we will accumulate by angle in this dictionary and then divide
    bar_firing_rate, bar_dsi, bar_osi = data
    analytics = glia.by_speed_width_then_angle(bar_firing_rate)
    speed_widths = analytics.keys()
    speeds = sorted(list(set([speed for speed,width in speed_widths])))
    widths = sorted(list(set([width for speed,width in speed_widths])))
    color=iter(plt.cm.rainbow(np.linspace(0,1,len(speeds))))
    w = iter(np.linspace(1,5,len(widths)))
    speed_style = {speed: next(color) for speed in speeds}
    width_style = {width: next(w) for width in widths}
    
    for speed_width, angle_dictionary in analytics.items():
        ax = next(axis_gen)
        speed, width = speed_width
        line_angle = []
        line_radius = []
        for angle, average_number_spikes in angle_dictionary.items():
            line_angle.append(angle)
            line_radius.append(average_number_spikes)
        # connect the line
        line_angle, line_radius = glia.sort_two_arrays_by_first(line_angle,line_radius)
        line_angle.append(line_angle[0])
        line_radius.append(line_radius[0])
        ax.plot(line_angle,line_radius, linewidth=width_style[width], color=speed_style[speed])
        ax.set_title("speed: {}, width: {}".format(*speed_width), y=1.1)
        ax.set_xlabel("avg # of spikes", labelpad=12)
        


def plot_unit_dsi_osi_table(axis_gen,data):
    ax = next(axis_gen)
    bar_firing_rate, bar_dsi, bar_osi = data
    analytics = glia.by_speed_width_then_angle(bar_firing_rate)
    speed_widths = analytics.keys()
    speeds = sorted(list(set([speed for speed,width in speed_widths])))
    widths = sorted(list(set([width for speed,width in speed_widths])))
    color=iter(plt.cm.rainbow(np.linspace(0,1,len(speeds))))
    w = iter(np.linspace(1,5,len(widths)))
    speed_style = {speed: next(color) for speed in speeds}
    width_style = {width: next(w) for width in widths}
    
    speed_style["overall"] = "white"
    unique_speed_width = sorted(speed_widths, key=f_get_key(1))
    unique_speed_width = sorted(unique_speed_width, key=f_get_key(0))
    
    columns = unique_speed_width + ["overall"]
    colors = [speed_style[speed] for speed,width in unique_speed_width] + ['white']
    cells = [["{:1.3f}".format(bar_dsi[speed_width]) for speed_width in columns], \
             ["{:1.3f}".format(bar_osi[speed_width]) for speed_width in columns]]
    # ax.xaxis.set_visible(False) 
    # ax.yaxis.set_visible(False)
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=cells,
                      rowLabels=['DSI',"OSI"],
                      colLabels=columns,
                     colColours=colors,
                        loc='bottom', bbox = [0,0,1,0.5])
    table.auto_set_font_size(False)
    table.set_fontsize(12)

def plot_population_dsi_osi(ax,data):
    bar_dsi, bar_osi = data

    population_dsi = pd.DataFrame.from_dict(bar_dsi, orient="index")
    population_osi = pd.DataFrame.from_dict(bar_osi, orient="index")

    number_of_units = len(bar_dsi.keys())

    def f_histogram(bins, the_range):
        return lambda x: np.histogram(x,bins,the_range)

    dsi_population = population_dsi.apply(f_histogram(10,(0,1))).apply(lambda counts_bins: (counts_bins[0]/number_of_units, counts_bins[1]))
    osi_population = population_osi.apply(f_histogram(10,(0,1))).apply(lambda counts_bins: (counts_bins[0]/number_of_units, counts_bins[1]))

    bins = np.arange(0,1,0.1)
    dh = pd.DataFrame(index=bins)
    oh = pd.DataFrame(index=bins)

    for item in dsi_population.iteritems():
        parameter = item[0]
        values, bins = item[1]
        dh[parameter] = values
        
    for item in osi_population.iteritems():
        parameter = item[0]
        values, bins = item[1]
        oh[parameter] = values

    dh.plot.bar(figsize=(20,20), ax=ax[0])
    ax[0].set_title("Direction Selectivity Index (DSI) histogram")
    ax[0].set_ylabel("% of units")
    ax[0].set_xlabel("DSI")
    oh.plot.bar(figsize=(20,20), ax=ax[1])
    ax[1].set_title("Orientation Selectivity Index (OSI) histogram")
    ax[1].set_ylabel("% of units")
    ax[1].set_xlabel("OSI")


def save_unit_response_by_angle(units, stimulus_list, c_add_unit_figures, c_add_retina_figure):
    print("Calculating DSI & OSI")
    bar_firing_rate, bar_dsi, bar_osi = get_fr_dsi_osi(units, stimulus_list)

    print("plotting unit response by angle")
    analytics = glia.by_speed_width_then_angle(glia.get_unit(bar_firing_rate)[1])
    nplots = len(list(analytics.keys()))
    del analytics

    if nplots>1:
        ncols=3
    else:
        ncols=1

    result = glia.plot_units(plot_unit_response_by_angle,
        bar_firing_rate,bar_dsi,bar_osi,
        nplots=nplots, subplot_kw={"projection": "polar"},
        ax_xsize=4, ax_ysize=5, ncols=3)
    c_add_unit_figures(result)
    glia.close_figs([fig for the_id,fig in result])


    print("plotting unit DSI/OSI table")
    result = glia.plot_units(plot_unit_dsi_osi_table,
        bar_firing_rate,bar_dsi,bar_osi,
        ax_xsize=6, ax_ysize=4)
    c_add_unit_figures(result)
    glia.close_figs([fig for the_id,fig in result])



    fig_population,ax = plt.subplots(2,1)
    print("plotting population by DSI & OSI")
    plot_population_dsi_osi(ax, (bar_dsi, bar_osi))
    c_add_retina_figure(fig_population)
    plt.close(fig_population)



def save_unit_spike_trains(units, stimulus_list, c_add_unit_figures, c_add_retina_figure):
    print("Creating bar unit spike trains")
    
    get_solid = glia.compose(
        glia.f_create_experiments(stimulus_list),
        glia.f_has_stimulus_type(["BAR"]),
        partial(sorted, key=lambda e: e["stimulus"]["angle"]),
    )
    response = glia.apply_pipeline(get_solid,units)

    speed_widths = {}
    n_repetitions = 0
    bar_stimuli = filter(lambda k: k['stimulus']['stimulusType']=='BAR', stimulus_list)
    for key in bar_stimuli:
        stimulus = key['stimulus']
        speed_width = (stimulus['speed'], stimulus['width'])
        angle = stimulus['angle']
        try:
            speed_widths[speed_width][angle] += 1
        except:
            if speed_width not in speed_widths:
                speed_widths[speed_width] = {angle: 1}
            else:
                speed_widths[speed_width][angle] = 1
    nplots = 0
    for sw,v in speed_widths.items():
        nreps=0
        for a,count in v.items():
            nreps = max(nreps,count)
        nplots+= nreps
    # nplots = len(speed_widths)
    result = glia.plot_units(plot_spike_trains,response, nplots=nplots,
        ncols=3,ax_xsize=10, ax_ysize=5,
        figure_title="Unit spike train by BAR angle")
    c_add_unit_figures(result)
    glia.close_figs([fig for the_id,fig in result])
