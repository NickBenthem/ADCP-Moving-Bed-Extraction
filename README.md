# ADCP-Moving-Bed-Extraction
Pulls extraction files from ADCP files for the USGS. Can be run on a given folder with subdirectories. For all the subdirectories - the script will scan through all files looking for two conditions:
1) File extension is xml
2) `QRev` (case sensitive) is present in the file name. 

An error log will be generated to the folder. There may be some bad field data / assumptions taken, and the script will do its best to inform you of those decisions.

# Installation
`pip install usgs_mbe`

# Usage
`usgs_mbe --test-folder=/path/to/folder` 

or - more simply - 

`usgs_mbe` 

# Output 

A csv file in each subfolder with the following columns:
```
MovingBedSpeed
MovingBedSpeedUnit
TestTimestamp
MovingBedTestResults
StationName
siteid
MovingBedTestQuality
Duplicates -- If multiple values were found - this indicates that the first was taken.
gage_height_va -- USGS value for the closest height to the TestTimestamp.
```