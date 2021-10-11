# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 12:04:54 2021

@author: cdhabro
"""

"""
### ASSIGN ITEMS TO LIMITED-SIZED GROUPS (E.G. ('AGILE SPRINT SIZE', 'TANK CAPACITY', 'MAX STUDENTS IN CLASS') WHEN 
### THE ITEMS HAVE A PRIORITY [OR NOT] (E.G. ('BEST, BETTER, GOOD'); ('MUST HAVE, NICE TO HAVE, CAN WAIT'), ('TEACHER A', 'TEACHER B', TEACHER C')),
### AND A UNIT SIZE (E.G. ('PRODUCTION PER DAY', 'HOURS PER TASK', 'STUDENTS PER CLASS')) 
"""
### use to group tasks into agile sprints based on critical priority and unit size per supervisor ###
### use to take wells with different development priority and known BOED and set a max tank limit, then determine which wells go in which tanks and how many tanks are needed ###
### use to sequentially fill tables with guests based on priority list

import pandas as pd
pd.set_option('display.max_columns', 10)
pd.set_option('display.max_rows', 80)
pd.set_option("max_colwidth", 10)


import numpy as np
import time
import datetime

### variable 'haltLoops' is used to control if pausing on each loop (either "YES" or "NO")
haltLoop = "NO"
allowedHaltLoopWords = ["YES", "NO"]
if haltLoop not in allowedHaltLoopWords:
    raise ValueError("'haltLoop' variable not an allowable string")
### END variable 'haltLoops'

    

starttime = time.time()
############### PARAMETERS FOR METRICS (YOU CAN CHANGE THESE) ###################
### for below calculations in minutes, 8 hrs * 60 mins = 480 so enter 480 below
humanMinutesInteger = 60
numberTimes = 26
yearlySalary = 150000
############### PARAMETERS FOR METRICS (YOU CAN CHANGE THESE) ###################



taskFile = r"\\hotce15\p\l48esri\per\working\c_habrock\AICOE\AGILE_PROJECT_RANKING\AGILE_PROJECT_RANKING.xlsx"

# originally written using 'Sheet1', use 'Sheet5' for larger example, use 'Sheet6' for table seating
dfOriginal = pd.read_excel(taskFile, sheet_name="Sheet5")

print("ORIGINAL DATA:", "\n", dfOriginal,"\n")
dfOriginalRows = dfOriginal.shape[0]
dfOriginalCols = dfOriginal.shape[1]
print(f"Rows: {dfOriginalRows:,.0f}; Columns: {dfOriginalCols:,.0f}")
print()


###################### MAP COLUMNS FOR YOUR DATA TO VARIABLE NAMES BELOW #############
### provide csv name for saving results (this gets appened to a partial file path and partial name)
### ex: (''' r"agile_sprints"    OR     r"wells_per_tank"     OR    r"wedding_guests_per_table"   OR   r"maximize_number_wells_visit_per_day"''')
csvName = r"wells_per_tank" 


### create variables mapped to column names for easier usage with other tables and files ###
### AGILE SPRINTS AND TASKS
groupCol = "SUPV"
thingCol = "TASK"
thingAmountCol = "UNITS"
priorityCol = "PRIORITY"
groupSizeCol = "SPRINT_SIZE"

#"""
### TANKS AND WELLS
groupCol = "ASSET"
thingCol = "WELL_NAME"
thingAmountCol = "BOED_IP"
priorityCol = "TYPE_CURVE_GROUP"
groupSizeCol = "TANK_LIMIT_BBL"
#"""


"""
### TABLES AND GUESTS
groupCol = "WHO"
thingCol = "GUEST"
thingAmountCol = "NUMBER_PPL"
priorityCol = "RELATION"
groupSizeCol = "TABLE_SIZE"
"""


"""
### AREAS AND WELL VISITS 
### change logic to "smallest" instead of "largest" to maximize count rather than size
groupCol = "AREA"
thingCol = "WELL_NAME"
thingAmountCol = "DRIVE_TIME_MINUTES"
priorityCol = "TIER"
groupSizeCol = "HOURS_LIMIT"
"""


### create lookup dictionary to assign priority column a value to sort and prioritize ###
### (low to high (i.e. lowest number is highest priority)) ###

priorityDict = {
    "MH":1,
    "CBN":2,
    "WAIT":3
    }


#"""
priorityDict = {
    "BEST":1,
    "GOOD ENOUGH":3,
    "ABOVE AVERAGE":2
    }
#"""


"""
priorityDict = {
    "IMMEDIATE":1,
    "FRIENDS":3,
    "EXTENDED":2
    }
"""


"""
priorityDict = {
    1:1,
    3:3,
    2:2
    }
"""


print(priorityDict)
print()
### 




############ don't alter these or major code logic break ############
"""
determine if a column should be considered for subgrouping (e.g. a Supervisor or Asset or other categorial)
we did so by creating a second column of the subgroup column that we'll iterate over
if no subgroup to iterate over (so just treat all data as one big group) then
new subgroup column is equal to the original subgroup column
otherwise if subgroup (iterate over rows based on a categorical) is required
then new subgroup column is equal to "ALL"
"""
### IMPORTANT IN CODE FUNCTIONALITY
### allOrSubgroup below should only be "ALL" or "SUBGROUP" !!!

allOrSubgroup = "SUBGROUP"

allowedWordsAllOrSubgroup = ["ALL", "SUBGROUP"]
if allOrSubgroup not in allowedWordsAllOrSubgroup:
    raise ValueError("'allOrSubgroup' variable not an allowable string")

if allOrSubgroup == "ALL":
    dfOriginal["TEMPGROUP"] = "ALL"
else:
    dfOriginal["TEMPGROUP"] = dfOriginal[groupCol]

############ END don't alter these or major code logic break ############



############ don't alter these or major code logic break ############

### specify columns to remove nulls from (needed for logic so have to remove)
removeNullCols = ["TEMPGROUP",priorityCol,thingAmountCol]
df = dfOriginal.dropna(subset=removeNullCols).copy()


uniqueSupv = df["TEMPGROUP"].unique()
print(f"Unique supervisors: {uniqueSupv}")
print(f"Unique supervisors: {', '.join(uniqueSupv)}")
print()


## getting max SPRINT_SIZE in case user forgot to remove a value hundreds of 
## rows down the task list and always updates the first row or so 
df["MAX_LIMIT"] = df.groupby(["TEMPGROUP"])[groupSizeCol].transform(func=np.max)
print(df)
print()




## using dictionary from above to map numeric value to priority column to use in sorting
df["PRIORITY_VALUE"] = df[priorityCol].map(priorityDict)




df = df[df.columns[~df.columns.isin([groupSizeCol,])]]

allGroupList = []
allNullList = []
allNotAllowedList = []

### keep track of every while loop for each supv
whileControlList = []

for supv in uniqueSupv:#[0:1]:
    
    tempDf = df[df["TEMPGROUP"] == supv]
    tempDfRows = tempDf.shape[0]
    tempDfSprintSize = tempDf["MAX_LIMIT"].max()
    
    ### how to handle when MAX_LIMIT is null (nan)
    """
    use 'limitMethod' below to determine how missing MAX_LIMIT values are handled:
    either apply a single MAX_LIMIT value to all groups, only those with missing (null)
    or remove those rows
    """
    limitMethod = "MISSING"
    limitReplacementValue = 10
    validLimitType = ["ALL", "MISSING", "REMOVE"]
    
    if limitMethod not in validLimitType:
        raise ValueError("'limitMethod' variable not an allowable string")
    
    if limitMethod == "ALL":
        tempDfSprintSize = limitReplacementValue
        print(f"ALL: changed max limit to {limitReplacementValue:,.0f}")
    elif limitMethod == "MISSING":
        if np.isnan(tempDfSprintSize) == True:
            tempDfSprintSize = limitReplacementValue
            print(f"MISSING: changed max limit to {limitReplacementValue:,.0f}")
    elif limitMethod == "REMOVE":
        if np.isnan(tempDfSprintSize) == True:
            print(f"REMOVE: np.isnan == True, should remove {supv} rows and break for loop to move onto next iteration")
            continue
    
    tempDf["TEMPLIMIT"] = tempDfSprintSize
    ### END how to handle when MAX_LIMIT is nan
    

    print(f"Working on {supv}'s tasks ({tempDfRows:,.0f})...")
    print(f"Sprint unit size: {tempDfSprintSize:,.0f}")
    print(tempDf)
    print()
    sortCriticalCategory = "PRIORITY_VALUE"
    sortCriticalCategoryAsc = True
    sortCriticalValue = thingAmountCol
    sortCriticalValueAsc = True
    
    tempDf = tempDf.sort_values(by=sortCriticalCategory, ascending=sortCriticalCategoryAsc)
    print(tempDf)
    print()    
    
    sortCol = [sortCriticalCategory, sortCriticalValue]
    sortAsc = [sortCriticalCategoryAsc, sortCriticalValueAsc]
    fillStartOrder = "largest"
    
    if fillStartOrder == "largest":
        sortAsc[1] = False
    elif fillStartOrder == "smallest":
        sortAsc[1] = True
    else:
        print("Error, unexpected parameter value (killing program by del sortAsc variable name used to sort.")
        del sortAsc
    
    tempDf = tempDf.sort_values(by=sortCol, ascending=sortAsc)
    print("Sorted:")
    print(tempDf)
    print()
    
    tempCriticalUniqueList = tempDf[priorityCol].unique()
    for tcul in tempCriticalUniqueList:
        print(f"Unique critical items: {tcul}")
    print()
    
    initialTempDfRows = tempDf.shape[0]
    print(f"Initial temp df rows: {initialTempDfRows:,.0f}")
    currentTempDfRows = 0
    
    supvGroupList = []
    groupAllowed = tempDfSprintSize
    currentGroupSize = 0
    currentGroupNumber = 0
    
    ### removing null value in unit sizes
    ## if want to reference null value rows then below
    tempDfNull = tempDf[tempDf[thingAmountCol].isna()].copy()
    tempDf = tempDf[tempDf[thingAmountCol].notna()]
    
    ### removing rows with unit sizes greater than group allowable sprint size
    tempDfNotAllowed = tempDf[tempDf[thingAmountCol] > groupAllowed].copy()###### or tempDf[tempDf[thingAmountCol].isna()]
    tempDfAllowed = tempDf[tempDf[thingAmountCol] <= groupAllowed].copy()
    ## bc made copies of rows that are over, rows with nulls, and rows allowed, all have been allocated and copied to new df so can delete 'tempDf'
    del tempDf
    if tempDfNotAllowed.shape[0] >= 1:
        print(f"WARNING: removing {tempDfNotAllowed.shape[0]:,.0f} rows due to unit sizes greater than allowable group size!)")
        print(tempDfNotAllowed)
        print()
    else:
        print(f"GREAT, all {initialTempDfRows:,.0f} tasks have unit sizes within the allowable group size!")
        print()
    

    ######removedUnallowedInitialTempDfRows = tempDfAllowed.shape[0]
    print(f"New temp df rows after removing unallowed rows: {tempDfAllowed.shape[0]:,.0f}")
    tempDfAllowedRows = tempDfAllowed.shape[0]
    currentTempDfRows = 0
    
    ### MAIN PART OF PROGRAM AND GROUP ASSIGNING STARTS HERE ###
    print("---"*20)    
    whileCounter = 0

    while currentTempDfRows < tempDfAllowedRows:
        whileCounter += 1
        print(f"Entered while loop #{whileCounter:,.0f} for {supv}...")
        print(f"current temp df row count ({currentTempDfRows:,.0f}) <  allowed temp df row count ({tempDfAllowedRows:,.0f})")
        whileControl = supv + "_" + str(whileCounter)
        whileControlList.append(whileControl)
        print()

        ### because columns from multiple data sets are in different locations
        ### we need to access itertuple rows by integer so need to obtain it from name first
        ### and then add 1 to that number to account for added Index created during itertuple
        thingAmountColIdx = tempDfAllowed.columns.get_loc(thingAmountCol) + 1
        print(f"thingAmountColIdx: {thingAmountColIdx:,.0f}")
        

        groupAvailable = groupAllowed - currentGroupSize

        if currentGroupSize < groupAllowed:
            print(f"entered current group size ({currentGroupSize:,.0f}) < group size allowed ({groupAllowed:,.0f})")
            currentGroupList = []
            currentGroupNumber += 1
            print(f"CURRENT GROUP NUMBER: {currentGroupNumber:,.0f}")
            print(tempDfAllowed)
            print(tempDfAllowed.shape)
            print()
            
            if haltLoop == "YES":
                input("Press Enter to continue...")

            for row in tempDfAllowed.itertuples():
                print()
                ### no need to get integer location of Index because it is always
                ### at location [0] during itertuples
                rowIndex = row[0]
                print(f"Entered for row loop: evaluating row index ***({rowIndex:,.0f})***")
                unitSize = row[thingAmountColIdx]
                groupAvailable = groupAllowed - currentGroupSize
                print(f"new group available ({groupAvailable:,.0f})")
                print(f"evaluating current row's unit size ({unitSize:,.0f})")
                if haltLoop == "YES":
                    input("Press Enter to continue...")
                    
                if unitSize <= groupAvailable:
                    
                    print(f"UNDER: entered if unitsize ({unitSize:,.0f}) <= available ({groupAvailable:,.0f})")
                    currentGroupList.append(row)
                    tempDfAllowed.drop(index=rowIndex, inplace=True)
                    currentTempDfRows += 1
                    currentGroupSize += unitSize
                    print(f"entered if unitsize <= available end of current loop: added ({unitSize:,.0f}) for new total: ({currentGroupSize:,.0f})")
                    
                    
                    ###
                    newMinimumUnitSize = np.min(tempDfAllowed[thingAmountCol])
                    currentAvailableForEndingBecauseLessThanAllowedButNoMoreRows =  (groupAllowed - currentGroupSize)
                    print("temp currentGroupList:")
                    print(currentGroupList)
                    print(f"current minimum unit size in data after removing current row: {newMinimumUnitSize:,.0f}")
                    print(f"current available size left in iterated group after removing current row: {currentAvailableForEndingBecauseLessThanAllowedButNoMoreRows:,.0f}")
                    canMoreRowsFit = ((newMinimumUnitSize <= currentAvailableForEndingBecauseLessThanAllowedButNoMoreRows) or (currentAvailableForEndingBecauseLessThanAllowedButNoMoreRows == 0))
                    print(f"**more rows can fit OR group is filled (aka {newMinimumUnitSize:,.0f} <= {currentAvailableForEndingBecauseLessThanAllowedButNoMoreRows:,.0f} OR {currentAvailableForEndingBecauseLessThanAllowedButNoMoreRows:,.0f} == 0: T/F): {canMoreRowsFit}**")
                    print("*** if False, create a group! ***")
                    print()
                    ###
                    if haltLoop == "YES":
                        input("Press Enter to continue...")


                else:
                    print(f"OVER: entered else statement: unit size ({unitSize:,.0f}) too big")
                    if haltLoop == "YES":
                        input("Press Enter to continue...")
                    pass
                
                if currentGroupSize == groupAllowed or canMoreRowsFit == False: ### (THIS IS CURRENT PROBLEM...NO MORE UNITS FIT BUT GROUP MAX IS NOT FULL!!!)
                    print("FULL (or not full BUT no more can fit) !!!: entered if to break: group limit is filled")
                    currentGroupListDf = pd.DataFrame(currentGroupList)
                    currentGroupListDf["GROUP"] = currentGroupNumber
                    print(currentGroupListDf)
                    print(currentGroupListDf.shape)
                    supvGroupList.append(currentGroupListDf)
                    currentGroupSize = 0
                    print(f"Done with group #{currentGroupNumber:,.0f} (resetting groupsize to {currentGroupSize:,.0f})")
                    if haltLoop == "YES":
                        input("Press Enter to continue...")
                    break
                


        else:
            print()
            print("TRY TO RESET CURRENT GROUP SIZE")
            print(f"did NOT enter: current group size ({currentGroupSize:,.0f}) < group size allowed ({groupAllowed:,.0f})")
            currentGroupSize = 0
            print(f"reset currentGroupSize ({currentGroupSize:,.0f})")
            if haltLoop == "YES":
                input("Press Enter to continue...")
    
    if haltLoop == "YES":
        input("Press Enter to continue...")
    print()
    print("DONE with main program of creating groups.")                                  
    print("Attempting to create df out of this supv's group(s)...")
    supvGroupListConcat = pd.concat(supvGroupList, ignore_index=True)
    supvGroupListDf = pd.DataFrame(supvGroupListConcat)
    print("Complete...df created (df shape): {supvGropuListDf.shape}")
    print("DONE")
    print()
    print(supvGroupListDf)
    print()
    print("Attempting to add df to all iterated lists...")
    allGroupList.append(supvGroupListDf)
    print("Complete...added concatenated lists as a dataframe to 'all group list'")
    print()
    
    ######################################## this is potential error fix area (check if works when no Nulls or NotAllowed values exist)
    if (tempDfNull.shape[0]) > 0:
        #allNullListConcat = pd.concat(tempDfNull, ignore_index=True)
        allNullListDf = pd.DataFrame(tempDfNull)
        allNullList.append(allNullListDf)
    else:
        print("No nulls in null list")
        
    if (tempDfNotAllowed.shape[0]) > 0:
        #allNotAllowedListConcat = pd.concat(tempDfNotAllowed, ignore_index=True)
        allNotAllowedListDf = pd.DataFrame(tempDfNotAllowed)
        allNotAllowedList.append(allNotAllowedListDf)
    ###########################################


    print("REPRINTING REMOVED ROWS (IF ANY)")
    if tempDfNotAllowed.shape[0] >= 1:
        print(f"WARNING: removing {tempDfNotAllowed.shape[0]:,.0f} rows due to unit sizes greater than allowable group size!)")
        print(tempDfNotAllowed)
        print()
    else:
        print(f"GREAT, all {initialTempDfRows:,.0f} tasks have unit sizes within the allowable group size!")
        print()
    
print("Done working on all data and with all concatenated lists and dfs, attempting to create single resulting df...")


###################### only handling Null and Not allowed below (may have bugs if no values exist)
if len(allNotAllowedList) > 0:
    allGroupNotAllowedListConcat = pd.concat(allNotAllowedList, ignore_index=True)
    allGroupNotAllowedListDf = pd.DataFrame(allGroupNotAllowedListConcat)
else:
    print("GREAT, no values larger than allowable size exist in any of the data!")


if len(allNullList) > 0:
    allGroupNullListConcat = pd.concat(allNullList, ignore_index=True)
    allGroupNullListDf = pd.DataFrame(allGroupNullListConcat)
else:
    print("GREAT, no null values exist in any of the data!")
######################



if len(allGroupList) > 0:
    allGroupListConcat = pd.concat(allGroupList, ignore_index=True)
    allGroupListDf = pd.DataFrame(allGroupListConcat)    
    print("Done creating single df from all data!")
    
    allGroupListDf["GROUP_SUM"] = allGroupListDf.groupby(["TEMPGROUP","GROUP"])[thingAmountCol].transform(pd.Series.sum)
    allGroupListDf["SupvGroupCumSum"] = allGroupListDf.groupby(["TEMPGROUP","GROUP"])[thingAmountCol].transform(pd.Series.cumsum)
    allGroupListDf.sort_values(by=["TEMPGROUP", "GROUP", "GROUP_SUM", ], ascending=[True, True, False], inplace=True)
    print(allGroupListDf)
    print(allGroupListDf.shape)
    
    finalKeepCols = ['TEMPGROUP', 'TEMPLIMIT', 'GROUP_SUM', 'GROUP', thingAmountCol, priorityCol, thingCol, 'MAX_LIMIT']
    finalDf = allGroupListDf[finalKeepCols]


    print("FINAL RESULT DATAFRAME (type 'finalDf' to view...'):")
    print(finalDf)
    print("\n"*2)
    
    summary = (finalDf.groupby(["TEMPGROUP"])
           .agg({"GROUP":["nunique", "count"], "TEMPLIMIT":["max"], thingAmountCol:["sum","max","min","mean"]})
           .reset_index())
    print(f"Sanity check of summary results (type 'summary'...):")
    print(summary)
    print("\n"*3)
else:
    print("NO DATAFRAMES TO CONCATENATE")
    


print("TO VIEW DATA THAT WAS EXCLUDED (i.e. unit size above allowable limit or null)")
print("type 'allGroupNotAllowedListDf' or 'allGroupNullListDf'...")
print("\n"*3)

print(f"QC while loop: to view each while loop iteration ({len(whileControlList):,.0f} loop(s))")
print("type 'whileControlList'...")
print("\n"*3)



##### BELOW IS FOR CALCULATING TIME SAVINGS METRICS #####
endtime = time.time()
print("\n"*3+"--------------------------","\n","DONE!","\n"*2,"Start time:  ",starttime,"\n","Finish time: ",endtime,"\n"*2,)
computeTime = round((endtime-starttime),0)
#print("Total time:  ",computeTime, "seconds","\n")

print()
print("Total time (h,m,s):", str(datetime.timedelta(seconds=computeTime)),"\n")


############ don't alter these ############
humanSeconds = humanMinutesInteger * 60
hourlyWage = yearlySalary / 52 / 40
minuteWagePaid = hourlyWage / (humanMinutesInteger/60) 
humanMins = humanSeconds/60
scriptMins = computeTime/60
totalHumanTime = humanMins * numberTimes
totalScriptTime = scriptMins * numberTimes

print(f"It would take a person {(round(humanMins,2)):,.1f} minutes.")
#print()
print(f" It took the script {(round(scriptMins,2)):,.1f} minutes.")
##### need to handle for 0-minute rounded script runtimes b/c 'float division by zero' error
print(f" The script is {(int(round(humanMins/scriptMins,0))):,.0f} times faster.")
print()
print(f"When ran {numberTimes:,.0f} time(s):")
print(f" Manual mins: {(round(totalHumanTime,2)):,.1f}", "\t", f"(hours: {(round(totalHumanTime/60,2)):,.0f})")
print(f" Script mins, {(round(totalScriptTime,2)):,.1f}", "\t", f"(hours: {(round(totalScriptTime/60,2)):,.0f})")
print(f"The script saved {(round(totalHumanTime/60,2) - round(totalScriptTime/60,2)):,.0f} hours (salary savings: ${(int(round((totalHumanTime/60 - totalScriptTime/60) * hourlyWage,0))):,.0f} based on ${(int(round(yearlySalary,0))):,.0f} per year)")
print()
############ END don't alter these ############






### WRITING TO CSV ###
partialPathAndName = r"\\hotce15\p\l48esri\per\working\c_habrock\AICOE\AGILE_PROJECT_RANKING\OUTPUT_RESULTS\GROUP_RESULTS_"
outFile = partialPathAndName + csvName + r".csv"
#finalDf.to_csv(outFile, index=False)                
print("DONE WRITING CSV")
print(f"Written to: {outFile}")