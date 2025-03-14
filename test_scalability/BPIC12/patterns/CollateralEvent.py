import pandas as pd
import numpy as np
from datetime import datetime
from utils.filtering import filter_time, filter_declare
import random
import re
import tracemalloc

def CollateralEvent(data: pd.DataFrame, target_collats: list, DecConstraint: str= None, tstart: datetime= None, 
                     tend: datetime= None, ratio:float= None,timep:float = 1, unit = 'sec',
                     case_id_key:str = "Case", timestamp_key:str = "Timestamp",  activity_key:str = "Activity"):
    
    tracemalloc.start()

    if tstart or tend:
        data = data.groupby(case_id_key).apply(lambda x: filter_time(x, tstart, tend, timestamp_key)).reset_index(drop=True)
        if data.empty:
            raise ValueError("Error: no matched cases in the time interval")
        print(f"Filtering step 1. The number of cases in the time interval ({tstart}, {tend}): {len(data[case_id_key].unique())}")

    if DecConstraint:
        declared_cases = filter_declare(data, DecConstraint, case_id_key)
        print(f"Filtering step 2. The number of cases by declare rule: {len(declared_cases)}")
        data = data[data[case_id_key].isin(declared_cases)].reset_index(drop=True)
    
    case_sampled = data[case_id_key].unique()
    if ratio is not None:
        case_sampled = np.random.choice(case_sampled, round(len(case_sampled) * ratio), replace=False)
        print(f"Filtering step 3. The number of cases to be filtered by defined random portion: {len(case_sampled)}")

    result = data.copy()
    result['label'] = ""

    if '>>' in target_collats:  # "[Activity:Make decision>>('Make revision1', 'Make revision2')]"
        attr = (re.split(r"\:", target_collats)[0])[1:]
        remain = (re.split(r"\:", target_collats)[1])[:-1]
        act_init = (re.split(r"\>\>", remain)[0])[1:-1]
        act_added =  (re.split(r"\>\>", remain)[1])
        data_attr = list(result.columns.values)
        data_attr = [i for i in data_attr if i not in [case_id_key, activity_key, timestamp_key]]
        if type(eval(act_added)) == str:
            act_added = [eval(act_added)]
        else:
            act_added = list(eval(act_added))

    temp_df = result.loc[(result[case_id_key].isin(case_sampled))]
    temp_df = temp_df.loc[temp_df[activity_key]== act_init]
    case_sampled = temp_df[case_id_key].unique()
    new_rows = []
    for c_id in case_sampled:
        case_data = result[(result[case_id_key] == c_id) ]
        for index, row in case_data.iterrows():
            form_time = row[timestamp_key]
            temp_time = pd.to_timedelta(0, unit=unit)
            for act in act_added:
                new_row = row.copy()
                new_row[activity_key] = act
                time_add = pd.to_timedelta(round(np.random.uniform(0, timep), 1), unit=unit) + temp_time
                new_row[timestamp_key] = form_time + time_add
                temp_time = time_add
                new_row['label'] = f"collateral events({act_init})"
                new_rows.append(new_row)

    result = pd.concat([result, pd.DataFrame(new_rows)], ignore_index=True)

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    tracemalloc.stop()
    return result.sort_values([case_id_key, timestamp_key]).reset_index(drop=True), top_stats