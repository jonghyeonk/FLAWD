# Project Name: FLAWD

## General info
FLAWD is a tool to generate pseudo-real imperfection patterns in event logs. Imperfection patterns to be injected are defined by their root cause, i.e., resource behaviour or system malfunctioning. For each root cause, several anomaly types can be specified, e.g., deleting, replacing or moving events in a trace. Root causes and anomalies have been modelled based on existing literature on event log cleaning and data quality analysis. AIR-BAGEL addresses the issue of unavailability of labelled real world event logs for developing and evaluating event log cleaning and reconstruction techniques and it represents a step forward compared to current approaches in the literature that simply inject different types of anomalies randomly in event logs.

## Technologies
* Python - version 3.11.9
* scipy - version 1.10.1
* Declare4Py - local folder (ref= https://github.com/ivanDonadello/Declare4Py)
* PM4Py - version 2.7.9.1
* sklearn - version 1.2.2
* re, pandas, numpy, random, datetime

## Implementation
See the Jyupyter Notebook "Implementation.ipynb"
