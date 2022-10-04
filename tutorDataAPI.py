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

def getStudentIDsByTime(tutorLogDF, startTime=None, endTime=None): 
    """
    Get student ID's who have transaction records between start and end time
    """
    # input check
    assert(startTime == None or endTime == None or endTime > startTime) 

    filteredDF = filterWithTime(tutorLogDF, startTime, endTime) 
    studentIDs = filteredDF["Anon Student Id"].unique().tolist() 
    return studentIDs 

def getStudentIDsByPeriod(tutorLogDF, periodID): 
    """
    Get student ID's who have transaction records by period ID. Note that the 
    period ID used in tutor log does not match with our regular definition, and 
    this function does not account for that 
    """
    filteredDF = tutorLogDF.loc[tutorLogDF["Class"] == f"Period{periodID}"] 
    studentIDs = filteredDF["Anon Student Id"].unique().tolist() 
    return studentIDs 

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


def getIncorrectCount(tutorLogDF, students=None, startTime=None, endTime=None): 
    """
    Returns a dataframe with total count of incorrect attempts for each student 
    in a given list within a given time period (startTime, endTime). If student 
    list is not specified (None), all students that appear in the data will be
    counted 
    """

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 
    filteredDF = filteredDF.loc[filteredDF["Outcome"] == "INCORRECT"]

    # count the number of incorrect attempts 
    countDF = filteredDF.groupby("Anon Student Id").count()
    resDF = pd.DataFrame() 
    resDF["studentID"]= countDF.index
    resDF["IncorrectCount"] = countDF["Row"].tolist()

    return resDF


def getFirstAttemptPerf(tutorLogDF, students=None, startTime=None, endTime=None): 
    """
    Returned a pandas dataframe with two columns: `studentID` and `firstAttemptPerformance`. 

    Args:
        tutorLogDF (pandas.DataFrame): tutor log dataframe
        students (list, optional): list to student to generate first attempt 
            performance on. Defaults to None to include all students
        startTime (int/float, optional): start time stamp. Defaults to None.
        endTime (int/float, optional): end time stamp. Defaults to None.

    Returns:
        pandas.DataFrame: a pandas dataframe with two columns: `studentID` and `firstAttemptPerformance`
    """

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 
    # only consider the first attempt
    filteredDF = filteredDF.loc[ filteredDF["Attempt At Step"] == 1 ] 
    # get the correct first attempts only 
    studentGroups = filteredDF.groupby("Anon Student Id") # groupby object by studentID's 

    def getIndStudFirstAttemptPerf(indStudDF): 

        indStudDF = indStudDF.loc[ indStudDF["Attempt At Step"] == 1 ] 
        valueCounts = indStudDF["Outcome"].value_counts() 
        correctFirstAttemptCount = valueCounts.get("CORRECT", 0)
        firstAttemptCount = correctFirstAttemptCount + \
                            valueCounts.get("INCORRECT", 0) + \
                            valueCounts.get("HINT", 0) 

        return correctFirstAttemptCount / firstAttemptCount 

    firstAttemptPerf = studentGroups.apply(getIndStudFirstAttemptPerf) 
    firstAttemptPerf = pd.DataFrame({"firstAttemptPerformance": firstAttemptPerf}) 
    firstAttemptPerf["studentID"] = firstAttemptPerf.index
    firstAttemptPerf.index = np.arange(len(firstAttemptPerf)) 
    return firstAttemptPerf

def getAvgCorrectStepDuration(tutorLogDF, students=None, startTime=None, endTime=None): 
    """
    Returns a dataframe with a column of `studentID` and a column with the average 
    seconds spent on correct steps

    Args:
        tutorLogDF (pandas.DataFrame): usually a pandas.DataFrame object returned by getAnnotated getAnnotatedTutorLogDF()
        students (list[str], optional): a list of students to be filtered. Defaults to None to get all student's information 
        startTime (int/float, optional): period start time for filtering. Defaults to None to include all transactions 
        endTime (int/float, optional): period end time for filtering. Defaults to None to include all transactions 

    Returns:
        pandas.DataFrame: a dataframe with a column of `studentID` and a column with the average time named `avgCorrectStepDuration`
    """

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 
    # consider only the first correct attempts 
    filteredDF = filteredDF.loc[ (filteredDF["Outcome"] == "CORRECT") & \
                                 (filteredDF["Attempt At Step"] == 1) & \
                                 (filteredDF["Is Last Attempt"] == 1) ] 
    studentGroups = filteredDF.groupby("Anon Student Id") 
    avgCorrectStepDuration = studentGroups.apply(getTimePerStep) 
    # pass to a new dataframe with correct column names 
    resDF = pd.DataFrame()
    resDF["studentID"] = avgCorrectStepDuration.index 
    resDF["avgCorrectStepDuration"] = avgCorrectStepDuration.tolist()
    
    return resDF 

def getAvgErrorStepDuration(tutorLogDF, students=None, startTime=None, endTime=None): 
    """
    Returns a dataframe with a column of `studentID` and a column with the average 
    seconds spent on errorous steps, which include both hints and incorrect steps

    Args:
        tutorLogDF (pandas.DataFrame): usually a pandas.DataFrame object returned by getAnnotated getAnnotatedTutorLogDF()
        students (list[str], optional): a list of students to be filtered. Defaults to None to get all student's information 
        startTime (int/float, optional): period start time for filtering. Defaults to None to include all transactions 
        endTime (int/float, optional): period end time for filtering. Defaults to None to include all transactions 

    Returns:
        pandas.DataFrame: a dataframe with a column of `studentID` and a column with the average time named `avgErrorStepDuration`
    """

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 
    # error incorporates incorrect and hint 
    incorrect = filteredDF.loc[filteredDF["Outcome"] == "INCORRECT"] 
    hint = filteredDF.loc[filteredDF["Outcome"] == "HINT"] 
    # get the correct transaction which is the last correct attempt after a sequence of error attempts 
    correctAtLast = filteredDF.loc[ (filteredDF["Outcome"] == "CORRECT") & \
                                    (filteredDF["Attempt At Step"] != 1) & \
                                    (filteredDF["Is Last Attempt"] == 1)]
    filteredDF = pd.concat([incorrect, hint, correctAtLast], ignore_index=True) 

    studentGroups = filteredDF.groupby("Anon Student Id") 
    avgCorrectStepDuration = studentGroups.apply(getTimePerStep) 
    # pass to a new dataframe with correct column names 
    resDF = pd.DataFrame()
    resDF["studentID"] = avgCorrectStepDuration.index 
    resDF["avgErrorStepDuration"] = avgCorrectStepDuration.tolist()
    
    return resDF 

def getAvgHintDurationPerStep(tutorLogDF, students=None, startTime=None, endTime=None): 

    """
    Returns a dataframe with a column of `studentID` and a column with the average 
    seconds spent on looking at hints for errorous steps

    Args:
        tutorLogDF (pandas.DataFrame): usually a pandas.DataFrame object returned by getAnnotated getAnnotatedTutorLogDF()
        students (list[str], optional): a list of students to be filtered. Defaults to None to get all student's information 
        startTime (int/float, optional): period start time for filtering. Defaults to None to include all transactions 
        endTime (int/float, optional): period end time for filtering. Defaults to None to include all transactions 

    Returns:
        pandas.DataFrame: a dataframe with a column of `studentID` and a column with the average time named `avgHintDurationPerStep`
    """

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    studentGroups = filteredDF.groupby("Anon Student Id") 

    # helper function to put into .apply() 
    def getAvgHintDurationPerStepPerStud(studDF): 

        # obtain the errorous steps count 
        errorCount = 0
        # obtain time spent looking at hints 
        hintDuration = 0 

        for i in studDF.index: 

            # is errorous step if the first attempt is not correct, i.e., hint or incorrect 
            if studDF.loc[i, "Attempt At Step"] == 1 and \
               (studDF.loc[i, "Outcome"] == "HINT" or studDF.loc[i, "Outcome"] == "INCORRECT"): 
               errorCount += 1

            # summarize for number of seconds spent looking at hints 
            if studDF.loc[i, "Outcome"] == "HINT": 
                hintDuration += studDF.loc[i, "Duration (sec)"]

        if errorCount == 0: 
            return np.nan
        else: return hintDuration / errorCount 

    # pandas series indexed by anon student id that has avg. time for each student 
    avgHintDurationPerStep = studentGroups.apply(getAvgHintDurationPerStepPerStud) 

    resDF = pd.DataFrame() # to be returned 
    resDF["studentID"] = avgHintDurationPerStep.index
    resDF["avgHintDurationPerStep"] = avgHintDurationPerStep.tolist()

    return resDF 

def getAssistanceScorePerStep(tutorLogDF, students=None, startTime=None, endTime=None): 

    """
    Returns a dataframe with a column of `studentID` and a column with the average 
    assistance score for each student per step, where assistance score is defined 
    as number of incorrect + number of hint. Here each student's result will be
    calculated as (totalAssistanceScore / number of steps)

    Args:
        tutorLogDF (pandas.DataFrame): usually a pandas.DataFrame object returned by getAnnotated getAnnotatedTutorLogDF()
        students (list[str], optional): a list of students to be filtered. Defaults to None to get all student's information 
        startTime (int/float, optional): period start time for filtering. Defaults to None to include all transactions 
        endTime (int/float, optional): period end time for filtering. Defaults to None to include all transactions 

    Returns:
        pandas.DataFrame: a dataframe with a column of `studentID` and a column with the average time named `avgHintDurationPerStep`
    """

    # basic filtering 
    filteredDF = filterWithStudents(tutorLogDF, students) 
    filteredDF = filterWithTime(filteredDF, startTime, endTime) 

    studentGroups = filteredDF.groupby("Anon Student Id") 

    # helper function to put into .apply() 
    def getAssistanceScorePerStepPerStud(studDF): 

        totalAssistanceScore = 0 
        # formula for assistance score: number of incorrect + number of hints 
        assistanceScore = len(studDF.loc[ (studDF["Outcome"] == "INCORRECT") | (studDF["Outcome"] == "HINT") ])
        totalSteps = getNumOfSteps(studDF) 

        if totalSteps == 0: return np.nan 
        else: return assistanceScore / totalSteps 

    assistanceScorePerStep = studentGroups.apply(getAssistanceScorePerStepPerStud) 

    resDF = pd.DataFrame()
    resDF["studentID"] = assistanceScorePerStep.index
    resDF["assistanceScorePerStep"] = assistanceScorePerStep.tolist() 

    return resDF 

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

    