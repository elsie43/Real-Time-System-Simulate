# highest-utilization version
# sort by utilMax from large to little: 1 tasks; response 2421.79; util 0.9724
from operator import methodcaller
import math
APTaskStr = []
TaskModel = []
apQueue = []
cpuUsed = 0 # off-line max utilization
systemTime = 0
file = "OnlinejobsOf100AP.txt"
fileOnline = "OnlinejobsOfHRT.txt"

class Task:
    def __init__(self, info, realExe):
        self.__id = int(info[0])
        self.__phase = int(info[1])
        self.__period = float(info[2])
        self.__exeMin = float(info[3])
        self.__exeMax = float(info[4])
        self.__ddl = int(info[2])
        self.__allInfo = info
        self.ddlOnline = self.__ddl
        self.realExeLeft = realExe
        self.maxExeLeft = self.__exeMax
        self.__utilMax = self.__exeMax / self.__period

    def getInfo(self, x):
        if x == "id":
            return self.__id
        elif x == "phase":
            return self.__phase
        elif x == "period":
            return self.__period
        elif x == "exeMin":
            return self.__exeMin
        elif x == "exeMax":
            return self.__exeMax
        elif x == "ddl":
            return self.__ddl
        elif x == "utilMax":
            return self.__utilMax
        elif x == "allInfo":
            return self.__allInfo
        else:
            return "Error"

    def waiting(self): # after release and in ready queue
        self.ddlOnline -= 1

    def executing(self):
        self.realExeLeft -= 1
        self.maxExeLeft -= 1

class TaskAP:
    def __init__(self, info):
        self.__id = int(info[0])
        self.__arrivalTime = int(info[1])
        self.__exe = float(info[2])
        self.__allInfo = info
        self.realExeLeft = self.__exe

    def getInfo(self, x):
        if x == "id":
            return self.__id
        elif x == "arrivalTime":
            return self.__arrivalTime
        elif x == "exe":
            return self.__exe
        elif x == "allInfo":
            return self.__allInfo
        else:
            return "Error"

    def executing(self):
        self.realExeLeft -= 1

# read "OnlinejobsOf100AP.txt"
with open(file,'r', encoding='utf-8-sig') as p: # read file
    for line in p:
        if line.strip(): # skip blank
            APTaskStr.append(line)

for i in range(len(APTaskStr)): # build TaskModel list
    tempInfo = APTaskStr[i].split()
    apQueue.append(TaskAP(tempInfo))

# sorted Aperiodic task list by arrival time
apQueue = sorted(apQueue, key = lambda x : (x.getInfo("arrivalTime"))) # sort 100 tasks by Uitilization

# read "OnlinejobsOfHRT.txt"
temp = []
onlineJob = [] # to save each job's execution time in a task
with open(fileOnline,'r') as file:
    for line in file:
      if line.strip():
        temp.append(line)

onlineJob.append([]) # shift (for starting from 1 rather than 0 to adjust job's id)
for i in range(len(temp)): # build TaskModel list
    temp[i] = temp[i].split()
    if (i%2) == 0:
        TaskModel.append(Task(temp[i], -1))
    temp[i] = list(map(int, temp[i]))
    if (i%2) == 1:
        onlineJob.append(temp[i])


# HW1 Question 1: check infeasible or inconsistence
infeasible = [] #id
def checkModel(TaskModel): # check infeasible or inconsistence
    #print("(1) Inconsistence & Infeasible Tasks:") 
    for i in range(len(TaskModel)):
        if TaskModel[i].getInfo("exeMax") < TaskModel[i].getInfo("exeMin") or \
        TaskModel[i].getInfo("exeMax") > TaskModel[i].getInfo("ddl"):
            infeasible.append(TaskModel[i].getInfo("id"))
            print("Task", TaskModel[i].getInfo("id"))
checkModel(TaskModel)

sorted_list = sorted(TaskModel, key = lambda x : (x.getInfo("utilMax")), reverse = True) # sort 100 tasks by Uitilization
#sorted_list = sorted(TaskModel, key = lambda x : (x.getInfo("exeMax"))) # sort 100 tasks by Uitilization
#sorted_list = sorted(TaskModel, key = lambda x : (x.getInfo("utilMax"))) # sort 100 tasks by Uitilization

#Question 2 & 3
selected = []
periodSelect = []
lcm = 1
for i in range(len(sorted_list)):
    if sorted_list[i].getInfo("id") in infeasible:
        continue    
    elif (sorted_list[i].getInfo("ddl") / sorted_list[i].getInfo("period")) < 0.8:
        continue
    elif (lcm * sorted_list[i].getInfo("period") // math.gcd(lcm, int(sorted_list[i].getInfo("period")))) > 10000: # elif: hyper-period > 10000
        continue
    elif (cpuUsed + sorted_list[i].getInfo("utilMax")) <= 1: # avoid overload
        selected.append(sorted_list[i])
        periodSelect.append(int(sorted_list[i].getInfo("period"))) #Q3
        lcm = math.lcm(*periodSelect)
        cpuUsed += sorted_list[i].getInfo("utilMax")
    else:
        #break # without reverse: stop scanning earlier if utilization sorted from little to large
        continue

hyperPeriod = lcm
readyQueue = []
apReadyQueue = []
exeTask = []
realUsed = 0
apTotalResponse = 0

def simulate(time):
    print("(5) Scheduling\n")
    global systemTime
    global realUsed
    global readyQueue
    global apReadyQueue
    global apTotalResponse
    realUsed = 0
    lastJobLeft = 0
    systemTime = 0
    for i in range(time):
        if len(exeTask) > 1:
            print("Error: number of task > 1")
            return -1

        for j in range(len(selected)): # job release and put into readyQueue
            if systemTime % selected[j].getInfo("period") == selected[j].getInfo("phase")\
            and len(onlineJob[selected[j].getInfo("id")]) > 0: # job release
                et = onlineJob[selected[j].getInfo("id")][0]
                readyQueue.append(Task(selected[j].getInfo("allInfo"), et))
                onlineJob[selected[j].getInfo("id")].pop(0) # get execution time
                print(int(systemTime), "\tTask{:4}   release,  execution time =".format(selected[j].getInfo("id")), et,sep = "  ")

        while (len(apQueue) > 0 and (apQueue[0].getInfo("arrivalTime")) == systemTime): # aperiodic task release
            apReadyQueue.append(apQueue[0])
            apQueue.pop(0)

        if len(exeTask) == 0: # system idle, select to execute; or ap executing, but periodic task ready
            if len(readyQueue) > 0 and lastJobLeft <= 0: # select period task first, and never use the time interval left from last job
                readyQueue = sorted(readyQueue, key = lambda x : (x.ddlOnline)) # EDF: sort 100 tasks by Uitilization                                  
                lastJobLeft = 0
                exeTask.append(readyQueue[0])
                readyQueue.pop(0)
            else:
                if len(apReadyQueue) > 0:
                    apReadyQueue = sorted(apReadyQueue, key = lambda x : (x.getInfo("exe"))) 
                    exeTask.append(apReadyQueue[0])
                    apReadyQueue.pop(0)
                else:
                    lastJobLeft -= 1
                    print(int(systemTime), "\tidle")
        elif len(exeTask) > 0 and isinstance(exeTask[0], TaskAP): # executing aperiodic task
            if len(readyQueue) > 0 and lastJobLeft <= 0: # select period task first
                readyQueue = sorted(readyQueue, key = lambda x : (x.ddlOnline)) # EDF: sort 100 tasks by Uitilization
                apReadyQueue.insert(0, exeTask[0])
                exeTask.pop(0) 
                lastJobLeft = 0                            
                exeTask.append(readyQueue[0])
                readyQueue.pop(0)

        for j in range(len(readyQueue)): # task in ready queue: wating time +1
            readyQueue[j].waiting()
            if readyQueue[j].ddlOnline < 0:
                print("Task ", readyQueue[j].getInfo("id"), "miss deadline")
                print("Validation failed")
                return 0

        for j in range(len(exeTask)): # executing time +1
            if isinstance(exeTask[0], Task):
                if exeTask[j].realExeLeft > 0:
                    realUsed += 1
                    print(int(systemTime), "\tTask{:4}   execute".format(exeTask[j].getInfo("id")), sep = "  ")
                exeTask[j].executing()
                if exeTask[j].realExeLeft <= 0:
                    lastJobLeft = exeTask[j].maxExeLeft + 1
                    exeTask.pop(0)
                    if (lastJobLeft > 0 and len(apReadyQueue) > 0):
                        exeTask.append(apReadyQueue[0])
                        ap_exe = 1
                        apReadyQueue.pop(0)
            elif isinstance(exeTask[0], TaskAP):
                if exeTask[j].realExeLeft > 0:
                    realUsed += 1
                    print(int(systemTime), "\tAperiodic Task{:4}   execute".format(exeTask[j].getInfo("id")),sep = "  ")
                exeTask[j].executing()
                if exeTask[j].realExeLeft <= 0:
                    apTotalResponse += (systemTime - exeTask[j].getInfo("arrivalTime"))
                    exeTask.pop(0)
            lastJobLeft -= 1
        systemTime += 1
    return (realUsed / time)

# print for Question 1
print("(1)", len(selected), "Tasks:", end = " Task ")
for i in range(len(selected)-1):
    print(selected[i].getInfo("id"), end = ", Task ")
print(selected[len(selected)-1].getInfo("id"), end = "\n")
#print(cpuUsed) # off-line Utilization

# Question 3
print("(2) Hyper-period:", hyperPeriod)

# Question 4 & 5
s = eval(input("\nEnter to Start simulation for Question___? (\
\"3\" to simulate for 10000 time units;\
\"4\" to simulate for 3 hyper-period)\n"))

if s == 3:
    print("(3) Average utilization of 10000 time units:", simulate(10000))
elif s == 4:
    simulate(hyperPeriod*3)
else:
    print("quit")

print("(5) Average response time of aperiodic jobs:", apTotalResponse / 100)