#!/usr/bin/env python

import Queue as Q
import tf
import tf2_ros
import rospy
import numpy
from numpy.linalg import inv
import traceback
import geometry_msgs.msg
from math import pi
import sensor_msgs.point_cloud2 as pc2
from std_msgs.msg import Header
from geometry_msgs.msg import PoseStamped
from grasp_planner.msg import apcGraspPose, apcGraspArray
from grasp_planner.srv import apcGraspDB, apcGraspDBResponse
#from apc_util.transformation_helpers import ExtractFromMatrix, BuildMatrix, PoseFromMatrix, PoseToMatrix, InvertMatrix
from transformation_helper import ExtractFromMatrix, BuildMatrix, PoseFromMatrix, PoseToMatrix, InvertMatrix

class Grasping:

    def __init__(self):
        self.description = "Online grasp planning code"
        self.tf = tf.TransformListener(True, rospy.Duration(10.0))
        self.br = tf2_ros.TransformBroadcaster()
        self.rate = rospy.Rate(60.0)
        self.tfList = []
        self.thetaList = numpy.linspace(-pi/4, pi/4, num=51)
        # self.thetaList = numpy.linspace(-pi/2, pi/2, num=51)
        # self.thetaList = numpy.linspace(-pi, pi, num=51)

        # Variables that can be set
        self.showOutput = False  # Enable to show print statements
        self.padding = 0.015  # Extra padding between object and gripper is 1 cm.
        self.fingerlength = 0.115  # palm to finger tip offset is 11.5 cm
        self.gripperwidth = 0.155 - self.padding  # gripper width is 15.5 cm
        self.z_lowerboundoffset = 0.065  # Palm center to bottom of hand is 6.5 cm
        self.approachpose_offset = -0.3  # Set aproach pose to be 30cm back from the front of the bin

        if self.showOutput:
            print "theta range list"
            print self.thetaList
            
        rospy.sleep(rospy.Duration(1.0))  # Wait for network timing to load TFs

    def get_tf(self, parent, child):
        if self.showOutput:
            print "Looking up TF transform from %s to %s" % (parent, child)
        try:
            (trans, quat) = self.tf.lookupTransform(parent, child, rospy.Time(0))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
            print "Failed to lookup TF transform from source:%s to target:%s" % (parent, child)
        trans = numpy.asarray(trans)
        quat = numpy.asarray(quat)
        translation = [trans.item(0), trans.item(1), trans.item(2)]
        quaternion = [quat.item(0), quat.item(1), quat.item(2), quat.item(3)]
        transform = BuildMatrix(translation, quaternion)
        return transform

    def broadcast_single_tf(self, t):
        rate = rospy.Rate(1000)
        for time in range(0, 10):
            t.header.stamp = rospy.Time.now()
            self.br.sendTransform(t)
            rate.sleep()

    def generate_tf(self, parent, child, transform):
        t = geometry_msgs.msg.TransformStamped()
        t.header.stamp = rospy.Time.now()
        t.header.frame_id = parent
        t.child_frame_id = child
        [trans, quat] = ExtractFromMatrix(transform)
        t.transform.translation.x = trans[0]
        t.transform.translation.y = trans[1]
        t.transform.translation.z = trans[2]
        t.transform.rotation.x = quat[0]
        t.transform.rotation.y = quat[1]
        t.transform.rotation.z = quat[2]
        t.transform.rotation.w = quat[3]
        self.broadcast_single_tf(t)

    def construct_4Dmatrix(self, trans, rot):
        # print trans, rot
        transform = numpy.zeros([4, 4])
        transform[0:3, 0:3] = rot
        transform[0:3, 3] = trans
        transform[3, 3] = 1
        return transform

    def generate_rotation_matrix(self, theta):
        # Generate matrix to rotation about the z-axis of shelf frame to get bunch of new transforms to use for projection
        transform = numpy.array([[numpy.cos(theta), numpy.sin(theta), 0, 0],
                                [-numpy.sin(theta), numpy.cos(theta), 0, 0],
                                [0, 0, 1, 0],
                                [0, 0, 0, 1]])
        return transform

    def get_shelf_bounds(self, req):
        if req.bin == 'A':
            size = [-0.43, -.01,  0.15764, 0.41,    1.55794, 1.77212]
        elif req.bin == 'B':
            size = [-0.43, -.01, -0.14331, 0.14331, 1.55794, 1.77212]
        elif req.bin == 'C':
            size = [-0.43, -.01, -0.41,   -0.15764, 1.55794, 1.77212]
        elif req.bin == 'D':
            size = [-0.43, -.01,  0.15764, 0.41,    1.32733, 1.50775]
        elif req.bin == 'E':
            size = [-0.43, -.01, -0.14331, 0.14331, 1.32733, 1.50775]
        elif req.bin == 'F':
            size = [-0.43, -.01, -0.41,   -0.15764, 1.32733, 1.50775]
        elif req.bin == 'G':
            size = [-0.43, -.01,  0.15764, 0.41,    1.11053, 1.29092]
        elif req.bin == 'H':
            size = [-0.43, -.01, -0.14331, 0.14331, 1.11053, 1.29092]
        elif req.bin == 'I':
            size = [-0.43, -.01,  0.41,   -0.15764, 1.11053, 1.29092]
        elif req.bin == 'J':
            size = [-0.43, -.01,  0.15764, 0.41,    0.83651, 1.05069]
        elif req.bin == 'K':
            size = [-0.43, -.01, -0.14331, 0.14331, 0.83651, 1.05069]
        elif req.bin == 'L':
            size = [-0.43, -.01,  0.41,   -0.15764, 0.83651, 1.05069]
        else:
            print "could not find bin size: %s" % req.item
        return numpy.array(size)

    def get_object_extents(self, req):
        if req.item == 'cheezit_big_original':
            item = '../env/cheezit.env.xml'
            size = [0.062, 0.16, 0.226]
        elif req.item == 'kyjen_squeakin_eggs_plush_puppies':
            item = '../env/colorballs.env.xml'
            size = [0.06, 0.121, 0.18]
        elif req.item == 'crayola_64_ct':
            item = '../env/crayon.env.xml'
            size = [0.037, 0.125, 0.145]
        elif req.item == 'feline_greenies_dental_treats':
            item = '../env/dentaltreat.env.xml'
            size = [0.04, 0.175, 0.21]
        elif req.item == 'expo_dry_erase_board_eraser':
            item = '../env/eraser.env.xml'
            size = [0.035, 0.055, 0.13]
        elif req.item == 'elmers_washable_no_run_school_glue':
            item = '../env/glue.env.xml'
            size = [0.025, 0.06, 0.145]
        elif req.item == 'sharpie_accent_tank_style_highlighters':ros
            item = '../env/highlighters.env.xml'
            size = [0.023, 0.116, 0.125]
        elif req.item == 'mark_twain_huckleberry_finn':
            item = '../env/huckfinn.env.xml'
            size = [0.012, 0.132, 0.21]
        elif req.item == 'mead_index_cards':
            item = '../env/indexcards.env.xml'
            size = [0.02, 0.076, 0.127]
        elif req.item == 'oreo_mega_stuf':
            item = '../env/oreo.env.xml'
            size = [0.06, 0.155, 0.2]
        elif req.item == 'mommys_helper_outlet_plugs':
            item = '../env/outletplugs.env.xml'
            size = [0.055, 0.09, 0.19]
        elif req.item == 'paper_mate_12_count_mirado_black_warrior':
            item = '../env/pencil.env.xml'
            size = [0.016, 0.05, 0.195]
        elif req.item == 'rolodex_jumbo_pencil_cup':
            item = '../env/pencilcup.env.xml'
            size = [0.107, 0.14, 0.107]
        elif req.item == 'kong_duck_dog_toy':
            item = '../env/plushduck.env.xml'
            size = [0.05, 0.09, 0.18]
        elif req.item == 'kong_sitting_frog_dog_toy':
            item = '../env/plushfrog.env.xml'
            size = [0.045, 0.09, 0.21]
        elif req.item == 'munchkin_white_hot_duck_bath_toy':
            item = '../env/rubberduck.env.xml'
            size = [0.065, 0.095, 0.13]
        elif req.item == 'safety_works_safety_glasses':
            item = '../env/safetyglasses.env.xml'
            size = [0.05, 0.07, 0.2]
        elif req.item == 'stanley_66_052':
            item = '../env/screwdrivers.env.xml'
            size = [0.02, 0.1, 0.195]
        elif req.item == 'champion_copper_plus_spark_plug':
            item = '../env/sparkplug.env.xml'
            size = [0.02, 0.025, 0.095]
        elif req.item == 'highland_6539_self_stick_notes':
            item = '../env/stickynotes.env.xml'
            size = [0.05, 0.04, 0.115]
        elif req.item == 'genuine_joe_plastic_stir_sticks':
            item = '../env/stirsticks.env.xml'
            size = [0.095, 0.107, 0.145]
        elif req.item == 'first_years_take_and_toss_straw_cup':
            item = '../env/strawcups.env.xml'
            size = [0.08, 0.09, 0.17]
        elif req.item == 'kong_air_dog_squeakair_tennis_ball':
            item = '../env/tennisball.env.xml'
            size = [0.07, 0.108, 0.19]
        else:
            print "could not find scene xml for object: %s" % req.item

        return numpy.array(size)

    def generate_apc_grasp_poses(self, projectionList, approachList):
        grasps = []
        for i in range(len(approachList)):
            projection = projectionList[i]
            approach = approachList[i]
            grasp = apcGraspPose()
            grasp.pregrasp.position = projection.position
            grasp.pregrasp.orientation = projection.orientation
            grasp.approach.position = approach.position
            grasp.approach.orientation = approach.orientation
            grasps.append(grasp)
        return grasps

    def get_obb_points(self, size):
        x = size[0]
        y = size[1]
        z = size[2]

        point1 = (x/2, y/2, z/2)
        point2 = (x/2, -y/2, z/2)
        point3 = (-x/2, y/2, z/2)
        point4 = (-x/2, -y/2, z/2)
        point5 = (x/2, y/2, -z/2)
        point6 = (x/2, -y/2, -z/2)
        point7 = (-x/2, y/2, -z/2)
        point8 = (-x/2, -y/2, -z/2)
        points = numpy.array([point1, point2, point3, point4, point5, point6, point7, point8])
        return points

    def compute_width(self, min_y, max_y):
        return abs(max_y-min_y)

    def compute_depth(self, min_x, max_x, object_xmid):
        edge_offset = abs(object_xmid - min_x) # Distance from ymid of object to edge of object
        obj_depth = abs(max_x-min_x)
        offset = numpy.true_divide(obj_depth, 2)
        if offset > self.fingerlength:
            offset = 0.06
        return (-edge_offset - self.fingerlength + offset) # the palm is located at min_x so move out till lenght of finger to place lenght of finger at min_x. Then move in 1/4 of the total depth of object

    def compute_height(self, bin_min_z):
        return bin_min_z + self.z_lowerboundoffset - 0.045  # minus 5cm height as magic number adjustment. Should have to do this if binmin z is correct

    def compute_midpt(self, points):
        avg = numpy.array([0, 0, 0])
        for point in points:
            avg = numpy.array([avg[0]+point[0], avg[1]+point[1], avg[2]+point[2]])
        return avg/len(points)

    def check_width(self, width):
        if width <= self.gripperwidth:
            isSmaller = True
        else:
            isSmaller = False
        return isSmaller

    def compute_approach_offset(self, grasp_depth, bin_min_x, min_x, max_x, theta):
        item_depth = abs(max_x - min_x)
        offset = numpy.cos(abs(theta)) * (abs(grasp_depth - bin_min_x) + self.fingerlength + item_depth + self.approachpose_offset)
        # offset = bin_min_x - self.approachpose_offset
        return -offset

    def compute_score(self, width, rotation):
        fscore = numpy.true_divide(width, self.gripperwidth)[0]
        gscore = abs(rotation)
        weight = 0.6
        score = (1-weight)*fscore + weight*gscore
        # print "%s = 0.5*%s + 0.5*%s" % (score, fscore, gscore)
        return score

    def compute_minmax(self, pointList):
        x = []
        y = []
        z = []
        for point in pointList:
            x.append(point[0])
            y.append(point[1])
            z.append(point[2])
        min_x = min(x)
        max_x = max(x)
        min_y = min(y)
        max_y = max(y)
        min_z = min(z)
        max_z = max(z)
        min_max = numpy.array([min_x, max_x, min_y, max_y, min_z, max_z])
        return min_max

    def checkquaternion(self, transform, name):
        approach = geometry_msgs.msg.Pose()
        [trans, quat] = ExtractFromMatrix(transform)
        approach.position.x = trans[0]
        approach.position.y = trans[1]
        approach.position.z = trans[2]
        approach.orientation.x = quat[0]
        approach.orientation.y = quat[1]
        approach.orientation.z = quat[2]
        approach.orientation.w = quat[3]
        unit_quat = str((approach.orientation.x)**2 + (approach.orientation.y)**2 + (approach.orientation.z)**2 + (approach.orientation.w)**2)
        if unit_quat != 1:
            print name + " is unit quaternion: " + str(unit_quat)

    def get_grasp_cb(self, req):

        q_proj_msg = Q.PriorityQueue()
        q_approach_msg = Q.PriorityQueue()
        approachList = []
        projectionList = []
        countbad = 0

        print "************************************************** Request start **************************************************"
        print "Requesting valid grasps for %s" % req.item
        print "Requesting object in bin %s" % req.bin

        size = self.get_object_extents(req)
        binbounds = self.get_shelf_bounds(req)
        bin_min_x, bin_max_x, bin_min_y, bin_max_y, bin_min_z, bin_max_z = binbounds
        print "bin min z: " + str(bin_min_z)

        # Generate TFs to project onto
        for theta in self.thetaList:
            Tbaseshelf = self.get_tf('/base_link', '/shelf')

            select = False  # set to true to use the local boudindbox points. set to else for point cloud stuff
            if select:
                Tshelfobj = self.get_tf('/shelf', '/object')
                pointcloud = self.get_obb_points(size)

            else:
                # for ptcloud
                Tbaseobj = PoseToMatrix(req.object_pose)  # same Trob_obj request from offline planner
                Tshelfobj = numpy.dot(inv(Tbaseshelf), Tbaseobj)
                pointcloud = list(pc2.read_points(req.object_points, skip_nans=True,
                                  field_names=("x", "y", "z")))

            if self.showOutput:
                print "********************************************** Start loop ********************************************"
                print "OBBPoints: ", pointcloud
                print "Transform from base to shelf: ", Tbaseshelf
                print "Transform from shelf to obj: ", Tshelfobj

            Tshelfproj = self.generate_rotation_matrix(theta)
            Tbaseproj = numpy.dot(Tbaseshelf, Tshelfproj)
            if theta == 0:
                print "projecting to shelf frame"

            if self.showOutput:
                print "Transform from shelf to proj: ", Tshelfproj, type(Tshelfproj)

            # Extract Translation component of Tshelfobj
            Trans_shelfobj = Tshelfobj[0:3, 3]
            Rot_shelfproj = Tshelfproj[0:3, 0:3]
            Tshelfproj_new = self.construct_4Dmatrix(Trans_shelfobj, Rot_shelfproj)
            if self.showOutput:
                print Tshelfproj_new

            # Transform form projection to object
            Tprojshelf = inv(Tshelfproj_new)
            Tprojobj = numpy.dot(Tprojshelf, Tshelfobj)

            # Loop through object points and transform them to be wrt to the target projection frame 
            points = []
            for OBBPoint in pointcloud:
                oldpt = numpy.array([[OBBPoint[0]], [OBBPoint[1]], [OBBPoint[2]], [1]])
                projected_OBBPoint = numpy.dot(Tprojshelf, oldpt)
                points.append(projected_OBBPoint)
            if self.showOutput:
                print "List of transformed object points after projection to target projection frame"
                print points

            # Get min max points. Pass in transformed OBBPoints list to get min max for target frame. Compute width of projection shadow. Width is the y axis because shelf frame is set that way with y axis as width. Check if width of shadow projection can fit inside gripper width
            min_max = self.compute_minmax(points)
            min_x, max_x, min_y, max_y, min_z, max_z = min_max
            width = self.compute_width(min_y, max_y)
            
            if self.showOutput:
                print "Min-max values [minx,maxx,miny,maxy,minz,maxz]: ", min_x, max_x, min_y, max_y, min_z, max_z
                print "projection width: " + str(width)
                print "min_y: " + str(min_y)
                print "max_y: " + str(max_y)
            
            # Get hand pose
            isSmaller = self.check_width(width)
            if isSmaller:
                object_xmid = Tshelfproj_new[0, 3]
                score = self.compute_score(width, theta)
                grasp_depth = self.compute_depth(min_x, max_x, object_xmid)  # set how far hand should go past front edge of object
                height = self.compute_height(bin_min_z)  # select the height so bottom of object and also hand won't collide wit shelf lip. may need to take into acount the max_z and objects height to see if object will hit top of shelf.
                approach_offset = self.compute_approach_offset(grasp_depth, bin_min_x, min_x, max_x, theta)
                if self.showOutput:
                    print "score: "+str(score)
                    print "x grasp depth value "+str(grasp_depth)
                    print "x height value "+str(height)

                # Update projection TF with new y value set to be middle of the projection wrt to the projection frame
                Trans_shelfproj = numpy.array([Tshelfproj_new[0, 3], Tshelfproj_new[1, 3], Tshelfproj_new[2, 3]])
                Rot_shelfproj = Tshelfproj_new[0:3, 0:3]
                Tshelfproj_update = self.construct_4Dmatrix(Trans_shelfproj, Rot_shelfproj)

                # Transform from projection to pregrasp pose
                Trans_projpregrasp = numpy.array([grasp_depth, 0, 0])
                Rot_projpregrasp = numpy.eye(3, 3)
                Tprojpregrasp = self.construct_4Dmatrix(Trans_projpregrasp, Rot_projpregrasp)
                Tshelfpregrasp = numpy.dot(Tshelfproj_update, Tprojpregrasp)

                # Transform from pregrasp to approach pose
                Trans_projapproach = numpy.array([approach_offset, 0, 0])
                # Trans_projapproach = numpy.array([self.approachpose_offset, 0, 0])
                Rot_projapproach = numpy.eye(3, 3)
                Tprojapproach = self.construct_4Dmatrix(Trans_projapproach, Rot_projapproach)

                # Generate and display TF
                self.generate_tf('/shelf', '/pregrasp', Tshelfpregrasp)
                self.generate_tf('/pregrasp', '/approach', Tprojapproach)

                # camera -15 deg offset about z-axis
                camtheta = 0.261799
                Tcamera = numpy.array([[1, 0, 0, 0],
                                       [0, numpy.cos(camtheta), -numpy.sin(camtheta), 0],
                                       [0, numpy.sin(camtheta), numpy.cos(camtheta), 0],
                                       [0, 0, 0, 1]])

                # Transform to orient hand to use x as approach direction
                Tcamgrasp = numpy.array([[0, 0, -1, -0.17],
                                        [-1, 0, 0, 0],
                                        [0, 1, 0, 0],
                                        [0, 0, 0, 1]])
                TgraspIK = numpy.dot(Tcamera, Tcamgrasp)

                # Transform from arm solved from IK to handpose for pregrasp
                Tbasepregrasp = numpy.dot(Tbaseshelf, Tshelfpregrasp)
                TbaseIK_pregrasp = numpy.dot(Tbasepregrasp, TgraspIK)

                # Transform from arm solved from IK to handpose for approach
                Tshelfapproach = numpy.dot(Tshelfpregrasp, Tprojapproach)
                Tbaseapproach = numpy.dot(Tbaseshelf, Tshelfapproach)
                TbaseIK_approach = numpy.dot(Tbaseapproach, TgraspIK)

                # Construct msg. Then appened to queue with score as the priority in queue. This will put lowest score msg first in list.
                proj_msg = PoseFromMatrix(TbaseIK_pregrasp)
                proj_msg.position.z = height
                approach_msg = PoseFromMatrix(TbaseIK_approach)
                approach_msg.position.z = height
                # approach_msg.position.x = bin_min_x
                q_proj_msg.put((score, proj_msg))
                q_approach_msg.put((score, approach_msg))

                if self.showOutput:
                    print "score is %f. Good approach direction. Gripper is wide enough" % score
            else:
                score = self.compute_score(width, theta)
                if self.showOutput:
                    print "score is %f. Bad approach direction. Gripper not wide enough" % score
                countbad += 1

        print "number of bad approach directions: " + str(countbad)
        
        while not q_proj_msg.empty():
            projectionList.append(q_proj_msg.get()[1])
        while not q_approach_msg.empty():
            approachList.append(q_approach_msg.get()[1])

        # Construct APC grasp message to return
        graspList = self.generate_apc_grasp_poses(projectionList, approachList)
        grasps = apcGraspArray(
            grasps=graspList
        )
        print "************************************************** end loop **************************************************"
        print "************************************************** Request end ***********************************************"
        return apcGraspDBResponse(status=True, grasps=grasps)


def publisher():
    rospy.init_node('online_grasp_server')

    grasp = Grasping()
    while not rospy.is_shutdown():
        try:
            rospy.Service('getGrasps_online_server', apcGraspDB, grasp.get_grasp_cb)
            print "Online grasp planner ready"
            rospy.spin()
        except:
            print traceback.format_exc()

if __name__ == '__main__':
    publisher()
