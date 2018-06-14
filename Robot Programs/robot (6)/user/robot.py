#random notes https://docs.google.com/document/d/1MEBg9Nf95mLGEn88KWNFtYFSTWBaT7gpDShVzDPCxLk/edit
# Modified from Pete's january code
# 10/02 added a quickdrive state for when the box is far enough away
# 26/02 added choons init. Also ramming mode. Also a few more comments.
# 27/02 Tech day - got robot successfully and fairly consistently finding and flipping box.
# 02/03  Put r.see in a function and the entire program went to shit since the image wasn't being changed outside the function.
# 03/03 in an attempt to fix the shitstorm of r.see I added a boolean activated version in the main loop outside the state machine
# 09/03 timings reduced and bugs fixed. Robot now accurately speeds towards box with only short stops for new pictures. 
# 19/03 Tech day - Alignment arms working. Spins robot when turning box since carpet is grippy. Hopefully patched bugs regarding blind state.
# 22/03 Changed to choose the correct marker in preparation for whichsideup
# 13/04 Bug fixes
# 22/04 Merged with whichsideup a week ago, and the unrelated crashing bug was fixed. "ready" for the competition next week.
#       Emergencyreposition state added, and code prepared for bump sensors
# 27/04 Having issues with power surges, exploring potential causes. Custom initialisation code added.

from sr.robot import *

import time

print "Current robot name 'Let's call it Gerald'"

#########################################################################################################################
#################################################   Initialisation   ####################################################
#########################################################################################################################

#R = Robot() <--Standard setup

R = Robot.setup()
print "Setting up the robot"

# Setup phase.
# Here you can configure hardware enumeration

R.init()

#Level arm switch
R.ruggeduinos[0].pin_mode(2, INPUT)
pin2=R.ruggeduinos[0].digital_read(2)

print"Initialising hardware"
R.servos["sr0QQ2K"][7] = 100
R.servos["sr0QQ2K"][1] = -100
print"Straightening main arm"
while pin2==False:
            R.motors[0].m0.power = 15
            time.sleep(0.1)
            R.motors[0].m0.power = 0
            pin2=R.ruggeduinos[0].digital_read(2)
            
print"Closing arms to be in size limit"
#move little arms out of way
R.servos["sr0QQ2K"][7] = -100
time.sleep(0.5)
R.servos["sr0QQ2K"][1] = 100
R.power.beep(100, note='a')

R.wait_start()
R.power.beep(100, note='b')
print "Robot started"

#########################################################################################################################
###################################################   Variables   #######################################################
#########################################################################################################################

SEARCHING, LEVELARM, QUICKDRIVE, FLIP, DANKTUNE, RAM, FINALADJUST, RETURN, BLIND, TOKENLOST, EMERGENCYREPOSITION, DOUBLECHECK, PUSHHOME = range(13)

########### Ruggeduino test


#Bump sensors
R.ruggeduinos[0].pin_mode(3, INPUT)      #Front left
pin3=R.ruggeduinos[0].digital_read(3)
R.ruggeduinos[0].pin_mode(4, INPUT)      #Front right
pin4=R.ruggeduinos[0].digital_read(4)
R.ruggeduinos[0].pin_mode(5, INPUT)      #Back right
pin5=R.ruggeduinos[0].digital_read(5)
R.ruggeduinos[0].pin_mode(6, INPUT)      #Back left
pin6=R.ruggeduinos[0].digital_read(6)

###################################################
################## TURNING MAPS ###################
###################################################

netA = {36:"pink" ,34:"green" ,37:"yellow" ,35:"orange" ,32:"top",33:"bot"} #Dictionary for box Net A
netB = {42:"pink" ,40:"green" ,43:"yellow" ,41:"orange" ,38:"top",39:"bot"} #Dictionary for box Net B
netC = {48:"pink" ,46:"green" ,49:"yellow" ,47:"orange" ,44:"top",45:"bot"} #Dictionary for box Net C

netAturns = {0:"pink", 1:"green", 2:"yellow"}

netATurningMap = {"top": ["green", "orange", "pink", "yellow"],   #To See whether we can achieve our colour from this approach?????
                  "pink": ["top", "orange", "bot", "yellow"],
                  "orange": ["top", "green", "bot", "pink"],
                  "bot": ["green", "yellow", "pink", "orange"],
                  "green": ["top", "yellow", "bot", "orange"],
                  "yellow": ["top", "pink", "bot", "green"]
                  }
                  
netBTurningMap = {"top": ["green", "pink", "orange", "yellow"], #To See whether we can achieve our colour from this approach?????
                  "pink": ["top", "green", "bot", "orange"],
                  "orange": ["top", "pink", "bot", "yellow"],
                  "bot": ["green", "yellow", "orange", "pink"],
                  "green": ["top", "yellow", "bot", "pink"],
                  "yellow": ["top", "orange", "bot", "green"]
                  }
                 
netCTurningMap = {"top": ["green", "pink", "yellow", "orange"], #To See whether we can achieve our colour from this approach?????
                  "pink": ["top", "green", "bot", "yellow"],
                  "orange": ["top", "yellow", "bot", "green"],
                  "bot": ["green", "orange", "yellow", "pink"],
                  "green": ["top", "orange", "bot", "pink"],
                  "yellow": ["top", "pink", "bot", "orange"]
                  }
      
zoneColours = {0:"green", 1:"orange", 2:"pink", 3:"yellow"}
ourColour = zoneColours[R.zone] # R.zone is our zone, our zone gives us ourColour from above dictionary
zones = {0:[0, 27, 1, 26], 1:[6, 7, 5, 8], 2:[13, 14, 12, 15], 3:[20, 21, 19, 22]}
####################################################

#doesn't like it when markers is not declared
oldmarkers=R.see()
markers=R.see()

spinneg= False

takepicturebool= False

ourCorner0 = zones[R.zone][0]
ourCorner1 = zones[R.zone][1]

count=0
failsafeCounter=0
failsafeCounter2=0
howtimes=0

#########################################################################################################################
###################################################   Functions   #######################################################
#########################################################################################################################
    
    #####################################################################
    ############################## HOW MANY TIMES #######################    
    
    # USE try: howManyTimes , except(IndexError): pass EVERYTIME WHEN CALLING THIS FUNCTION
    
def howManyTimes(box):
    def lookFor(array, word):
        index = 0
        for i in array:
            if i == word:
                print("Found" + i)
                return index
            index = index+1
        return 404
        
    def calculate(sideOnTop, sideWeSee, netTurningMap):
        for i in range (0,4):
            print(netTurningMap[sideWeSee][i])
            if netTurningMap[sideWeSee][i] == ourColour:
                print ("Side On Top =", sideOnTop)       #### Was Set to sideOnTop ######
                return i - lookFor(netTurningMap[sideWeSee], sideOnTop)
        return 400
    
    def getTopSide(net, netTurningMap):
        sideWeSee = net[box.info.code]     #Tell box code from box marker
        index = round(box.orientation.rot_z/90) #Index is equal to the (box's rotation on the z axis) divided by (90)...but why? to get a whole number i.e Box Rot = 0 or 1
        print "index: %d, side we see : %s, z-rotation: %f side on top: %s" % (index, sideWeSee, box.orientation.rot_z, netTurningMap[sideWeSee][int(index)], ) #basically displays box infos
        return netTurningMap[sideWeSee][(int(index) + 4) % 4], sideWeSee
        
    if box.info.code >= 32 and box.info.code < 38:  #If Net A box
        sides = getTopSide(netA, netATurningMap)
        return calculate(sides[0], sides[1], netATurningMap)
        
        
    elif box.info.code >= 38 and box.info.code < 44: #If Net B box
        sides = getTopSide(netB, netBTurningMap)
        return calculate(sides[0], sides[1], netBTurningMap)
        
    elif box.info.code >= 44 and box.info.code <= 49: #If Net C box
        sides = getTopSide(netC, netCTurningMap)
        return calculate(sides[0], sides[1], netCTurningMap)
        
    else:
        print(box.info.code)
        return 401 #Then What?!
        #changed from "not a box"
    
    #######################################################################
    #######################################################################
    
def twist(speed, secs):
    #move little arms out of way
    R.servos["sr0QQ2K"][7] = 200
    R.servos["sr0QQ2K"][1] = -200
    
    #turn whole robot in direction
    R.motors[1].m0.power = speed/2
    #R.motors[1].m1.power = -speed+20
    
    #spin arm
    R.motors[0].m0.power = speed/4
    time.sleep(0.2)
    R.motors[0].m0.power = speed/2
    time.sleep(0.4)
    R.motors[0].m0.power = speed
    time.sleep(secs-0.5)
    R.motors[0].m0.power = 0
    
    #Stop turningrobot
    R.motors[1].m0.power = 0
    R.motors[1].m1.power = 0
    
def shakeoff(speed,seconds):
    R.motors[1].m0.power = speed
    R.motors[1].m1.power = speed+5
    R.motors[0].m0.power = speed
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[0].m0.power = speed*-1
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[0].m0.power = speed
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[0].m0.power = speed*-1
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[0].m0.power = speed
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[0].m0.power = speed/-1
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[0].m0.power = speed
    print "Wiggle"
    time.sleep(seconds/8)
    R.motors[1].m0.power = 0
    R.motors[1].m1.power = 0
    R.motors[0].m0.power = 0

def twisttimes(times):
    print "Turning token {0} times"\
    .format(times)
    spin = 0.70*times
    spinneg=False
    power=60
    if spin <0:
        spinneg=True
        spin=spin*-1
        power=power*-1
    twist(power, spin)
    spineg=False
    
def drive(speed, seconds):
    R.motors[1].m0.power = speed
    R.motors[1].m1.power = speed+5
    time.sleep(seconds)
    R.motors[1].m0.power = 0
    R.motors[1].m1.power = 0

def turn(speed, seconds):
    R.motors[1].m0.power = speed
    R.motors[1].m1.power = -speed
    time.sleep(seconds)
    R.motors[1].m0.power = 0
    R.motors[1].m1.power = 0
    
def straightenbox():
    #placeholder for dancing disco arms
    R.power.beep(500, note='a')
    print "Arms open"
    R.servos["sr0QQ2K"][1] = -100
    R.servos["sr0QQ2K"][7] = 100
    time.sleep(0.5)
    print("Arms closed (left first)")
    R.servos["sr0QQ2K"][7] = -15
    time.sleep(0.5)
    R.servos["sr0QQ2K"][1] = 25
    time.sleep(0.5)
    print "Arms open"
    R.servos["sr0QQ2K"][1] = -100
    R.servos["sr0QQ2K"][7] = 100
    time.sleep(0.5)
    print("Arms closed (right first)")
    R.servos["sr0QQ2K"][1] = -25
    time.sleep(0.5)
    R.servos["sr0QQ2K"][7] = 25
    time.sleep(0.5)
    print "Arms open"
    R.servos["sr0QQ2K"][1] = -100
    R.servos["sr0QQ2K"][7] = 100
    time.sleep(3.0)
    
def takepicture():
    markers = R.see()
    time.sleep(3)
    print "Photo taken"
    time.sleep(0.3)
    print "Checking Photo"

def levelarm(secs):
    R.motors[0].m0.power = 10
    
    R.motors[1].m0.power = -5
    R.motors[1].m1.power = -15
    R.motors[1].m0.power = 0
    R.motors[1].m1.power = 0
    
    
    time.sleep(secs)
    R.motors[0].m0.power = 0
    
    
    R.motors[1].m0.power = 0
    R.motors[1].m1.power = 0

#######################################################################################################################################################################################
#####################################################===============-------------- MAIN ---------------=================##############################################################
#######################################################################################################################################################################################

#Starting conditions that aren't specified in variables

state = SEARCHING
#default state set to searching
takepicturebool= True
chosentoken=False

#The code of the marker
targettokencode = 0
#The number of the marker in the list
targettokennumber=0

#Open servo arms
R.servos["sr0QQ2K"][1] = 100
R.servos["sr0QQ2K"][7] = -100

#Drive out
print"Driving out"
#turn (-25, 0.9)
drive(60, 8)


#try: 
#    twisttimes(-1*howtimes)
#    print(howtimes)
#except:
#    pass

while True:
#infinite loop

#########################################################################################################################
###############--------------###################   Pre-state code   ###################---------------###################
#########################################################################################################################

    #Bump sensors
    pin3=R.ruggeduinos[0].digital_read(3)
    if pin3==True:
        print "Back bump sensor activated, moving forward slightly"
        drive(30, 1)
#    if pin3==True and pin4==True:
#        print "Both front bump sensors activated, reversing slightly"
#        drive(-40, 1)
#    if pin5==True and pin6==True:
#         print "Both back bump sensors activated, moving forward slightly"
#        drive(30, 1)
#    
#    if pin3==True:
#        print "Front left bump sensor activated, reversing and correcting alignment slightly"
#        drive(-30, 1)
#        turn(20, 1)
#    if pin4==True:
#        print "Front right bump sensor activated, reversing and correcting alignment slightly"
#        drive(-30, 1)
#        turn(-20, 1)
#    if pin5==True:
#        print "Back right bump sensor activated, moving and correcting alignment slightly"
#        drive(30, 1)
#        turn(-20, 1)
#    if pin6==True:
#        print "Back left bump sensor activated, moving and correcting alignment slightly"
#        drive(30, 1)
#        turn(20, 1)

    if takepicturebool == True:
        print "---Pre state machine takephoto---" 
        print "takepicturebool=true, so picture will be taken and relevant variables updated."
        
        oldmarkers = markers
        
        time.sleep(0.8)
        markers = R.see()
        print "Photo taken"
        time.sleep(0.3)
        print "Checking Photo"
        
    #New pre-state code for finding the target token
        if chosentoken==True:
            
            print"Entering chosentoken in pre-state loop"

            count=0
            
            loopbreakerbool=False
            if len(markers) > 0:
                for m in markers:
                    if loopbreakerbool==False:
                        if m.info.code==targettokencode:
                            print "Target token found in new photo"
                            targettokennumber= count
                            loopbreakerbool==True
                            #state=QUICKDRIVE
    
                        else:
                            print "The target token has not been found in the new photo"
                            #print"Going to TOKENLOST from Pre-state takephoto if our target token is not found in this loop"    
                            #state=TOKENLOST
                    count=count+1
                #if loopbreakerbool==False:            
                #    state=TOKENLOST        
                        
                        
            else:
                print "Something's gone wrong in the pre-state machine takepicture - no markers found in new photo (Not even arena or robots)"
                print "Camera was potentially obstructed"
                print"Going to BLIND from Pre-state takephoto"
                state=BLIND
    
#############################################################################################################################################################################
#########################################===============-------------- State machine start ---------------=================##################################################
#############################################################################################################################################################################

###############################################################################################################################
###################################################   Searching state   #######################################################
###############################################################################################################################
    if state == SEARCHING:
        print "--Entering searching state--"
        takepicturebool= True
        chosentoken=False
        
        if len(markers)>0:
            count=0
            for m in markers:
                howTimes=howManyTimes(m)
                if howTimes==0:
                    print"Token with our side up sighted, ignoring"
                else:
                    if howTimes <10:
                        #If markers[targettokennumber].dist > markers[count] ??? Get closest marker
                        failsafeCounter=0
                        targettokencode=m.info.code
                        chosentoken=True
                        targettokennumber=count
                        print"Valid token sighted - Token code: {0} is {1} away at bearing {2}. To be flipped {3} times."\
                        .format(m.info.code, m.dist, m.rot_y, howTimes)
                        
                        if m.dist <= 0.7:
                            # If closer than than 0.7m, make final adjustments before going ahead blind
                            print "Going to FINALADJUST from SEARCHING"
                            state = FINALADJUST
                            takepicturebool= False
                        else:
                            print "Going to QUICKDRIVE from SEARCHING"
                            state = QUICKDRIVE
                            takepicturebool= False
                    else:
                        print"Token which can not be flipped sighted, ignoring"
                        print"Error: {0}"\
                        .format(howTimes)
                count=count+1
                
        if state == SEARCHING:
            print "Can't see anything."
            turn(25, 0.8)
            failsafeCounter=failsafeCounter+1
            time.sleep(1)
            #When no tokens are found, turn slightly right and check again
            
            if failsafeCounter>=10:
                print"I've spun round 10 times, there's not much chance of there being any valid tokens here so I'm going to move"
                state=EMERGENCYREPOSITION
                
################################################################################################################################
###################################################   Quickdrive state   #######################################################
################################################################################################################################    
        
    elif state == QUICKDRIVE:
        print "--Entering Quickdrive state--"
        
        takepicturebool= True
        
        try: 
                
            if len(markers) > 0:
                print "Can see token"
                m = markers[targettokennumber]
                #quickdrive sound
                R.power.beep(500, note='c')
                time.sleep(0.1)
                R.power.beep(500, note='d')
                time.sleep(0.1)
                if -10 <= m.rot_y <= 10:
                        if m.dist >=3:
                            print "Full speed ahead! Token spotted 3 or more metres away."
                            drive(60, 4)
                        elif m.dist >=2:
                            print "Full speed ahead! Token spotted over 2m away"
                            drive(60, 2)          
                        elif m.dist >=1.5:
                            print "Full speed ahead! Token spotted over 1.5m away"
                            drive(60, 1)
                        elif m.dist>=0.9:
                            print "Ahead! (Reduced speed) Token spotted over 0.9m away"
                            drive(50, 1)
                        elif m.dist>=0.7:
                            print "Token spotted between 0.7 and 0.9 metres away. Driving slightly forward."
                            drive(50, 0.5)
                        elif m.dist < 0.7:
                            print "Token less than 70cm from camera, going to FINALADJUST from QUICKDRIVE"
                            state = FINALADJUST
                            takepicturebool= False
                        else:
                            print "Defaulting to search after none of the options working (There are serious problems if this message is shown)"
                            state= SEARCHING   
        
                elif m.rot_y < -7:
                        print "Left a bit..."
                        turn(-12.5, 0.7)
                        takepicturebool= True
                elif m.rot_y > 7:
                        print "Right a bit..."
                        turn (12.5, 0.7)
                        takepicturebool= True
                else:
                    state = BLIND
                    print "Second quickdrive default to BLIND"
                    takepicturebool= False
                    
            else:
                print "index error - can't see any tokens (Quickdrive)"
                state = BLIND
                takepicturebool= False
        except IndexError:
                pass            

##################################################################################################################################
###################################################   Final adjust state   #######################################################
##################################################################################################################################

    elif state == FINALADJUST:
        print "--final adjust state--"
        R.power.beep(500, note='e')
        
        if len(markers) > 0:
            m = markers[targettokennumber]
            ourSavedMarker = m
            if -4 <= m.rot_y <= 4:
                print "Token sighted at bearing {0} degrees." \
                .format(m.rot_y)
                state=RAM
                takepicturebool= False
            elif m.rot_y < -4:
                    print "Token sighted at bearing {0} degrees." \
                    .format(m.rot_y)
                    print "Left a tiny bit..."
                    turn(-12.5, 0.4)
                    takepicturebool= True
                     
            elif m.rot_y > 4:
                    print "Token sighted at bearing {0} degrees." \
                    .format(m.rot_y)
                    print "Right a tiny bit..."
                    turn (12.5, 0.4)
                    takepicturebool= True
        else:
            print "index error - can't see any tokens (Final adjust)"
            state=BLIND
            takepicturebool= False
        
#######################################################################################################################################        
###################################################   RAM/final assault state   #######################################################
#######################################################################################################################################

    elif state == RAM:
        print "--ram state--"
        R.servos["sr0QQ2K"][7] = 200
        R.servos["sr0QQ2K"][1] = -200
        drive(25,2)
        straightenbox()
        turn(20,0.18)
        R.power.beep(500, note='f')
        time.sleep(0.1)
        R.power.beep(500, note='f')
        time.sleep(0.1)
        R.power.beep(1000, note='g')
        print "RIP token"
        drive(40,2)
        state=FLIP

##########################################################################################################################        
###################################################   Flip state   #######################################################
##########################################################################################################################

    elif state == FLIP:
        print "--flip state--"
        
        R.power.beep(500, note='g')
        time.sleep(2)
        howtimes =howManyTimes(ourSavedMarker)
        if howtimes<5:
            if howtimes==3:
                howtimes=-1
            if howtimes==-3:
                howtimes=1
            print "Attempting to turn the box {0} times"\
            .format(howtimes)
            try: 
                twisttimes(-1*howtimes)
                print(howtimes)
            except IndexError:
                pass
            state=LEVELARM
        else:
            state=SEARCHING
        
###########################################################################################################################
###################################################   Choon state   #######################################################
###########################################################################################################################

    elif state==DANKTUNE:
        print "--choon state--"
        #Mario coin sound to reduce wasted time
        
        #Added one second wait in attempt to stop power surges
        time.sleep(1)
        R.power.beep(100, note='b')
        time.sleep(0.1)
        R.power.beep(1000, note='e')
        #choon
        state=RETURN

############################################################################################################################
###################################################   Return state   #######################################################
############################################################################################################################
        
    elif state==RETURN:
        print "--RETURN STATE: Task complete, turning round and searching again--"
        drive(-50, 1)
        turn (25, 2)
        state=SEARCHING
        takepicturebool= True      
        #Searches for other tokens
        chosentoken=False

###########################################################################################################################
###################################################   Blind state   #######################################################
###########################################################################################################################
       
    elif state==BLIND:
        print"--Entering BLIND state--"
        R.power.beep(500, note='d')
        time.sleep(0.1)
        R.power.beep(1000, note='b')
        time.sleep(0.1)
            
        if len(oldmarkers) > 0:
            m2 = oldmarkers[targettokennumber]
            
            if m2.dist >1.5:
                print"Token was more than 1.5m away, turning slightly to test if it's in view"
                turn(-20, 0.5) 
                time.sleep(0.2)
                
            elif m2.dist <=1.5:    
                print"Token was less than 1.5m away, reversing (and turning slightly) to see if token is still there"
                drive(-50, 0.5)
                turn(-20, 0.8) 
                time.sleep(0.2)
                #Experimental break of forward backward cycle
        else:
            print "Issues with old picture in BLIND"
            turn(-20, 0.2) 
            time.sleep(0.2)
        state = SEARCHING
        takepicturebool= False
                
###############################################################################################################################
###################################################   Level arm state   #######################################################
###############################################################################################################################
        
    elif state==LEVELARM:
        print"--Entering LEVELARM state--"
        print"Shaking token off robot"
        shakeoff(-50,6)
        print "Straightening arm in preparation for next assault"
        
        if howtimes<0:
            twist(10,1)
        else:
            twist(-10,1)
        R.servos["sr0QQ2K"][7] = -30
        R.servos["sr0QQ2K"][1] = 30
        R.servos["sr0QQ2K"][7] = 0
        R.servos["sr0QQ2K"][1] = 0
        R.servos["sr0QQ2K"][7] = -30
        R.servos["sr0QQ2K"][1] = 30
        R.servos["sr0QQ2K"][7] = 100
        R.servos["sr0QQ2K"][1] = -100
        
        
        R.servos["sr0QQ2K"][7] = 70
        time.sleep(0.5)
        R.servos["sr0QQ2K"][1] = -70
        drive(-50,3)
        pin2=R.ruggeduinos[0].digital_read(2)
        while pin2==False:
            levelarm(0.1)
            #time.sleep(0.01)
            pin2=R.ruggeduinos[0].digital_read(2)
        
        takepicturebool= True
        state=DOUBLECHECK
        R.servos["sr0QQ2K"][1] = 100
        R.servos["sr0QQ2K"][7] = -100
        
###########################################################################################################################
#################################################   Lost token state   ####################################################
###########################################################################################################################
       
    elif state==TOKENLOST:
        print"--Entering TOKENLOST state--"
        
        drive(-20,1)
        time.sleep(0.3)
        markers = R.see()
        
        if len(markers) > 0:
                numberOfLoops = 0
                for m in markers:
                    if m.info.code==targettokencode:
                        print "Target token found in new photo"
                        targettokennumber=numberOfLoops
                        print "Going to QUICKDRIVE from TOKENLOST"
                        state=QUICKDRIVE
                    else:
                        print "The target token has not been found in the new photo"
                        print "Going to BLIND from TOKENLOST (1)"
                        state=BLIND
                    numberOfLoops = numberOfLoops+1
        else:
            print "No markers of any kind found in lost token"
            print "Going to BLIND from TOKENLOST (2)"
            state=BLIND
            
###########################################################################################################################
############################################   Emergency Re-position state   ##############################################
###########################################################################################################################
            
    elif state==EMERGENCYREPOSITION:
        print"--Entering EMERGENCY REPOSITION state--"
        #This state activates when the robot has spun 10 times finding no valid tokens. It will drive according to how far away the furthest marker is and try again.
        takepicturebool=True
        chosentoken=False
        tokendistance=0
        R.power.beep(100, note='a')
        drive(-20,3)
        time.sleep(0.3)
        print"Taking picture"
        markers = R.see()
        if len(markers) > 0:
            print"markers found in new photo, identifying furthest marker"
            for m in markers:
                if m.dist>tokendistance:
                    tokendistance = m.dist
            print"Furthest marker is {0} metres away"\
            .format(tokendistance)
            print"Driving at full speed. Going roughly the distance of that marker"
            drive(60,tokendistance*1.2)
            drive(-30,2)
            state=SEARCHING
            failsafeCounter=3
                        
        else:
            print "No markers of any kind found"
            print "Reversing and turning around"
            drive(-50, 3)
            turn (25, 4)
            failsafeCounter2=failsafeCounter2+1
            
        if failsafeCounter2==4:
            failsafeCounter2=0
            state=SEARCHING
            
###########################################################################################################################
##############################################   Double check state   #####################################################
###########################################################################################################################
            
    elif state==DOUBLECHECK:
        print"--Entering DOUBLE CHECK state--"
        print"Checking marker to see if ours in on top"
        if len(markers) > 0:
            m= markers[targettokennumber]
            if howManyTimes(m) == 0:
                print"Mission success"
                state=DANKTUNE
            else:
                state=QUICKDRIVE
                print"Mission failed, trying again"
        else:
            print"Index error"
            state=SEARCHING
            
###########################################################################################################################
#################################################   Push home state   #####################################################
###########################################################################################################################
            
    elif state==PUSHHOME:
        #To be used directly after flip"
        print"--Entering Push Home state--"
        print"This will be used if we suddenly decide to push our token back home"
        #?? wat the hell do I put here
        
        print"grabbing token"
        R.servos["sr0QQ2K"][7] = -60
        R.servos["sr0QQ2K"][1] = 60
        
        
###########################################################################################################################################################################
#########################################===============-------------- State machine end ---------------=================##################################################
###########################################################################################################################################################################
        
        
        
        
