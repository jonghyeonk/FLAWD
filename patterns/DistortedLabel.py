import re
import pandas as pd
import numpy as np
from datetime import datetime
from utils.filtering import filter_time
from utils.filtering import filter_declare
import random
import string
import itertools

QWERTY= np.array([['Q','W','E','R','T','Y','U','I','O','P'], 
         ['A','S','D','F','G','H','J','K','L',';'], 
         ['Z','X','C','V','B','N','M',',','.','/']])

qwerty= np.array([['q','w','e','r','t','y','u','i','o','p'], 
         ['a','s','d','f','g','h','j','k','l',';'], 
         ['z','x','c','v','b','n','m',',','.','/']])

def distortion(oldstr, method):
    if method == "Skip":
        str_len = len(oldstr)
        loc = random.choice(range(0,str_len))
        newstr = oldstr[:loc] + oldstr[loc+1:]
        
    elif method == "Insert":
        str_len = len(oldstr)
        loc = random.choice(range(0,str_len))
        newstr = oldstr[:loc] +  ''.join(random.choices(string.ascii_letters))  + oldstr[loc:]
        
    elif method == "Interchange":
        str_len = len(oldstr)
        midlen = len(oldstr) // 2
        loc = random.choice(range(0,str_len))
        if loc >= midlen:
            newstr = oldstr[:loc-1] + oldstr[loc] + oldstr[loc-1] + oldstr[loc+1:]
        else:
            newstr = oldstr[:loc] + oldstr[loc+1] + oldstr[loc] + oldstr[loc+2:]
        
    elif method == "UpLow":
        if oldstr[0].isupper():
            newstr = oldstr[0].lower() + oldstr[1:]
        else:
            newstr = oldstr[0].upper() + oldstr[1:]
    

    elif method == "Proximity":
        str_len = len(oldstr)
        loc = random.choice(range(0,str_len))

        while (len(np.where(QWERTY == oldstr[loc])[0])==0) and (len(np.where(qwerty == oldstr[loc])[0])==0):
            loc = random.choice(range(0,str_len))
        if oldstr[loc].isupper():
            rows, cols = np.where(QWERTY == oldstr[loc])
            rows = int(rows)
            cols = int(cols)
            nearstrs = list(itertools.chain(*QWERTY[( max(0, rows-1)  ):(rows+2), ( max(0,cols-1)):(cols+2)].tolist())) 
            nearstrs.remove( oldstr[loc] )
            nearstr = random.choices( nearstrs )
        else:
            rows, cols = np.where(qwerty == oldstr[loc])
            rows = int(rows)
            cols = int(cols)
            nearstrs = list(itertools.chain(*qwerty[( max(0, rows-1)  ):(rows+2), ( max(0,cols-1)):(cols+2)].tolist())) 
            nearstrs.remove( oldstr[loc] )
            nearstr = random.choices( nearstrs )

        newstr = oldstr[:loc] +  nearstr[0] + oldstr[loc+1:]

    return newstr


def DistortedLabel(data, who, distortion, DecConstraint:str, 
                    tstart: datetime= None, tend: datetime= None, ratio:float= None, 
                    case_id_key:str = 'Case', timestamp_key:str = "Timestamp"):
    
    step = 1
    if (tstart == None) & (tend == None):
        pass
    else:
        data = data.groupby([case_id_key]).apply(lambda x: filter_time(x, tstart, tend, timestamp_key))
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
    
    if ratio == None:
        case_sampled = data[case_id_key].unique().tolist()
    else:
        case_sampled = random.sample(data[case_id_key].unique().tolist(), round(len(data[case_id_key].unique().tolist())* ratio))
        print("Filtering step", step, ". The number of cases to be filtered by defined random portion: ", len(case_sampled))

    result = data.copy()
    result['label'] ="" 
    
    result_filtered = result.loc[result[case_id_key].isin(case_sampled)].reset_index(drop=True)
    result_nonfiltered = result.loc[~result[case_id_key].isin(case_sampled)]

    condition_root = None
    if ":" in who:
        attr_root = (re.split(r"\:", who)[0])[1:]
        condition_root = (re.split(r"\:", who)[1])[:-1]
    
    
    condition = None
    attr = (re.split(r"\:", distortion)[0])[1:]
    condition = (re.split(r"\:(?!\')", distortion)[1])[:-1]
    
    
    if "random(" in distortion:
        pattern = []
        if "Skip" in condition:
            pattern = pattern + ["Skip"]
        if "Insert" in condition:
            pattern = pattern + ["Insert"]
        if "Interchange" in condition:
            pattern = pattern + ["Interchange"]
        if "UpLow" in condition:
            pattern = pattern + ["UpLow"]
        if "Proximity" in condition:
            pattern = pattern + ["Proximity"]

        condition = pattern
    else:
        if type(eval(condition)) == str:
            condition = dict(eval(condition))
        else:
            condition = dict(eval(condition))

    
    
    if 'random{' in condition_root:
        cut1 = re.split(r"\{|\}", condition_root)[1]
        cut2 = (re.split(r"\=|\,", cut1))
        m = float(cut2[1])
        s = float(cut2[3])
        rate = np.random.normal(m,s, len(result_filtered[attr_root].unique()))
        rate = [max(i, 0) for i in rate]
        df_resource = pd.DataFrame()
        df_resource[attr_root] = result_filtered[attr_root].unique().tolist()
        df_resource['rate'] = rate
        
        result_filtered = result_filtered.merge(df_resource, distortion='left', on=attr_root)
        PF = np.random.binomial(np.repeat(1, len(result_filtered)), result_filtered["rate"])
        print("Total number of events with resource's mistake: ", sum(PF) )
        result_filtered['mistake_true/false'] = PF
        
        if type(condition)==list:
            result_selected = result_filtered.loc[result_filtered['mistake_true/false']==1]
            result_others = result_filtered.loc[result_filtered['mistake_true/false']==0]
            list_polluted_act = []
            list_label = []
            for str_act in result_selected[attr]:
                p = random.choice(pattern)
                polluted_act = distortion(str_act, method = p)
                list_polluted_act = list_polluted_act + [polluted_act]
                label = str("distorted label(") + str(p) + ")"
                list_label = list_label + [label]
                
            result_selected[attr] = list_polluted_act
            result_selected['label'] = list_label
            result_filtered = pd.concat([result_selected, result_others]).reset_index(drop=True)
            
        else:  
            for key in condition.keys():
                result_filtered.loc[(result_filtered['mistake_true/false']==1 ) & (result_filtered[attr] == key), 'label'] = str("distorted label(") + str(key) + ")"
                result_filtered.loc[(result_filtered['mistake_true/false']==1 ) & (result_filtered[attr] == key), attr] = condition[key]
        
    else:
    
        if type(eval(condition_root)) == str:
            condition_root = [eval(condition_root)]
        else:
            condition_root = list(eval(condition_root))
            
        if type(condition)==list:
            result_selected = result_filtered.loc[result_filtered[attr_root].isin(condition_root)]
            result_others = result_filtered.loc[~result_filtered[attr_root].isin(condition_root)]
            list_polluted_act = []
            list_label = []
            for str_act in result_selected[attr]:
                p = random.choice(pattern)
                polluted_act = distortion(str_act, method = p)
                list_polluted_act = list_polluted_act + [polluted_act]
                label = str("distorted label(") + str(p) + ")"
                list_label = list_label + [label]
                
            result_selected[attr] = list_polluted_act
            result_selected['label'] = list_label
            
            result_filtered = pd.concat([result_selected, result_others]).reset_index(drop=True)
            
        else:  
            for key in condition.keys():
                result_filtered.loc[(result_filtered[attr_root].isin(condition_root)) & (result_filtered[attr] == key), 'label'] = str("distorted label(") + str(key) + ")"
                result_filtered.loc[(result_filtered[attr_root].isin(condition_root)) & (result_filtered[attr] == key), attr] = condition[key]

        
    result_filtered = result_filtered[list(result_nonfiltered.columns.values)]
    result = pd.concat([result_filtered, result_nonfiltered]).reset_index(drop=True)
        
    return result
