import pandas as pd
from datetime import datetime
from utils.filtering import filter_time, filter_declare
import random

def FormBased(data: pd.DataFrame, which: list, DecConstraint: str = None, tstart: datetime= None, 
              tend: datetime= None, ratio:float= None,
              case_id_key:str = "Case", timestamp_key:str = "Timestamp"):
    
    if tstart or tend:
        data = data.groupby(case_id_key).apply(lambda x: filter_time(x, tstart, tend, timestamp_key)).reset_index(drop=True)
        if data.empty:
            raise ValueError("Error: no matched cases in the time interval")
        print(f"Filtering step 1. The number of cases in the time interval ({tstart}, {tend}): {len(data[case_id_key].unique())}")

    if DecConstraint:
        declared_cases = filter_declare(data, DecConstraint, case_id_key)
        print(f"Filtering step 2. The number of cases by declare rule: {len(declared_cases)}")
        data = data[data[case_id_key].isin(declared_cases)].reset_index(drop=True)
    
    cases = data[case_id_key].unique()

    sub_patterns = []
    c_index = []

    for c in cases:
        dat = data.loc[data.Case == c]
        c_seq = dat['Activity'].tolist()
        c_index = c_index + dat.index.tolist()[0:(len(c_seq) - len(which)) ]
        for l in range(0, len(c_seq) - len(which)):
            sub_patterns.append(c_seq[l:(l+len(which))])
    
    c_index2 = [c_index[i] for i in [index for index, e in enumerate(sub_patterns) if (which == e)]]


    print(f"Filtering step 3. The number of cases containing the defined subseq {which}: {len(data[case_id_key].loc[c_index2].unique())}")
    cases2 = data[case_id_key].loc[c_index2].unique()

    if ratio is None:
        case_sampled = cases2.tolist()
    else:
        case_sampled = random.sample(cases2.tolist(), round(len(cases2) * ratio))
        print(f"Filtering step 4. The number of cases to be filtered by defined random portion: {len(cases2)}")
    
    result = data.copy()
    result['label'] = ""
    
    for i in c_index2:
        if result.loc[i, case_id_key] in case_sampled:
            form_time = result.loc[i, timestamp_key]
            org_time = result.loc[i:i + len(which) - 1, timestamp_key]
            result.loc[org_time.index, 'label'] = "form-based events(" + org_time.astype(str) + ")"
            result.loc[i + 1:i + len(which) - 1, timestamp_key] = form_time

    return result