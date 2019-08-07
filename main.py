from collections import defaultdict
import numpy as np
from bokeh import plotting as plt
from bokeh.palettes import viridis
from bokeh.models import DatetimeTickFormatter, FixedTicker, Label
from bokeh.models.tools import HoverTool
from datetime import datetime, timedelta

# generates tick locations so that they are placed in the middle of each month
def gen_x_axis_ticks():
    ticks = []      # output container

    for i in range(1,13):
        # start point
        start = datetime(2000,i,1)
        # compute endpoint
        if i != 12:
            end = datetime(2000,i+1,1)
        else:
            end = datetime(2001,1,1)
        # compute middle point based on start and end
        middle = start + (end - start) / 2
        # convert the result to miliseconds
        ticks.append(int(middle.strftime('%s')) * 1000)
    return ticks


# hacky way to create a colour palette for the graph
def gen_color_palette():
    # pick 7 middle-ish elements of the gradient
    tmp_month_clrs = viridis(36)[17:-12]
    # stitch them together to create 12 elements
    return tmp_month_clrs[::-1][:-1] + tmp_month_clrs[:-1]


DATASET_LOC = "dataset/P1PRUZ01.csv"
DAY_IN_MS = 86400000
# days of the year stored in the graph
DATES = [datetime(2000,1,1) + timedelta(days=d) for d in range(366)]
PALETTE = gen_color_palette()

# initiate array that will hold dict data about each month
full_dataset = []
for i in range(12):
    full_dataset.append(defaultdict(list))

# dataset I/O
file = open(DATASET_LOC, "r")
data = file.readlines()[4:]     # first 4 lines unimportant
file.close()

# parse csv file
for raw_line in data:
    line = raw_line[:-1]        # remove newline
    entry = line.split(',')
    year, month, rainfall = int(entry[0]), int(entry[1])-1, entry[2:]
    # add value to corresponding day bucket
    for day, val in enumerate(rainfall):
        # if day does exist
        if val != '':
            full_dataset[month][day].append(float(val))

# canvas
plt.output_file("plot.html")
p = plt.figure(plot_height=750, plot_width=1500,
               title="Average daily rainfall in Prague (data from 1961-2018)",
               y_range=(0,5),
               x_axis_type="datetime")

# compute statistics
month_first_day_i = 0
for month_i, month_vals in enumerate(full_dataset):
    month_len = len(month_vals.keys())
    month_last_day_i = month_first_day_i + month_len
    # containers for results within one month
    rainfall_mean = []
    rain_prob = []
    # compute daily metrics accross all collected years
    for day_i in range(month_len):
        day_vals = month_vals[day_i]
        # compute mean
        mean = np.mean(day_vals)
        rainfall_mean.append(mean)
        # compute rain probability
        nonzeros = np.count_nonzero(day_vals)           # days with some rain
        any_rain = nonzeros / float(len(day_vals))      # & their proportion
        rain_prob.append(any_rain)

    source = plt.ColumnDataSource(data=dict(
        x=DATES[month_first_day_i:month_last_day_i],
        y=rainfall_mean,
        prob=rain_prob
    ))

    # plot the monthly histogram
    p.vbar(x='x', top='y', source=source, name="histogram", width=DAY_IN_MS,
           color=PALETTE[month_i], alpha=0.85,
           hover_color=PALETTE[month_i], hover_alpha=1)

    # save new initial value for the next iteration
    month_first_day_i = month_last_day_i

# recompute today's value for "today" label
today_month = datetime.now().month
today_day = datetime.now().day
# need to use year 2000 consistently everywhere due to leap years
today_index = datetime(2000,today_month,today_day).timetuple().tm_yday-1
today_mean = np.mean(full_dataset[today_month-1][today_day-1])
# the label itself
label = Label(x=DATES[today_index], y=today_mean, x_offset=-5, y_offset=3,
              text=u"\u25BE" + "Today", text_font_size='10pt',
              background_fill_color='white', background_fill_alpha=0.8)
p.add_layout(label)

# interactive hover tool
p.add_tools(HoverTool(
  names=["histogram"],
  mode='vline',
  tooltips=[("Day", "@x{%d %B}"),
            ("Avg rainfall (mm)", "@y{0.00}"),
            ("Probability of rain", "@prob{0%}")],
  formatters={'x': 'datetime'},
  point_policy='follow_mouse'
))

# grid / axis formatting
p.xaxis.ticker = FixedTicker(ticks=gen_x_axis_ticks())
p.xaxis.formatter=DatetimeTickFormatter(months=["%B"])
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.yaxis.axis_label = "Perticipitation in millimeters"
p.toolbar.logo = None
p.toolbar_location = None
p.outline_line_color = None
p.sizing_mode="scale_both"

plt.show(p)
