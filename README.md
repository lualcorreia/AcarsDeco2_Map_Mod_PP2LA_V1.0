# 📡 AcarsDeco2 Map Mod PP2LA

This project is a customized modification of **[AcarsDeco2](https://xdeco.org/acarsdeco2)**, designed to integrate **ACARS decoding** with a **real-time interactive map** and **message management**.  
It has been developed to provide a modern interface, extra controls, and improved usability for radio listeners, aviation enthusiasts, and researchers.

---

## 🔄 Main changes from the original AcarsDeco2

1. **Integrated Web Server**
   - Built using **Flask (Python)** to read and serve AcarsDeco2 logs in real time.
   - Provides a JSON API for the new web interface.

2. **Modern Web Interface (HTML + JavaScript + Leaflet)**
   - Replaces the default AcarsDeco2 page with a **fully redesigned, responsive interface**.
   - Uses the **Leaflet** library to display aircraft and flight paths.

3. **Flight Trails**
   - Instead of plotting each position separately, the system keeps a **line trail** for each aircraft.
   - Only the **latest position** is marked with a map marker.

4. **Sidebar Statistics**
   - Displays **total detected aircraft**.
   - Displays **total received messages**.
   - Shows **connection status** and **last update time**.

5. **Message System with History**
   - Dedicated tab to view all received messages for each aircraft.
   - **Optional auto-scroll** to keep the newest message at the top.
   - Buttons to **clear messages** and **clear locations** directly from the interface.

6. **Enhanced Coordinate Extraction**
   - Supports **multiple ACARS coordinate formats**:
     - Old format: `DDMM.mm[NS],DDDMM.mm[EW]`
     - New format: `DDMMSS[NS]DDDMMSS[EW]`
     - POS format: `POS[NS]xxxxx[EW]xxxxxx`
   - Automatically converts to **decimal degrees** (latitude/longitude).

7. **Improved Startup Script (AD2.bat)**
   - Windows `.bat` file launches:
     1. AcarsDeco2 with pre-configured parameters.
     2. `acars_bridge.py` Flask server.
     3. Browser with the map already loaded.

8. **Custom Look**
   - Header with project title.
   - Footer with `"73 from PP2LA"`.
   - **Dark mode** color scheme for better night-time visibility.

---

## ⚙️ How it works

### **1. ACARS Capture and Decoding**
- **AcarsDeco2** receives SDR signals and decodes ACARS messages.
- Messages are saved into log files named `YYYYMMDD-HHMM-log`.

### **2. Python Server (`acars_bridge.py`)**
- Continuously monitors the log directory.
- When a new log file or update is detected:
  - Copies it to `log_temp.txt`.
  - Processes it and extracts:
    - **Flight ID**
    - **Aircraft registration**
    - **Geographic coordinates**
    - **Raw message content**
- Stores everything in an **in-memory dictionary** (`aircraft_data`).
- Provides two main API endpoints:
  - `/data.json` → List of aircraft with position and message count.
  - `/messages/<flight>` → All messages for the selected flight.

### **3. Web Interface (`acarsdeco_mapa.html`)**
- Periodically connects to the Flask server and fetches `/data.json`.
- Updates the sidebar with aircraft and statistics.
- Plots positions on the map and maintains path trails.
- When clicking an aircraft:
  - Opens the messages tab with all stored messages.
  - Options to clear messages and locations.
- Additional controls:
  - **Connect button**
  - **Auto-scroll toggle**
  - **Manual history clearing**

---

## 📂 Project Structure

/acarsdeco2_mod
│
├── acarsdeco2.exe # Original AcarsDeco2 binary
├── acars_bridge.py # Flask server to process logs
├── acarsdeco_mapa.html # Customized web interface
├── ad2.bat # Startup script
├── datasets/ # Auxiliary datasets (aircraft, airports, etc.)
└── logs/ # Processed log files


---

## 🚀 How to use

1. **Connect the SDR** and make sure the driver is working.
2. **Configure parameters** in `ad2.bat` (frequencies, gain, HTTP port).
3. **Run `ad2.bat`** to start:
   - AcarsDeco2
   - Flask server
   - Web map in your browser
4. Monitor aircraft on the map and view ACARS messages in real time.

---

## 📌 Notes
- Developed for **local** use on Windows.
- Can be adapted for Linux or Raspberry Pi.
- Requires Python 3.8+ and Flask:
  ```bash
  pip install flask
