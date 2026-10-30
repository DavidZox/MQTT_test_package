from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 啟動 MQTT 接收節點 (Subscriber)
        Node(
            package='fms_mqtt_bridge',
            executable='fms_mqtt_subscriber_node',
            name='fms_mqtt_subscriber',
            output='screen',
            parameters=[{
                'broker_ip': '10.57.54.201',
                'broker_port': 8001,
                'username': 'fms_server',
                'password': 'fms_secure_password'
            }]
        ),
        
        # 啟動 MQTT 發送節點 (Publisher)
        Node(
            package='fms_mqtt_bridge',
            executable='fms_mqtt_publisher_node',
            name='fms_mqtt_publisher',
            output='screen',
            parameters=[{
                'broker_ip': '10.57.54.201',
                'broker_port': 8001,
                'username': 'fms_server',
                'password': 'fms_secure_password',
                'target_robot_id': 'robot_01'
            }]
        )
    ])