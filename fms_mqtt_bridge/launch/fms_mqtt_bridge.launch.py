import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 從環境變數中讀取，若無則給予預設測試值
    broker_ip = os.getenv('MQTT_BROKER_IP', '10.57.54.201')
    broker_port = int(os.getenv('MQTT_BROKER_PORT', 8001))
    username = os.getenv('MQTT_USERNAME', 'fms_server')
    password = os.getenv('MQTT_PASSWORD', 'fms_server123')

    return LaunchDescription([
        # 啟動 MQTT 接收節點 (Subscriber)
        Node(
            package='fms_mqtt_bridge',
            executable='fms_mqtt_subscriber_node',
            name='fms_mqtt_subscriber',
            output='screen',
            parameters=[{
                'broker_ip': broker_ip,
                'broker_port': broker_port,
                'username': username,
                'password': password
            }]
        ),
        
        # 啟動 MQTT 發送節點 (Publisher)
        Node(
            package='fms_mqtt_bridge',
            executable='fms_mqtt_publisher_node',
            name='fms_mqtt_publisher',
            output='screen',
            parameters=[{
                'broker_ip': broker_ip,
                'broker_port': broker_port,
                'username': username,
                'password': password,
                'target_robot_id': 'robot_01'
            }]
        )
    ])