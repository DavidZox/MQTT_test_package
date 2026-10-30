#!/usr/bin/env python3
import asyncio
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import aiomqtt

class FmsMqttPublisherNode(Node):
    def __init__(self):
        super().__init__('fms_mqtt_publisher_node')
        
        # 參數設定（測試階段使用明文連接埠 8001）
        self.declare_parameter('broker_ip', '10.57.54.201')
        self.declare_parameter('broker_port', 8001)
        self.declare_parameter('username', 'fms_server')
        self.declare_parameter('password', 'fms_secure_password')
        self.declare_parameter('target_robot_id', 'robot_01')
        
        self.broker_ip = self.get_parameter('broker_ip').value
        self.broker_port = self.get_parameter('broker_port').value
        self.username = self.get_parameter('username').value
        self.password = self.get_parameter('password').value
        self.target_robot_id = self.get_parameter('target_robot_id').value
        
        self.subscription = self.create_subscription(
            String,
            '/fms/command_to_send',
            self.ros_listener_callback,
            10
        )
        
        self.get_logger().info(f"FMS MQTT Publisher Node initialized -> Target Broker: {self.broker_ip}:{self.broker_port} (Plaintext)")
        
        self.latest_msg_payload = None
        self.loop = asyncio.get_event_loop()
        self.mqtt_task = self.loop.create_task(self.mqtt_publisher_worker())

    def ros_listener_callback(self, msg):
        self.latest_msg_payload = msg.data

    async def mqtt_publisher_worker(self):
        topic = f"fms/robots/{self.target_robot_id}/command"
        
        while rclpy.ok():
            try:
                self.get_logger().info(f"Connecting to MQTT Broker as '{self.username}' for publishing...")
                async with aiomqtt.Client(
                    hostname=self.broker_ip,
                    port=self.broker_port,
                    username=self.username,
                    password=self.password,
                ) as client:
                    self.get_logger().info("Connected to MQTT Broker for publishing!")
                    
                    while rclpy.ok():
                        if self.latest_msg_payload is not None:
                            payload = self.latest_msg_payload
                            self.latest_msg_payload = None
                            
                            await client.publish(topic, payload=payload, qos=0)
                            self.get_logger().info(f"Published command to [{topic}]: {payload}")
                            
                        await asyncio.sleep(0.05)
                        
            except aiomqtt.MqttError as error:
                self.get_logger().warn(f"MQTT connection lost: {error}. Retrying in 3 seconds...")
                await asyncio.sleep(3)
            except Exception as e:
                self.get_logger().error(f"Unexpected error: {e}")
                await asyncio.sleep(3)

def main(args=None):
    rclpy.init(args=args)
    node = FmsMqttPublisherNode()
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