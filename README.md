這是一份為您整理的 **ROS 2 與 MQTT (Mosquitto) 容器化 FMS 橋接系統** 從部署到實際測試的完整系統性說明文件。內容涵蓋架構設計、環境與網路配置、防火牆調校以及雙向通訊驗證的完整實務指南。

# 🤖 ROS 2 與 MQTT FMS 橋接系統建置與測試技術手冊

---

## 一、 系統架構與設計理念

本系統旨在建立一個高可移植、支援從「單機容器測試」無縫遷移至「獨立生產主機」的車隊管理系統（FMS）通訊橋接架構。

* **通訊核心**：採用 `MQTT` 作為跨網路層的輕量化傳輸協議，底層透過非同步 Python 庫 (`aiomqtt`) 確保 ROS 2 與 MQTT 事件迴圈流暢執行。
* **部署策略**：
  * **Broker 端**：獨立運行於 Mosquitto 容器中，透過 `0.0.0.0` 監聽所有網路介面，適應未來獨立主機的擴展需求。
  * **節點端**：ROS 2 橋接器（包含調度端與機器人端）透過環境變數（`.env`）動態綁定目標 Broker IP 與連接埠，確保未來更換伺服器時**完全無需修改程式碼**。

---

## 二、 部署步驟與網路架構設定

### 1. MQTT Broker (Mosquitto) 設定
確保 Mosquitto 容器的設定檔（`mosquitto.conf`）正確開啟對外監聽，以支援多介面與跨網段連線：

```conf
listener 8001 0.0.0.0
listener 8883 0.0.0.0
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl
```

### 2. 環境變數設定 (`.env`)
在開發與測試階段，容器與 Broker 位於同一台宿主機但獨立運作時，採用 Docker 預設的網關 IP 進行內部互聯：

```env
MQTT_BROKER_IP=172.17.0.1
MQTT_BROKER_PORT=8001
MQTT_USERNAME=fms_server
MQTT_PASSWORD=fms_server123
```

> 💡 **未來遷移指南**：當 Broker 獨立部署至不同實體伺服器（例如 `10.57.54.250`）時，僅需將此處的 `MQTT_BROKER_IP` 替換為新主機的真實 IP，並重啟容器即可完成遷移。

---

## 三、 網路與防火牆（UFW）除錯關鍵

在早期測試中，常因容器存取宿主機 Port 遭到拒絕而引發 `timed out` 逾時錯誤。透過系統日誌交叉比對，確認了解決此問題的關鍵步驟：

1. **UFW 防火牆規則放行**：
   Linux 主機的 UFW 預設阻擋所有外部進來（`deny incoming`）的連線。必須針對 Docker 容器內部的橋接網段進行放行，允許其存取 MQTT 的 `8001` 埠：
   ```bash
   sudo ufw allow from 172.16.0.0/12 to any port 8001 proto tcp
   ```
2. **通訊狀態驗證**：
   當規則生效後，Mosquitto 日誌會顯示來自 Docker 內網（如 `172.21.0.1`）的成功連線（`New client connected`），且 MQTT 內建的心跳機制（`PINGREQ` / `PINGRESP`）會開始穩定交替，代表雙方通道完全打通。

---

## 四、 雙向通訊驗證與實測指令

系統上線後，可透過以下 ROS 2 指令與對應的節點驗證雙向資料流：

### 1. 調度端發布測試（FMS 發送指令給機器人）
* **對應程式碼**：`fms_mqtt_publisher_node.py`（訂閱 `/fms/command_to_send`，轉發至 `fms/robots/robot_01/command`）
* **測試指令**：
  ```bash
  ros2 topic pub --once /fms/command_to_send std_msgs/msg/String "{data: 'Hello FMS MQTT'}"
  ```

### 2. 機器人端發布與接收測試（AMR 回報狀態與接收控制）
* **狀態發布端**：`robot_mqtt_publisher_node.py`（訂閱 `/amr/status`，轉發至 `fms/robots/robot_01/status`）
* **指令接收端**：`robot_mqtt_subscriber_node.py`（訂閱 `fms/robots/robot_01/command`，轉發至 `/amr/command`）