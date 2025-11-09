import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import os

class Database:
    def __init__(self, db_path: str = "patients.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self, timeout: float = 20.0):
        """Get a database connection with timeout and proper settings
        
        Args:
            timeout: How long to wait for the database to unlock (in seconds)
        """
        conn = sqlite3.connect(self.db_path, timeout=timeout)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency (Write-Ahead Logging)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except:
            pass  # If WAL mode is not supported, continue with default
        # Enable foreign key constraints (must be enabled for each connection)
        conn.execute("PRAGMA foreign_keys = ON")
        # Set busy timeout
        conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Patients table - add migration for medications structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                gestational_age_weeks INTEGER,
                risk_factors TEXT,
                medications TEXT,
                risk_category TEXT DEFAULT 'low',
                call_schedule TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Try to migrate medications to new structure if needed
        try:
            cursor.execute("SELECT medications FROM patients LIMIT 1")
            row = cursor.fetchone()
            if row and row[0]:
                # Check if old format (simple list) or new format (structured)
                try:
                    meds = json.loads(row[0])
                    if meds and isinstance(meds, list) and len(meds) > 0:
                        if isinstance(meds[0], str):
                            # Old format - migrate
                            print("Migrating medications to new format...")
                            cursor.execute("SELECT id, medications FROM patients WHERE medications IS NOT NULL AND medications != '[]'")
                            for patient_row in cursor.fetchall():
                                old_meds = json.loads(patient_row[1])
                                new_meds = [{"name": med, "dosage": "", "frequency": [], "time": ""} for med in old_meds if isinstance(med, str)]
                                cursor.execute("UPDATE patients SET medications = ? WHERE id = ?", 
                                             (json.dumps(new_meds), patient_row[0]))
                except:
                    pass
        except:
            pass
        
        # Patient messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                message_audio TEXT,
                transcript TEXT,
                gemma_response TEXT,
                status TEXT DEFAULT 'pending',
                scheduled_callback DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
        
        # Call logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                call_type TEXT,
                status TEXT,
                message_text TEXT,
                scheduled_time DATETIME,
                completed_at DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_patient(self, name: str, phone: str, gestational_age_weeks: int,
                      risk_factors: List[str] = None, medications: List[Dict] = None,
                      risk_category: str = "low") -> int:
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if phone number already exists
            cursor.execute("SELECT id, name FROM patients WHERE phone = ?", (phone,))
            existing = cursor.fetchone()
            
            if existing:
                raise ValueError(f"Phone number {phone} is already registered to patient: {existing[1]} (ID: {existing[0]})")
            
            risk_factors_str = json.dumps(risk_factors or [])
            # Medications is now a list of dicts: [{"name": "...", "dosage": "...", "frequency": "..."}]
            medications_str = json.dumps(medications or [])
            
            cursor.execute("""
                INSERT INTO patients (name, phone, gestational_age_weeks, risk_factors, medications, risk_category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, phone, gestational_age_weeks, risk_factors_str, medications_str, risk_category))
            
            patient_id = cursor.lastrowid
            conn.commit()
            return patient_id
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            if "UNIQUE constraint" in str(e) or "UNIQUE" in str(e):
                raise ValueError(f"Phone number {phone} is already registered. Please use a different phone number.")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_patient(self, patient_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_patients(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_patient(self, patient_id: int, **kwargs) -> bool:
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if phone is being updated and if it's a duplicate
            if 'phone' in kwargs:
                cursor.execute("SELECT id, name FROM patients WHERE phone = ? AND id != ?", 
                              (kwargs['phone'], patient_id))
                existing = cursor.fetchone()
                if existing:
                    raise ValueError(f"Phone number {kwargs['phone']} is already registered to patient: {existing[1]} (ID: {existing[0]})")
            
            allowed_fields = ['name', 'phone', 'gestational_age_weeks', 'risk_factors', 
                             'medications', 'risk_category', 'call_schedule']
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in allowed_fields:
                    if key in ['risk_factors', 'medications', 'call_schedule']:
                        value = json.dumps(value) if value else None
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            values.append(patient_id)
            cursor.execute(f"""
                UPDATE patients 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            
            conn.commit()
            return True
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            if "UNIQUE constraint" in str(e) or "UNIQUE" in str(e):
                raise ValueError(f"Phone number is already registered. Please use a different phone number.")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_message(self, patient_id: int, message_audio: str = None, 
                      transcript: str = None, status: str = "pending") -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO patient_messages (patient_id, message_audio, transcript, status)
            VALUES (?, ?, ?, ?)
        """, (patient_id, message_audio, transcript, status))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id
    
    def update_message(self, message_id: int, gemma_response: str = None, 
                      status: str = None, scheduled_callback: datetime = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if gemma_response:
            updates.append("gemma_response = ?")
            values.append(gemma_response)
        if status:
            updates.append("status = ?")
            values.append(status)
        if scheduled_callback:
            updates.append("scheduled_callback = ?")
            values.append(scheduled_callback.isoformat())
        
        if updates:
            values.append(message_id)
            cursor.execute(f"""
                UPDATE patient_messages 
                SET {', '.join(updates)}
                WHERE id = ?
            """, values)
        
        conn.commit()
        conn.close()
    
    def get_pending_messages(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM patient_messages 
            WHERE status = 'pending' 
            ORDER BY created_at ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def create_call_log(self, patient_id: int, call_type: str, status: str,
                       message_text: str = None, scheduled_time: datetime = None,
                       completed_at: datetime = None) -> int:
        """Create a single call log entry (legacy method - use create_call_logs_batch for multiple)"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO call_logs (patient_id, call_type, status, message_text, scheduled_time, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, call_type, status, message_text, 
                  scheduled_time.isoformat() if scheduled_time else None,
                  completed_at.isoformat() if completed_at else None))
            
            call_log_id = cursor.lastrowid
            conn.commit()
            return call_log_id
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def create_call_logs_batch(self, call_logs: List[Dict]) -> List[int]:
        """Create multiple call log entries in a single transaction
        
        Args:
            call_logs: List of dicts with keys: patient_id, call_type, status, message_text, scheduled_time, completed_at
            
        Returns:
            List of created call log IDs
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            call_log_ids = []
            
            for log in call_logs:
                scheduled_time = log.get('scheduled_time')
                completed_at = log.get('completed_at')
                
                cursor.execute("""
                    INSERT INTO call_logs (patient_id, call_type, status, message_text, scheduled_time, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    log['patient_id'],
                    log['call_type'],
                    log['status'],
                    log.get('message_text'),
                    scheduled_time.isoformat() if scheduled_time and hasattr(scheduled_time, 'isoformat') else (scheduled_time if scheduled_time else None),
                    completed_at.isoformat() if completed_at and hasattr(completed_at, 'isoformat') else (completed_at if completed_at else None)
                ))
                call_log_ids.append(cursor.lastrowid)
            
            conn.commit()
            return call_log_ids
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def get_upcoming_calls(self, limit: int = 10, patient_id: int = None) -> List[Dict]:
        """Get upcoming calls, limited to most recent 10
        
        Only returns calls that are:
        - Status is 'scheduled'
        - Scheduled time is in the future (not past)
        - Optional: Filter by patient_id
        - Ordered by scheduled_time ascending (earliest first)
        """
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get only future scheduled calls, ordered by time (earliest first)
        # Use datetime comparison to handle timezone properly
        current_time = datetime.now()
        # Convert to string for SQLite comparison (SQLite stores as TEXT)
        current_time_str = current_time.isoformat()
        
        if patient_id:
            # Get calls for specific patient
            cursor.execute("""
                SELECT cl.*, p.name, p.phone 
                FROM call_logs cl
                JOIN patients p ON cl.patient_id = p.id
                WHERE cl.status = 'scheduled'
                AND cl.patient_id = ?
                AND datetime(cl.scheduled_time) > datetime(?)
                ORDER BY datetime(cl.scheduled_time) ASC
                LIMIT ?
            """, (patient_id, current_time_str, limit))
        else:
            # Get all upcoming calls
            cursor.execute("""
                SELECT cl.*, p.name, p.phone 
                FROM call_logs cl
                JOIN patients p ON cl.patient_id = p.id
                WHERE cl.status = 'scheduled'
                AND datetime(cl.scheduled_time) > datetime(?)
                ORDER BY datetime(cl.scheduled_time) ASC
                LIMIT ?
            """, (current_time_str, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_call_status(self, call_id: int, status: str, completed_at: datetime = None):
        """Update call status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if completed_at:
            cursor.execute("""
                UPDATE call_logs 
                SET status = ?, completed_at = ?
                WHERE id = ?
            """, (status, completed_at.isoformat(), call_id))
        else:
            cursor.execute("""
                UPDATE call_logs 
                SET status = ?
                WHERE id = ?
            """, (status, call_id))
        
        conn.commit()
        conn.close()
    
    def delete_patient(self, patient_id: int) -> bool:
        """Delete a patient and all associated data"""
        conn = self.get_connection()
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        try:
            # First, check if patient exists
            cursor.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
            if not cursor.fetchone():
                conn.close()
                return False
            
            # Delete associated messages first
            cursor.execute("DELETE FROM patient_messages WHERE patient_id = ?", (patient_id,))
            messages_deleted = cursor.rowcount
            
            # Delete associated call logs
            cursor.execute("DELETE FROM call_logs WHERE patient_id = ?", (patient_id,))
            calls_deleted = cursor.rowcount
            
            # Delete the patient
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            patients_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if patients_deleted > 0:
                print(f"Deleted patient {patient_id}: {patients_deleted} patient, {messages_deleted} messages, {calls_deleted} calls")
                return True
            else:
                return False
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error deleting patient {patient_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
