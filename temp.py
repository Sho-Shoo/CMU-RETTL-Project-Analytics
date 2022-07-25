import pandas as pd 

def getInRangePerc(file): 

    eventsDF = pd.read_csv(file) 
    stopDF = eventsDF.loc[eventsDF["event"] == "Stopping"] 
    notNAcount = sum(stopDF["subject"].notnull())

    return notNAcount / len(stopDF) 

def getTableThreePerc(file): 

    eventsDF = pd.read_csv(file) 
    stopDF = eventsDF.loc[eventsDF["event"] == "Stopping"] 
    tableThreeCount = stopDF["subject"].value_counts()[3]

    return tableThreePerc / len(stopDF)

if __name__ == "__main__": 

    fileNames = ["event_master_file_D10_R500_RNG500_sprint2_shou.csv", 
                 "event_master_file_D10_R500_RNG1000_sprint2_shou.csv", 
                 "event_master_file_D10_R500_RNG2000_sprint2_shou.csv"] 
    fileNames = "output_files/" + pd.Series(fileNames) 

    for file in fileNames: 

        inRangePerc = getInRangePerc(file) 
        tableThreePerc = getTableThreePerc(file) 

        print("In file", file) 
        print("Percentage of stops that have student in-range is", inRangePerc)

        print("**************************************************************")