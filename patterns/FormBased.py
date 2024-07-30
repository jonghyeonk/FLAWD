import pandas as pd
from datetime import datetime
from utils.filtering import filter_time
from utils.filtering import filter_declare
import random


def FormBased(data: pd.DataFrame, which: list, DecConstraint: str, tstart: datetime= None, 
              tend: datetime= None, ratio:float= None,
              case_id_key:str = "Case", timestamp_key:str = "Timestamp"):
    step = 1
    if (tstart == None) & (tend == None):
        pass
    else:
        data = data.groupby(['Case']).apply(lambda x: filter_time(x, tstart, tend, timestamp_key))
        data = data.reset_index(drop=True)
        if data.empty:
            raise ValueError("Error: no matched cases in the time interval")
        else:
            print("Filtering step", step, ". The number of cases in the time interval (", tstart, ",", tend ,"): ", len(data.Case.unique()))
        step += 1
    
    if DecConstraint:
        declared_cases = filter_declare(data, DecConstraint, case_id_key)
        print("Filtering step", step, ". The number of cases by declare rule: ", len(declared_cases) )
        data = data[data[case_id_key].isin(declared_cases)].reset_index(drop=True)
        step += 1
    
    
    cases = data.Case.unique()
    sub_patterns = []
    c_index = []
    for c in cases:
        dat = data.loc[data.Case == c]
        c_seq = dat['Activity'].tolist()
        c_index = c_index + dat.index.tolist()[0:(len(c_seq) - len(which)) ]
        for l in range(0, len(c_seq) - len(which)):
            sub_patterns.append(c_seq[l:(l+len(which))])
    
    c_index2 = [c_index[i] for i in [index for index, e in enumerate(sub_patterns) if (which == e)]]
    print("Filtering step", step, ". The number of cases containing the defined subseq ", which ,": ", len(data.Case[c_index2].unique()))
    step += 1
    
    if ratio == None:
        case_sampled = data[case_id_key].unique().tolist()
    else:
        case_sampled = random.sample(data[case_id_key].unique().tolist(), round(len(data[case_id_key].unique().tolist())* ratio))
        print("Filtering step", step, ". The number of cases to be filtered by defined random portion: ", len(case_sampled))
    
    result = data.copy()
    result['label'] = ""
    
    for i in c_index2:
        if result.iloc[i].Case in case_sampled:
            form_time = result[timestamp_key].iloc[i]
            # polluted_time = sorted(list([form_time+pd.to_timedelta(round(np.random.uniform(0,1), 3), unit='s') for i in range(len(subseq)-1)]))
            org_time = result.loc[(i):(i+len(which)-1), timestamp_key]
            for index_time in org_time.index:
                result.loc[index_time, 'label'] = "form-based events(" + str(org_time[index_time]) + ")"
            result.loc[(i+1):(i+len(which)-1), timestamp_key] = form_time
            

    return result