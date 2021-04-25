# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
from pathlib import Path

import pandas
import pandas as pd
import xmltodict
import requests

def extract_critical_info(file_path=None):
    xml_data = open( file_path,'r',encoding="utf-8").read()  # Read data
    xmlDict = xmltodict.parse(xml_data)  # Parse XML
    rootkeys = xmlDict['Channel'].keys()
    MovingBedSpeed = xmlDict['Channel']['QA']['MovingBedTest']['MovingBedSpeed']
    MovingBedQuality = xmlDict['Channel']['QA']['MovingBedTest']['TestQuality']['#text']
    # The following isn't structured - so we'll have to parse
    TestTimestamp_text = xmlDict['Channel']['QA']['DiagnosticTest']['Text']['#text']
    lines = TestTimestamp_text.splitlines()
    possible_matches = [x[3:] for x in TestTimestamp_text.splitlines() if 'TS ' in x]
    assert len(possible_matches) == 1, "Too many `TS` elements found - check your data to ensure only one exists."
    TestTimestamp = possible_matches[0]
    # Moving bed
    movingbed = xmlDict['Channel']['QA']['MovingBedTestResult']['#text']
    # Station Name
    stationname = xmlDict['Channel']['SiteInformation']['StationName']['#text']
    siteid = xmlDict['Channel']['SiteInformation']['SiteID']['#text']
    return ({
        "MovingBedSpeed": MovingBedSpeed["#text"],
        "MovingBedSpeedUnit": MovingBedSpeed["@unitsCode"],
        "TestTimestamp": TestTimestamp,
        "MovingBedTestResults": movingbed,
        "StationName": stationname,
        "siteid": siteid,
        "MovingBedTestQuality" : MovingBedQuality
    })


def get_usgs_web_date(site_id: int = None):
    url = f"https://waterdata.usgs.gov/nwis/measurements?site_no={site_id}&agency_cd=USGS&format=rdb_expanded"
    page = requests.get(url)
    # The first portion of the data has a bunch of ### - we need to remove these to make a tsv.
    raw_data = [x.split(sep="\t") for x in page.text.splitlines() if x[0] != '#']
    # There's some garbage data in the first row - we'll have to remove it :(
    # It looks like 5s	15s	6s	19d	12s	1s	12s	5s	12s	12s	12s	7s	6s	21s	15s	11n	64s	4s	5s	5s	14s	14s	14s	14s	4s	4s	4s	12s	9s	12s	7s	14s - which I don't get.
    raw_data.pop(1)

    df = pd.DataFrame.from_records(raw_data)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])

    return(df)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some files to get critical ADCP information.')
    parser.add_argument('--test-folder',  type=str, default="/Users/nick/downloads/Adam_Moving_bed" ,
                        help='The folder where this is located - either posix or relative.')
    parser.add_argument('--csvfile', default="moving_bed_results.csv",
                        help='The file  where to save the csv that was generated - either posix or relative.')

    args = parser.parse_args()


    # Scrape the file to generate a CSV.

    file_folder = args.test_folder
    list_write = []
    for path in Path(file_folder).rglob('*.xml'):
        if 'QRev' not in str(path.name):
            pass
        else:
            list_write.append(extract_critical_info(path.resolve()))
    # Now write to a path.
    df = pd.DataFrame(list_write)


    # Now we need to get some information from the web.

    site_ids = df['siteid'].unique()
    usgs_dict = {}

    for row in site_ids:
        usgs_dict[row] = get_usgs_web_date(row)

    # we need to initialize the df to have a None value column for things we want to add.
    df["gage_height_va"] = None
    for index,row in df.iterrows():
        # print(usgs_dict[row['siteid']])

        # Compare the two datasets - we need the lowest here.
        usgs_dict[row['siteid']]["time_diff"] = abs(pd.to_datetime(usgs_dict[row['siteid']]["measurement_dt"]) - pd.to_datetime(str(row["TestTimestamp"]).strip(),format="%y/%m/%d,%H:%M:%S.%f"))
        usgs_dict[row['siteid']].sort_values(by="time_diff",ascending=True,inplace=True)
        matched_column = usgs_dict[row['siteid']].iloc[0]

        # Now that we've matched - we can just append the value we want.
        df.iloc[index]["gage_height_va"] = matched_column["gage_height_va"]

    df.to_csv(args.csvfile,index=False)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
