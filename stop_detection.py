###########################################################
# Created by Tianze (Steven) Shou for RETTL Summer 2022 
# This file serves as a utility package to detect teacher's stopping behavior
# defined in Martinez-Maldonado R, et al.
# Full citation below: 
# Roberto Martínez-Maldonado, Lixiang Yan, Joanne Deppeler, Michael Phillips, Dragan Gašević, Classroom Analytics: Telling Stories About Learning Spaces Using Sensor Data, Hybrid Learning Spaces, 10.1007/978-3-030-88520-5_11, (185-203), (2022).
###########################################################


import math
import pandas as pd
from os import times 

def getObsStopEvents(): 

    """
    :return: returns a set of strings, which are all stopping event names in distilled observation log 
    """

    return {"Talking to student: ON-task", 
            "Talking to student: OFF-task",
            "Talking to small group: ON-task",
            "Talking to small group: OFF-task"}

def cols2tuples(Xcol, Ycol): 

    '''
    Converts the columns representing a position in a dataframe to an array of 
    tuples of the same length
    '''

    # input check 
    assert len(Xcol) == len(Ycol), "Error: Xcol and Ycol of different size"

    tuplePoints = [] # initialize an output array
    for i in range(len(Xcol)): 
        tuplePoints.append( (Xcol.iloc[i], Ycol.iloc[i]) ) 

    # return check
    assert len(tuplePoints) == len(Xcol), "Error output number of point different from input"

    return tuplePoints



def getDist(point0, point1):

    '''
    Points are represented by tuples in this funciton 
    Returns the distance between point1 and point2
    '''
    
    X0 = point0[0] 
    Y0 = point0[1]
    X1 = point1[0]
    Y1 = point1[1] 

    return math.sqrt( (X0 - X1)**2 + (Y0 - Y1)**2 )


def getCentroid(points): 
    sumX, sumY = 0, 0
    for point in points: 
        sumX += point[0] 
        sumY += point[1] 
    centroid = (sumX / len(points), sumY / len(points)) 
    return centroid


def withinRadius(points, radius):

    '''
    @param points: an array of points (represented by tuples). 
                Example: [(point1X, point1Y), (point2X, point2Y), ...] 
    @param radius: radius parameter that specifies a stop, unit is milimeter 
    @return: return a boolean logical of whether all points are with the radius 
            range of these points' centroid 
    '''

    # calculate the centroid of these points 
    sumX, sumY = 0, 0
    for point in points: 
        sumX += point[0] 
        sumY += point[1] 
    centroid = (sumX / len(points), sumY / len(points)) 

    for point in points: 
        # return False if one point is not within radius range
        if(getDist(point, centroid) > radius): return False 

    return True


def validateStops(stops, duration, maxDuration, epsilon=0.4): 

    '''
    @param stops: a list of start timestamp and end timestamp of stops. 
                Example: [(start0, end0), (start1, end1), ...] 
    @param duration: the minimum duration that the teacher has to stay in-place 
                    in order to define a stop 
    @param epsilon: allows a margin for mistake in timestamp
    @return: returns a logical, indicating whether the sequence of start and stop 
            times are valid
    '''

    for i in range(len(stops)-1): 
        currStopStart = stops[i][0]
        currStopEnd = stops[i][1]
        nextStopStart = stops[i+1][0]
        nextStopEnd = stops[i+1][1] 

        # the stop duration much reach indicated parameter
        if(currStopEnd - currStopStart < duration - epsilon or 
           currStopEnd - currStopStart > maxDuration): 
            print("stop", i, "is invalid") 
            print("start is", currStopStart) 
            print("end is", currStopEnd)
            return False 
        if(nextStopEnd - nextStopStart < duration - epsilon): 
            print("stop", i + 1, "is invalid")
            print("start is", nextStopStart) 
            print("end is", nextStopEnd)
            return False 

        # the end of current stop must be ealier than next stop's start
        if(currStopEnd > nextStopStart): 
            print("stop", i, "and", i+1, "are overlapping")
            return False 

    return True

def getStops(X, Y, timestamp, periods, days, duration, radius): 

    '''
    @param X: an numpy array of x-coordinates 
    @param Y: an numpy array of y-coordinates, must be same length as X
    @param timestamp: an array of timestamps, must be same length as X and Y
    @param duration: the minimum duration that the teacher stays in-place to 
                    establish a stop. Unit is second
    @param radius: teacher position must be with in the radius of coordinate 
                centroid to establish a stop. Unit is milimeter
    @return: an array of tuple (<stopStartTime>, <stopEndTime>) 
    '''

    assert len(X) == len(Y), "Lengths of X, Y coordinate arrays should be identical"
    assert len(timestamp) == len(X), "Lengths timestamp array should be identical to coordinate arrays" 

    maxDuration = 600 # a stop should not exceed 10 minutes 

    # arrange X, Y coordinates into a array of tuples 
    pos = [] 
    for i in range(len(X)): 
        pos.append( (X[i], Y[i]) ) 
    assert(len(pos) == len(timestamp)) 
    
    stops = [] # output array
    # format:[ (<stop_start_time>, <stop_end_time>), ... ]

    # loop thru the pos array in the time frame specified by `duration`
    startIndex = 0
    while(startIndex < len(pos) - duration): 
        
        endIndex = startIndex + 1

        # look further down position points if all points are within radius
        while(withinRadius(pos[startIndex: endIndex], radius) and 
              endIndex < len(pos) and 
              # the following condition is to ensure that we do not detect
              # a stop that goes into two periods or days
              periods[startIndex] == periods[endIndex] and 
              days[startIndex] == days[endIndex]): 
            endIndex += 1 
        
        # edge case where endIndex advances to the next day/period
        # edge case where endIndex is out of bound by 1
        # if(endIndex >= len(pos) or
        #    periods[startIndex] != periods[endIndex] or
        #    days[startIndex] != days[endIndex]): 
        #     endIndex -= 1

        endIndex -= 1 # since endIndex always go over by 1, and we want end and start to be both inclusive 

        # this means that no stop is detected 
        if(timestamp[endIndex] < timestamp[startIndex] + duration):
            # move the timeframe to the next second
            startIndex += 1
        # a stop is detected 
        else:
            # pass this stop to output array 
            if(endIndex >= len(pos)): endIndex = len(pos) - 1 # to catch the edge case 
            stops.append( (timestamp[startIndex], timestamp[endIndex]) ) 
            # start of next timeframe should be the end of this stop 
            startIndex = endIndex


    assert(validateStops(stops, duration, maxDuration))
    return stops

def getStopsAndCentroids(X, Y, timestamp, periods, days, duration, radius): 

    '''
    This function is adapted from getStops(), adding centroid coordinates to 
    the returned result 
    
    @param X: an numpy array of x-coordinates 
    @param Y: an numpy array of y-coordinates, must be same length as X
    @param timestamp: an array of timestamps, must be same length as X and Y
    @param duration: the minimum duration that the teacher stays in-place to 
                    establish a stop. Unit is second
    @param radius: teacher position must be with in the radius of coordinate 
                centroid to establish a stop. Unit is milimeter
    @return: an array of tuple (<stopStartTime>, <stopEndTime>, <centroidX>, <centroidY>) 
    '''

    assert len(X) == len(Y), "Lengths of X, Y coordinate arrays should be identical"
    assert len(timestamp) == len(X), "Lengths timestamp array should be identical to coordinate arrays" 

    # arrange X, Y coordinates into a array of tuples 
    pos = [] 
    for i in range(len(X)): 
        pos.append( (X[i], Y[i]) ) 
    assert(len(pos) == len(timestamp)) 
    
    stops = [] # output array
    # format:[ (<stop_start_time>, <stop_end_time>), ... ]

    # loop thru the pos array in the time frame specified by `duration`
    startIndex = 0
    while(startIndex < len(pos) - duration): 
        
        endIndex = startIndex + 1

        # look further down position points if all points are within radius
        while(withinRadius(pos[startIndex: endIndex], radius) and 
              endIndex < len(pos) and 
              # the following condition is to ensure that we do not detect
              # a stop that goes into two periods or days
              periods[startIndex] == periods[endIndex] and 
              days[startIndex] == days[endIndex]): 
            endIndex += 1 

        endIndex -= 1 # since endIndex always go over by 1, and we want end and start to be both inclusive 

        # this means that no stop is detected 
        if(timestamp[endIndex] < timestamp[startIndex] + duration):
            # move the timeframe to the next second
            startIndex += 1
        # a stop is detected 
        else:
            # pass this stop to output array 
            if(endIndex >= len(pos)): endIndex = len(pos) - 1 # to catch the edge case 

            # slice out the points to calculate stops centroid
            points = cols2tuples(X[startIndex: endIndex+1], Y[startIndex: endIndex+1]) 
            centroidX, centroidY = getCentroid(points)
            # append time start/end time and centroid X/Y to output list of tuples 
            stops.append( (timestamp[startIndex], timestamp[endIndex], centroidX, centroidY) ) 

            # start of next timeframe should be the end of this stop 
            startIndex = endIndex
    
    return stops

def getStopsFromObs(obsLog): 

    """
    :param obsLog: distilled observation data file
    :return: returns a list of timestamps signaling the start of each stopping events in observation log. Ending timestamp is not included here since it is difficult to datamine the end of an observation event 
    """ 

    stops = [] # to be returned 
    # go through observation log to find the stopping events 
    for i in range(len(obsLog)): 
        if( obsLog.iloc[i]["event"] in getObsStopEvents() ): 
            stops.append(obsLog.iloc[i]["timestamp"]) # attach the stopping event's timestamp to the list if found 

    return stops

def getStopTags(timestamps, stops): 
    """
    Returns a pd.Series object of the same length as input variable timestamp, tagging True or False for every timestamp on if it is in any stop

    Args:
        timestamps (a pd.Series of epoch timestamps): an iterable of epoch timestamps, assumed to be sorted and increasing 
        stops (List[(int, int)]): a list of tuples of two ints, indicating the start time and end time of each stop, usually returned by getStops(), also stricting increasing
    """    

    assert(timestamps.is_monotonic_increasing) 

    tags = [] # to be populated and returned 
    i = 0 # indexing for stops 

    for timestamp in timestamps: 
        # go to the next stop if the end of current stop is before current timestamp 
        while(i < len(stops) and stops[i][1] < timestamp):
            i += 1

        if(i == len(stops)): break # stops are ran out 

        # current timestamp is within current stop 
        if(stops[i][0] <= timestamp and timestamp <= stops[i][1]): tags.append(True) 
        # current timestamp not within a stop 
        else: tags.append(False)

    while(len(tags) < len(timestamps)): tags.append(False) # if stops are ran out, just append False to the following tags 
    assert(len(tags) == len(timestamps)) 

    return pd.Series(tags) 


# testing code 
# teacherPosDF = pd.read_csv("teacher_position_sprint1_shou.csv", index_col="Unnamed: 0") 
# duration, radius = 10, 1000
# stops = getStops(teacherPosDF["chosen_X"], 
#                  teacherPosDF["chosen_Y"], 
#                  teacherPosDF["time_stamp"], 
#                  duration, radius) 
# print(stops) 
