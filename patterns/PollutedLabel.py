import re
import pandas as pd
from datetime import datetime
from utils.filtering import filter_time, filter_declare
import random
import string
import tracemalloc
import warnings
warnings.filterwarnings(action='ignore')


def PollutedLabel(data: pd.DataFrame, target: str, action: str, DecConstraint: str = None, 
                  tstart: datetime = None, tend: datetime = None, ratio: float = None,
                  case_id_key='Case', timestamp_key: str = "Timestamp"):
    
    tracemalloc.start()

    step = 1
    if tstart or tend:
        data = data.groupby(case_id_key).apply(lambda x: filter_time(x, tstart, tend, timestamp_key)).reset_index(drop=True)
        if data.empty:
            raise ValueError("Error: no matched cases in the time interval")
        print(f"Filtering step {step}. The number of cases in the time interval ({tstart}, {tend}): {len(data[case_id_key].unique())}")
        step += 1

    if DecConstraint:
        declared_cases = filter_declare(data, DecConstraint, case_id_key)
        print(f"Filtering step {step}. The number of cases by declare rule: {len(declared_cases)}")
        data = data[data[case_id_key].isin(declared_cases)].reset_index(drop=True)
        step += 1
    
    case_sampled = data[case_id_key].unique()
    if ratio is not None:
        case_sampled = random.sample(case_sampled.tolist(), round(len(case_sampled) * ratio))
        print(f"Filtering step {step}. The number of cases to be filtered by defined random portion: {len(case_sampled)}")
    else:
        case_sampled = case_sampled.tolist()
    
    form_parts = [s for s in re.split(r"\[|\]", action) if s != '']
    
    attr_time = None
    form_time = None
    for idx, x in enumerate(form_parts):
        if re.search(r"[^\(]*\([^\)]*\)", x):
            attr_time, form_time = x.split('*(')
            form_time = form_time[:-1]
            form_parts[idx] = attr_time

    form_var = [i for i in form_parts if action[action.find(i) - 1] == "["]
    form_attr = [i for i in form_var if i in data.columns]
    form_regular = [i for i in form_var if i not in data.columns]
    
    result = data.copy()
    result['label'] = ""
    

    condition = None
    if ':' in target:
        attr_polluted = (re.split(r"\:", target)[0])[1:]
        condition = (re.split(r"\:", target)[1])[:-1]
        if type(eval(condition)) == str:
            condition = [eval(condition)]
        else:
            condition = list(eval(condition))


    for c_id in case_sampled:
        case_data = result[result[case_id_key] == c_id]
        if condition is None:
            loc = case_data.index
        else:
            loc = case_data[case_data[attr_polluted].isin(condition)].index
        if loc.empty:
          continue

        for index in loc:
            row_str = ''
            for part in form_parts:
                if part in form_attr:
                    if part == attr_time and form_time:
                        row_str += result.loc[index, part].strftime(form_time)
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
                        print(f"Error: wrong or unsupportable regular expression: {part}")
                        random_text = ""
                    row_str += random_text
                else:
                    row_str += part

            org = result.loc[index, attr_polluted]
            result.loc[index, attr_polluted] = row_str
            result.loc[index, 'label'] = f"polluted Label({attr_polluted}:'{org}')"

    return result