#!/usr/bin/python

import roslib; roslib.load_manifest('task_controller')
import rospy
import yaml
import os

from task_controller.MotomanController import MotomanController
from task_controller.Scheduler import SimpleScheduler

if __name__ == '__main__':
    rospy.init_node("motoman_apc_controller")

    schedule_file = rospy.get_param("~schedule", "default.yaml")

    if not schedule_file.startswith("/"):
        schedule_file = os.path.join(os.path.dirname(__file__),
                                     "../schedules", schedule_file)
    print schedule_file
    with open(schedule_file) as file:
        schedule = yaml.load(file)
    print schedule

    controller = MotomanController(SimpleScheduler(schedule))
    controller.Start()