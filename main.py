# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
from pathlib import Path
import pandas as pd
import xmltodict


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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Process some files to get critical ADCP information.')
    parser.add_argument('--test-folder',  type=str,
                        help='The folder where this is located - either posix or relative.')
    parser.add_argument('--csvfile', default="moving_bed_results.csv",
                        help='The file  where to save the csv that was generated - either posix or relative.')

    args = parser.parse_args()



    file_folder = args.test_folder
    list_write = []
    for path in Path(file_folder).rglob('*.xml'):
        if 'QRev' not in str(path.name):
            pass
        else:
            list_write.append(extract_critical_info(path.resolve()))
    # Now write to a path.
    df = pd.DataFrame(list_write)
    df.to_csv(args.csvfile,index=False)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
