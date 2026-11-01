"""
FREY AI - Edge SQLite Telemetry & Detection History Storage
Stores structured detections, system metrics, and configurable runtime parameters.
"""

import os
import json
import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("frey.database")


class FreyDatabase:
    """Thread-safe SQLite database manager for edge logging and analytics."""

    def __init__(self, db_path: str = "data/frey.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._init_default_settings()

    @contextmanager
    def _get_connection(self):
        """Create new connection with Row factory and WAL mode for low contention."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self):
        """Create database tables and performance indexes."""
        with self._get_connection() as conn:
            # 1. Detections Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    disease TEXT NOT NULL,
                    is_healthy INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    bbox_json TEXT NOT NULL,
                    image_path TEXT,
                    recommendation TEXT,
                    notes TEXT
                );
            """)

            # 2. System Metrics Telemetry Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    ram_percent REAL,
                    ram_used_mb REAL,
                    ram_total_mb REAL,
                    temp_c REAL,
                    inference_fps REAL,
                    inference_time_ms REAL
                );
            """)

            # 3. Settings Key-Value Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_det_timestamp ON detections(timestamp);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_det_crop ON detections(crop);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_det_healthy ON detections(is_healthy);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp);")
            conn.commit()

    def _init_default_settings(self):
        """Seed default configuration values if not present."""
        defaults = {
            "conf_threshold": "0.30",
            "nms_threshold": "0.45",
            "camera_device": "0",
            "camera_res": "320x240",
            "camera_fps": "15",
            "inference_rate_hz": "2.0",
            "auto_save_history": "true",
            "overlay_boxes": "true",
            "overlay_labels": "true",
            "eco_mode": "true",
            "num_threads": "2",
            "jpeg_quality": "65",
        }
        with self._get_connection() as conn:
            for k, v in defaults.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'));",
                    (k, v),
                )
            conn.commit()

    def log_detection(self, det: Dict[str, Any], image_path: Optional[str] = None) -> int:
        """Insert single detection record into database."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO detections (
                    timestamp, crop, disease, is_healthy, confidence, bbox_json, image_path, recommendation, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    det.get("timestamp"),
                    det.get("crop", "Unknown"),
                    det.get("disease", "Unknown"),
                    1 if det.get("is_healthy", False) else 0,
                    float(det.get("confidence", 0.0)),
                    json.dumps(det.get("bbox", [])),
                    image_path,
                    det.get("recommendation", ""),
                    det.get("notes", ""),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def log_batch_detections(self, detections: List[Dict[str, Any]], image_path: Optional[str] = None):
        """Insert multiple detections recorded from a single frame."""
        if not detections:
            return
        with self._get_connection() as conn:
            for det in detections:
                conn.execute(
                    """
                    INSERT INTO detections (
                        timestamp, crop, disease, is_healthy, confidence, bbox_json, image_path, recommendation, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        det.get("timestamp"),
                        det.get("crop", "Unknown"),
                        det.get("disease", "Unknown"),
                        1 if det.get("is_healthy", False) else 0,
                        float(det.get("confidence", 0.0)),
                        json.dumps(det.get("bbox", [])),
                        image_path,
                        det.get("recommendation", ""),
                        det.get("notes", ""),
                    ),
                )
            conn.commit()

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        crop: Optional[str] = None,
        is_healthy: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query historical detections with multi-field filtering and pagination."""
        query = "SELECT * FROM detections WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM detections WHERE 1=1"
        params: List[Any] = []

        if crop and crop != "all":
            query += " AND crop = ?"
            count_query += " AND crop = ?"
            params.append(crop)

        if is_healthy is not None:
            query += " AND is_healthy = ?"
            count_query += " AND is_healthy = ?"
            params.append(1 if is_healthy else 0)

        if search:
            query += " AND (crop LIKE ? OR disease LIKE ? OR recommendation LIKE ?)"
            count_query += " AND (crop LIKE ? OR disease LIKE ? OR recommendation LIKE ?)"
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])

        with self._get_connection() as conn:
            # Get total count
            total = conn.execute(count_query, params).fetchone()["total"]

            # Query page
            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            page_params = params + [limit, offset]
            rows = conn.execute(query, page_params).fetchall()

            results = []
            for r in rows:
                item = dict(r)
                item["is_healthy"] = bool(item["is_healthy"])
                try:
                    item["bbox"] = json.loads(item["bbox_json"])
                except Exception:
                    item["bbox"] = []
                results.append(item)

            return results, total

    def get_summary_stats(self) -> Dict[str, Any]:
        """Compute aggregate agronomic metrics across all recorded detections."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM detections;").fetchone()["c"]
            healthy = conn.execute("SELECT COUNT(*) as c FROM detections WHERE is_healthy = 1;").fetchone()["c"]
            diseased = conn.execute("SELECT COUNT(*) as c FROM detections WHERE is_healthy = 0;").fetchone()["c"]
            
            # Crop distribution
            crop_rows = conn.execute(
                "SELECT crop, COUNT(*) as count FROM detections GROUP BY crop ORDER BY count DESC LIMIT 8;"
            ).fetchall()
            crop_distribution = {r["crop"]: r["count"] for r in crop_rows}

            # Disease distribution
            disease_rows = conn.execute(
                "SELECT disease, COUNT(*) as count FROM detections WHERE is_healthy = 0 GROUP BY disease ORDER BY count DESC LIMIT 8;"
            ).fetchall()
            disease_distribution = {r["disease"]: r["count"] for r in disease_rows}

            return {
                "total_detections": total,
                "healthy_detections": healthy,
                "diseased_detections": diseased,
                "healthy_ratio": round((healthy / total * 100), 1) if total > 0 else 0.0,
                "crop_distribution": crop_distribution,
                "top_diseases": disease_distribution,
            }

    def log_system_metrics(self, metrics: Dict[str, Any]):
        """Record board CPU, RAM, and temperature telemetry snapshot."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO system_metrics (
                    timestamp, cpu_percent, ram_percent, ram_used_mb, ram_total_mb, temp_c, inference_fps, inference_time_ms
                ) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics.get("cpu_percent"),
                    metrics.get("ram_percent"),
                    metrics.get("ram_used_mb"),
                    metrics.get("ram_total_mb"),
                    metrics.get("temp_c"),
                    metrics.get("inference_fps"),
                    metrics.get("inference_time_ms"),
                ),
            )
            conn.commit()

    def get_recent_metrics(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieve recent system metrics time series for dashboard charts."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM system_metrics ORDER BY id DESC LIMIT ?;", (limit,)
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    def get_setting(self, key: str, default: str = "") -> str:
        """Fetch setting value by key."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?;", (key,)).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: Any):
        """Update or insert configuration key."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;",
                (key, str(value)),
            )
            conn.commit()

    def get_all_settings(self) -> Dict[str, str]:
        """Fetch dictionary of all runtime settings."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings;").fetchall()
            return {r["key"]: r["value"] for r in rows}
