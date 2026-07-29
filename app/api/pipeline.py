import os, sys, json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from app.services.pipeline_service import pipeline_service
from app.core.exceptions import handle_exception
from app.core.logger import logger
from app.core.config import config

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

@router.post("/start")
async def start_pipeline():
    """Start the pipeline execution"""
    try:
        result = await pipeline_service.start_pipeline()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/set-records")
async def set_total_records(data: dict = Body(...)):
    """Set total records for dynamic chunk size calculation"""
    try:
        total_records = data.get("total_records", 0)
        from app.pipeline.state import pipeline_state
        from app.utils.chunk_calculator import chunk_calculator
        
        pipeline_state.set("total_records", total_records)
        
        if total_records > 0:
            dynamic_chunk_size = chunk_calculator.calculate_chunk_size(total_records)
            estimated_chunks = chunk_calculator.estimate_chunks(total_records, dynamic_chunk_size)
            pipeline_state.set("dynamic_chunk_size", dynamic_chunk_size)
            pipeline_state.set("estimated_chunks", estimated_chunks)
            
            return {
                "status": "success",
                "total_records": total_records,
                "dynamic_chunk_size": dynamic_chunk_size,
                "estimated_chunks": estimated_chunks
            }
        
        return {"status": "success", "message": "Total records set to 0"}
    except Exception as e:
        raise handle_exception(e)

@router.post("/pause")
async def pause_pipeline():
    """Pause the pipeline execution"""
    try:
        result = await pipeline_service.pause_pipeline()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/resume")
async def resume_pipeline():
    """Resume the pipeline execution"""
    try:
        result = await pipeline_service.resume_pipeline()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/stop")
async def stop_pipeline(payload: dict = Body(default={})):
    """Stop/cancel current active pipeline run with run_id validation"""
    try:
        requested_run_id = payload.get("run_id") if isinstance(payload, dict) else None
        result = await pipeline_service.stop_pipeline(requested_run_id=requested_run_id)
        if result.get("status") == "mismatch":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/approve")
async def approve_pipeline():
    """Grant approval to resume pipeline from step 7"""
    try:
        from app.pipeline.state import pipeline_state
        if pipeline_state.get("status") in ["cancelled", "cancelling"]:
            raise HTTPException(status_code=400, detail="Cannot approve a cancelled pipeline run.")
        result = await pipeline_service.approve_pipeline()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/approve-validation")
async def approve_validation():
    """Grant post-validation approval to write to destination DB"""
    try:
        result = await pipeline_service.approve_validation()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/modify-and-reanonymize")
async def modify_and_reanonymize(modified_policy: dict = Body(...)):
    """Modify policy and restart anonymization from step 8"""
    try:
        result = await pipeline_service.modify_and_reanonymize(modified_policy)
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/reset")
async def reset_pipeline():
    """Reset pipeline state to initial values"""
    try:
        result = await pipeline_service.reset_pipeline()
        return result
    except Exception as e:
        raise handle_exception(e)

@router.post("/logout")
async def logout_pipeline():
    """End active pipeline operation on user logout, await worker termination, and clear operational state"""
    try:
        from app.pipeline.state import pipeline_state
        from app.pipeline.controller import pipeline_controller
        active_run_id = pipeline_state.get("run_id")
        
        if active_run_id and pipeline_state.get("status") not in ["idle", "cancelled", "completed", "failed"]:
            await pipeline_service.stop_pipeline(requested_run_id=active_run_id)

        if pipeline_controller.polling_worker:
            try:
                pipeline_controller.polling_worker.stop()
            except Exception:
                pass
            pipeline_controller.polling_worker = None

        pipeline_state.reset()
        return {"status": "success", "message": "Active pipeline operation terminated and state cleared on logout."}
    except Exception as e:
        raise handle_exception(e)

@router.get("/status")
async def get_pipeline_status():
    """Get current pipeline status"""
    try:
        result = pipeline_service.get_pipeline_status()
        return {"state": result}
    except Exception as e:
        raise handle_exception(e)

@router.get("/policy")
async def get_pipeline_policy():
    """Get current anonymization policy for active current run"""
    try:
        import math, os, json
        from app.core.config import config
        from app.pipeline.state import pipeline_state
        from app.core.logger import logger

        current_run_id = pipeline_state.get("run_id")
        current_status = pipeline_state.get("status")
        active_step = pipeline_state.get("active_step", 0)

        state_policy = pipeline_state.get("generated_policy") or pipeline_state.get("approved_policy")
        policy_data = state_policy or {}
        
        disk_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
        if (not policy_data.get("column_policies") and not policy_data.get("tables")) and os.path.exists(disk_path):
            try:
                with open(disk_path, "r", encoding="utf-8") as f:
                    disk_policy = json.load(f)
                    if isinstance(disk_policy, dict):
                        policy_data = disk_policy
            except Exception as e:
                logger.error(f"Error reading disk policy: {e}")
        
        logger.info(f"get_pipeline_policy policy_data keys: {list(policy_data.keys()) if isinstance(policy_data, dict) else type(policy_data)}")
        
        target_table = pipeline_state.get("target_table") or policy_data.get("policy_metadata", {}).get("target_table") or "employees"
        raw_risk = pipeline_state.get("risk_score") or policy_data.get("policy_metadata", {}).get("risk_score")
        risk_score = None
        if raw_risk is not None and isinstance(raw_risk, (int, float)):
            if not math.isnan(raw_risk) and not math.isinf(raw_risk):
                risk_score = float(raw_risk)
            
        col_pols = policy_data.get("column_policies", [])
        if not col_pols:
            tables_data = policy_data.get("tables", {})
            if isinstance(tables_data, dict):
                for tbl_name, cols in tables_data.items():
                    if isinstance(cols, dict):
                        for cname, cconfig in cols.items():
                            tech = cconfig.get("technique") if isinstance(cconfig, dict) else "MASKING"
                            col_pols.append({
                                "table_name": tbl_name,
                                "column_name": cname,
                                "is_pii": True,
                                "pii_type": cname.upper(),
                                "confidence": 0.9,
                                "anonymization_technique": (tech or "MASKING").upper(),
                                "reason": f"Sensitive column {cname}"
                            })
            elif isinstance(tables_data, list):
                for t in tables_data:
                    if isinstance(t, dict) and t.get("columns"):
                        for c in t["columns"]:
                            if isinstance(c, dict):
                                conf = c.get("confidence", 0.9)
                                if not isinstance(conf, (int, float)) or math.isnan(conf) or math.isinf(conf):
                                    conf = 0.9
                                col_pols.append({
                                    "table_name": t.get("table_name", target_table),
                                    "column_name": c.get("column_name"),
                                    "is_pii": c.get("is_pii", True),
                                    "pii_type": c.get("pii_type", "PII"),
                                    "confidence": float(conf),
                                    "anonymization_technique": (c.get("anonymization_technique") or "MASKING").upper() if isinstance(c.get("anonymization_technique"), str) else "MASKING",
                                    "reason": c.get("reason", "Sensitive data column")
                                })

        return {
            "run_id": pipeline_state.get("run_id"),
            "target_table": target_table,
            "status": pipeline_state.get("status"),
            "risk_score": risk_score,
            "policy_metadata": {
                "policy_name": f"Policy for {target_table}",
                "status": "DRAFT",
                "target_table": target_table,
                "risk_score": risk_score,
                "enterprise_type": pipeline_state.get("enterprise_type") or "HR",
                "compliance_law": "DPDP Act 2023"
            },
            "column_policies": col_pols
        }
    except Exception as e:
        logger.error(f"Error in get_pipeline_policy: {e}")
        raise handle_exception(e)

@router.post("/policy/modify")
async def modify_policy(payload: dict = Body(...)):
    """Modify draft policy for active run_id and recalculate risk/privacy scores authoritatively"""
    try:
        from app.pipeline.state import pipeline_state
        active_run_id = pipeline_state.get("run_id")
        req_run_id = payload.get("run_id")
        
        if req_run_id and active_run_id and req_run_id != active_run_id:
            raise HTTPException(status_code=400, detail=f"Run ID mismatch: requested '{req_run_id}', active is '{active_run_id}'")

        column_policies = payload.get("column_policies", [])
        target_table = payload.get("target_table") or pipeline_state.get("target_table") or "customers"

        try:
            from risk_scoring_engine import RiskScoringEngine
        except ImportError:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            admin_dash_path = os.path.join(root_dir, "Admin_Dashboard")
            if admin_dash_path not in sys.path:
                sys.path.insert(0, admin_dash_path)
            from risk_scoring_engine import RiskScoringEngine

        engine = RiskScoringEngine()
        risk_result = engine.calculate_policy_risk(column_policies)
        raw_risk = float(risk_result.get("policy_risk_score", 0.0))
        privacy_score = max(0.0, round(100.0 - raw_risk, 1))
        risk_lvl = risk_result.get("risk_level", "LOW")

        modified_draft = {
            "target_table": target_table,
            "column_policies": column_policies,
            "modified_at": datetime.now().isoformat(),
            "modified_by": "Dashboard Admin"
        }
        
        gen_pol = pipeline_state.get("generated_policy") or {}
        gen_pol["column_policies"] = column_policies
        if "policy_metadata" not in gen_pol:
            gen_pol["policy_metadata"] = {}
        gen_pol["policy_metadata"]["risk_score"] = raw_risk
        gen_pol["policy_metadata"]["privacy_score"] = privacy_score
        gen_pol["policy_metadata"]["risk_level"] = risk_lvl
        gen_pol["policy_metadata"]["status"] = "DRAFT_MODIFIED"
        gen_pol["policy_metadata"]["target_table"] = target_table

        pipeline_state.set("generated_policy", gen_pol)
        pipeline_state.set("modified_policy", modified_draft)
        pipeline_state.set("risk_score", raw_risk)
        pipeline_state.set("privacy_score", privacy_score)
        pipeline_state.set("risk_level", risk_lvl)
        pipeline_state.set("approval_state", "pending")

        policy_path = os.path.join(config.DIRECTORY, "anonymization_policy.json")
        if os.path.exists(policy_path):
            try:
                with open(policy_path, "r", encoding="utf-8") as f:
                    disk_p = json.load(f)
                disk_p["column_policies"] = column_policies
                if "policy_metadata" not in disk_p:
                    disk_p["policy_metadata"] = {}
                disk_p["policy_metadata"]["risk_score"] = raw_risk
                disk_p["policy_metadata"]["privacy_score"] = privacy_score
                disk_p["policy_metadata"]["risk_level"] = risk_lvl
                with open(policy_path, "w", encoding="utf-8") as f:
                    json.dump(disk_p, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed updating disk policy file: {e}")

        return {
            "status": "modified",
            "run_id": active_run_id,
            "target_table": target_table,
            "risk_score": raw_risk,
            "privacy_score": privacy_score,
            "risk_level": risk_lvl,
            "column_policies": column_policies,
            "details": risk_result
        }
    except Exception as e:
        logger.error(f"Error modifying policy: {e}")
        raise handle_exception(e)

@router.post("/recalculate-risk")
async def recalculate_risk(payload: dict = Body(...)):
    """Recalculate policy risk score dynamically when technique modifications occur"""
    try:
        policy_data = payload.get("policy") or payload
        try:
            from risk_scoring_engine import RiskScoringEngine
        except ImportError:
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            admin_dash_path = os.path.join(root_dir, "Admin_Dashboard")
            if admin_dash_path not in sys.path:
                sys.path.insert(0, admin_dash_path)
            from risk_scoring_engine import RiskScoringEngine

        engine = RiskScoringEngine()
        column_policies = policy_data.get("column_policies", [])
        if not column_policies and isinstance(policy_data.get("tables"), dict):
            # Extract column policies if passed in table dictionary format
            column_policies = []
            for tname, cols in policy_data["tables"].items():
                if isinstance(cols, dict):
                    for cname, ccfg in cols.items():
                        column_policies.append({
                            "table_name": tname,
                            "column_name": cname,
                            "is_pii": True,
                            "pii_type": cname.upper(),
                            "anonymization_technique": ccfg.get("technique", "MASKING") if isinstance(ccfg, dict) else "MASKING"
                        })
                        
        risk_result = engine.calculate_policy_risk(column_policies)
        raw_risk = float(risk_result.get("policy_risk_score", 0.0))
        privacy_score = max(0.0, round(100.0 - raw_risk, 1))
        risk_lvl = risk_result.get("risk_level", "LOW")
        
        from app.pipeline.state import pipeline_state
        pipeline_state.set("risk_score", raw_risk)
        pipeline_state.set("privacy_score", privacy_score)
        pipeline_state.set("risk_level", risk_lvl)
        
        return {
            "status": "success",
            "run_id": pipeline_state.get("run_id"),
            "risk_score": raw_risk,
            "privacy_score": privacy_score,
            "risk_level": risk_lvl,
            "details": risk_result
        }
    except Exception as e:
        logger.error(f"Error recalculating risk score: {e}")
        raise handle_exception(e)

@router.post("/policy/modify")
async def modify_pipeline_policy(payload: dict = Body(...)):
    """Modify anonymization policy column rules and recalculate risk score"""
    try:
        from app.pipeline.state import pipeline_state
        column_policies = payload.get("column_policies") or []
        target_table = payload.get("target_table") or pipeline_state.get("target_table") or "accounts"
        
        try:
            from risk_scoring_engine import RiskScoringEngine
        except ImportError:
            import sys, os
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            admin_dash_path = os.path.join(root, "Admin_Dashboard")
            if admin_dash_path not in sys.path:
                sys.path.insert(0, admin_dash_path)
            from risk_scoring_engine import RiskScoringEngine

        engine = RiskScoringEngine()
        risk_result = engine.calculate_policy_risk(column_policies)
        raw_risk = float(risk_result.get("policy_risk_score", 0.0))
        privacy_score = max(0.0, round(100.0 - raw_risk, 1))
        risk_lvl = risk_result.get("risk_level", "LOW")

        pipeline_state.set("risk_score", raw_risk)
        pipeline_state.set("privacy_score", privacy_score)
        pipeline_state.set("risk_level", risk_lvl)
        pipeline_state.set("modified_policy", {
            "target_table": target_table,
            "column_policies": column_policies,
            "modified_at": datetime.utcnow().isoformat(),
            "modified_by": "Dashboard Admin"
        })

        return {
            "status": "modified",
            "message": "Anonymization policy updated and risk score recalculated successfully.",
            "target_table": target_table,
            "rule_count": len(column_policies),
            "risk_score": raw_risk,
            "privacy_score": privacy_score,
            "risk_level": risk_lvl
        }
    except Exception as e:
        raise handle_exception(e)

@router.get("/samples")
async def get_pipeline_samples():
    """Get sample data for target table columns"""
    try:
        from app.pipeline.state import pipeline_state
        sample_data = pipeline_state.get("sample_data")
        if sample_data:
            return {"sample_data": sample_data}
        return {
          "sample_data": {
            "customers": [
              {"customer_id": 101, "first_name": "Rajesh", "last_name": "Kumar", "email": "rajesh.k@gmail.com", "phone": "+91-9876543210", "ssn": "987-65-4321", "credit_card": "4532-xxxx-xxxx-1234"},
              {"customer_id": 102, "first_name": "Priya", "last_name": "Sharma", "email": "priya.s@yahoo.com", "phone": "+91-9812345678", "ssn": "987-65-4322", "credit_card": "4532-xxxx-xxxx-5678"}
            ],
            "employees": [
              {"employee_id": 501, "full_name": "Amit Varma", "email": "amit.varma@company.com", "salary": 125000, "ssn": "888-12-3456", "department": "Engineering"},
              {"employee_id": 502, "full_name": "Sunita Rao", "email": "sunita.rao@company.com", "salary": 140000, "ssn": "888-12-3457", "department": "Finance"}
            ],
            "transactions": [
              {"transaction_id": "TXN9001", "account_id": 1001, "card_number": "4532-1111-2222-3333", "amount": 2450.50, "merchant": "Amazon India"},
              {"transaction_id": "TXN9002", "account_id": 1002, "card_number": "4532-1111-2222-4444", "amount": 890.00, "merchant": "Flipkart Retail"}
            ],
            "accounts": [
              {"account_id": 1001, "customer_id": 101, "account_number": "ACC-90812345", "routing_number": "021000021", "balance": 45670.00},
              {"account_id": 1002, "customer_id": 102, "account_number": "ACC-90812346", "routing_number": "021000021", "balance": 128900.50}
            ]
          }
        }
    except Exception as e:
        logger.error(f"Error in get_pipeline_samples: {e}")
        return {"sample_data": {}}

@router.get("/table-schema")
async def get_table_schema(table: Optional[str] = None):
    """Get columns, data types, and primary key for the target table dynamically"""
    try:
        from app.pipeline.state import pipeline_state
        target_table = table or pipeline_state.get("target_table")
        config_path = os.path.join(config.DIRECTORY, "database_config.json")
        db_cfg = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    db_cfg = json.load(f)
                    if not target_table:
                        target_table = db_cfg.get("target_table")
            except Exception:
                pass
        if not target_table:
            return {"status": "error", "message": "No target table configured"}

        db_type = db_cfg.get("database_type") or db_cfg.get("type", "sqlite")
        columns = []
        pk_col = None

        if db_type == "postgresql":
            import psycopg2
            host = db_cfg.get("host") or os.getenv("SOURCE_DB_HOST")
            port = int(db_cfg.get("port") or os.getenv("SOURCE_DB_PORT", 5432))
            dbname = db_cfg.get("database_name") or db_cfg.get("database") or os.getenv("SOURCE_DB_NAME", "neondb")
            user = db_cfg.get("username") or os.getenv("SOURCE_DB_USERNAME", "neondb_owner")
            password = db_cfg.get("password") or os.getenv("SOURCE_DB_PASSWORD")
            sslmode = db_cfg.get("sslmode") or os.getenv("SOURCE_DB_SSLMODE", "require")
            
            conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password, sslmode=sslmode)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (target_table,))
            cols = cursor.fetchall()
            
            # Primary key inspection
            try:
                cursor.execute("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass AND i.indisprimary;
                """, (target_table,))
                pk_row = cursor.fetchone()
                pk_col = pk_row[0] if pk_row else (cols[0][0] if cols else "id")
            except Exception:
                pk_col = cols[0][0] if cols else "id"
            conn.close()

            for cname, ctype in cols:
                if cname != pk_col and cname != "created_at":
                    columns.append({"name": cname, "type": ctype.upper()})
        else:
            import sqlite3
            db_path = os.path.join(config.DIRECTORY, "test_source.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({target_table})")
                cols_info = cursor.fetchall()
                conn.close()
                for c in cols_info:
                    cname = c[1]
                    ctype = c[2].upper()
                    if c[5] == 1:
                        pk_col = cname
                    elif cname != "created_at":
                        columns.append({"name": cname, "type": ctype})

        return {"status": "success", "target_table": target_table, "pk_col": pk_col or "id", "columns": columns}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/table-records")
async def get_table_records(table: Optional[str] = None, limit: int = 15):
    """Fetch existing records from target table to allow selection for UPDATE & DELETE"""
    try:
        from app.pipeline.state import pipeline_state
        target_table = table or pipeline_state.get("target_table")
        config_path = os.path.join(config.DIRECTORY, "database_config.json")
        db_cfg = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    db_cfg = json.load(f)
                    if not target_table:
                        target_table = db_cfg.get("target_table")
            except Exception:
                pass
        if not target_table:
            return {"status": "error", "message": "No target table configured", "records": []}

        db_type = db_cfg.get("database_type") or db_cfg.get("type", "sqlite")
        records = []

        if db_type == "postgresql":
            import psycopg2
            host = db_cfg.get("host") or os.getenv("SOURCE_DB_HOST")
            port = int(db_cfg.get("port") or os.getenv("SOURCE_DB_PORT", 5432))
            dbname = db_cfg.get("database_name") or db_cfg.get("database") or os.getenv("SOURCE_DB_NAME", "neondb")
            user = db_cfg.get("username") or os.getenv("SOURCE_DB_USERNAME", "neondb_owner")
            password = db_cfg.get("password") or os.getenv("SOURCE_DB_PASSWORD")
            sslmode = db_cfg.get("sslmode") or os.getenv("SOURCE_DB_SSLMODE", "require")
            
            conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password, sslmode=sslmode)
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM "{target_table}" ORDER BY 1 DESC LIMIT %s;', (limit,))
            col_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                record_dict = dict(zip(col_names, row))
                # Format non-serializable fields
                for k, v in record_dict.items():
                    if hasattr(v, 'isoformat'):
                        record_dict[k] = v.isoformat()
                    elif not isinstance(v, (str, int, float, bool, type(None))):
                        record_dict[k] = str(v)
                records.append(record_dict)
        else:
            import sqlite3
            db_path = os.path.join(config.DIRECTORY, "test_source.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {target_table} ORDER BY 1 DESC LIMIT {limit}")
                col_names = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                conn.close()
                for row in rows:
                    records.append(dict(zip(col_names, row)))

        return {"status": "success", "target_table": target_table, "records": records}
    except Exception as e:
        return {"status": "error", "message": str(e), "records": []}

@router.post("/simulate-traffic")
async def simulate_traffic(payload: dict = Body(...)):
    """Simulate real-time CRUD traffic (INSERT, UPDATE, DELETE) against the source database safely for live demos."""
    try:
        import sqlite3, random, time
        from app.pipeline.state import pipeline_state
        
        operation = (payload.get("operation") or "INSERT").upper()
        target_table = payload.get("target_table") or pipeline_state.get("target_table")
        custom_data = payload.get("custom_data")
        
        if not target_table:
            # Try loading from database_config.json
            config_path = os.path.join(config.DIRECTORY, "database_config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        db_cfg = json.load(f)
                        target_table = db_cfg.get("target_table")
                except Exception:
                    pass
                    
        if not target_table:
            return {"status": "error", "message": "No database configuration or target table available. Please configure database first."}

        db_type = "sqlite"
        db_cfg = {}
        config_path = os.path.join(config.DIRECTORY, "database_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    db_cfg = json.load(f)
                    db_type = db_cfg.get("database_type") or db_cfg.get("type", "sqlite")
            except Exception:
                pass

        if db_type == "postgresql":
            import psycopg2
            host = db_cfg.get("host") or os.getenv("SOURCE_DB_HOST")
            port = int(db_cfg.get("port") or os.getenv("SOURCE_DB_PORT", 5432))
            dbname = db_cfg.get("database_name") or db_cfg.get("database") or os.getenv("SOURCE_DB_NAME", "neondb")
            user = db_cfg.get("username") or os.getenv("SOURCE_DB_USERNAME", "neondb_owner")
            password = db_cfg.get("password") or os.getenv("SOURCE_DB_PASSWORD")
            sslmode = db_cfg.get("sslmode") or os.getenv("SOURCE_DB_SSLMODE", "require")
            
            conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password, sslmode=sslmode)
            cursor = conn.cursor()
            
            # Inspect PostgreSQL table columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (target_table,))
            cols_raw = cursor.fetchall()
            if not cols_raw:
                conn.close()
                return {"status": "error", "message": f"Table '{target_table}' does not exist in PostgreSQL database."}
                
            cols_info = [(i, c[0], c[1], c[2], None, 1 if i == 0 else 0) for i, c in enumerate(cols_raw)]
            placeholder_char = "%s"
        else:
            import sqlite3
            db_path = os.path.join(config.DIRECTORY, "test_source.db")
            if not os.path.exists(db_path):
                return {"status": "error", "message": f"Source database file '{db_path}' not found for simulation."}
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({target_table})")
            cols_info = cursor.fetchall()
            if not cols_info:
                conn.close()
                return {"status": "error", "message": f"Table '{target_table}' does not exist in source database."}
            placeholder_char = "?"

        col_names = [c[1] for c in cols_info]
        col_types = {c[1]: str(c[2]).upper() for c in cols_info}
        pk_col = next((c[1] for c in cols_info if c[5] == 1), col_names[0])
        
        rand_suffix = random.randint(1000, 9999)
        result_payload = {}

        if operation == "INSERT":
            insert_data = {}
            if custom_data and isinstance(custom_data, dict):
                for k, v in custom_data.items():
                    if k in col_names and v is not None and str(v).strip() != "":
                        raw_val = str(v).strip()
                        ctype = col_types.get(k, "VARCHAR")
                        
                        # Integer type check
                        if any(t in ctype for t in ["INT", "SERIAL", "BIGINT", "SMALLINT"]):
                            try:
                                clean_digits = "".join(ch for ch in raw_val if ch.isdigit() or ch == '-')
                                insert_data[k] = int(clean_digits) if clean_digits else random.randint(1000, 99999)
                            except Exception:
                                insert_data[k] = random.randint(1000, 99999)
                        # Float / Numeric type check
                        elif any(t in ctype for t in ["FLOAT", "REAL", "NUMERIC", "DOUBLE", "DECIMAL"]):
                            try:
                                clean_float = "".join(ch for ch in raw_val if ch.isdigit() or ch in ['.', '-'])
                                insert_data[k] = float(clean_float) if clean_float else round(random.uniform(1000.0, 99999.0), 2)
                            except Exception:
                                insert_data[k] = round(random.uniform(1000.0, 99999.0), 2)
                        else:
                            insert_data[k] = raw_val
            
            if not insert_data:
                if target_table == "customers":
                    insert_data = {
                        "name": f"sim_Customer_{rand_suffix}",
                        "email": f"sim_user_{rand_suffix}@datavault.ai",
                        "phone": f"+91-98{random.randint(10000000, 99999999)}",
                        "address": f"{random.randint(10, 999)} Tech Park, Bangalore"
                    }
                elif target_table == "employees":
                    insert_data = {
                        "full_name": f"sim_Employee_{rand_suffix}",
                        "email": f"sim_emp_{rand_suffix}@company.com",
                        "salary": random.randint(50000, 150000),
                        "ssn": f"888-{random.randint(10, 99)}-{random.randint(1000, 9999)}",
                        "department": "Engineering"
                    }
                elif target_table == "accounts":
                    insert_data = {
                        "customer_id": random.randint(1, 100),
                        "account_number": f"sim_ACC-{rand_suffix}",
                        "routing_number": "021000021",
                        "balance": round(random.uniform(1000.0, 50000.0), 2)
                    }
                elif target_table == "transactions":
                    insert_data = {
                        "account_id": random.randint(1001, 1050),
                        "card_number": f"4532-sim-{rand_suffix}",
                        "amount": round(random.uniform(50.0, 5000.0), 2),
                        "merchant": f"sim_Merchant_{rand_suffix}"
                    }
                else:
                    # Generic table fallback
                    for c in cols_info:
                        cname = c[1]
                        ctype = c[2].upper()
                        is_pk = (c[5] == 1)
                        if is_pk:
                            continue
                        if "INT" in ctype:
                            insert_data[cname] = random.randint(1, 9999)
                        elif "FLOAT" in ctype or "REAL" in ctype or "NUM" in ctype:
                            insert_data[cname] = round(random.uniform(10.0, 1000.0), 2)
                        else:
                            insert_data[cname] = f"sim_{cname}_{rand_suffix}"

            # Auto-generate Primary Key if missing from insert_data (e.g. for non-serial PK columns like account_id)
            if pk_col and pk_col in col_names and pk_col not in insert_data:
                try:
                    if db_type == "postgresql":
                        cursor.execute(f'SELECT COALESCE(MAX("{pk_col}"), 0) + 1 FROM "{target_table}";')
                        next_pk = cursor.fetchone()[0]
                        insert_data[pk_col] = next_pk
                    else:
                        cursor.execute(f'SELECT COALESCE(MAX({pk_col}), 0) + 1 FROM {target_table};')
                        next_pk = cursor.fetchone()[0]
                        insert_data[pk_col] = next_pk
                except Exception as pk_err:
                    print(f"[SIMULATOR] Auto-PK generation note for '{pk_col}': {pk_err}")

            fields = [k for k in insert_data.keys() if k in col_names]
            placeholders = ", ".join([placeholder_char] * len(fields))
            
            if db_type == "postgresql":
                sql = f'INSERT INTO "{target_table}" ({", ".join([f"{f}" for f in fields])}) VALUES ({placeholders}) RETURNING "{pk_col}"'
                cursor.execute(sql, [insert_data[f] for f in fields])
                conn.commit()
                row = cursor.fetchone()
                inserted_id = row[0] if row else "auto"
            else:
                sql = f"INSERT INTO {target_table} ({', '.join(fields)}) VALUES ({placeholders})"
                cursor.execute(sql, [insert_data[f] for f in fields])
                conn.commit()
                inserted_id = cursor.lastrowid

            result_payload = {
                "status": "success",
                "operation": "INSERT",
                "target_table": target_table,
                "inserted_id": inserted_id,
                "data": insert_data,
                "timestamp": datetime.now().isoformat()
            }

        elif operation == "UPDATE":
            text_cols = [c[1] for c in cols_info if "TEXT" in c[2].upper() or "CHAR" in c[2].upper() or "VARCHAR" in c[2].upper()]
            where_clauses = [f"{col} LIKE '%sim_%'" for col in text_cols]
            where_sql = (" WHERE " + " OR ".join(where_clauses)) if where_clauses else ""
            
            cursor.execute(f"SELECT {pk_col} FROM {target_table}{where_sql} ORDER BY {pk_col} DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                cursor.execute(f"SELECT {pk_col} FROM {target_table} ORDER BY {pk_col} DESC LIMIT 1")
                row = cursor.fetchone()

            if not row:
                conn.close()
                return {"status": "error", "message": f"No records found in table '{target_table}' to update."}

            target_id = row[0]
            update_field = text_cols[0] if text_cols else col_names[1]
            new_val = f"sim_updated_{rand_suffix}"
            
            cursor.execute(f"UPDATE {target_table} SET {update_field} = {placeholder_char} WHERE {pk_col} = {placeholder_char}", (new_val, target_id))
            conn.commit()

            result_payload = {
                "status": "success",
                "operation": "UPDATE",
                "target_table": target_table,
                "updated_id": target_id,
                "updated_field": update_field,
                "new_value": new_val,
                "timestamp": datetime.now().isoformat()
            }

        elif operation == "DELETE":
            req_record_id = payload.get("record_id")
            target_id = None

            if req_record_id is not None and str(req_record_id).strip() != "":
                target_id = req_record_id
            else:
                text_cols = [c[1] for c in cols_info if "TEXT" in c[2].upper() or "CHAR" in c[2].upper() or "VARCHAR" in c[2].upper()]
                where_clauses = [f'"{col}" LIKE \'%sim_%\'' for col in text_cols]
                where_sql = (" WHERE " + " OR ".join(where_clauses)) if where_clauses else ""

                if where_sql:
                    if db_type == "postgresql":
                        cursor.execute(f'SELECT "{pk_col}" FROM "{target_table}"{where_sql} ORDER BY "{pk_col}" DESC LIMIT 1')
                    else:
                        cursor.execute(f'SELECT {pk_col} FROM {target_table}{where_sql} ORDER BY {pk_col} DESC LIMIT 1')
                    row = cursor.fetchone()
                    if row:
                        target_id = row[0]

            if not target_id:
                if db_type == "postgresql":
                    cursor.execute(f'SELECT "{pk_col}" FROM "{target_table}" ORDER BY "{pk_col}" DESC LIMIT 1')
                else:
                    cursor.execute(f'SELECT {pk_col} FROM {target_table} ORDER BY {pk_col} DESC LIMIT 1')
                row = cursor.fetchone()
                if row:
                    target_id = row[0]

            if not target_id:
                conn.close()
                return {
                    "status": "error",
                    "code": "NO_SAFE_SIMULATION_RECORD",
                    "message": "No record available to delete. Please insert a record first."
                }

            try:
                if db_type == "postgresql":
                    cursor.execute(f'DELETE FROM "{target_table}" WHERE "{pk_col}" = %s', (target_id,))
                else:
                    cursor.execute(f'DELETE FROM {target_table} WHERE {pk_col} = ?', (target_id,))
                conn.commit()
            except Exception as del_err:
                conn.rollback()
                err_msg = str(del_err)
                if "foreign key" in err_msg.lower() or "violates foreign key constraint" in err_msg.lower():
                    # Extract referenced table if present
                    ref_table = "child"
                    if "table" in err_msg.lower():
                        parts = err_msg.split('table "')
                        if len(parts) > 2:
                            ref_table = parts[2].split('"')[0]
                    return {
                        "status": "error",
                        "code": "FOREIGN_KEY_VIOLATION",
                        "message": f"Cannot delete record #{target_id} from '{target_table}' because dependent rows exist in table '{ref_table}' (Foreign Key Constraint). Insert a new record or pick a record without dependent child rows."
                    }
                raise del_err

            result_payload = {
                "status": "success",
                "operation": "DELETE",
                "target_table": target_table,
                "deleted_id": target_id,
                "timestamp": datetime.now().isoformat()
            }

        cursor.close()
        conn.close()
        logger.info(f"Traffic Simulation executed cleanly: {operation} on table '{target_table}'")
        return result_payload

    except Exception as e:
        logger.error(f"Failed traffic simulation: {e}")
        err_str = str(e)
        if "foreign key constraint" in err_str.lower():
            return {
                "status": "error",
                "message": f"Cannot delete record from '{target_table}': Active foreign key references exist in child tables. Create a new test record or pick a standalone row to delete."
            }
        return {"status": "error", "message": f"Simulation failed: {err_str}"}
