"""
FREY AI - Embedded Linux System Monitor
Reads CPU load, RAM allocation, and Qualcomm QRB2210 SoC thermal sensor readings
directly through Linux sysfs and procfs.
"""

import os
import glob
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("frey.system_monitor")


class SystemMonitor:
    """Hardware monitoring engine tailored for Debian 13 on Qualcomm ARM processor."""

    def __init__(self):
        self.last_cpu_times: Optional[tuple] = None
        self.thermal_zones = self._discover_thermal_zones()

    def _discover_thermal_zones(self) -> list:
        """Find available thermal zone sysfs paths."""
        zones = glob.glob("/sys/class/thermal/thermal_zone*")
        return sorted(zones)

    def get_cpu_usage(self) -> float:
        """Compute CPU utilization without external dependencies like psutil."""
        try:
            if os.path.exists("/proc/stat"):
                with open("/proc/stat", "r") as f:
                    line = f.readline()
                fields = [float(x) for x in line.strip().split()[1:8]]
                idle_time = fields[3] + fields[4]
                total_time = sum(fields)

                if self.last_cpu_times:
                    prev_idle, prev_total = self.last_cpu_times
                    delta_idle = idle_time - prev_idle
                    delta_total = total_time - prev_total
                    usage = 100.0 * (1.0 - (delta_idle / max(1.0, delta_total)))
                else:
                    usage = 0.0

                self.last_cpu_times = (idle_time, total_time)
                return round(max(0.0, min(100.0, usage)), 1)
        except Exception:
            pass

        # Fallback using psutil if installed or loadavg
        try:
            import psutil
            return round(psutil.cpu_percent(interval=None), 1)
        except Exception:
            try:
                load1, _, _ = os.getloadavg()
                cores = os.cpu_count() or 4
                return round(min(100.0, (load1 / cores) * 100.0), 1)
            except Exception:
                return 0.0

    def get_ram_usage(self) -> Dict[str, Any]:
        """Read memory usage via /proc/meminfo or psutil."""
        try:
            if os.path.exists("/proc/meminfo"):
                meminfo = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = int(parts[1].strip().split()[0])  # kB
                            meminfo[key] = val

                total_kb = meminfo.get("MemTotal", 4000000)
                avail_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 2000000))
                used_kb = total_kb - avail_kb

                total_mb = round(total_kb / 1024, 1)
                used_mb = round(used_kb / 1024, 1)
                percent = round((used_kb / total_kb) * 100.0, 1)

                return {
                    "total_mb": total_mb,
                    "used_mb": used_mb,
                    "free_mb": round(avail_kb / 1024, 1),
                    "percent": percent,
                }
        except Exception:
            pass

        # Fallback via psutil or default 4GB Arduino UNO Q spec
        try:
            import psutil
            v = psutil.virtual_memory()
            return {
                "total_mb": round(v.total / (1024 * 1024), 1),
                "used_mb": round(v.used / (1024 * 1024), 1),
                "free_mb": round(v.available / (1024 * 1024), 1),
                "percent": round(v.percent, 1),
            }
        except Exception:
            return {
                "total_mb": 4096.0,
                "used_mb": 850.0,
                "free_mb": 3246.0,
                "percent": 20.8,
            }

    def get_temperature(self) -> Optional[float]:
        """Query SoC thermal sensor through Linux thermal zone sysfs."""
        for zone in self.thermal_zones:
            temp_file = os.path.join(zone, "temp")
            if os.path.exists(temp_file):
                try:
                    with open(temp_file, "r") as f:
                        raw = f.read().strip()
                        val = float(raw)
                        # Many Linux kernels report millidegrees C
                        if val > 1000:
                            val /= 1000.0
                        return round(val, 1)
                except Exception:
                    continue

        # Check Raspberry Pi / Qualcomm alternate thermal paths
        alt_paths = [
            "/sys/devices/virtual/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
        ]
        for p in alt_paths:
            if os.path.exists(p):
                try:
                    with open(p, "r") as f:
                        val = float(f.read().strip())
                        if val > 1000:
                            val /= 1000.0
                        return round(val, 1)
                except Exception:
                    continue

        return None

    def get_full_telemetry(self) -> Dict[str, Any]:
        """Compile complete system status dictionary."""
        ram = self.get_ram_usage()
        cpu = self.get_cpu_usage()
        temp = self.get_temperature()

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "cpu_percent": cpu,
            "ram_percent": ram["percent"],
            "ram_used_mb": ram["used_mb"],
            "ram_total_mb": ram["total_mb"],
            "ram_free_mb": ram["free_mb"],
            "temp_c": temp,
            "hardware_platform": "Arduino UNO Q (Qualcomm QRB2210)",
            "os": "Debian GNU/Linux 13 (Trixie)",
        }
