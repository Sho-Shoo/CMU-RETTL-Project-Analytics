################################################################################
# Created by Tianze (Steven) Shou during CMU Vincent's Lab, RETTL Project, Summer 2022

# This set of API provides analytics tools for Lynnette intelligent tutor 
# logging data, which must have follow the Datashop by-transaction export data 
# format 
################################################################################

import pandas as pd 
import numpy as np 
from datetime import datetime, timezone, timedelta

def EDTDatetime2epoch(dateTime, format="%Y-%m-%d %H:%M:%S"):
    """Converts EDT date-time string to epoch time represented by an interger 

    Args:
        datetime (str): date-time string, in EDT time zone
        format (str, optional): python time module time string formats, read more in `time` documentation. Defaults to "%Y-%m-%d %H:%M:%S".

    Returns: 
        int: epoch/unix time stamp integer
    """    

    # read-in datetime string
    datetimeStruct = datetime.strptime(dateTime, format) 
    # add time zone informartion 
    datetimeStruct = datetimeStruct.replace(tzinfo=timezone(timedelta(hours=-4))) 
    timestamp = datetimeStruct.timestamp()
    return timestamp 

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

def epoch2datetimeInEDT(timestamp):
    """Converts epoch time stamp to date-time string in EDT time zone 

    Args:
        timestamp (int or float): epoch time stamp 

    Returns:
        string: date-time string in EDT time zone
    """    

    assert(timestamp >= 0)

    dateTime = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return dateTime 

def filterWithStudents(tutorLogDF, students): 
    """filter tutor log dataframe by students' anon user ids and return a filtered dataset 

    Args:
        tutorLogDF (pd.DataFrame): tutor log data set 
        students (None or Iterable): an iterable with desired student anon ids 

    Returns:
        pd.DataFrame: a filtered dataset with just these wanted students 
    """    
    assert(students == None or len(students) > 0) # input check 

    filteredDF = tutorLogDF.copy()
    if(students != None): filteredDF = tutorLogDF.loc[tutorLogDF["Anon Student Id"].isin(students)] 

    return filteredDF

def filterWithTime(tutorLogDF, startTime, endTime):
    """filter tutor log data by start and end time stamp. Usually used to extract data from a period 

    Args:
        tutorLogDF (pd.DataFrame): tutor log data set 
        startTime (int): start time stamp
        endTime (int): end time stamp

    Returns:
        pd.DataFrame: filtered dataset with entries from the time stamp interval 
    """    
    
    assert(startTime == None or endTime == None or endTime > startTime) # input check 

    # filteredDF = tutorLogDF.copy()
    # if(startTime != None): filteredDF = filteredDF.loc[filteredDF["timestamp"] >= startTime]
    # if(endTime != None): filteredDF = filteredDF.loc[filteredDF["timestamp"] <= endTime] 
    
    filteredDF = tutorLogDF.copy()
    if(startTime != None): filteredDF = tutorLogDF.loc[tutorLogDF["timestamp"] >= startTime]
    if(endTime != None): filteredDF = filteredDF.loc[filteredDF["timestamp"] <= endTime] 

    return filteredDF

def getStudentPerformanceSummary(tutorLogDF, students=None, startTime=None, endTime=None):
    """
    Measures student performance by percentage of attempt correctness during a time interval

    Args:
        tutorLogDF (pd.Dataframe): tutor log dataframe imported from a datashop exported file 
        students (Iterable): one/several anon_stud_id's to get the performance percentage 
        startTime (_int_): unix time stamp indicating the start of the interval 
        endTime (_int_): unix time stamp indicating the end of the interval 

    Returns: 
        float: a float representing attempt correct rate
        
    """ 

    # input check 
    assert(students == None or len(students) > 0) 
    assert(startTime == None or endTime == None or endTime > startTime) 

    # only get rows with desired students and start/end time 
    filteredDF = tutorLogDF.copy()
    if(students != None): filteredDF = tutorLogDF.loc[tutorLogDF["Anon Student Id"].isin(students)] 
    if(startTime != None): filteredDF = filteredDF.loc[filteredDF["timestamp"] >= startTime]
    if(endTime != None): filteredDF = filteredDF.loc[filteredDF["timestamp"] <= endTime] 

    # total number of attempt = number of correct attempt + number of incorrect + number of hints requested 
    totalCorrect = filteredDF["Outcome"].value_counts().get("CORRECT", 0)
    totalIncorrect = filteredDF["Outcome"].value_counts().get("INCORRECT", 0)
    totalHint = filteredDF["Outcome"].value_counts().get("HINT", 0)
    totalAttempts = totalCorrect + totalIncorrect + totalHint

    # Tried some validation. However, the number of ATTEMPS values in the 
    # `Student Response Type` column does not match with CORRECT and INCORRECT
    # outcomes, so the total number of attempts will be the sum of the two

    # if(totalAttempts == 0): return 0
    if(totalAttempts == 0): return np.nan
    else: return totalCorrect / totalAttempts


def getNumOfProblemsSolved(tutorLogDF, students=None, startTime=None, endTime=None): 
    """Generate descriptive stats of the total number of problems solved by given students during given time interval 

    Args:
        tutorLogDF (pd.Dataframe): tutor log dataframe imported from a datashop exported file 
        students (Iterable): one/several anon_stud_id's to get the performance percentage 
        startTime (_int_): unix time stamp indicating the start of the interval 
        endTime (_int_): unix time stamp indicating the end of the interval 

    Returns:
        int: total number of problems solved by given students during given time interval 
    """    

    # do some filtering with students and start/end timestamp 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    # Each problem should correspond to one and only one `done ButtonPressed`, 
    # so we can use the "done ButtonPressed" values in the `Step Name` column to 
    # extract the number of problems solved with these students between this 
    # time interval
    numOfProblemsSolved = filteredDF["Step Name"].value_counts().get("done ButtonPressed", 0)

    return numOfProblemsSolved

def getNumOfHints(tutorLogDF, students=None, startTime=None, endTime=None): 
    """Generate descriptive stats of the total number of hints requested by given students during given time interval 

    Args:
        tutorLogDF (pd.Dataframe): tutor log dataframe imported from a datashop exported file 
        students (Iterable): one/several anon_stud_id's to get the performance percentage 
        startTime (_int_): unix time stamp indicating the start of the interval 
        endTime (_int_): unix time stamp indicating the end of the interval 

    Returns:
        int: total number of hints requested by given students during given time interval 
    """  

    # do some filtering with students and start/end timestamp 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    numOfHints = filteredDF["Student Response Type"].value_counts().get("HINT_REQUEST", 0)

    return numOfHints


def getAveNumOfHintsPerProblem(tutorLogDF, students=None, startTime=None, endTime=None): 
    """Generates average number of hints used by given students in given time period 

    Args:
        tutorLogDF (pd.Dataframe): tutor log dataframe imported from a datashop exported file 
        students (Iterable): one/several anon_stud_id's to get the performance percentage 
        startTime (_int_): unix time stamp indicating the start of the interval 
        endTime (_int_): unix time stamp indicating the end of the interval 

    Returns:
        float: average number of hints used by given students in given time period
    """  

    numOfHints = getNumOfHints(tutorLogDF, students=students, startTime=startTime, endTime=endTime) 
    numOfProblems = getNumOfProblemsSolved(tutorLogDF, students=students, startTime=startTime, endTime=endTime) 
    assert numOfProblems != 0, "there is no problem solved with given conditions" 

    return numOfHints / numOfProblems 

def getTimeToSolveSummary(tutorLogDF, students=None, startTime=None, endTime=None): 
    """ 
    Get the mean and std the time, in seconds, to solve each problem for 
    given student in given time interval

    Args:
        tutorLogDF (pd.Dataframe): tutor log dataframe imported from a datashop exported file 
        students (Iterable): one/several anon_stud_id's to get the performance percentage 
        startTime (_int_): unix time stamp indicating the start of the interval 
        endTime (_int_): unix time stamp indicating the end of the interval 

    Returns:
        (float, float): mean and std of time taken to solve the problems (unit is second)
    """    

    timeTakenForOneProblemUpperBound = 60*20 # in second 

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    # rows with "done ButtonPressed" as value of `Step Name` should indicate the 
    # last transaction of the problem 
    filteredDF = filteredDF.loc[filteredDF["Step Name"] == "done ButtonPressed"] 
    # the difference in time between the "done ButtonPressed" transaction and 
    # the `Problem Start Time` value should be time taken to solve the problem
    timeTaken = filteredDF["Time"].apply(UTCDatetime2epoch) - filteredDF["Problem Start Time"].apply(UTCDatetime2epoch) 
    timeTaken = timeTaken.loc[timeTaken < timeTakenForOneProblemUpperBound]

    return np.mean(timeTaken), np.std(timeTaken) 

def getKCLevelPerformance(tutorLogDF, students=None, startTime=None, endTime=None, suffix="_rate"): 
    """Generate the performance of given students in given time interval in each KC levels 

    Args:
        tutorLogDF (pd.Dataframe): tutor log dataframe imported from a datashop exported file 
        students (Iterable): one/several anon_stud_id's to get the performance percentage 
        startTime (_int_): unix time stamp indicating the start of the interval 
        endTime (_int_): unix time stamp indicating the end of the interval 
        suffix (str): in the returned dictionary mapping, keys will be strings formated as "{KCName} + {suffix}". Default to "_rate" 

    Returns:
        dict: a dictionary mapping from KC's (string) to its correct rate (float)
    """    

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    # all KC levels are here: 
    KCLevels = ['cancel-const', 'division-simple', 'divide',
                'subtraction-const', 'combine-like-const', 'subtraction-var',
                'combine-like-var', 'cancel-var', 'distribute-division',
                'division-complex'] 
    kc2CorrectRateMapping = dict() # to be returned 

    for kc in KCLevels: 
        kcDF = filteredDF.loc[filteredDF["KC (Default)"] == kc] # dataframe with this KC only 
        correctRate = getStudentPerformanceSummary(kcDF) # calculate correct rate with this KC
        kc2CorrectRateMapping[kc + suffix] = correctRate # populate the mapping dictionary
    
    return kc2CorrectRateMapping


def getProblemLevelSummary(tutorLogDF, students=None, startTime=None, endTime=None): 

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    # get the last transaction for each problem since it is unique 
    filteredDF = filteredDF.loc[filteredDF["Step Name"] == "done ButtonPressed"] 

    # return problem level mean and std 
    return np.mean(filteredDF["Level (Position)"]), np.std(filteredDF["Level (Position)"])


def getNumOfSteps(tutorLogDF, students=None, startTime=None, endTime=None):

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 
    # `Is Last Attemp` column documents whether this attempt transaction is 
    # the last attempt for the step. Since one step can only have one last attempt, 
    # so we are counting this as number of steps 
    numOfSteps = filteredDF["Is Last Attempt"].sum()

    return numOfSteps

def getTimePerStep(tutorLogDF, students=None, startTime=None, endTime=None): 

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    numOfSteps = getNumOfSteps(filteredDF) 
    # calcultae total time for these steps by `Duration` column 
    totalTime = filteredDF["Duration (sec)"].sum() 

    if numOfSteps == 0: return np.nan 
    else: return totalTime / numOfSteps

def getAnnotatedTutorLogDF(tutorLogFilePath: str, delimiter: str="\t", startTimestamp: float=None, endTimestamp: float=None): 

    """
    Function for reading-in Datashop by-transaction format Lynnette tutor log 
    data. Use this function instead in calling pandas.read_csv(). 

    Args:
        tutorLogFilePath (str): file path to tutor log file
        delimiter (str, optional): Defaults to "\t".
        startTimestamp (float, optional): start timestamp for filtering the data. Defaults to None.
        endTimestamp (float, optional): end timestamp for filtering the data. Defaults to None.

    Returns:
        pandas.DataFrame: pandas dataframe that carries the annotated Lynnette tutor log data
    """    

    tutorLogDF = pd.read_csv(tutorLogFilePath, delimiter=delimiter, index_col=False) 
    tutorLogDF["Time Zone"] = "UTC" # the logs are entered in UTC time zone 
    tutorLogDF["timestamp"] = tutorLogDF["Time"].apply(UTCDatetime2epoch) # add a new column with unix time stamps 
    tutorLogDF["EDT_time"] = tutorLogDF["timestamp"].apply(epoch2datetimeInEDT) # append a new column with EDT time information to be more intuitive 

    # only aceepting data within the experiment period, which is between 05/23/2022 and 05/25/2022 
    tutorLogDF = filterWithTime(tutorLogDF, startTimestamp, endTimestamp) 

    # change 'Duration (sec)' column to numeric 
    tutorLogDF = tutorLogDF.replace({ "Duration (sec)": {".": "0"} }) # replace dot with 0, sicne dot cannot be parsed 
    tutorLogDF["Duration (sec)"] = pd.to_numeric(tutorLogDF["Duration (sec)"]) 

    return tutorLogDF

    