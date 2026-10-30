# 1. 使用 ROS 2 Humble 官方開發基底映像檔（包含完整的 rclpy 與 ROS 2 基礎環境）
FROM ros:jazzy-ros-base

# 設定容器內部工作目錄
WORKDIR /ros2_ws/src/fms_mqtt_bridge

# 2. 安裝 Python 環境與系統依賴
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /lib/apt/lists/*

# 3. 安裝 aiomqtt 與必要套件
RUN pip3 install --no-cache-dir aiomqtt setuptools

# 4. 將當前專案原始碼複製進容器內部
COPY . .

# 5. 切換至工作空間根目錄進行 colcon build 編譯
WORKDIR /ros2_ws
RUN . /opt/ros/jazzy/setup.sh && colcon build --packages-select fms_mqtt_bridge

# 6. 設定容器啟動時自動載入 ROS 2 與專案環境設定檔
SHELL ["/bin/bash", "-c"]

# 7. 預設啟動指令：載入環境並執行 ros2 launch
CMD ["/bin/bash", "-c", "source /opt/ros/jazzy/setup.sh && source /ros2_ws/install/setup.bash && ros2 launch fms_mqtt_bridge fms_mqtt_bridge.launch.py"]