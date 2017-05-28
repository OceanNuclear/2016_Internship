//This is the header portion of the file from demo_src_client.cpp, with comments from Ocean linking the location of each  
#include <ros/ros.h>
//^still haven't found this one

#include <dji_sdk/dji_drone.h>

#include <actionlib/client/simple_action_client.h>
#include <actionlib/client/terminal_state.h>
/* found here:
https://github.com/dji-sdk/Onboard-SDK-ROS/blob/3.1/dji_sdk/include/dji_sdk/dji_sdk_node.h
*/

using namespace DJI::onboardSDK;
// https://github.com/dji-sdk/Onboard-SDK-ROS/blob/3.1/dji_sdk_doc/doxygen/html/namespaceDJI.html

/* Structure pic1:
https://raw.githubusercontent.com/dji-sdk/Onboard-SDK-ROS/3.1/dji_sdk_doc/structure.jpg
pic2:
https://raw.githubusercontent.com/dji-sdk/Onboard-SDK-ROS/3.1/dji_sdk_lib/docs/img/LibV3_0Structure.jpg
pic3:
https://github.com/dji-sdk/Onboard-SDK-ROS/blob/3.1/dji_sdk_lib/docs/img/LibV2_3Structure.jpg
*/

/*
https://github.com/dji-sdk/Onboard-SDK-ROS/tree/3.1/dji_sdk_doc/doxygen/html
*/

//where velocity is seen
/*
https://github.com/dji-sdk/Onboard-SDK-ROS/blob/3.1/dji_sdk_lib/include/dji_sdk_lib/DJI_Flight.h
*/

/*
https://github.com/dji-sdk/Onboard-SDK-ROS/blob/3.1/dji_sdk_lib/src/DJI_Flight.cpp
*/

//where vector3dData and SpaceVector are declared
/*
https://github.com/dji-sdk/Onboard-SDK-ROS/blob/3.1/dji_sdk_lib/include/dji_sdk_lib/DJICommonType.h*/
