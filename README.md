# Naturindeks

Code for collecting and managing raw data used for calculating Naturindeks.
Primarly intended to run within Jupyterhub.

## Installing Python packages

We're using Poetry. To install aquamonitor do the following:
```
poetry shell
pip install git+https://github.com/NIVANorge/AquaMonitor-Python.git
exit
```

## Export Vannmiljø

The call for PTI is as follows:
POST
https://vannmiljowebapi.miljodirektoratet.no/api/Vannmiljo/ExportRegistrations
```json
{"RegType":1,"ParameterIDs":["PPTI"],"MediumID":"","FromDateSamplingTime":"2020-01-01","ToDateSamplingTime":"2024-10-22","LatinskNavnID":"","ActivityID":"","AnalysisMethodID":"","SamplingMethodID":"","RegValueOperator":"","RegValue":"","RegValue2":"","UpperDepthOperator":"","UpperDepth":"","UpperDepth2":"","UpperDepthIncludeNull":"","LowerDepthOperator":"","LowerDepth":"","LowerDepth2":"","LowerDepthIncludeNull":"","Employer":"","Contractor":"","ExportType":"redigering","WaterLocationIDFilter":[]}
```
Response is the file.