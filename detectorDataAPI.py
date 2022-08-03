################################################################################
# Created by Tianze (Steven) Shou during CMU Vincent's Lab, RETTL Project, 
# Summer 2022

# This set of API provides analytics tools for LearnSphere detector results, 
# which must have `studentID`, `timestamp`, `dayID`, and `periodID` columns 
# and detector result columns specifed. Detector result columns must be label 
# encoded. 
################################################################################

import pandas as pd 
import numpy as np 

def getDetectorResultsDF(path="output_files/detector_results.csv", delimiter=","): 

    DF = pd.read_csv(path, delimiter=delimiter, index_col=False)

    # ensure that necessary columns are in DF 
    assert "studentID" in DF.columns and "timestamp" in DF.columns and \
           "dayID" in DF.columns and "periodID" in DF.columns, \
           "Imported detector results data file does not have necessary column(s)" 

    return DF 

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
    
    # filtered rows with given detector's results available 
    filteredDF = detectorResultsDF.loc[detectorResultsDF[detectorName].notnull()] 
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

                # if not in the same day/period, triggered is off and add time chunk to retuls
                triggered = False
                timeAdded = filteredDF.loc[i-1, "timestamp"] - timeTriggered

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
    print(getStudentStatusDurationByDetector(DF, "struggle", "Stu_03cac10de8d282be297f7b1550ef153d")) 



