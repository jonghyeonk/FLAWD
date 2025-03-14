import os
import warnings
warnings.filterwarnings(action='ignore')
import pandas as pd
from datetime import datetime
os.environ["PATH"]+=os.pathsep+'C:/Program Files/Graphviz/bin/'
import graphviz
import pm4py
import numpy as np
import tracemalloc
import time
import csv

org_path = os.getcwd()
input_path = os.sep.join([str(org_path), "input"])

from patterns.ScatteredEvent import ScatteredEvent

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--log', default=None, help='input data')
parser.add_argument('--rate', default=None, help='input rate')
log = parser.parse_args().log
rate = parser.parse_args().rate

event_log = pm4py.read_xes(input_path+ '\\' + log +'.xes.gz')
start_activities = pm4py.get_start_activities(event_log)
end_activities = pm4py.get_end_activities(event_log)
print("Start activities: {}\nEnd activities: {}".format(start_activities, end_activities))

extracted_data = event_log[['case:concept:name', 'concept:name', 'time:timestamp', 'org:resource']]
extracted_data.columns = ["Case", "Activity", "Timestamp", 'Resource']
form = "%Y-%m-%d %H:%M:%S.%f" 

extracted_data = extracted_data.sort_values(["Case", "Timestamp", "Activity"],ascending=[True, True, True]) # Reorder rows
extracted_data.Case = extracted_data.Case.astype(str) 
# time = extracted_data['Timestamp'].apply(lambda x: datetime.strptime(str(x)[0:23], form))
# extracted_data['Timestamp'] = time
EL = extracted_data.copy()
EL = EL.dropna(subset=['Case'])
EL.head()

for rate in [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]:

    start_time = time.time()
    tracemalloc.start()

    EL_polluted = ScatteredEvent(EL, 
                                target = "[Activity:'O_Returned'>>('O_Returned1', 'O_Returned2')]",                                                   # "[Activity:('Make decision', 'Notify accept', 'Deliver card')]",
                                action = "[Resource]_[0-9:{2}][a-zA-Z:{5}]_[Timestamp*(%Y%m%d %H%M%S%f)]",
                                loc = "[Description:idx(-1)]",
                                Del = True, 
                                ratio = float(rate), 
                                case_id_key = "Case",
                                activity_key = "Activity",
                                timestamp_key = "Timestamp")

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    tracemalloc.stop()
    end_time = time.time()

    execution_time = end_time - start_time
    print(execution_time)
    # list_time = list_time + [execution_time]
    # list_memory = list_memory + [sum([stat.size for stat in top_stats])]
    output = [rate, sum([stat.size for stat in top_stats])/len(top_stats), max([stat.size for stat in top_stats]), execution_time]
    print(output)
    with open('summary_ScatteredEvent.csv', 'a', encoding='utf-8', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        if float(rate) <= 0.05:
            spamwriter.writerow(['Rate', 'Memory_Ave', 'Memory_Max', 'Time'])
        spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(output)