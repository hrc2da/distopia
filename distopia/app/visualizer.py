# read a file and parse the designs
# pass the designs to distopia via fiducial_layout (json dumps'ed dict)

import json
import roslibpy
import time

filename = "/home/dev/research/distopia/logs/logs/-1.0,0.0,0.0,0.0,0.0,0.0,0.0_log"

ros = roslibpy.Ros(host="localhost", port=9090)
ros.run()
publisher = roslibpy.Topic(ros, '/fiducial_layout', 'std_msgs/String')


with open(filename) as logfile:
    i = 0
    for row in logfile:
        i += 1
        if i % 20 == 0:
            design = eval(row)[3]
            publisher.publish(roslibpy.Message({'data':json.dumps(design)}))
            print("publishing {}".format(i))
        time.sleep(0.01)

