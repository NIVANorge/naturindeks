import aquamonitor as am
import requests as req
import json
import pandas as pd
from pandas import ExcelWriter as xlsWriter

ROOT_PATH = "data/"

def downloadNIVA_PTI():
    # PTI -> plankton.parameter_id = 7
    am.Query(where="Plankton.parameter_id=7 and sample_date>=01.01.2020") \
        .export(format="excel", filename="Nivabase-plankton.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_Begroing():
    # PIT -> begroing.parameter_id = 1
    # AIP -> begroing.parameter_id = 2
    # HBI2 -> begroing.parameter_id = 64

    am.Query(where="Begroing.parameter_id in (1,2,64) and sample_date>=01.01.2020") \
        .export(format="excel", filename="Nivabase-begroing.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_ASPT():
    am.Query(where="Bunndyr.parameter_id = 1 and sample_date>=01.01.2020") \
        .export(format="excel", filename="Nivabase-bunndyr.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_Blotbunn():
    am.Query(where="Blotbunn.parameter_id in (111,26,15,11,116) and sample_date>=01.01.2020") \
        .export(format="excel", filename="Nivabase-blotbunn.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_Hardbunn():
    am.Query(where="Hardbunn.parameter_id in (13,189,190,191,187,188,184,185,186,113) and sample_date>=01.01.2020") \
        .export(format="excel", filename="Nivabase-hardbunn.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_MarinChla():
    am.Query(where="station_type_id=3 and Water.parameter_id = 261 and sample_date>=01.01.2020") \
        .export(format="excel", filename="Nivabase-marin-klfa.xlsx") \
        .download(path=ROOT_PATH)


def rewriteNIVA_PTI():
    pti_df = pd.read_excel(f"{ROOT_PATH}Nivabase-plankton.xlsx", "PlanktonParameter", header=1)

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-plankton.xlsx", "StationPoint")

    data_rows = []
    for idx, pti_row in pti_df.iterrows():
        stationid = pti_row[2]
        point = point_df.loc[point_df["StationId"] == stationid].iloc[0]
        latitude = point["Latitude"]
        longitude = point["Longitude"]

        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("miljodir_innsjovannforekomster_f", latitude, longitude)
        if vannforekomst is not None:
            vannforekomstID = vannforekomst["vannforekomstID"]
            okoregion = vannforekomst["okoregion"]
            vanntype = vannforekomst["vanntype"]
            interkalibrering = vannforekomst["interkalibrering"]
        
        sampledate = str(pti_row[6])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate]) == 0:
            data_rows.append({"Latitude": point["Latitude"],
                          "Longitude": point["Longitude"],
                          "Date": sampledate,
                          "PTI": round(pti_row[10], 5),
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomstID,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "Interkalibreringstype": interkalibrering,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "PTI", "Kommunenr",
                                   "VannforekomstID", "Økoregion",
                                   "Vanntype", "Interkalibreringstype", "Station_id"])
    writer = xlsWriter(f"{ROOT_PATH}Plankton-niva.xlsx")
    out_df.to_excel(writer)
    writer.save()


def rewriteNIVA_Begroing():
    begroing_df = pd.read_excel(f"{ROOT_PATH}Nivabase-begroing.xlsx", "BegroingVariables")

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-begroing.xlsx", "StationPoint")

    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-elver.xlsx", "Sheet1")

    data_rows = []
    for idx, begroing_row in begroing_df.iterrows():
        stationid = begroing_row[2]
        point = point_df.loc[point_df["StationId"] == stationid].iloc[0]
        latitude = point["Latitude"]
        longitude = point["Longitude"]

        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_l", latitude, longitude)
        if vannforekomst is not None:
            vannforekomstID = vannforekomst["vannforekomstID"]
            okoregion = vannforekomst["okoregion"]
            vanntype = vannforekomst["vanntype"]
            nasj_vanntype = vannforekomst["nasjonalvanntype"]

        sampledate = str(begroing_row[5])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate]) == 0:
            data_rows.append({"Latitude": point["Latitude"],
                          "Longitude": point["Longitude"],
                          "Date": sampledate,
                          "PIT": round(begroing_row[8], 5),
                          "AIP": round(begroing_row[6], 5),
                          "HBI2": round(begroing_row[7], 5),
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomstID,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "PIT", "AIP", "HBI2", "Kommunenr",
                                   "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type", "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Begroing-niva.xlsx")
    out_df.to_excel(writer)
    writer.save()


def rewriteNIVA_Blotbunn():
    indexes_df = pd.read_excel(f"{ROOT_PATH}Nivabase-blotbunn.xlsx", "BlotbunnVariables", header=1)

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-blotbunn.xlsx", "StationPoint")

    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-kyst.xlsx", "Sheet1")

    data_rows = []
    for idx, index_row in indexes_df.iterrows():
        stationid = index_row[4]
        latitude = None
        longitude = None
        kommune = None
        vannforekomst = None
        try:
            point = point_df.loc[point_df["StationId"] == stationid].iloc[0]
            latitude = point["Latitude"]
            longitude = point["Longitude"]

            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_kyst_f", latitude, longitude)
        except IndexError:
            print(str(stationid) + " mangler i StationPoint")
        okoregion = ""
        vanntype = ""
        nasj_vanntype = ""
        if not vannforekomst is None:
            try:
                vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                if not vannett_row.empty:
                    okoregion = vannett_row["Økoregion"]
                    vanntype = vannett_row["Vanntype"]
                    nasj_vanntype = vannett_row["Nasjonal vanntype"]
            except IndexError:
                print(vannforekomst + " mangler i Vann-nett-kyst.xlsx")

        sampledate = str(index_row[5])[0:10]
        grabb = index_row[6]

        # Check for dublett on StationId / Date / Grabb before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate and r["Grabb"] == grabb]) == 0:
            data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": sampledate,
                          "Grabb": grabb,
                          "ES100": round(index_row[7], 5),
                          "H": round(index_row[8], 5),
                          "ISI": round(index_row[9], 5),
                          "NQI": round(index_row[10], 5),
                          "NSI": round(index_row[11], 5),
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomst,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "Grabb", "ES100", "H", "ISI", "NQI", "NSI", "Kommunenr",
                                   "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type", "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Blotbunn-niva.xlsx")
    out_df.to_excel(writer)
    writer.save()


def rewriteNIVA_Hardbunn():
    indexes_df = pd.read_excel(f"{ROOT_PATH}Nivabase-hardbunn.xlsx", "HardbunnVariables", header=2)

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-hardbunn.xlsx", "StationPoint")

    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-kyst.xlsx", "Sheet1")

    data_rows = []
    for idx, index_row in indexes_df.iterrows():
        stationid = index_row[1]
        latitude = None
        longitude = None
        kommune = None
        vannforekomst = None
        try:
            point = point_df.loc[point_df["StationId"] == stationid].iloc[0]
            latitude = point["Latitude"]
            longitude = point["Longitude"]

            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_kyst_f", latitude, longitude)
        except IndexError:
            print(str(stationid) + " mangler i StationPoint")
        okoregion = ""
        vanntype = ""
        nasj_vanntype = ""
        if not vannforekomst is None:
            try:
                vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                if not vannett_row.empty:
                    okoregion = vannett_row["Økoregion"]
                    vanntype = vannett_row["Vanntype"]
                    nasj_vanntype = vannett_row["Nasjonal vanntype"]
            except IndexError:
                print(vannforekomst + " mangler i Vann-nett-kyst.xlsx")

        sampledate = str(index_row[4])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate]) == 0:

            data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": sampledate,
                          "MSMDI": index_row[7],
                          "MSMDI1": index_row[8],
                          "MSMDI2": index_row[9],
                          "MSMDI3": index_row[10],
                          "RSLA": index_row[13],
                          "RSLA1": index_row[14],
                          "RSLA2": index_row[15],
                          "RSLA3": index_row[16],
                          "RSL4": index_row[11],
                          "RSL5": index_row[12],
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomst,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "MSMDI", "MSMDI1", "MSMDI2", "MSMDI3",
                                   "RSLA", "RSLA1", "RSLA2", "RSLA3", "RSL4", "RSL5", "Kommunenr",
                                   "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type", "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Hardbunn-niva.xlsx")
    out_df.to_excel(writer)
    writer.save()

def rewriteNIVA_MarinPlankton():
    indexes_df = pd.read_excel(f"{ROOT_PATH}Nivabase-plankton.xlsx", "WaterChemistry", header=1)

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-plankton.xlsx", "StationPoint")

    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-kyst.xlsx", "Sheet1")

    data_rows = []
    for idx, index_row in indexes_df.iterrows():
        stationid = index_row[2]
        latitude = None
        longitude = None
        kommune = None
        vannforekomst = None
        try:
            point = point_df.loc[point_df["StationId"] == stationid].iloc[0]
            latitude = point["Latitude"]
            longitude = point["Longitude"]

            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_kyst_f", latitude, longitude)
        except IndexError:
            print(str(stationid) + " mangler i StationPoint")
        okoregion = ""
        vanntype = ""
        nasj_vanntype = ""
        if not vannforekomst is None:
            try:
                vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                if not vannett_row.empty:
                    okoregion = vannett_row["Økoregion"]
                    vanntype = vannett_row["Vanntype"]
                    nasj_vanntype = vannett_row["Nasjonal vanntype"]
            except IndexError:
                print(vannforekomst + " mangler i Vann-nett-kyst.xlsx")

        sampledate = str(index_row[5])[0:10]
        depth1 = index_row[6]
        depth2 = index_row[7]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate
               and r["Depth1"] == depth1 and r["Depth2"] == depth2]) == 0:

            data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": sampledate,
                          "Depth1": depth1,
                          "Depth2": depth2,
                          "ChlA": index_row[8],
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomst,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "Depth1", "Depth2", "ChlA",
                                   "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type",
                                   "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Marin-Plankton-niva.xlsx")
    out_df.to_excel(writer)
    writer.save()



def rewriteNIVA_ASPT():
    aspt_df = pd.read_excel(f"{ROOT_PATH}Nivabase-bunndyr.xlsx", "BunndyrVariables")
    attribute_df = pd.read_excel(f"{ROOT_PATH}Nivabase-bunndyr.xlsx", "StationAttribute")
    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-bunndyr.xlsx", "StationPoint")

    data_rows = []
    for idx, aspt_row in aspt_df.iterrows():
        stationid = aspt_row[2]
        attribute_row = attribute_df.loc[attribute_df["StationId"] == stationid].iloc[0]

        point_row = point_df.loc[point_df["StationId"] == stationid].iloc[0]
        latitude = point_row["Latitude"]
        longitude = point_row["Longitude"]
        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_l", latitude, longitude)

        data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": str(aspt_row[5])[0:10],
                          "ASPT": aspt_row[6],
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomst})

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "ASPT", "Kommunenr", "VannforekomstID"])
    writer = xlsWriter(f"{ROOT_PATH}Bunndyr.xlsx")
    out_df.to_excel(writer)
    writer.save()


def callVannmiljoLokalitet(code):
    url = "https://kart.miljodirektoratet.no/arcgis/rest/services/vannmiljo/MapServer/1/query"
    params = {
        "where": "WaterLocationCode='" + code + "'",
        "outFields": "SourceID",
        "returnGeometry": True,
        "outSR": 4326,
        "f": "pjson"
    }
    try:
        resp = req.post(url, params)
        features = json.loads(resp.text)["features"]
    except Exception as ex:
        print("Feil ved kall på Vannmiljo lokalitet med kode:" + code + ". Feilen var: " + ex)
        features = []

    if len(features) == 1:
        return features[0]
    else:
        return None


def callGeoserverQueryVannforekomst(layer, latitude, longitude):
    url = "https://geoserver.t.niva.no/rest/query/no.niva.public/" + layer + "/distance/4326_" \
          + str(latitude) + "_" + str(longitude) + "_100/features.json"
    resp = req.get(url)
    features = json.loads(resp.text)["features"]
    if len(features) == 1:
        return features[0]
    else:
        return None


def callGeoserverQueryKommuneF(latitude, longitude):
    url = "https://aquamonitor.niva.no/geoserver/rest/query/no.niva/ni_kommune_f/distance/4326_" \
          + str(latitude) + "_" + str(longitude) + "_0.01/features.json"
    resp = req.get(url)
    features = json.loads(resp.text)["features"]
    if len(features) == 1:
        return features[0]["KOMM"]
    else:
        return None


def issueVannmiljoDownloadfile(datatype):
    url = "https://vannmiljowebapi.miljodirektoratet.no/api/Vannmiljo/ExportRegistrations"

    if datatype == "plankton":
        parameters = ["PPTI"]
    elif datatype == "begroing":
        parameters = ["PTI", "AIP", "HBI2"]
    elif datatype == "bløtbunn":
        parameters = ["ES100", "NQI1", "NSI", "MBH"]

    if parameters:
        params = {
            "ParametersIDs": parameters,
            "ExportEmail": "roar.branden@niva.no",
            "ExportType": "redigering",
            "RegType": 1,
            "FromDateSamplingTime": "1900-01-01",
            "ToDateSamplingTime": "2100-01-01",
            "MediumID": "",
            "LatinskNavnID": "",
            "ActivityID": "",
            "AnalysisMethodID": "",
            "SamplingMethodID": "",
            "RegValueOperator": "",
            "RegValue": "",
            "RegValue2": "",
            "UpperDepthOperator": "",
            "UpperDepth": "",
            "UpperDepth2": "",
            "LowerDepthOperator": "",
            "LowerDepth": "",
            "LowerDepth2": "",
            "Employer": "",
            "Contractor": "",
            "WaterLocationIDFilter": [],
            "WaterLocationQueryFilter": ""
        }

        resp = req.post(url, params)
        if resp.status_code != 200:
            print(resp.text)


def rewriteVannmiljo_PTI():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}ppti/VannmiljoEksport_vannreg.xlsx", "VannmiljoEksport")
    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-sjoer.xlsx", "Sheet1")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_f", latitude, longitude)
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            okoregion = ""
            vanntype = ""
            interkalibrering = ""
            if vannforekomst is not None:
                try:
                    vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                    if not vannett_row.empty:
                        okoregion = vannett_row["Økoregion"]
                        vanntype = vannett_row["Vanntype"]
                        interkalibrering = vannett_row["Interkalibreringstype"]
                except IndexError:
                    print(vannforekomst + " mangler i Vann-nett-sjoer.xlsx.")

            stationId = ""
            sourceId = str(vannlok["attributes"]["SourceID"])
            if len(sourceId) > 5 and sourceId[:5] == "NIVA@":
                stationId = sourceId[5:]

            planktonId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 9 and lokalId[:9] == "NIVA@PLA@":
                planktonId = lokalId[9:]

            date = vannmiljo_row["Tid_provetak"][8:10] + "." + \
                   vannmiljo_row["Tid_provetak"][5:7] + "." + \
                   vannmiljo_row["Tid_provetak"][0:4]

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": date,
                "PTI": float(vannmiljo_row["Verdi"].replace(",", ".")),
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomst,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "Interkalibreringstype": interkalibrering,
                "Plankton_parameter_values_id": planktonId,
                "Station_id": stationId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "PTI",
                                              "Kommunenr", "VannforekomstID", "Økoregion",
                                              "Vanntype", "Interkalibreringstype",
                                              "Plankton_parameter_values_id", "Station_id"])
    writer = xlsWriter(f"{ROOT_PATH}Plankton-vannmiljo.xlsx")
    out_df.to_excel(writer)
    writer.save()


def rewriteVannmiljo_Begroing():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}begroing/VannmiljoEksport_vannreg.xlsx", "VannmiljoEksport")
    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-elver.xlsx", "Sheet1")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_l", latitude, longitude)
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            okoregion = ""
            vanntype = ""
            nasj_vanntype = ""
            if vannforekomst is not None:
                try:
                    vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                    if not vannett_row.empty:
                        okoregion = vannett_row["Økoregion"]
                        vanntype = vannett_row["Vanntype"]
                        nasj_vanntype = vannett_row["Nasjonal vanntype"]
                except IndexError:
                    print(vannforekomst + " mangler i Vann-nett-elver.xlsx.")

            stationId = ""
            sourceId = str(vannlok["attributes"]["SourceID"])
            if len(sourceId) > 5 and sourceId[:5] == "NIVA@":
                try:
                     stationId = int(sourceId[5:])
                except:
                    print(sourceId + " seems to be from NIVA, but isn't correct.")

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@BA@":
                nivabaseId = int(lokalId[8:])

            date = vannmiljo_row["Tid_provetak"][8:10] + "." + \
                   vannmiljo_row["Tid_provetak"][5:7] + "." + \
                   vannmiljo_row["Tid_provetak"][0:4]

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": date,
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": float(vannmiljo_row["Verdi"].replace(",", ".")),
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomst,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "Begalg_parameter_values_id": nivabaseId,
                "Station_id": stationId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "Begalg_parameter_values_id", "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Vannmiljo-Begroing.xlsx")
    out_df.to_excel(writer)
    writer.save()


def rewriteVannmiljo_Blotbunn():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}bløtbunn/VannmiljoEksport_vannreg.xlsx", "VannmiljoEksport")
    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-kyst.xlsx", "Sheet1")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_kyst_f", latitude, longitude)
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            okoregion = ""
            vanntype = ""
            nasj_vanntype = ""
            if vannforekomst is not None:
                try:
                    vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                    if not vannett_row.empty:
                        okoregion = vannett_row["Økoregion"]
                        vanntype = vannett_row["Vanntype"]
                        nasj_vanntype = vannett_row["Nasjonal vanntype"]
                except IndexError:
                    print(vannforekomst + " mangler i Vann-nett-kyst.xlsx.")

            stationId = ""
            sourceId = str(vannlok["attributes"]["SourceID"])
            if len(sourceId) > 5 and sourceId[:5] == "NIVA@":
                try:
                     stationId = int(sourceId[5:])
                except:
                    print(sourceId + " seems to be from NIVA, but isn't correct.")

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            grabb = str(vannmiljo_row["Provenr"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@BB@":
                try:
                    nivabaseId = int(lokalId[8:])
                except:
                    print("Dette var ikke helt riktig NIVA-id: " + lokalId)

            date = vannmiljo_row["Tid_provetak"][8:10] + "." + \
                   vannmiljo_row["Tid_provetak"][5:7] + "." + \
                   vannmiljo_row["Tid_provetak"][0:4]

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": date,
                "Grabb": grabb,
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": float(vannmiljo_row["Verdi"].replace(",", ".")),
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomst,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "BB_Index_Values_Value_id": nivabaseId,
                "Station_id": stationId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Grabb", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "BB_Index_Values_id", "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Vannmiljo-Bløtbunn.xlsx")
    out_df.to_excel(writer)
    writer.save()

def rewriteVannmiljo_Hardbunn():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}hardbunn/VannmiljoEksport_vannreg.xlsx", "VannmiljoEksport")
    vannett_df = pd.read_excel(f"{ROOT_PATH}Vann-nett-kyst.xlsx", "Sheet1")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            vannforekomst = callGeoserverQueryVannforekomst("nve_vannforekomst_kyst_f", latitude, longitude)
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            okoregion = ""
            vanntype = ""
            nasj_vanntype = ""
            if vannforekomst is not None:
                try:
                    vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                    if not vannett_row.empty:
                        okoregion = vannett_row["Økoregion"]
                        vanntype = vannett_row["Vanntype"]
                        nasj_vanntype = vannett_row["Nasjonal vanntype"]
                except IndexError:
                    print(vannforekomst + " mangler i Vann-nett-kyst.xlsx.")

            stationId = ""
            sourceId = str(vannlok["attributes"]["SourceID"])
            if len(sourceId) > 5 and sourceId[:5] == "NIVA@":
                try:
                    stationId = int(sourceId[5:])
                except:
                    print(sourceId + " seems to be from NIVA, but isn't correct.")

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@HB@":
                try:
                    nivabaseId = int(lokalId[8:])
                except:
                    print("Dette var ikke helt riktig NIVA-id: " + lokalId)

            date = vannmiljo_row["Tid_provetak"][8:10] + "." + \
                   vannmiljo_row["Tid_provetak"][5:7] + "." + \
                   vannmiljo_row["Tid_provetak"][0:4]

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": date,
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": float(vannmiljo_row["Verdi"].replace(",", ".")),
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomst,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "HB_Parameter_Values_Value_id": nivabaseId,
                "Station_id": stationId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "HB_Parameter_Values_Value_id", "Station_id"])

    writer = xlsWriter(f"{ROOT_PATH}Vannmiljo-Hardbunn.xlsx")
    out_df.to_excel(writer)
    writer.save()

def mergePlankton():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Plankton-vannmiljo.xlsx")
    niva_df = pd.read_excel(f"{ROOT_PATH}Plankton-niva.xlsx")

    for idx, niva_row in niva_df.iterrows():
        match_df = vannmiljo_df[(vannmiljo_df["Station_id"] == niva_row["Station_id"]) & (vannmiljo_df["Date"] == niva_row["Date"])]
        if len(match_df) == 0:
            vannmiljo_df = vannmiljo_df.append(niva_row)
        else:
            for idx2, match_row in match_df.iterrows():
                if not match_row["PTI"] == niva_row["PTI"]:
                    print("Sjekk stasjon:" + str(match_row["Station_id"]) + " på dato:" + match_row["Date"] + " og med id:" + str(match_row["Plankton_parameter_values_id"]))

    out_df = pd.DataFrame(vannmiljo_df, columns=["Latitude", "Longitude", "Date", "PTI",
                                              "Kommunenr", "VannforekomstID", "Økoregion",
                                              "Vanntype", "Interkalibreringstype"])

    writer = xlsWriter(f"{ROOT_PATH}Naturindeks-plankton-PTI.xlsx")
    out_df.to_excel(writer)
    writer.save()

def mergeBegroing():
    niva_df = pd.read_excel(f"{ROOT_PATH}Begroing-niva.xlsx")
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Vannmiljo-Begroing.xlsx")
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        pit = None
        aip = None
        hbi2 = None
        parameter = vannmiljo_row["Parameter"]

        if parameter == "PIT":
            pit = vannmiljo_row["Verdi"]
        elif parameter == "AIP":
            aip = vannmiljo_row["Verdi"]
        elif parameter == "HBI2":
            hbi2 = vannmiljo_row["Verdi"]

        if vannmiljo_row["Station_id"] is not None:
            match_df = niva_df[(niva_df["Station_id"] == vannmiljo_row["Station_id"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                niva_df.append({
                    "Latitude": vannmiljo_row["Latitude"],
                    "Longitude": vannmiljo_row["Longitude"],
                    "Date": vannmiljo_row["Date"],
                    "PIT": pit,
                    "AIP": aip,
                    "HBI2": hbi2,
                    "Kommunenr": vannmiljo_row["Kommunenr"],
                    "VannforekomstID": vannmiljo_row["VannforekomstID"],
                    "Økoregion": vannmiljo_row["Økoregion"],
                    "Vanntype": vannmiljo_row["Vanntype"],
                    "EQR_Type": vannmiljo_row["EQR_Type"],
                    "Station_id": vannmiljo_row["Station_id"]
                }, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if match_row[parameter] is None:
                        match_row[parameter] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[parameter] == vannmiljo_row["Verdi"]:
                            try:
                                print("Sjekk parameter:" + parameter + " på stasjon:" + str(match_row["Station_id"])) +\
                                    " på dato:" + str(match_row["Date"])
                            except:
                                print("Huff")
        else:
            match_df = niva_df[(niva_df["Latitude"] == vannmiljo_row["Latitude"])
                               & (niva_df["Longitude"] == vannmiljo_df["Longitude"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                niva_df.append({
                    "Latitude": vannmiljo_row["Latitude"],
                    "Longitude": vannmiljo_row["Longitude"],
                    "Date": vannmiljo_row["Date"],
                    "PIT": pit,
                    "AIP": aip,
                    "HBI2": hbi2,
                    "Kommunenr": vannmiljo_row["Kommunenr"],
                    "VannforekomstID": vannmiljo_row["VannforekomstID"],
                    "Økoregion": vannmiljo_row["Økoregion"],
                    "Vanntype": vannmiljo_row["Vanntype"],
                    "EQR_Type": vannmiljo_row["EQR_Type"],
                    "Station_id": vannmiljo_row["Station_id"]
                }, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if match_row[parameter] is None:
                        match_row[parameter] = vannmiljo_row["Verdi"]

    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date", "PIT", "AIP", "HBI2",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    writer = xlsWriter(f"{ROOT_PATH}Naturindeks-begroing.xlsx")
    out_df.to_excel(writer)
    writer.save()


def mergeBlotbunn():
    niva_df = pd.read_excel(f"{ROOT_PATH}Blotbunn-niva.xlsx")
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Vannmiljo-Bløtbunn.xlsx")
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        es100 = None
        h = None
        isi = None
        nqi = None
        nsi = None
        parameter = vannmiljo_row["Parameter"]
        field = None
        if parameter == "ES100":
            es100 = vannmiljo_row["Verdi"]
            field = "ES100"
        elif parameter == "MBH":
            h = vannmiljo_row["Verdi"]
            field = "H"
        elif parameter == "NQI1":
            nqi = vannmiljo_row["Verdi"]
            field = "NQI"
        elif parameter == "NSI":
            nsi = vannmiljo_row["Verdi"]
            field = "NSI"
        elif parameter == "ISI_2012":
            isi = vannmiljo_row["Verdi"]
            field = "ISI"

        if not pd.isna(vannmiljo_row["Station_id"]):
            match_df = niva_df[(niva_df["Station_id"] == vannmiljo_row["Station_id"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])
                               & (niva_df["Grabb"] == vannmiljo_row["Grabb"])]
            if len(match_df) == 0:
                niva_df.append({
                    "Latitude": vannmiljo_row["Latitude"],
                    "Longitude": vannmiljo_row["Longitude"],
                    "Date": vannmiljo_row["Date"],
                    "Grabb": vannmiljo_row["Grabb"],
                    "ES100": es100,
                    "H": h,
                    "ISI": isi,
                    "NQI": nqi,
                    "NSI": nsi,
                    "Kommunenr": vannmiljo_row["Kommunenr"],
                    "VannforekomstID": vannmiljo_row["VannforekomstID"],
                    "Økoregion": vannmiljo_row["Økoregion"],
                    "Vanntype": vannmiljo_row["Vanntype"],
                    "EQR_Type": vannmiljo_row["EQR_Type"],
                    "Station_id": vannmiljo_row["Station_id"]
                }, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if pd.isna(match_row[field]):
                        match_row[field] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[field] == vannmiljo_row["Verdi"]:
                            dato = match_row["Date"]
                            stasjon = str(match_row["Station_id"])
                            print("Sjekk parameter:" + field + " på stasjon:" + stasjon + " på dato:" + dato)
        else:
            match_df = niva_df[(niva_df["Latitude"] == vannmiljo_row["Latitude"])
                               & (niva_df["Longitude"] == vannmiljo_row["Longitude"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])
                               & (niva_df["Grabb"] == vannmiljo_row["Grabb"])]
            if len(match_df) == 0:
                niva_df.append({
                    "Latitude": vannmiljo_row["Latitude"],
                    "Longitude": vannmiljo_row["Longitude"],
                    "Date": vannmiljo_row["Date"],
                    "Grabb": vannmiljo_row["Grabb"],
                    "ES100": es100,
                    "H": h,
                    "ISI": isi,
                    "NQI": nqi,
                    "NSI": nsi,
                    "Kommunenr": vannmiljo_row["Kommunenr"],
                    "VannforekomstID": vannmiljo_row["VannforekomstID"],
                    "Økoregion": vannmiljo_row["Økoregion"],
                    "Vanntype": vannmiljo_row["Vanntype"],
                    "EQR_Type": vannmiljo_row["EQR_Type"],
                    "Station_id": vannmiljo_row["Station_id"]
                }, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if pd.isna(match_row[parameter]):
                        match_row[parameter] = vannmiljo_row["Verdi"]

    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date", "Grabb", "ES100", "H", "ISI", "NQI", "NSI",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    writer = xlsWriter(f"{ROOT_PATH}Naturindeks-blotbunn.xlsx")
    out_df.to_excel(writer)
    writer.save()


def mergeHardbunn():
    niva_df = pd.read_excel(f"{ROOT_PATH}Hardbunn-niva.xlsx")
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Vannmiljo-Hardbunn.xlsx")
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        msmdi1 = None
        msmdi2 = None
        msmdi3 = None
        rsla1 = None
        rsla2 = None
        rsla3 = None
        rsl4 = None
        rsl5 = None
        parameter = vannmiljo_row["Parameter"]
        if parameter == "MSMDI1":
            msmdi1 = vannmiljo_row["Verdi"]
        elif parameter == "MSMDI2":
            msmdi2 = vannmiljo_row["Verdi"]
        elif parameter == "MSMDI3":
            msmdi3 = vannmiljo_row["Verdi"]
        elif parameter == "RSLA1":
            rsla1 = vannmiljo_row["Verdi"]
        elif parameter == "RSLA2":
            rsla2 = vannmiljo_row["Verdi"]
        elif parameter == "RSLA3":
            rsla3 = vannmiljo_row["Verdi"]
        elif parameter == "RSL4":
            rsl4 = vannmiljo_row["Verdi"]
        elif parameter == "RSL5":
            rsl5 = vannmiljo_row["Verdi"]

        if not pd.isna(vannmiljo_row["Station_id"]):
            match_df = niva_df[(niva_df["Station_id"] == vannmiljo_row["Station_id"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                niva_df.append({
                    "Latitude": vannmiljo_row["Latitude"],
                    "Longitude": vannmiljo_row["Longitude"],
                    "Date": vannmiljo_row["Date"],
                    "MSMDI": "",
                    "MSMDI1": msmdi1,
                    "MSMDI2": msmdi2,
                    "MSMDI3": msmdi3,
                    "RSLA": "",
                    "RSLA1": rsla1,
                    "RSLA2": rsla2,
                    "RSLA3": rsla3,
                    "RSL4": rsl4,
                    "RSL5": rsl5,
                    "Kommunenr": vannmiljo_row["Kommunenr"],
                    "VannforekomstID": vannmiljo_row["VannforekomstID"],
                    "Økoregion": vannmiljo_row["Økoregion"],
                    "Vanntype": vannmiljo_row["Vanntype"],
                    "EQR_Type": vannmiljo_row["EQR_Type"],
                    "Station_id": vannmiljo_row["Station_id"]
                }, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if pd.isna(match_row[parameter]):
                        match_row[parameter] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[parameter] == vannmiljo_row["Verdi"]:
                            dato = match_row["Date"]
                            stasjon = match_row["Station_id"]
                            print("Sjekk parameter:" + parameter + " på stasjon:" + str(stasjon) + " på dato:" + dato)
        else:
            match_df = niva_df[(niva_df["Latitude"] == vannmiljo_row["Latitude"])
                               & (niva_df["Longitude"] == vannmiljo_row["Longitude"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                niva_df.append({
                    "Latitude": vannmiljo_row["Latitude"],
                    "Longitude": vannmiljo_row["Longitude"],
                    "Date": vannmiljo_row["Date"],
                    "MSMDI": "",
                    "MSMDI1": msmdi1,
                    "MSMDI2": msmdi2,
                    "MSMDI3": msmdi3,
                    "RSLA": "",
                    "RSLA1": rsla1,
                    "RSLA2": rsla2,
                    "RSLA3": rsla3,
                    "RSL4": rsl4,
                    "RSL5": rsl5,
                    "Kommunenr": vannmiljo_row["Kommunenr"],
                    "VannforekomstID": vannmiljo_row["VannforekomstID"],
                    "Økoregion": vannmiljo_row["Økoregion"],
                    "Vanntype": vannmiljo_row["Vanntype"],
                    "EQR_Type": vannmiljo_row["EQR_Type"],
                    "Station_id": vannmiljo_row["Station_id"]
                }, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if pd.isna(match_row[parameter]):
                        match_row[parameter] = vannmiljo_row["Verdi"]

    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date",
                                            "MSMDI", "MSMDI1", "MSMDI2", "MSMDI3",
                                            "RSLA", "RSLA1",
                                            "RSLA2", "RSLA3", "RSL4", "RSL5",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    writer = xlsWriter(f"{ROOT_PATH}Naturindeks-Hardbunn.xlsx")
    out_df.to_excel(writer)
    writer.save()

def rewriteKommuneVannforekomst(resultat_fil, kommune_fil, vann_nett_fil):
    kommuneVannforekomst_df = pd.read_excel(f"{ROOT_PATH}{kommune_fil}")  # Fila kommune_vannforekomst_f kommer fra en spatial join operasjon i QGIS(??).
                                                        # Meny Vektor -> "Slå sammen attributter basert på plassering"
    vannett_df = pd.read_excel(f"{ROOT_PATH}{vann_nett_fil}")
    data_rows = []

    for idx, kommuneVannforekomst_row in kommuneVannforekomst_df.iterrows():
        vannforekomst = kommuneVannforekomst_row["vannforekomstid"]
        kommune = kommuneVannforekomst_row["KOMM"]
        print(vannforekomst + " i " + str(kommune))

        okoregion = ""
        vanntype = ""
        if vannforekomst is not None:
            try:
                vannett_row = vannett_df.loc[vannett_df["VannforekomstID"] == vannforekomst].iloc[0]
                if not vannett_row.empty:
                    okoregion = vannett_row["Økoregion"]
                    vanntype = vannett_row["Vanntype"]
            except IndexError:
                print(vannforekomst + " mangler i " + vann_nett_fil)

        data_rows.append({
            "Kommunenr": kommune,
            "VannforekomstID": vannforekomst,
            "Økoregion": okoregion,
            "Vanntype": vanntype
        })

    out_df = pd.DataFrame(data_rows, columns=["Kommunenr", "VannforekomstID", "Økoregion", "Vanntype"])
    writer = xlsWriter(f"{ROOT_PATH}{resultat_fil}")
    out_df.to_excel(writer)
    writer.save()
