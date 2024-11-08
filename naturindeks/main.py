import aquamonitor as am
import requests
from requests.adapters import HTTPAdapter, Retry
import json
import pandas as pd
from pandas import ExcelWriter

ROOT_PATH = "data/"
WHERE_PERIOD = "sample_date>=01.01.2020"

req = requests.Session()
retries = Retry(total=5, backoff_factor=0.1)
req.mount("https://", HTTPAdapter(max_retries=retries))


def downloadNIVA_PTI():
    # PTI -> plankton.parameter_id = 7
    am.Query(where=f"Plankton.parameter_id=7 and { WHERE_PERIOD }") \
        .export(format="excel", filename="Nivabase-plankton.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_Begroing():
    # PIT -> begroing.parameter_id = 1
    # AIP -> begroing.parameter_id = 2
    # HBI2 -> begroing.parameter_id = 64

    am.Query(where=f"Begroing.parameter_id in (1,2,64) and { WHERE_PERIOD }") \
        .export(format="excel", filename="Nivabase-begroing.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_ASPT():
    am.Query(where=f"Bunndyr.parameter_id = 1 and { WHERE_PERIOD }") \
        .export(format="excel", filename="Nivabase-bunndyr.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_Blotbunn():
    am.Query(where=f"Blotbunn.parameter_id in (111,26,15,11,116) and { WHERE_PERIOD }") \
        .export(format="excel", filename="Nivabase-blotbunn.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_Hardbunn():
    am.Query(where=f"Hardbunn.parameter_id in (13,189,190,191,187,188,184,185,186,113) and { WHERE_PERIOD }") \
        .export(format="excel", filename="Nivabase-hardbunn.xlsx") \
        .download(path=ROOT_PATH)


def downloadNIVA_MarinChla():
    am.Query(where=f"station_type_id=3 and Water.parameter_id = 261 and { WHERE_PERIOD }") \
        .export(format="excel", filename="Nivabase-marin-klfa.xlsx") \
        .download(path=ROOT_PATH)


def rewriteNIVA_PTI():
    pti_df = pd.read_excel(f"{ROOT_PATH}Nivabase-plankton.xlsx", "Plankton parameter values", header=0)

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-plankton.xlsx", "Stations")

    data_rows = []
    for idx, pti_row in pti_df.iterrows():
        stationid = pti_row["Station id"]
        point = point_df.loc[point_df["Station Id"] == stationid].iloc[0]
        latitude = point["Latitude"]
        longitude = point["Longitude"]

        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("miljodir_innsjovannforekomster_f", \
                                                        latitude, longitude)
        if vannforekomst is not None:
            vannforekomstID = vannforekomst["vannforekomstid"]
            okoregion = vannforekomst["okoregion"]
            vanntype = vannforekomst["vanntype"]
            interkalibrering = vannforekomst["interkalibreringstype"]
        
        sampledate = str(pti_row["Sample date"])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid \
                and r["Date"] == sampledate]) == 0:
            data_rows.append({"Latitude": point["Latitude"],
                          "Longitude": point["Longitude"],
                          "Date": sampledate,
                          "PTI": round(pti_row[8], 8),
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
    with ExcelWriter(f"{ROOT_PATH}Plankton-niva.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteNIVA_Begroing():
    begroing_df = pd.read_excel(f"{ROOT_PATH}Nivabase-begroing.xlsx", "Begroing variabler")

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-begroing.xlsx", "Stations")

    data_rows = []
    for idx, begroing_row in begroing_df.iterrows():
        stationid = begroing_row["Station id"]
        point = point_df.loc[point_df["Station Id"] == stationid].iloc[0]
        latitude = point["Latitude"]
        longitude = point["Longitude"]

        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("miljodir_elvevannforekomster_l", latitude, longitude)
        vannforekomstID = None
        okoregion = None
        vanntype = None
        nasj_vanntype = None
        if vannforekomst is not None:
            vannforekomstID = vannforekomst["vannforekomstid"]
            okoregion = vannforekomst["okoregion"]
            vanntype = vannforekomst["vanntype"]
            nasj_vanntype = vannforekomst["nasjonalvanntype"]

        sampledate = str(begroing_row["Sample date"])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate]) == 0:
            data_rows.append({"Latitude": point["Latitude"],
                          "Longitude": point["Longitude"],
                          "Date": sampledate,
                          "PIT": round(begroing_row["PIT"], 5),
                          "AIP": round(begroing_row["AIP"], 5),
                          "HBI2": round(begroing_row["HBI2"], 5),
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomstID,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "PIT", "AIP", "HBI2", "Kommunenr",
                                   "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type", "Station_id"])

    with ExcelWriter(f"{ROOT_PATH}Begroing-niva.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteNIVA_Blotbunn():
    indexes_df = pd.read_excel(f"{ROOT_PATH}Nivabase-blotbunn.xlsx", "Bløtbunn variabler")

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-blotbunn.xlsx", "Stations")

    data_rows = []
    for idx, index_row in indexes_df.iterrows():
        stationid = index_row["Station id"]
        point = point_df.loc[point_df["Station Id"] == stationid].iloc[0]
        latitude = point["Latitude"]
        longitude = point["Longitude"]

        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("miljodir_kystvannforekomster_f", latitude, longitude)
        if vannforekomst is not None:
            vannforekomstid = vannforekomst["vannforekomstid"]
            okoregion = vannforekomst["okoregion"]
            vanntype = vannforekomst["vanntype"]
            nasjonalvanntype = vannforekomst["nasjonalvanntype"]

        sampledate = str(index_row["Sample date"])[0:10]
        grabb = index_row["Grab"]

        # Check for dublett on StationId / Date / Grabb before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate and r["Grabb"] == grabb]) == 0:
            data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": sampledate,
                          "Grabb": grabb,
                          "ES100": round(index_row["ES100 Grabb"], 5),
                          "H": round(index_row["H Grabb"], 5),
                          "ISI": round(index_row["ISI2012 Grabb"], 5),
                          "NQI": round(index_row["NQI1 Grabb"], 5),
                          "NSI": round(index_row["NSI2012 Grabb"], 5),
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomstid,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasjonalvanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "Grabb", "ES100", "H", "ISI", "NQI", "NSI", "Kommunenr",
                                   "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type", "Station_id"])
    with ExcelWriter(f"{ROOT_PATH}Blotbunn-niva.xlsx") as writer:
        out_df.to_excel(writer)



def rewriteNIVA_Hardbunn():
    indexes_df = pd.read_excel(f"{ROOT_PATH}Nivabase-hardbunn.xlsx", "HardbunnVariables", header=2)

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-hardbunn.xlsx", "Stations")

    data_rows = []
    for idx, index_row in indexes_df.iterrows():
        stationid = index_row[1]
        point = point_df.loc[point_df["Station Id"] == stationid].iloc[0]
        latitude = point["Latitude"]
        longitude = point["Longitude"]

        kommune = callGeoserverQueryKommuneF(latitude, longitude)
        vannforekomst = callGeoserverQueryVannforekomst("miljodir_kystvannforekomster_f", latitude, longitude)
        vannforekomstID = None
        okoregion = None
        vanntype = None
        nasj_vanntype = None
        if vannforekomst is not None:
            vannforekomstID = vannforekomst["vannforekomstid"]
            okoregion = vannforekomst["okoregion"]
            vanntype = vannforekomst["vanntype"]
            nasj_vanntype = vannforekomst["nasjonalvanntype"]

        sampledate = str(index_row[4])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate]) == 0:

            data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": sampledate,
                          "MSMDI1": index_row[7],
                          "MSMDI2": index_row[8],
                          "MSMDI3": index_row[9],
                          "RSL4": index_row[10],
                          "RSLA1": index_row[11],
                          "RSLA2": index_row[12],
                          "RSLA3": index_row[13],
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomstID,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "MSMDI1", "MSMDI2", "MSMDI3",
                                   "RSL4", "RSLA1", "RSLA2", "RSLA3", "Kommunenr",
                                   "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type", "Station_id"])

    with ExcelWriter(f"{ROOT_PATH}Hardbunn-niva.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteNIVA_MarinPlankton():
    indexes_df = pd.read_excel(f"{ROOT_PATH}Nivabase-marin-klfa.xlsx", "Water chemistry")

    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-marin-klfa.xlsx", "Stations")

    data_rows = []
    for idx, index_row in indexes_df.iterrows():
        stationid = index_row["Station id"]
        sampledate = str(index_row["Sample date"])[0:10]
        depth1 = index_row["Depth 1"]
        depth2 = index_row["Depth 2"]
        # Check for dublett on StationId / Date / depths before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate
               and r["Depth1"] == depth1 and r["Depth2"] == depth2]) == 0:

            point = point_df.loc[point_df["Station Id"] == stationid].iloc[0]
            latitude = point["Latitude"]
            longitude = point["Longitude"]

            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_kystvannforekomster_f", latitude, longitude)
            vannforekomstID = None
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                nasj_vanntype = vannforekomst["nasjonalvanntype"]

            data_rows.append({"Latitude": latitude,
                          "Longitude": longitude,
                          "Date": sampledate,
                          "Depth1": depth1,
                          "Depth2": depth2,
                          "ChlA": index_row["KlfA\nµg/l"],
                          "Kommunenr": kommune,
                          "VannforekomstID": vannforekomstID,
                          "Økoregion": okoregion,
                          "Vanntype": vanntype,
                          "EQR_Type": nasj_vanntype,
                          "Station_id": stationid})

    out_df = pd.DataFrame(data_rows,
                          columns=["Latitude", "Longitude", "Date", "Depth1", "Depth2", "ChlA",
                                   "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type",
                                   "Station_id"])

    with ExcelWriter(f"{ROOT_PATH}Marin-Plankton-niva.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteNIVA_Bunndyr():
    aspt_df = pd.read_excel(f"{ROOT_PATH}Nivabase-bunndyr.xlsx", "BunndyrVariables")
    point_df = pd.read_excel(f"{ROOT_PATH}Nivabase-bunndyr.xlsx", "Stations")

    data_rows = []
    for idx, aspt_row in aspt_df.iterrows():
        stationid = aspt_row["StationId"]
        sampledate = str(aspt_row["SampleDate"])[0:10]

        # Check for dublett on StationId / Date before appending.
        if len([r for r in data_rows if r["Station_id"] == stationid and r["Date"] == sampledate]) == 0:
            point = point_df.loc[point_df["Station Id"] == stationid].iloc[0]
            latitude = point["Latitude"]
            longitude = point["Longitude"]
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_elvevannforekomster_l", latitude, longitude)
            vannforekomstID = None
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                nasj_vanntype = vannforekomst["nasjonalvanntype"]

            data_rows.append({"Latitude": latitude,
                              "Longitude": longitude,
                              "Date": sampledate,
                              "ASPT": aspt_row["ASPT"],
                              "Kommunenr": kommune,
                              "VannforekomstID": vannforekomstID,
                              "Økoregion": okoregion,
                              "Vanntype": vanntype,
                              "EQR_Type": nasj_vanntype,
                              "Station_id": stationid})

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "ASPT", "Kommunenr", "VannforekomstID", 
                                              "Økoregion", "Vanntype", "EQR_Type", "Station_id"])
    
    with ExcelWriter(f"{ROOT_PATH}Bunndyr-niva.xlsx") as writer:
        out_df.to_excel(writer)



def rewriteVannmiljo_PTI():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}WaterRegistrationExport-plankton.xlsx", "VannmiljoEksport")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_innsjovannforekomster_f", \
                                                            latitude, longitude)
            okoregion = None
            vanntype = None
            interkalibrering = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                interkalibrering = vannforekomst["interkalibreringstype"]

            planktonId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 9 and lokalId[:9] == "NIVA@PLA@":
                planktonId = lokalId[9:]

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": vannmiljo_row["Tid_provetak"][0:10],
                "PTI": vannmiljo_row["Verdi"],
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomstID,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "Interkalibreringstype": interkalibrering,
                "Plankton_parameter_values_id": planktonId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "PTI",
                                              "Kommunenr", "VannforekomstID", "Økoregion",
                                              "Vanntype", "Interkalibreringstype",
                                              "Plankton_parameter_values_id"])
    with ExcelWriter(f"{ROOT_PATH}Vannmiljo-plankton.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteVannmiljo_Begroing():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}WaterRegistrationExport-begroing.xlsx", "VannmiljoEksport")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_elvevannforekomster_l", \
                                                            latitude, longitude)
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                nasj_vanntype = vannforekomst["nasjonalvanntype"]

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@BA@":
                nivabaseId = int(lokalId[8:])

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": vannmiljo_row["Tid_provetak"][0:10],
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": vannmiljo_row["Verdi"],
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomstID,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "Begalg_parameter_values_id": nivabaseId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "Begalg_parameter_values_id"])

    with ExcelWriter(f"{ROOT_PATH}Vannmiljo-Begroing.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteVannmiljo_Bunndyr():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}WaterRegistrationExport-bunndyr.xlsx", "VannmiljoEksport")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_elvevannforekomster_l", \
                                                            latitude, longitude)
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                nasj_vanntype = vannforekomst["nasjonalvanntype"]

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@BD@":
                nivabaseId = int(lokalId[8:])

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": vannmiljo_row["Tid_provetak"][0:10],
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": vannmiljo_row["Verdi"],
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomstID,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "Bd_parameter_values_id": nivabaseId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "Bd_parameter_values_id"])

    with ExcelWriter(f"{ROOT_PATH}Vannmiljo-Bunndyr.xlsx") as writer:
        out_df.to_excel(writer)



def rewriteVannmiljo_Blotbunn():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}WaterRegistrationExport-blotbunn.xlsx", "VannmiljoEksport")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_kystvannforekomster_f", \
                                                            latitude, longitude)
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            vannforekomstID = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                nasj_vanntype = vannforekomst["nasjonalvanntype"]

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            grabb = str(vannmiljo_row["Provenr"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@BB@":
                try:
                    nivabaseId = int(lokalId[8:])
                except:
                    print("Dette var ikke helt riktig NIVA-id: " + lokalId)

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": vannmiljo_row["Tid_provetak"][0:10],
                "Grabb": grabb,
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": vannmiljo_row["Verdi"],
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomstID,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "BB_Index_Values_Value_id": nivabaseId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Grabb", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "BB_Index_Values_id"])

    with ExcelWriter(f"{ROOT_PATH}Vannmiljo-Bløtbunn.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteVannmiljo_Hardbunn():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}WaterRegistrationExport-hardbunn.xlsx", "VannmiljoEksport")
    data_rows = []
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
        if vannlok is not None:
            latitude = vannlok["geometry"]["y"]
            longitude = vannlok["geometry"]["x"]
            kommune = callGeoserverQueryKommuneF(latitude, longitude)
            vannforekomst = callGeoserverQueryVannforekomst("miljodir_kystvannforekomster_f", \
                                                            latitude, longitude)
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            vannforekomstID = None
            if vannforekomst is not None:
                vannforekomstID = vannforekomst["vannforekomstid"]
                okoregion = vannforekomst["okoregion"]
                vanntype = vannforekomst["vanntype"]
                nasj_vanntype = vannforekomst["nasjonalvanntype"]

            nivabaseId = ""
            lokalId = str(vannmiljo_row["ID_lokal"])
            if len(lokalId) > 8 and lokalId[:8] == "NIVA@HB@":
                try:
                    nivabaseId = int(lokalId[8:])
                except:
                    print("Dette var ikke helt riktig NIVA-id: " + lokalId)

            data_rows.append({
                "Latitude": latitude,
                "Longitude": longitude,
                "Date": vannmiljo_row["Tid_provetak"][0:10],
                "Parameter": vannmiljo_row["Parameter_id"],
                "Verdi": vannmiljo_row["Verdi"],
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomstID,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype,
                "HB_Parameter_Values_Value_id": nivabaseId
            })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "HB_Parameter_Values_Value_id"])

    with ExcelWriter(f"{ROOT_PATH}Vannmiljo-Hardbunn.xlsx") as writer:
        out_df.to_excel(writer)


def rewriteVannmiljo_Marin():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}WaterRegistrationExport-marin.xlsx", "VannmiljoEksport")
    data_rows = []
    vannlok_set = {}
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        vannlok_code = vannmiljo_row["Vannlok_kode"]
        if vannlok_code not in vannlok_set:
            kommune = None
            latitude = None
            longitude = None
            okoregion = None
            vanntype = None
            nasj_vanntype = None
            vannforekomstID = None
            vannlok = callVannmiljoLokalitet(vannmiljo_row["Vannlok_kode"])
            if vannlok is not None:
                latitude = vannlok["geometry"]["y"]
                longitude = vannlok["geometry"]["x"]
                kommune = callGeoserverQueryKommuneF(latitude, longitude)
                vannforekomst = callGeoserverQueryVannforekomst("miljodir_kystvannforekomster_f", \
                                                                latitude, longitude)
                if vannforekomst is not None:
                    vannforekomstID = vannforekomst["vannforekomstid"]
                    okoregion = vannforekomst["okoregion"]
                    vanntype = vannforekomst["vanntype"]
                    nasj_vanntype = vannforekomst["nasjonalvanntype"]
            meta = {
                "Latitude": latitude,
                "Longitude": longitude,
                "Kommunenr": kommune,
                "VannforekomstID": vannforekomstID,
                "Økoregion": okoregion,
                "Vanntype": vanntype,
                "EQR_Type": nasj_vanntype
            }
            vannlok_set[vannlok_code] = meta
        else:
            meta = vannlok_set[vannlok_code]

        nivabaseId = ""
        lokalId = str(vannmiljo_row["ID_lokal"])
        if len(lokalId) > 8 and lokalId[:8] == "NIVA@WC@":
            try:
                nivabaseId = int(lokalId[8:])
            except:
                print("Dette var ikke helt riktig NIVA-id: " + lokalId)

        data_rows.append({
            "Latitude": meta["Latitude"],
            "Longitude": meta["Longitude"],
            "Date": vannmiljo_row["Tid_provetak"][0:10],
            "Depth1": vannmiljo_row["Ovre_dyp"],
            "Depth2": vannmiljo_row["Nedre_dyp"],
            "Parameter": vannmiljo_row["Parameter_id"],
            "Verdi": vannmiljo_row["Verdi"],
            "Kommunenr": meta["Kommunenr"],
            "VannforekomstID": meta["VannforekomstID"],
            "Økoregion": meta["Økoregion"],
            "Vanntype": meta["Vanntype"],
            "EQR_Type": meta["EQR_Type"],
            "WC_Value_id": nivabaseId
        })

    out_df = pd.DataFrame(data_rows, columns=["Latitude", "Longitude", "Date", "Depth1", "Depth2", "Parameter", "Verdi",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype",
                                              "EQR_Type", "WC_Value_id"])

    with ExcelWriter(f"{ROOT_PATH}Vannmiljo-Marin.xlsx") as writer:
        out_df.to_excel(writer)

def mergePlankton():
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Vannmiljo-Plankton.xlsx")
    niva_df = pd.read_excel(f"{ROOT_PATH}Plankton-niva.xlsx")

    for idx, niva_row in niva_df.iterrows():
        match_df = vannmiljo_df[(vannmiljo_df["VannforekomstID"] == niva_row["VannforekomstID"]) & (vannmiljo_df["Date"] == niva_row["Date"])]
        if len(match_df) == 0:
            new_df = pd.DataFrame([niva_row])
            vannmiljo_df = pd.concat([vannmiljo_df, new_df], axis=0, ignore_index=True)
        else:
            for idx2, match_row in match_df.iterrows():
                if not match_row["PTI"] == niva_row["PTI"]:
                    print("Sjekk PTI på dato:" + match_row["Date"] + " og med vannforekomstID:" + match_row["VannforekomstID"])

    out_df = pd.DataFrame(vannmiljo_df, columns=["Latitude", "Longitude", "Date", "PTI",
                                              "Kommunenr", "VannforekomstID", "Økoregion",
                                              "Vanntype", "Interkalibreringstype"])

    with ExcelWriter(f"{ROOT_PATH}Naturindeks-plankton.xlsx") as writer:
        out_df.to_excel(writer)


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

        if vannmiljo_row["VannforekomstID"] is not None:
            match_df = niva_df[(niva_df["VannforekomstID"] == vannmiljo_row["VannforekomstID"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                new_df = pd.DataFrame({
                    "Latitude": [vannmiljo_row["Latitude"]],
                    "Longitude": [vannmiljo_row["Longitude"]],
                    "Date": [vannmiljo_row["Date"]],
                    "PIT": [pit],
                    "AIP": [aip],
                    "HBI2": [hbi2],
                    "Kommunenr": [vannmiljo_row["Kommunenr"]],
                    "VannforekomstID": [vannmiljo_row["VannforekomstID"]],
                    "Økoregion": [vannmiljo_row["Økoregion"]],
                    "Vanntype": [vannmiljo_row["Vanntype"]],
                    "EQR_Type": [vannmiljo_row["EQR_Type"]]
                })
                niva_df = pd.concat([niva_df, new_df], axis=0, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if match_row[parameter] is None:
                        match_row[parameter] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[parameter] == vannmiljo_row["Verdi"]:
                            try:
                                print("Sjekk parameter:" + parameter + " på vannforekomst:" + match_row["VannforekomstID"] \
                                    + " på dato:" + str(match_row["Date"]))
                            except:
                                print("Huff")


    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date", "PIT", "AIP", "HBI2",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    with ExcelWriter(f"{ROOT_PATH}Naturindeks-begroing.xlsx") as writer:
        out_df.to_excel(writer)


def mergeBunndyr():
    niva_df = pd.read_excel(f"{ROOT_PATH}Bunndyr-niva.xlsx")
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Vannmiljo-Bunndyr.xlsx")
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        aspt = None
        parameter = vannmiljo_row["Parameter"]

        if parameter == "ASPT":
            aspt = vannmiljo_row["Verdi"]

        if vannmiljo_row["VannforekomstID"] is not None:
            match_df = niva_df[(niva_df["VannforekomstID"] == vannmiljo_row["VannforekomstID"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                new_df = pd.DataFrame({
                    "Latitude": [vannmiljo_row["Latitude"]],
                    "Longitude": [vannmiljo_row["Longitude"]],
                    "Date": [vannmiljo_row["Date"]],
                    "ASPT": [aspt],
                    "Kommunenr": [vannmiljo_row["Kommunenr"]],
                    "VannforekomstID": [vannmiljo_row["VannforekomstID"]],
                    "Økoregion": [vannmiljo_row["Økoregion"]],
                    "Vanntype": [vannmiljo_row["Vanntype"]],
                    "EQR_Type": [vannmiljo_row["EQR_Type"]]
                })
                niva_df = pd.concat([niva_df, new_df], axis=0, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if match_row[parameter] is None:
                        match_row[parameter] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[parameter] == vannmiljo_row["Verdi"]:
                            try:
                                print("Sjekk parameter:" + parameter + " på vannforekomst:" \
                                      + match_row["VannforekomstID"] + " på dato:" + str(match_row["Date"]))
                            except:
                                print("Huff")


    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date", "ASPT", "Kommunenr",
                                                    "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    with ExcelWriter(f"{ROOT_PATH}Naturindeks-bunndyr.xlsx") as writer:
        out_df.to_excel(writer)



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

        if not pd.isna(vannmiljo_row["VannforekomstID"]):
            match_df = niva_df[(niva_df["VannforekomstID"] == vannmiljo_row["VannforekomstID"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])
                               & (niva_df["Grabb"] == vannmiljo_row["Grabb"])]
            if len(match_df) == 0:
                new_df = pd.DataFrame({
                    "Latitude": [vannmiljo_row["Latitude"]],
                    "Longitude": [vannmiljo_row["Longitude"]],
                    "Date": [vannmiljo_row["Date"]],
                    "Grabb": [vannmiljo_row["Grabb"]],
                    "ES100": [es100],
                    "H": [h],
                    "ISI": [isi],
                    "NQI": [nqi],
                    "NSI": [nsi],
                    "Kommunenr": [vannmiljo_row["Kommunenr"]],
                    "VannforekomstID": [vannmiljo_row["VannforekomstID"]],
                    "Økoregion": [vannmiljo_row["Økoregion"]],
                    "Vanntype": [vannmiljo_row["Vanntype"]],
                    "EQR_Type": [vannmiljo_row["EQR_Type"]]
                })
                pd.concat([niva_df, new_df], axis=0, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if pd.isna(match_row[field]):
                        match_row[field] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[field] == vannmiljo_row["Verdi"]:
                            dato = match_row["Date"]
                            forekomst = str(match_row["VannforekomstID"])
                            print("Sjekk parameter:" + field + " på vannforekomst:" + forekomst + " på dato:" + dato)

    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date", "Grabb", "ES100", "H", "ISI", "NQI", "NSI",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    with ExcelWriter(f"{ROOT_PATH}Naturindeks-blotbunn.xlsx") as writer:
        out_df.to_excel(writer)


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


        if not pd.isna(vannmiljo_row["VannforekomstID"]):
            match_df = niva_df[(niva_df["VannforekomstID"] == vannmiljo_row["VannforekomstID"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])]
            if len(match_df) == 0:
                new_df = pd.DataFrame({
                    "Latitude": [vannmiljo_row["Latitude"]],
                    "Longitude": [vannmiljo_row["Longitude"]],
                    "Date": [vannmiljo_row["Date"]],
                    "MSMDI": [""],
                    "MSMDI1": [msmdi1],
                    "MSMDI2": [msmdi2],
                    "MSMDI3": [msmdi3],
                    "RSLA": [""],
                    "RSLA1": [rsla1],
                    "RSLA2": [rsla2],
                    "RSLA3": [rsla3],
                    "RSL4": [rsl4],
                    "Kommunenr": [vannmiljo_row["Kommunenr"]],
                    "VannforekomstID": [vannmiljo_row["VannforekomstID"]],
                    "Økoregion": [vannmiljo_row["Økoregion"]],
                    "Vanntype": [vannmiljo_row["Vanntype"]],
                    "EQR_Type": [vannmiljo_row["EQR_Type"]]
                })
                niva_df = pd.concat([niva_df, new_df], axis=0, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if pd.isna(match_row[parameter]):
                        match_row[parameter] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[parameter] == vannmiljo_row["Verdi"]:
                            dato = match_row["Date"]
                            forekomst = match_row["VannforekomstID"]
                            print("Sjekk parameter:" + parameter + " på vannforekomst:" + forekomst + " på dato:" + dato)


    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date",
                                            "MSMDI", "MSMDI1", "MSMDI2", "MSMDI3",
                                            "RSLA", "RSLA1",
                                            "RSLA2", "RSLA3", "RSL4", "RSL5",
                                              "Kommunenr", "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    with ExcelWriter(f"{ROOT_PATH}Naturindeks-hardbunn.xlsx") as writer:
        out_df.to_excel(writer)


def mergeMarinPlankton():
    niva_df = pd.read_excel(f"{ROOT_PATH}Marin-Plankton-niva.xlsx")
    vannmiljo_df = pd.read_excel(f"{ROOT_PATH}Vannmiljo-Marin.xlsx")
    for idx, vannmiljo_row in vannmiljo_df.iterrows():
        klfa = None
        parameter = vannmiljo_row["Parameter"]

        if parameter == "KLFA":
            klfa = vannmiljo_row["Verdi"]

        if vannmiljo_row["VannforekomstID"] is not None:
            match_df = niva_df[(niva_df["VannforekomstID"] == vannmiljo_row["VannforekomstID"])
                               & (niva_df["Date"] == vannmiljo_row["Date"])
                               & (niva_df["Depth1"] == vannmiljo_row["Depth1"])
                               & (niva_df["Depth2"] == vannmiljo_row["Depth2"])]
            if len(match_df) == 0:
                new_df = pd.DataFrame({
                    "Latitude": [vannmiljo_row["Latitude"]],
                    "Longitude": [vannmiljo_row["Longitude"]],
                    "Date": [vannmiljo_row["Date"]],
                    "Depth1": [vannmiljo_row["Depth1"]],
                    "Depth2": [vannmiljo_row["Depth2"]],
                    "ChlA": [klfa],
                    "Kommunenr": [vannmiljo_row["Kommunenr"]],
                    "VannforekomstID": [vannmiljo_row["VannforekomstID"]],
                    "Økoregion": [vannmiljo_row["Økoregion"]],
                    "Vanntype": [vannmiljo_row["Vanntype"]],
                    "EQR_Type": [vannmiljo_row["EQR_Type"]]
                })
                niva_df = pd.concat([niva_df, new_df], axis=0, ignore_index=True)
            else:
                for idx2, match_row in match_df.iterrows():
                    if match_row[parameter] is None:
                        match_row[parameter] = vannmiljo_row["Verdi"]
                    else:
                        if not match_row[parameter] == vannmiljo_row["Verdi"]:
                            try:
                                print("Sjekk parameter:" + parameter + " på vannforekomst:" \
                                      + match_row["VannforekomstID"] + " på dato:" + str(match_row["Date"]))
                            except:
                                print("Huff")


    out_df = pd.DataFrame(niva_df, columns=["Latitude", "Longitude", "Date", "Depth1", "DeptH2", "ChlA", "Kommunenr",
                                                    "VannforekomstID", "Økoregion", "Vanntype", "EQR_Type"])

    with ExcelWriter(f"{ROOT_PATH}Naturindeks-marin.xlsx") as writer:
        out_df.to_excel(writer)


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
    writer = ExcelWriter(f"{ROOT_PATH}{resultat_fil}")
    out_df.to_excel(writer)
    writer.save()



def callVannmiljoLokalitet(code):
    url = "https://kart.miljodirektoratet.no/arcgis/rest/services/vannmiljo/MapServer/1/query"
    params = {
        "where": "WaterLocationCode='" + code + "'",
        "outFields": "shape",
        "returnGeometry": True,
        "outSR": 4326,
        "f": "pjson"
    }
    try:
        resp = req.post(url, params)
        print(resp.text)
        features = json.loads(resp.text)["features"]
    except Exception as ex:
        print("Feil ved kall på Vannmiljo lokalitet med kode:" + code + ". Feilen var: " + str(ex))
        features = []

    if len(features) == 1:
        return features[0]
    else:
        return None


def callGeoserverQueryVannforekomst(layer, latitude, longitude):
    """ Will get vannforekomst in addition to vanntype from cloud Geoserver
    :param layer:
    :param latitude:
    :param longitude:
    :return:
    """

    url = "https://geoserver.p.niva.no/rest/query/no.niva.public/" + layer + "/distance/4326_" \
          + str(latitude) + "_" + str(longitude) + "_100/features.json"
    resp = req.get(url)
    print(f"Url: {url}\nResponse: {resp.text}")
    features = json.loads(resp.text)["features"]
    if len(features) == 1:
        return features[0]
    else:
        return None


def callGeoserverQueryKommuneF(latitude, longitude):
    url = "https://aquamonitor.niva.no/geoserver/rest/query/no.norgedigitalt/ni_kommune_f/geometry/4326_POINT(" \
          + str(longitude) + "%20" + str(latitude) + ")/features.json"
    resp = req.get(url)
    print(f"Url: {url}\nResponse: {resp.text}")
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
