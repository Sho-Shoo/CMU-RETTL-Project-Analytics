import tutorDataAPI as tutorAPI 

tutorLogDF = tutorAPI.getAnnotatedTutorLogDF("raw data/tutor_log.tsv") 
period3StudentIDs = tutorAPI.getStudentIDsByPeriod(tutorLogDF, 4)

print(period3StudentIDs)

