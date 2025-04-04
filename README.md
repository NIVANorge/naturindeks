# Naturindeks

Code for collecting and managing raw data used for calculating Naturindeks.<br>
Primarly intended to run within Jupyterhub. <br>
<br>
The <b>rscript</b> folder contains scripts for: <br>
* convert2neqr.r: Convert compiled raw data to nEQR values based on reference values and class limits for the given indicator <br>
* analyses_neqr.Rmd: Run a BRT model describing the observed nEQR values as function of water type and year, and predict nEQR for all relevant municipalities and years<br>
* analyses_neqr.r: Run analyses_neqr.Rmd for all indicators and produce summary html.<br>
* blotbunn_hav.Rmd: Combine data specifically for the 'bløtbunn hav' indicator, calculate averages per ocean area.<br>
* NICalc_upload.r: Update NI-database with the predictions <br>
* compile_mussel_data.R: Compile mussel data from internal NIVA database.<br>


## Installing Python packages

We're using Poetry. To install aquamonitor do the following:
```
pip install poetry
poetry shell
pip install git+https://github.com/NIVANorge/AquaMonitor-Python.git
exit
poetry install
```

## Export Vannmiljø

The call for PTI is as follows:
POST
https://vannmiljowebapi.miljodirektoratet.no/api/Vannmiljo/ExportRegistrations
```json
{"RegType":1,"ParameterIDs":["PPTI"],"MediumID":"","FromDateSamplingTime":"2020-01-01","ToDateSamplingTime":"2024-10-22","LatinskNavnID":"","ActivityID":"","AnalysisMethodID":"","SamplingMethodID":"","RegValueOperator":"","RegValue":"","RegValue2":"","UpperDepthOperator":"","UpperDepth":"","UpperDepth2":"","UpperDepthIncludeNull":"","LowerDepthOperator":"","LowerDepth":"","LowerDepth2":"","LowerDepthIncludeNull":"","Employer":"","Contractor":"","ExportType":"redigering","WaterLocationIDFilter":[]}
```
Response is the file.

Here is some sql to get Vannmiljø parameterid together with NIVA parameter / method.

```sql
SELECT c.code, a.parameterid, b.name FROM vannmiljo.conv_parameters a, nivadatabase.plankton_parameter_definitions b, vannmiljo.datatype c
WHERE a.datatype_id = c.datatype_id AND a.niva_parameter_id = b.parameter_id 
AND b.name IN ('PTI')
AND c.code = 'Plankton'

SELECT c.code, a.parameterid, b.name FROM vannmiljo.conv_parameters a, nivadatabase.hb_parameter_defs b, vannmiljo.datatype c
WHERE a.datatype_id = c.datatype_id AND a.niva_parameter_id = b.parameter_id 
AND b.name IN ('MSMDI1','MSMDI2','MSMDI3','RSL4','RSLA1','RSLA2','RSLA3')
AND c.code = 'Hardbunn';

SELECT c.code, a.parameterid, b.name FROM vannmiljo.conv_parameters a, nivadatabase.begalg_parameter_definitions b, vannmiljo.datatype c
WHERE a.datatype_id = c.datatype_id AND a.niva_parameter_id = b.parameter_id 
AND b.name IN ('PIT','AIP','HBI2')
AND c.code = 'Begroing';

SELECT c.code, a.parameterid, b.index_name FROM vannmiljo.conv_parameters a, nivadatabase.bb_indexes_description b, vannmiljo.datatype c
WHERE a.datatype_id = c.datatype_id AND a.niva_parameter_id = b.index_id 
AND b.index_name IN ('ES100 Grabb','H Grabb','ISI2012 Grabb','NQI1 Grabb','NSI2012 Grabb')
AND c.code = 'Blotbunn';

SELECT c.code, a.parameterid, b.name FROM vannmiljo.conv_parameters a, nivadatabase.bd_parameter_definitions b, vannmiljo.datatype c
WHERE a.datatype_id = c.datatype_id AND a.niva_parameter_id = b.parameter_id 
AND b.name IN ('ASPT')
AND c.code = 'Bunndyr';

SELECT DISTINCT c.code, a.parameterid, b.name FROM vannmiljo.conv_methods a, nivadatabase.method_definitions b, vannmiljo.datatype c
WHERE a.method_id = b.method_id 
AND b.name IN ('Klorofyll A')
AND c.code = 'Water';
```
