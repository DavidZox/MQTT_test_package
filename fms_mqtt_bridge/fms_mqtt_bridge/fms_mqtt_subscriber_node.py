#!/usr/bin/env python3
import asyncio
import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import aiomqtt

class FmsMqttSubscriberNode(Node):
    def __init__(self):
        super().__init__('fms_mqtt_subscriber_node')
        
        # 宣告參數（預設值改為讀取環境變數，若 Launch 有傳參數則會被 Launch 覆蓋）
        self.declare_parameter('broker_ip', os.getenv('MQTT_BROKER_IP', '10.57.54.201'))
        self.declare_parameter('broker_port', int(os.getenv('MQTT_BROKER_PORT', 8001)))
        self.declare_parameter('username', os.getenv('MQTT_USERNAME', 'fms_server'))
        self.declare_parameter('password', os.getenv('MQTT_PASSWORD', 'fms_server123'))
        
        self.broker_ip = self.get_parameter('broker_ip').value
        self.broker_port = self.get_parameter('broker_port').value
        self.username = self.get_parameter('username').value
        self.password = self.get_parameter('password').value
        
        self.ros_publishers = {}
        self.get_logger().info(f"FMS MQTT Subscriber Node initialized -> Target Broker: {self.broker_ip}:{self.broker_port} (Plaintext)")
        
        self.loop = asyncio.get_event_loop()
        self.mqtt_task = self.loop.create_task(self.mqtt_subscriber_worker())

    def get_ros_publisher(self, robot_id: str):
        if robot_id not in self.ros_publishers:
            topic_name = f"/fms/{robot_id}/status_received"
            self.ros_publishers[robot_id] = self.create_publisher(String, topic_name, 10)
            self.get_logger().info(f"Created ROS 2 publisher for topic: {topic_name}")
        return self.ros_publishers[robot_id]

    async def mqtt_subscriber_worker(self):
        subscribe_topic = "fms/robots/+/status"
        
        while rclpy.ok():
            try:
                self.get_logger().info(f"Connecting to MQTT Broker as '{self.username}' for receiving...")
                async with aiomqtt.Client(
                    hostname=self.broker_ip,
                    port=self.broker_port,
                    username=self.username,
                    password=self.password,
                ) as client:
                    self.get_logger().info(f"Connected! Subscribing to [{subscribe_topic}]...")
                    await client.subscribe(subscribe_topic)
                    
                    async for message in client.messages:
                        try:
                            topic_parts = str(message.topic).split('/')
                            if len(topic_parts) >= 3:
                                robot_id = topic_parts[2]
                                payload = message.payload.decode('utf-8')
                                
                                self.get_logger().debug(f"Received from [{message.topic}]: {payload}")
                                
                                pub = self.get_ros_publisher(robot_id)
                                ros_msg = String()
                                ros_msg.data = payload
                                pub.publish(ros_msg)
                        except Exception as inner_e:
                            self.get_logger().error(f"Error processing incoming message: {inner_e}")
                            
            except aiomqtt.MqttError as error:
                self.get_logger().warn(f"MQTT connection lost: {error}. Retrying in 3 seconds...")
                await asyncio.sleep(3)
            except Exception as e:
                self.get_logger().error(f"Unexpected error: {e}")
                await asyncio.sleep(3)

def main(args=None):
    rclpy.init(args=args)
    node = FmsMqttSubscriberNode()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)
            node.loop.run_until_complete(asyncio.sleep(0.001))
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()