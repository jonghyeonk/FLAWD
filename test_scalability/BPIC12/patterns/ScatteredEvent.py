
import re
import pandas as pd
import numpy as np
from datetime import datetime
from utils.filtering import filter_time, filter_declare
import random
import string

def ScatteredEvent(data: pd.DataFrame, target: list, action:str, loc:str = None, Del:bool = False, ratio:float= None, 
                    tstart: datetime= None, tend: datetime= None,   DecConstraint:str = None,
                    case_id_key:str = "Case",  activity_key:str = "Activity" , timestamp_key:str = "Timestamp"):
    
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

    if '>>' in target:
        attr, remain = target[1:-1].split(':', 1)
        act_init, act_added = remain[1:-1].split('>>')
        act_added = eval(act_added) if '[' in act_added else [act_added]
        condition = act_added
    elif ':' in target:
        attr, condition = target[1:-1].split(':', 1)
        condition = eval(condition) if '[' in condition else [condition]
    elif '[' in target:
        attr = target.split('(', 1)[1].split(')', 1)[0] if '(' in target else target
        condition = None
    else:
        attr = target
        condition = None

    idx_move = None
    if ':' in loc:
        name, idx_str = loc[1:-1].split(':', 1)
        idx_move = int(idx_str.split('(', 1)[1].split(')', 1)[0])
        if idx_move >= 0:
            raise ValueError('Error: idx value to be moved should be less than 0')
    elif '[' in loc:
        name = loc[1:-1]
        if Del:
            idx_move = -1
    else:
        name = loc
        if Del:
            idx_move = -1

    result[name] = ""
    result['label'] = ""

    if '>>' in target:
        idx_add_all = result.index[(result[attr] == act_init) & (result[case_id_key].isin(case_sampled))]
        for idx_add in idx_add_all:
            row = result.iloc[[idx_add]].copy()
            form_time = result[timestamp_key].iloc[idx_add]
            form_time_next = result[timestamp_key].iloc[idx_add + 1]
            duration = form_time_next - form_time
            for i, act in enumerate(act_added, 1):
                row[attr] = act
                row[timestamp_key] = form_time + duration * i / (len(act_added) + 1)
                for col in result.columns:
                    if col not in [case_id_key, activity_key, timestamp_key, name, 'label']:
                        if isinstance(row[col].iat[0], str):
                            row[col] = result[col].sample(1).iat[0]
                        elif isinstance(row[col].iat[0], (float, int)):
                            row[col] = np.random.choice(np.arange(min(result[col]), max(result[col])))
                result = pd.concat([result, row], ignore_index=True)

    result = result.sort_values([case_id_key, timestamp_key, activity_key]).reset_index(drop=True)

    form_parts = [s for s in re.split(r"\[|\]", action) if s != '']
    form_attr = [part for part in form_parts if part in result.columns]
    form_regular = [part for part in form_parts if part not in result.columns]

    for c_id in case_sampled:
        case_data = result[result[case_id_key] == c_id]
        if condition is None:
            loc2 = case_data.index
        else:
            loc2 = case_data[case_data[attr].isin(condition)].index

        if not loc2.empty:
            start_idx = case_data.index.min()
            for index in loc2:
                row_str = ''
                for part in form_parts:
                    if part in form_attr:
                        if part in timestamp_key and '(' in action:
                            time_format = re.search(r'\((.*?)\)', action).group(1)
                            row_str += result.loc[index, part].strftime(time_format)
                        else:
                            row_str += str(result.loc[index, part])
                    elif part in form_regular:
                        repeat = 1
                        if ':' in part:
                            repeat = int(re.search(r'\{(\d+)\}', part).group(1))
                        if 'a-zA-Z' in part:
                            random_text = ''.join(random.choices(string.ascii_letters, k=repeat))
                        elif 'a-z' in part:
                            random_text = ''.join(random.choices(string.ascii_lowercase, k=repeat))
                        elif 'A-Z' in part:
                            random_text = ''.join(random.choices(string.ascii_uppercase, k=repeat))
                        elif '0-9' in part:
                            random_text = ''.join(random.choices(string.digits, k=repeat))
                        else:
                            raise ValueError(f"Error: wrong or unsupportable regular expression: {part}")
                        row_str += random_text
                    else:
                        row_str += part

                for f in form_attr:
                    result.loc[index, f] = result.loc[index - 1, f]

                if idx_move is None:
                    result.loc[index, name] = row_str
                else:
                    move_idx = min(loc2) + idx_move
                    if move_idx >= start_idx:
                        if result.loc[move_idx, name] == "":
                            result.loc[move_idx, name] = [row_str]
                        else:
                            result.at[move_idx, name] = result.loc[move_idx, name] + [row_str]
                    else:
                        result.loc[index, name] = row_str

                result.loc[index, 'label'] = f"Scattered Events(Scattered attr = {form_attr})"

            if Del and idx_move is not None and min(loc2) + idx_move >= start_idx:
                result.loc[min(loc2) + idx_move, 'label'] = f"Scattered Events(Scattered attr = {form_attr}, Activity: {condition})"
                result.loc[loc2, 'label'] = "DELETE"

    result = result[result['label'] != "DELETE"].reset_index(drop=True)
    return result.sort_values([case_id_key, timestamp_key, activity_key]).reset_index(drop=True)