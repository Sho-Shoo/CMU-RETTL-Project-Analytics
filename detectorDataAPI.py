################################################################################
# Created by Tianze (Steven) Shou during CMU Vincent's Lab, RETTL Project, 
# Summer 2022

# This set of API provides analytics tools for LearnSphere detector results, 
# which must have `studentID`, `timestamp`, `dayID`, and `periodID` columns 
# and detector result columns specifed. Detector result columns must be label 
# encoded. 
################################################################################

from time import time
import pandas as pd 
import numpy as np 
from datetime import datetime, timezone, timedelta
import os

def transformRawDetectorResults(path: str): 

    # name mapping from detector output file to the names we are going to use in this API
    nameMapping = {"critical_struggle": "struggle", 
                   "idle": "idle", 
                   "system_misuse": "misuse", 
                   "gaming": "gaming"} 
    shortNames = ["struggle", "idle", "misuse", "gaming"]
    # get the list of detector output file names
    fileNames = os.listdir(path)

    DFList = [] # a list to hold all detector-generated dataframes
    fetchedDetectors = []
    for fileName in fileNames: 
        fullPath = path + "/" + fileName
        DF = pd.read_csv(fullPath, delimiter="\t", index_col=False) 
        detectorName = DF.loc[0, "Detector_Name"] # get detector name of the file
        assert detectorName in nameMapping, f"Encountered unexpeted detector: {detectorName}" # safety 
        newDetectorName = nameMapping[detectorName] # get shorter name of detector
        fetchedDetectors.append(newDetectorName)
        DF = DF.drop(["Detector_Name"], axis=1) # drop the detector name column 
        DF = DF.rename({"Value": newDetectorName}, axis=1) # rename Value column to shorter detector name
        DFList.append(DF) 

    # prompt 
    print(f"Fetched results from {len(fetchedDetectors)} detectors: {fetchedDetectors}")

    # one dataframe to hold all detector results
    detectorDF = pd.concat(DFList, ignore_index=True)
    # get groups of each student_id&time pair
    studentTimePairs = detectorDF.groupby(["Student_ID", "Time"]) 

    def getFirstStringInIterable(series): 
        '''
        returns the first occurrence of string object in an iterable, if there is no
        string object, returns NaN
        '''
        for item in series: 
            if isinstance(item, str): return item 

        return np.nan

    # new dataframe with columns: studentID, time, values from four detectors
    studentStatusDF = pd.DataFrame() 
    # here we are going to get only the first string value in each student-time 
    # pair, since there may be multiple for on column
    for name in shortNames: 
        if name in pd.unique(detectorDF.columns): 
            studentStatusDF[name] = studentTimePairs[name].apply(getFirstStringInIterable)

    # extract studentID and time from group column 
    studentIDs = [] 
    times = [] 
    for groupName in studentStatusDF.index: 
        studentIDs.append(groupName[0]) 
        times.append(groupName[1])
    studentStatusDF["studentID"] = studentIDs 
    studentStatusDF["time"] = times 
    studentStatusDF.index = np.arange(len(studentStatusDF)) # re-order index as int series 

    # add time zone info 
    studentStatusDF["time_zone"] = "UTC" 

    def UTCDatetime2epoch(dateTime, format="%Y-%m-%d %H:%M:%S"):
        """Converts UTC date-time string to epoch time represented by an interger 

        Args:
            datetime (str): date-time string, in UTC time zone
            format (str, optional): python time module time string formats, read more in `time` documentation. Defaults to "%Y-%m-%d %H:%M:%S".

        Returns: 
            int: epoch/unix time stamp integer
        """    

        # read-in datetime string
        datetimeStruct = datetime.strptime(dateTime, format) 
        # add time zone informartion 
        datetimeStruct = datetimeStruct.replace(tzinfo=timezone.utc) 
        timestamp = datetimeStruct.timestamp()
        return timestamp 

    # transform UTC date-time to epoch time stamp 
    studentStatusDF["timestamp"] = studentStatusDF["time"].apply(lambda x: UTCDatetime2epoch(x, format="%Y-%m-%dT%H:%M:%S.%fZ"))

    # re-order the columns so that it looks better 
    reorderedCols = ['studentID', 'time', 'time_zone', 'timestamp'] + fetchedDetectors
    # make sure that we are not missing any columns 
    assert set(reorderedCols) == set(studentStatusDF.columns)
    studentStatusDF = studentStatusDF[reorderedCols] # re-order columns

    # do label encoding for the detector values 
    encoding = { 
            "struggle": {'0, > 0 s,  ': 0,
                            '1, > 25 s, slow to master some skills': 1,
                            '1, > 45 s, slow to master some skills': 2,
                            '1, > 1 min, slow to master some skills': 3,
                            '1, > 2 min, slow to master some skills': 4,
                            '1, > 5 min, slow to master some skills': 5, 
                            '1, > 10 min, slow to master some skills': 6
                            }, 
            "idle": {'1, > 2 min': 1, 
                        '1, > 5 min': 2,
                    }, 
            "misuse": {'0, > 0 s,  ': 0, 
                        '1, > 25 s, abusing hints?': 1,
                        '1, > 25 s, fast attempts in a row, not deliberate?': 1,
                        '1, > 45 s, abusing hints?': 2,
                        '1, > 45 s, fast attempts in a row, not deliberate?': 2,
                        '1, > 1 min, abusing hints?': 3,
                        '1, > 1 min, fast attempts in a row, not deliberate?': 3,
                        '1, > 2 min, abusing hints?': 4,
                        '1, > 2 min, fast attempts in a row, not deliberate?': 4,
                        '1, > 5 min, fast attempts in a row, not deliberate?': 5, 
                        '1, > 5 min, abusing hints?': 5
                        },
            "gaming": {'Gaming': 1, 
                        'Not gaming': 0
                        } 
            }

    encodedDF = studentStatusDF.replace(encoding)
    encodedDF = encodedDF.sort_values("timestamp")

    return encodedDF


def getDetectorResultsDF(path="output_files/detector_results.csv", delimiter=","): 

    DF = pd.read_csv(path, delimiter=delimiter, index_col=False)

    # ensure that necessary columns are in DF 
    assert "studentID" in DF.columns and "timestamp" in DF.columns and \
           "dayID" in DF.columns and "periodID" in DF.columns, \
           "Imported detector results data file does not have necessary column(s)" 

    return DF 

def getStatusStartEndTime(detectorResultsDF, studentID: str, detectorName: str): 

    """
    Extract the starting and ending timetamp of the status corresponding to 
    the given detector in argument 

    Args:
        detectorResultsDF (pd.DataFrame): encoded detector results dataframe, usually returned by getDetectorResultsDF()
        studentID (str): Anon student ID
        detectorName (str): detector name like `struggle`, must be a column in detectorResultsDF

    Returns:
        List[(float, float)]: (startTimestamp, endTimestamp) tuple representing 
        given student's time entering and exiting the state corresponding to the 
        detector
    """    

    assert detectorName in detectorResultsDF.columns, "detectorName not found amongst columns"

    intervals = [] # to be returned 
    # only get rows where detector result is not NaN
    DF = detectorResultsDF.loc[detectorResultsDF[detectorName].notnull()] 
    DF = DF.loc[DF["studentID"] == studentID]
    DF.index = np.arange(len(DF)) 

    start = None 
    dayID = None 
    periodID = None
    currLevel = 0 
    for i in DF.index: 
        
        # a new interval start signal 
        if DF.loc[i, detectorName] > 0 and start == None: 
            start = DF.loc[i, "timestamp"] 
            dayID = DF.loc[i, "dayID"] 
            periodID = DF.loc[i, "periodID"] 
            currLevel = DF.loc[i, detectorName]
            assert not np.isnan(currLevel)

        # interval end signal: jumping to the next day/period
        elif start != None and DF.loc[i, "dayID"] != dayID and DF.loc[i, "periodID"] != periodID: 
            end = DF.loc[i-1, "timestamp"]
            assert start != None 
            assert dayID != None 
            assert periodID != None
            # append interval information to result variable 
            intervals.append( (start, end, dayID, periodID) )

            # start of the next interval
            if DF.loc[i, detectorName] > 0: 
                start = DF.loc[i, "timestamp"] 
                dayID = DF.loc[i, "dayID"] 
                periodID = DF.loc[i, "periodID"] 
                currLevel = DF.loc[i, detectorName]
            # not starting a new interval at i, just reset variables 
            else: start, dayID, periodID, currLevel = None, None, None, 0

        # interval end signal: level drops
        elif start != None and DF.loc[i, detectorName] < currLevel:  
            end = DF.loc[i, "timestamp"]
            assert start != None 
            assert dayID != None 
            assert periodID != None
            # append interval information to result variable 
            intervals.append( (start, end, dayID, periodID) )

            # reset control variables 
            start, dayID, periodID, currLevel = None, None, None, 0

        # interval end signal: last row as end of interval 
        elif i == len(DF) - 1 and start != None:
            end = DF.loc[i, "timestamp"]
            intervals.append( (start, end, dayID, periodID) )

    return intervals


def getDetectorEvents(detectorResultsDF, detectorNames): 

    """
    Get a pandas dataframe with events data following the event-actor-subject 
    format from detecorResultsDF, usually returned by getDetectorResultsDF() in 
    this API. 

    Args:
        detectorResultsDF (pd.DataFrame): usually returned by getDetectorResultsDF()
        detectorNames (iterable): list of names of detectors, should be column names of detectorResultsDF

    Returns:
        pd.DataFrame: a pandas dataframe with events data following the event-actor-subject format
    """    

    detectorEventsDF = pd.DataFrame() # to be returned 
    
    studentIDs = detectorResultsDF["studentID"].unique()

    # generate events for each detector and student
    for detectorName in detectorNames: 
        for studentID in studentIDs: 

            intervals = getStatusStartEndTime(detectorResultsDF, studentID, detectorName)
            for start, end, dayID, periodID in intervals: 
                # create tow rows for entering state and exiting state events 
                twoRows = pd.DataFrame({"dayID": [dayID] * 2, 
                                        "periodID": [periodID] * 2, 
                                        "timestamp": [start, end], 
                                        "event": [f"Entering {detectorName} State", f"Exiting {detectorName} State"], 
                                        "actor": [studentID] * 2, 
                                        "subject": [np.nan] * 2, 
                                        "content": [np.nan] * 2, 
                                        "modality": ["detector"] * 2})
                detectorEventsDF = pd.concat([detectorEventsDF, twoRows], ignore_index=True) 

    # sort by timestamp and re-index 
    detectorEventsDF = detectorEventsDF.sort_values(by="timestamp")
    detectorEventsDF.index = np.arange(len(detectorEventsDF)) 

    return detectorEventsDF

def getStudentStatusDurationByDetector(detectorResultsDF, detectorName: str, studentID: str, periodID=None, dayID=None) -> float: 

    """
    Input a dataframe holding results from LearnSphere detector plugin (usually returned by getDetectorResultsDF())
    and specify the name of the detector and the student ID to see how long the student was detector to be under 
    the corresponding status (idle, gaming, etc.). 

    Args:
        detectorResultsDF (pd.DataFrame): usually pandas dataframe imported and validated by getDetectorResultsDF() 
        detectorName (str): name of the detector, must have corresponding column name in the input dataframe 
        studentID (str): student ID of the given student whose duration under status needs to be calculated
        periodID (int, optional): period ID specification. Defaults to None.
        dayID (int, optional): day ID specification. Defaults to None.

    Returns:
        float: number of seconds that the student spent under the status specified by corresponding detector 
    """    

    # ensure that necessary columns are in detectorResultsDF 
    assert "studentID" in detectorResultsDF.columns and "timestamp" in detectorResultsDF.columns and \
           "dayID" in detectorResultsDF.columns and "periodID" in detectorResultsDF.columns and \
           "Input detector results data file does not have necessary column(s)" 

    assert detectorName in detectorResultsDF.columns, "Input detector results data does not have input detector name column" 
    
    filteredDF = detectorResultsDF.copy()
    # filter by day and period ID's 
    if periodID != None: filteredDF = filteredDF.loc[filteredDF["periodID"] == periodID] 
    if dayID != None: filteredDF = filteredDF.loc[filteredDF["dayID"] == dayID] 
    # if the student is not found, just return NaN 
    if not studentID in filteredDF["studentID"].tolist(): return np.nan
    # filtered by studentID
    filteredDF = filteredDF.loc[filteredDF["studentID"] == studentID] 

    # sort by timestamp 
    filteredDF = filteredDF.sort_values(by="timestamp", ignore_index=True) 
    
    # get under-status intervals 
    intervals = getStatusStartEndTime(filteredDF, studentID, detectorName)

    # calculate length of each interval and add to res
    res = 0 # to be returned 
    for start, end, dayID, periodID in intervals: 
        assert end - start >= 0, f"Invalid interval length: end - start = {end - start}"
        res += end - start

    return res 

def getStudentStatusDurationByDetector2(detectorResultsDF, detectorName: str, studentID: str, periodID=None, dayID=None) -> float: 

    """
    Input a dataframe holding results from LearnSphere detector plugin (usually returned by getDetectorResultsDF())
    and specify the name of the detector and the student ID to see how long the student was detector to be under 
    the corresponding status (idle, gaming, etc.). 

    Args:
        detectorResultsDF (pd.DataFrame): usually pandas dataframe imported and validated by getDetectorResultsDF() 
        detectorName (str): name of the detector, must have corresponding column name in the input dataframe 
        studentID (str): student ID of the given student whose duration under status needs to be calculated
        periodID (int, optional): period ID specification. Defaults to None.
        dayID (int, optional): day ID specification. Defaults to None.

    Returns:
        float: number of seconds that the student spent under the status specified by corresponding detector 
    """    

    # ensure that necessary columns are in detectorResultsDF 
    assert "studentID" in detectorResultsDF.columns and "timestamp" in detectorResultsDF.columns and \
           "dayID" in detectorResultsDF.columns and "periodID" in detectorResultsDF.columns and \
           "Input detector results data file does not have necessary column(s)" 

    assert detectorName in detectorResultsDF.columns, "Input detector results data does not have input detector name column" 
    
    filteredDF = detectorResultsDF.copy()
    # filter by day and period ID's 
    if periodID != None: filteredDF = filteredDF.loc[filteredDF["periodID"] == periodID] 
    if dayID != None: filteredDF = filteredDF.loc[filteredDF["dayID"] == dayID] 
    # if the student is not found, just return NaN 
    if not studentID in filteredDF["studentID"].tolist(): return np.nan
    # filtered by studentID
    filteredDF = filteredDF.loc[filteredDF["studentID"] == studentID] 

    # sort by timestamp 
    filteredDF = filteredDF.sort_values(by="timestamp", ignore_index=True) 
    triggered = False # whether detector is triggered (giving > 0 values) when looping through filteredDF
    timeTriggered = None
    res = 0 # to be returned 
    for i in filteredDF.index: 

        timeAdded = 0 
        
        # see if the first row of filteredDF triggers the detector 
        if i == 0 and filteredDF.loc[i, detectorName] > 0: 
            triggered = True 
            timeTriggered = filteredDF.loc[i, "timestamp"] 

        elif triggered: # detector triggered in previous row 
            
            # check if current row is on the same day/period with previous row
            if not (filteredDF.loc[i, "dayID"] ==  filteredDF.loc[i-1, "dayID"] and \
                    filteredDF.loc[i, "periodID"] ==  filteredDF.loc[i-1, "periodID"]): 

                # if not in the same day/period, triggered is off and add time chunk to results
                triggered = False
                timeAdded = filteredDF.loc[i-1, "timestamp"] - timeTriggered

                # trigerring indicator turned back on if current row is greater than 0
                if filteredDF.loc[i, detectorName] > 0: 
                    triggered = True
                    timeTriggered = filteredDF.loc[i, "timestamp"]

            if filteredDF.loc[i, detectorName] > 0: # if current row is still triggered 
                triggered = True
            else: # current row is not triggered
                triggered = False
                timeAdded = filteredDF.loc[i-1, "timestamp"] - timeTriggered

        else: # not triggered
            assert not triggered 

            if filteredDF.loc[i, detectorName] > 0: 
                triggered = True 
                timeTriggered =  filteredDF.loc[i, "timestamp"]


        res += timeAdded

    return res 

# test cases 
if __name__ == "__main__": 

    DF = getDetectorResultsDF()
    print(getStudentStatusDurationByDetector(DF, "struggle", "Stu_011924479d5e1be392bb55cb21567c3f")) 
    print(getStudentStatusDurationByDetector(DF, "idle", "Stu_3c3d511146fad19db4b08d2ecb35a835")) 
    print(getStudentStatusDurationByDetector(DF, "struggle", "Stu_3c3d511146fad19db4b08d2ecb35a835")) 



