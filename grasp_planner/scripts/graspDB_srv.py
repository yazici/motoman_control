#!/usr/bin/env python


import tf
import math
import rospy
import numpy
import roslib
import sys
import traceback
import time
#from itertools import izip
"""OpenRave dependencies"""
import openravepy
from std_msgs.msg import Header
from geometry_msgs.msg import PoseArray, PoseStamped, Pose, Point, Quaternion
from grasp_planner.msg import apcGraspPose, apcGraspArray
from grasp_planner.srv import apcGraspDB, apcGraspDBResponse
if not __openravepy_build_doc__:
    from openravepy import *
    from numpy import *

"""
br = tf2_ros.TransformBroadcaster()
t.header.stamp = rospy.Time.now()
t.header.frame_id = "base_link"
t.child_frame_id = "grasp"
t.transform.translation = grasp.position
t.transform.rotation = grasp.orientation
br.sendTransform(t)

"""

"""
def graspOffset(apcPose):
    offset = 0.1 #offset by 10 cm
    x = apcPose.posegrasp.position.x
    y = apcPose.posegrasp.position.y
    z = apcPose.posegrasp.position.z
    vecx = apcPose.poseapproach.x
    vecy = apcPose.poseapproach.y
    vecz = apcPose.poseapproach.z
    vector = numpy.vector([vecx, vecy, vecz]) #approach vector
    vectorMagnitude = numpy.sqrt(vecx,vecy,vecz) #magnitude of approach vector
    unitVector = vector/vectorMagnitude
    offsetVector = -unitVector*offset #new grasp point

    print newPoint
"""

def genAPCGraspPose(grasp, object):    
    showOutput = False # If set to true, will show all print statments
    qw = numpy.sqrt(1 + grasp.item(0,0) + grasp.item(1,1) + grasp.item(2,2))/2
    qx = (grasp.item(2,1) - grasp.item(1,2)) / (4*qw)
    qy = (grasp.item(0,2) - grasp.item(2,0)) / (4*qw)
    qz = (grasp.item(1,0) - grasp.item(0,1)) / (4*qw)

    offset = 0.1 #offset by 10 cm
    vecx = grasp.item(0,3) - object.item(0,3)
    vecy = grasp.item(1,3) - object.item(1,3)
    vecz = grasp.item(2,3) - object.item(2,3)
    vector = numpy.array([grasp.item(0,3), grasp.item(1,3), grasp.item(2,3)]) #approach vector
    vectorMagnitude = numpy.sqrt(vecx*vecx+vecy*vecy+vecz*vecz) #magnitude of approach vector
    unitVector = numpy.array([vecx, vecy, vecz])/vectorMagnitude
    offsetVector = unitVector*offset #new grasp point
    newApproachVector = vector + offsetVector

    grasp = apcGraspPose(
        posegrasp = Pose(
            position=Point(
                x=grasp.item(0,3),
                y=grasp.item(1,3),
                z=grasp.item(2,3),
            ),
            orientation=Quaternion(
                x=qx,
                y=qy,
                z=qz,
                w=qw,
            )
        ),    
        poseapproach = Pose(
            position=Point(
                x=newApproachVector.item(0),
                y=newApproachVector.item(1),
                z=newApproachVector.item(2),
            ),
            orientation=Quaternion(
                x=qx,
                y=qy,
                z=qz,
                w=qw,
            )
        )
    )


    #graspOffset(grasp)
    if showOutput:
        print "convert matrix to pose msg"           
    return grasp

def quatToMatrix(quat):
    showOutput = False # If set to true, will show all print statments
    x = quat.position.x
    y = quat.position.y
    z = quat.position.z
    qw = quat.orientation.w
    qx = quat.orientation.x
    qy = quat.orientation.y
    qz = quat.orientation.z

    Trobobj = numpy.matrix([[1-2*qy*qy-2*qz*qz, 2*qx*qy-2*qz*qw, 2*qx*qz + 2*qy*qw, x],
        [2*qx*qy + 2*qz*qw, 1 - 2*qx*qx - 2*qz*qz, 2*qy*qz - 2*qx*qw, y],
        [2*qx*qz - 2*qy*qw, 2*qy*qz + 2*qx*qw, 1 - 2*qx*qx - 2*qy*qy, z],
        [0, 0, 0, 1]])             
    if showOutput:
        print "Inside quatToMatrix(). Conversion of req.Trob_obj to numpy matrix"
        print Trobobj
    return Trobobj
    
#def genTargetPose(graspPoseMsg, graspPoseReq):
    # take pose of multiply together to get trasnfrom of robot frame to grasping frame.
    # Outputs transform from grasping frame wrt to base frame to use for arm code.    

def initialize():
    global graspDict
    objectlist = ['../env/cheezit.env.xml',
                    '../env/colorballs.env.xml',
                    '../env/crayon.env.xml',
                    '../env/dentaltreat.env.xml',
                    '../env/eraser.env.xml',
                    '../env/glue.env.xml',
                    '../env/highlighters.env.xml',
                    '../env/huckfinn.env.xml',
                    '../env/indexcards.env.xml',
                    '../env/oreo.env.xml',
                    '../env/outletplugs.env.xml',
                    '../env/pencil.env.xml',
                    '../env/pencilcup.env.xml',
                    '../env/plushduck.env.xml',
                    '../env/plushfrog.env.xml',
                    '../env/rubberduck.env.xml',
                    '../env/safetyglasses.env.xml',
                    '../env/screwdrivers.env.xml',
                    '../env/sparkplug.env.xml',
                    '../env/stickynotes.env.xml',
                    '../env/stirsticks.env.xml',
                    '../env/strawcups.env.xml',
                    '../env/tennisball.env.xml']

    # Program options that can be set
    showGUI = False # If set to true, will show openRave qtcoin GUI
    showOutput = False # If set to true, will show all print statments
    #Debug level, one of (fatal,error,warn,info,debug,verbose,verifyplans)
    #RaveSetDebugLevel(DebugLevel.Verbose)

    # Create dictionary from grasp library
    graspDict = {}
    for item in objectlist:
        try:
            grasplist = []
            #Initialize OpenRave
            env = Environment()
            if showGUI:
                env.SetViewer('qtcoin')
            env.Reset()

            #Load item
            item = os.path.join(os.path.dirname(__file__), item)
            env.Load(item)
            print "loading object XML: "+ item

            # Find bodies
            bodies = [b for b in env.GetBodies() if not b.IsRobot() and linalg.norm(b.ComputeAABB().extents()) < 0.2]
            target = bodies[random.randint(len(bodies))]
            if showOutput:
                print 'choosing target %s'%target

            # Get robot from environment
            time.sleep(0.1)
            robot = env.GetRobots()[0]

            # Set manipulator
            robot.SetActiveManipulator('hand')

            # Load database
            gmodel = openravepy.databases.grasping.GraspingModel(robot,target)
            gmodel.load()
            validgrasps,validindices = gmodel.computeValidGrasps(returnnum=inf, checkik=False)
            print "Number of good grasps found: " + str(len(validgrasps))

            if showGUI:
                raw_input("Press enter to show grasp")

            # Show grasps
            for index in range(0, len(validgrasps)):
                if showOutput:
                    print "Showing grasp #: " + str(index)
                validgrasp=validgrasps[index] # choose grasp based on index number
                if showGUI:
                    gmodel.showgrasp(validgrasp) # show the grasp
                # It says global but the object is at (0,0,0) so this is actually object frame.
                approach = gmodel.getGlobalApproachDir(validgrasp)
                if showOutput:
                    print "Global approach vector: "+str(approach)
                    print "Global grasp transform: "
                transform = gmodel.getGlobalGraspTransform(validgrasp)
                if showOutput:
                    print "Transfrom from library: %i"%index
                    print transform
                approachVector = numpy.array([approach.item(0), approach.item(1), approach.item(2)])
                Tobjgrasp = numpy.matrix([[transform.item(0,0), transform.item(0,1), transform.item(0,2), transform.item(0,3)],
                                        [transform.item(1,0), transform.item(1,1), transform.item(1,2), transform.item(1,3)],
                                        [transform.item(2,0), transform.item(2,1), transform.item(2,2), transform.item(2,3)],
                                        [transform.item(3,0), transform.item(3,1), transform.item(3,2), transform.item(3,3)]])             
                if showOutput:
                    print "Transform from library after conversion to numpy matrix. should be same as above"
                # print Tobjgrasp
                grasplist.append(Tobjgrasp)

        except:     
            print "Failed to load grasp from database for object: " + item
            print "Traceback of error:"
            print traceback.format_exc()
        # Dictionary of grasps for each object
        if showOutput:
            print "Adding grasps for " + item + " to dictionary"
        graspDict[item] = grasplist
        #print graspDict

    print "Finish dictionary generation"
    print len(graspDict)
    RaveDestroy() # destroys all environments and loaded plugins

    return graspDict

def CB_getGrasp(req):
        showOutput = False # If set to true, will show all print statments
        # Initilaztion stuff
        global graspDict
        if showOutput:
            print graspDict
        graspList=[]
        poseList=[]
        Tobjgrasp=[]
        if showOutput:
            print "Requesting valid grasps for %s"%req.item
        if showOutput:
            print "Asking TF for Transform:"
        # try:
        #     (Trobobj_trans,Trobobj_rot) = listener.lookupTransform('/base_link', '/target_object', rospy.Time(0))
        # except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
        #     print "Failed to lookup TF transform"
        Trob_obj = req.Trob_obj
        # print Trobobj_trans
        # print Trobobj_rot

        # Load Scene in OpenRave
        if req.item == 'cheezit_big_original':
            item = '../env/cheezit.env.xml'
        elif req.item == 'kyjen_squeakin_eggs_plush_puppies':
            item = '../env/colorballs.env.xml'
        elif req.item == 'crayola_64_ct':
            item = '../env/crayon.env.xml'
        elif req.item == 'feline_greenies_dental_treats':
            item = '../env/dentaltreat.env.xml'
        elif req.item == 'expo_dry_erase_board_eraser':
            item = '../env/eraser.env.xml'
        elif req.item == 'elmers_washable_no_run_school_glue':
            item = '../env/glue.env.xml'
        elif req.item == 'sharpie_accent_tank_style_highlighters':
            item = '../env/highlighters.env.xml'
        elif req.item == 'mark_twain_huckleberry_finn':
            item = '../env/huckfinn.env.xml'
        elif req.item == 'mead_index_cards':
            item = '../env/indexcards.env.xml'
        elif req.item == 'oreo_mega_stuf':
            item = '../env/oreo.env.xml'
        elif req.item == 'mommys_helper_outlet_plugs':
            item = '../env/outletplugs.env.xml'
        elif req.item == 'paper_mate_12_count_mirado_black_warrior':
            item = '../env/pencil.env.xml'
        elif req.item == 'rolodex_jumbo_pencil_cup':
            item = '../env/pencilcup.env.xml'
        elif req.item == 'kong_duck_dog_toy':
            item = '../env/plushduck.env.xml'
        elif req.item == 'kong_sitting_frog_dog_toy':
            item = '../env/plushfrog.env.xml'
        elif req.item == 'munchkin_white_hot_duck_bath_toy':
            item = '../env/rubberduck.env.xml'
        elif req.item == 'safety_works_safety_glasses':
            item = '../env/safetyglasses.env.xml'
        elif req.item == 'stanley_66_052':
            item = '../env/screwdrivers.env.xml'
        elif req.item == 'champion_copper_plus_spark_plug':
            item = '../env/sparkplug.env.xml'
        elif req.item == 'highland_6539_self_stick_notes':
            item = '../env/stickynotes.env.xml'
        elif req.item == 'genuine_joe_plastic_stir_sticks':
            item = '../env/stirsticks.env.xml'
        elif req.item == 'first_years_take_and_toss_straw_cup':
            item = '../env/strawcups.env.xml'
        elif req.item == 'kong_air_dog_squeakair_tennis_ball':
            item = '../env/tennisball.env.xml'
        else:
            print "could not find scene xml for object: %s"%req.item
        #env.Load(item) # Load requested item
        if showOutput:
            print "loading object XML: "+ item

        try:
            graspList = graspDict[item]
            if showOutput:
                print "Grasp list from dictionary"
                print graspList
            for grasp in graspList:
                Tobjgrasp = grasp
                if showOutput:
                    print Tobjgrasp
                TgraspIK = numpy.matrix([[1, 0, 0, 0],
                            [0, 0, -1, -0.17],
                            [0, 1, 0, 0],
                            [0, 0, 0, 1]])
                Trobobj = quatToMatrix(Trob_obj)
                Trobgrasp = Trobobj * Tobjgrasp
                TrobIK = Trobgrasp * TgraspIK

                #print "Concatenated Transform Trobgrasp:"
                #print Trobgrasp
                if showOutput:
                    print "Converted Trobgrasp into APCGraspPose msg"
                #Trobgrasp_msg = genAPCGraspPose(Trobgrasp,approachVector) # This is a pose msg
                Trobgrasp_msg = genAPCGraspPose(TrobIK, Trobobj)
                if showOutput:
                    print Trobgrasp_msg
                grasp_qw = Trobgrasp_msg.posegrasp.orientation.w
                grasp_x = Trobgrasp_msg.posegrasp.position.x
                grasp_y = Trobgrasp_msg.posegrasp.position.y
                grasp_z = Trobgrasp_msg.posegrasp.position.z
                approach_qw = Trobgrasp_msg.poseapproach.orientation.w
                approach_x = Trobgrasp_msg.poseapproach.position.x
                approach_y = Trobgrasp_msg.poseapproach.position.y
                approach_z = Trobgrasp_msg.poseapproach.position.z
                
                if math.isnan(float(grasp_qw)) == False and math.isnan(float(approach_qw)) == False  and math.isnan(float(grasp_x)) == False and math.isnan(float(approach_x)) == False  and math.isnan(float(grasp_y)) == False and math.isnan(float(approach_y)) == False  and math.isnan(float(grasp_z)) == False and math.isnan(float(approach_z)) == False:
                    poseList.append(Trobgrasp_msg) # append pose to poselist                
                else:
                    print "Nan/inf value detected. Not appending pose to pose list"



                #print poseList                
                # append approach and pose to list  
                #approachList.append = approach
                #poseList.append = Trobgrasp_msg
        except:
            print "Failed : " + item
            print "Traceback of error:"
            print traceback.format_exc()


        # temp = []
        
        if showOutput:
            print "PoseList:"
        grasps = apcGraspArray(
                grasps = poseList
            )
        if showOutput:
            print grasps
        # res.status=True
        # res.Trobgrasp=poseArrayList

        
        return apcGraspDBResponse(status=True,apcGraspArray=grasps)
    
def publisher():
    # Main loop which requests validgrasps from database and returns it
    # Valid grasps should be in object frame I think
    # global graspDict
    rospy.init_node('graspDatabase_service')
    rate = rospy.Rate(10.0)
    graspDict = initialize()
    #print graspDict
    while not rospy.is_shutdown():
        #t.header.stamp = rospy.Time.now()
        #br.sendTransform(t)
        s = rospy.Service('getGrasps', apcGraspDB, CB_getGrasp)
        print "Ready to retrieve grasps from database"
        rate.sleep()
        rospy.spin()

if __name__ == '__main__':
    publisher()
