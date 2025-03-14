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

from patterns.PollutedLabel import PollutedLabel


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
# generatio system attributes 


start_time = time.time()

EL_polluted, top_stats = PollutedLabel(EL, 
                            target = "[Activity:('A_DECLINED', 'O_SENT_BACK')]",  # TBD: also numeric range
                            action = "[Activity]_[0-9:{2}][a-zA-Z:{5}]_[Timestamp*(%Y%m%d %H%M%S%f)]",
                            ratio = float(rate),
                            case_id_key = "Case",
                            timestamp_key = "Timestamp")

end_time = time.time()

execution_time = end_time - start_time
print(execution_time)
# list_time = list_time + [execution_time]
# list_memory = list_memory + [sum([stat.size for stat in top_stats])]
output = [rate, sum([stat.size for stat in top_stats])/len(top_stats), max([stat.size for stat in top_stats]), execution_time]

print(output)
with open('summary_PollutedLabel.csv', 'a', encoding='utf-8', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    if float(rate) <= 0.05:
        spamwriter.writerow(['Rate', 'Memory_Ave', 'Memory_Max', 'Time'])
    spamwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(output)