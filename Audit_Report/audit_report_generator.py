"""
Audit Report & Compliance Certificate Generator (Step 16).
Generates detailed compliance records in JSON and text certificate format.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AuditReportGenerator:
    """Generates official compliance reports and text certificates for the anonymization runs."""
    
    def __init__(self, policy: Dict[str, Any], compliance_law: str = "DPDP Act 2023"):
        self.policy = policy
        self.compliance_law = compliance_law
        
    def _make_json_serializable(self, obj: Any) -> Any:
        """Helper to convert numpy/pandas types to native Python serializable types."""
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(x) for x in obj]
        elif hasattr(obj, 'item'):
            try:
                return obj.item()
            except Exception:
                return str(obj)
        else:
            return obj

    def generate_report(
        self,
        table_reports: List[Dict[str, Any]],
        execution_stats: Dict[str, Any],
        output_dir: str,
        approved_by: str = "Admin"
    ) -> Dict[str, Any]:
        """
        Generates both JSON and human-readable text audit reports.
        
        Args:
            table_reports: A list of dicts containing validation outcomes per table
                           (e.g., table_name, row_counts_match, leaks, risk_score, thief_summary)
            execution_stats: A dict with keys: duration_seconds, tables_processed, total_rows_processed
            output_dir: The directory to save the reports to.
            approved_by: Name of the approving authority.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Determine overall certification status
        overall_risk_score = 0.0
        all_passed = True
        
        if table_reports:
            risk_scores = [t.get("risk_score", 0.0) for t in table_reports]
            overall_risk_score = sum(risk_scores) / len(risk_scores)
            
            # If any table failed validation checks or has high risk score, mark as not certified
            for t in table_reports:
                if t.get("risk_score", 0.0) > 25.0:
                    all_passed = False
                    
        certification_status = "APPROVED / SECURE [PASS]" if all_passed else "REJECTED / EXPOSURES DETECTED [FAIL]"
        
        # 2. Compile structured JSON report
        report_data = {
            "compliance_metadata": {
                "compliance_law": self.compliance_law,
                "certification_status": certification_status,
                "certification_date": datetime.utcnow().isoformat() + "Z",
                "auditor_signature": approved_by,
                "overall_privacy_risk_score": round(overall_risk_score, 2),
                "policy_version": self.policy.get("policy_metadata", {}).get("policy_version", "1.0")
            },
            "execution_summary": {
                "start_time": execution_stats.get("start_time", datetime.utcnow().isoformat()),
                "end_time": execution_stats.get("end_time", datetime.utcnow().isoformat()),
                "duration_seconds": round(execution_stats.get("duration_seconds", 0.0), 2),
                "total_execution_time": execution_stats.get("total_execution_time", f"{round(execution_stats.get('duration_seconds', 0.0), 2)} seconds"),
                "tables_processed_count": execution_stats.get("tables_processed", 0),
                "total_rows_anonymized": execution_stats.get("total_rows_processed", 0)
            },
            "table_compliance_details": table_reports
        }
        
        # Save JSON file
        json_path = os.path.join(output_dir, "compliance_report.json")
        try:
            serializable_report = self._make_json_serializable(report_data)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(serializable_report, f, indent=2)
            logger.info(f"Saved structured compliance report to {json_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON compliance report: {e}")
            
        # 3. Generate human-readable text certificate
        txt_path = os.path.join(output_dir, "compliance_report.txt")
        try:
            self._write_text_certificate(txt_path, report_data)
            logger.info(f"Saved human-readable certificate to {txt_path}")
        except Exception as e:
            logger.error(f"Failed to save text compliance certificate: {e}")
            
        return report_data
        
    def _write_text_certificate(self, filepath: str, r: Dict[str, Any]):
        """Formats and writes a print-ready text compliance certificate."""
        meta = r["compliance_metadata"]
        exec_sum = r["execution_summary"]
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("                    DATA PRIVACY COMPLIANCE AUDIT REPORT\n")
            f.write(f"                       {self.compliance_law.upper()} - TARGET SANDBOX\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("[AUDIT METADATA]\n")
            f.write(f"- Certification Status : {meta['certification_status']}\n")
            f.write(f"- Date of Verification : {meta['certification_date']}\n")
            f.write(f"- Compliance Standard  : {meta['compliance_law']}\n")
            f.write(f"- Authorized Auditor   : {meta['auditor_signature']}\n")
            f.write(f"- Overall Risk Score   : {meta['overall_privacy_risk_score']} / 100\n")
            f.write(f"- Policy Version Used  : {meta['policy_version']}\n\n")
            
            f.write("[AUDIT RISK LEGEND]\n")
            f.write("- GREEN flag (Score: 0/100)      : SECURE. All PII columns anonymized, zero linkage risk.\n")
            f.write("- YELLOW flag (Score: 1-69/100)  : WARNING. All PII data is successfully fake/anonymized, but theoretical quasi-identifier linkages exist.\n")
            f.write("- RED flag (Score: 70-100/100)   : CRITICAL. Direct raw PII leaks detected in target database, or high correlation risk.\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("1. EXECUTION METRICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"- Start Time           : {exec_sum.get('start_time', 'N/A')}\n")
            f.write(f"- End Time             : {exec_sum.get('end_time', 'N/A')}\n")
            f.write(f"- Total Execution Time : {exec_sum.get('total_execution_time', 'N/A')}\n")
            f.write(f"- Total Tables Synced  : {exec_sum['tables_processed_count']}\n")
            f.write(f"- Total Rows Processed : {exec_sum['total_rows_anonymized']:,}\n")
            f.write(f"- Process Duration     : {exec_sum['duration_seconds']} seconds\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("2. TABLE COMPLIANCE AUDIT DETAILED LOGS\n")
            f.write("-" * 80 + "\n")
            
            # Map column policy details
            column_policies = self.policy.get("column_policies", [])
            
            for t_detail in r["table_compliance_details"]:
                table_name = t_detail["table_name"]
                f.write(f"\nTable: '{table_name}'\n")
                f.write(f"  - Count validation   : {'PASSED' if t_detail.get('row_counts_match') else 'FAILED'}\n")
                f.write(f"  - Table Risk Score   : {t_detail.get('risk_score', 0.0)} / 100\n")
                
                # Direct leaks list
                leaks = t_detail.get("leaks", [])
                if leaks:
                    f.write("  - Deterministic Leaks: FAILED (PII exposures caught)\n")
                    for leak in leaks:
                        f.write(f"    * [LEAK DETECTED] {leak}\n")
                else:
                    f.write("  - Deterministic Leaks: PASSED (No raw PII leaks found)\n")
                    
                # Thief Agent Penetration Audit
                thief = t_detail.get("thief_report", {})
                if thief:
                    f.write(f"  - Thief Agent Status : {'BROKEN [FAIL]' if thief.get('anonymization_broken') else 'SECURE [PASS]'}\n")
                    f.write(f"  - Linkage Risk Level : {thief.get('risk_severity', 'LOW')}\n")
                    if thief.get("vulnerability_details") and thief.get("vulnerability_details") != "None":
                        f.write(f"  - Thief Agent Note   : \"{thief.get('vulnerability_details')}\"\n")
                else:
                    f.write("  - Thief Agent Status : UNVERIFIED\n")
                    
                # Columns trace log
                f.write("  - Applied Transformations:\n")
                t_cols = [c for c in column_policies if c["table_name"] == table_name]
                for col in t_cols:
                    col_name = col["column_name"]
                    pii_type = col.get("pii_type", "NONE")
                    tech = col.get("anonymization_technique", "NO_CHANGE")
                    f.write(f"    * {col_name:<20} -> Type: {pii_type:<15} | Technique: {tech}\n")
                    
            f.write("\n" + "=" * 80 + "\n")
            f.write("                   END OF CERTIFICATE OF COMPLIANCE\n")
            f.write("=" * 80 + "\n")
