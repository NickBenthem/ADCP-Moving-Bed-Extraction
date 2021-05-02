# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import os
import sys
from pathlib import Path

import pandas as pd
import xmltodict
import requests
import logging

class extracter():
    def __init__(self,file_path):
        self.repeat = False
        self.file_path = file_path

    def set_repeat(self,value):
        self.repeat = value

    def parse_possible_multiples(self,xmldict, key):
        try:
            xml_return = xmldict[key]  # If its just one - return just one.
        except:  # If there's multiple values - we just want the last one - they reran multiple.
            xml_return = xmldict[-1][key]
            self.set_repeat(True)
        return xml_return

    def extract_critical_info(self,file_path=None):
        if file_path is None:
            file_path = self.file_path
        xml_data = open(file_path, 'r', encoding="utf-8").read()  # Read data
        xmlDict = xmltodict.parse(xml_data)  # Parse XML
        rootkeys = xmlDict['Channel'].keys()
        MovingBedSpeed = self.parse_possible_multiples(xmlDict['Channel']['QA']['MovingBedTest'],'MovingBedSpeed')
        MovingBedQuality = self.parse_possible_multiples(xmlDict['Channel']['QA']['MovingBedTest'],'TestQuality')['#text']
        # The following isn't structured - so we'll have to parse
        TestTimestamp_text = xmlDict['Channel']['QA']['DiagnosticTest']['Text']['#text']
        lines = TestTimestamp_text.splitlines()
        possible_matches = [x[3:] for x in TestTimestamp_text.splitlines() if 'TS ' in x]
        if (len(possible_matches) != 0):
            # This is the case where the file is not the format we want.
            if len(possible_matches) > 1:
                logging.info(f"\t  ({possible_matches} timestamps were found - grabbing the first.")
            TestTimestamp = possible_matches[0]
            try:
                TestTimestamp = pd.to_datetime(
                str(TestTimestamp).strip(), format="%y/%m/%d,%H:%M:%S.%f")
            except:
                TestTimestamp = None
                logging.warning(f'Unparsable TestTimestamp found.. Found datetime was { str(TestTimestamp).strip()}. Leaving empty.')

            # Moving bed
            movingbed = xmlDict['Channel']['QA']['MovingBedTestResult']['#text']
            # Station Name
            stationname = None
            try:
                stationname = xmlDict['Channel']['SiteInformation']['StationName']['#text']
            except:
                logging.warning("stationname not found - skipping.")
            siteid = xmlDict['Channel']['SiteInformation']['SiteID']['#text']
            return ({
                "MovingBedSpeed": MovingBedSpeed["#text"],
                "MovingBedSpeedUnit": MovingBedSpeed["@unitsCode"],
                "TestTimestamp": TestTimestamp,
                "MovingBedTestResults": movingbed,
                "StationName": stationname,
                "siteid": siteid,
                "MovingBedTestQuality": MovingBedQuality,
                "Duplicates" : self.repeat
            })
        return # the empty case


def get_usgs_web_date(site_id: int = None):
    url = f"https://waterdata.usgs.gov/nwis/measurements?site_no={site_id}&agency_cd=USGS&format=rdb_expanded"
    page = requests.get(url)
    # The first portion of the data has a bunch of ### - we need to remove these to make a tsv.
    try:
        raw_data = [x.split(sep="\t") for x in page.text.splitlines() if x is not None and x[0] != '#']
    except:
        logging.warning(f"Unable to scrape USGS site for site id {site_id}")
        return
    # There's some garbage data in the first row - we'll have to remove it :(
    # It looks like 5s	15s	6s	19d	12s	1s	12s	5s	12s	12s	12s	7s	6s	21s	15s	11n	64s	4s	5s	5s	14s	14s	14s	14s	4s	4s	4s	12s	9s	12s	7s	14s - which I don't get.
    raw_data.pop(1)

    df = pd.DataFrame.from_records(raw_data)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])

    return (df)


def cli(arg=None):
    if not arg:
        arg = sys.argv[1:]
    import argparse
    parser = argparse.ArgumentParser(description='Process some files to get critical ADCP information.')

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    parser.add_argument('--test-folder', type=dir_path, default=os.getcwd(),
                        help='The folder where this is located - either posix or relative.')
    parser.add_argument('--csvfile', default="moving_bed_results.csv",
                        help='The file  where to save the csv that was generated - either posix or relative.')
    args = parser.parse_args(arg)
    file_folder = args.test_folder
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler("../parser_output.log"),
            logging.StreamHandler()
        ]
    )
    logging.getLogger().setLevel(logging.INFO)
    # Scrape the file to generate a CSV.
    logging.info(f"Beginning scrape of {file_folder}")
    folder_dir = [f.path for f in os.scandir(file_folder) if f.is_dir()]
    if len(folder_dir) == 0:
        logging.error("No suitable folders found! Exiting.")
    for folder in folder_dir:
        logging.info(f"Running extract for {folder}")
        list_write = []
        for path in Path(folder).rglob('*.xml'):
            if 'QRev' not in str(path.name):
                pass
            else:
                logging.info(f"scraping: {path.resolve()}")
                extract = extracter(path.resolve())
                data = extract.extract_critical_info()
                if data:  # dont append empty.
                    list_write.append(data)
        # Now write to a path.
        df = pd.DataFrame(list_write)

        logging.info(f"Test folder successfully scraped. Found {len(list_write)} datasets.")
        logging.info("Beginning web scrape")
        # Now we need to get some information from the web.
        if len(list_write) == 0:
            logging.warning(f"No QREV XML files were found for {folder}- check your files.")
            continue

        site_ids = df['siteid'].unique()
        usgs_dict = {}

        for row in site_ids:
            logging.info(f"Scraping USGS site for site_id {row}")
            data = get_usgs_web_date(row)
            if data is not None:
                usgs_dict[row] = data
            else:  # Remove that site_id from the data set - it's garbage.
                logging.warning(f"Removing site_id {row} from the dataset")
                df = df[df['siteid'] != row]
        logging.info("Web scrape successfully scraped.")
        logging.info("Beginning merge ")

        # we need to initialize the df to have a None value column for things we want to add.
        df["gage_height_va"] = None
        for index, row in df.iterrows():
            # Compare the two datasets - we need the lowest here.
            try:
                usgs_dict[row['siteid']]["time_diff"] = abs(
                    pd.to_datetime(usgs_dict[row['siteid']]["measurement_dt"]) - pd.to_datetime(
                        str(row["TestTimestamp"]).strip()))
                usgs_dict[row['siteid']].sort_values(by="time_diff", ascending=True, inplace=True)
                matched_column = usgs_dict[row['siteid']].iloc[0]

                # Now that we've matched - we can just append the value we want.
                df.at[index, 'gage_height_va'] = matched_column["gage_height_va"]
            except:
                logging.warning(
                    f'Unable to match USGS site data with CSV. Found datetime was {str(row["TestTimestamp"]).strip()} Passing.')
        logging.info("Merge complete ")
        logging.info(f"Writing to CSV path: {os.path.join(folder, args.csvfile)} ")
        df.to_csv(os.path.join(folder, args.csvfile), index=False)
        logging.info("Write complete.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    cli()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
