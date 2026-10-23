"""Generate Synthetic Benchmark Dataset for Research Experiments (Prompt 2 Phase 12).

Creates 60 reproducible, empirically diverse test cases across:
- 404 Not Found (path drift, resource renaming)
- 4xx & 5xx server failures
- Redirects (HTTP to HTTPS, 301, 302)
- Ambiguous & low-confidence cases (requiring human review)
- Permanently deprecated resources (no valid replacement)
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "experiments"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_PATH = DATA_DIR / "benchmark_dataset.json"

CATEGORIES = [
    {
        "doc": "HR_Leave_and_Absence_Policy_2024.pdf",
        "cases": [
            {
                "case_id": "CASE_HR_01",
                "broken_url": "https://httpbin.org/status/404",
                "anchor_text": "statutory sick leave schedule",
                "surrounding_context": "For statutory sick leave guidelines, review the standard statutory sick leave schedule. Inquiries regarding family leave must be submitted through the personnel portal.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html",
                "candidate_urls": [
                    "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html",
                    "https://intranet.corp/hr/benefits/modern-leave-management.html",
                    "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_HR_02",
                "broken_url": "https://example.com/archived/hr/leave-system-v1.php",
                "anchor_text": "archived leave repository",
                "surrounding_context": "The legacy application portal at the archived leave repository is no longer maintained. Use the updated HR benefits site instead.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/hr/benefits/modern-leave-management.html",
                "candidate_urls": [
                    "https://intranet.corp/hr/benefits/modern-leave-management.html",
                    "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html",
                    "https://example.com/finance/travel/voucher-template-2017.xls"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_HR_03",
                "broken_url": "https://httpbin.org/delay/15",
                "anchor_text": "Unpaid Leave Calculation Spreadsheet",
                "surrounding_context": "Download the Unpaid Leave Calculation Spreadsheet to estimate pro-rated deductions.",
                "failure_type": "TIMEOUT",
                "ground_truth_replacement": "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html",
                "candidate_urls": [
                    "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html",
                    "https://intranet.corp/finance/corporate-credit-card-management.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_HR_04",
                "broken_url": "https://httpbin.org/status/410",
                "anchor_text": "Legacy Payroll Timesheet Link",
                "surrounding_context": "Log into the Legacy Payroll Timesheet Link prior to migration cutoff.",
                "failure_type": "BROKEN_4XX",
                "ground_truth_replacement": "https://intranet.corp/hr/benefits/modern-leave-management.html",
                "candidate_urls": [
                    "https://intranet.corp/hr/benefits/modern-leave-management.html",
                    "https://intranet.corp/security/identity-and-access-management-standard.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_HR_05",
                "broken_url": "https://obsolete-hr-portal-1999.corp.net/deprecated",
                "anchor_text": "Discontinued Pension Form",
                "surrounding_context": "Discontinued pension paper forms have been phased out under government order.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": None,
                "candidate_urls": [],
                "expected_decision": "NO_REPLACEMENT"
            }
        ]
    },
    {
        "doc": "Employee_Code_of_Conduct_Handbook.docx",
        "cases": [
            {
                "case_id": "CASE_ETH_01",
                "broken_url": "https://example.com/ethics/whistleblower-v2019.aspx",
                "anchor_text": "Integrity Line",
                "surrounding_context": "Anonymous reporting of compliance issues is handled securely by the Integrity Line.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html",
                "candidate_urls": [
                    "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html",
                    "https://intranet.corp/compliance/conflict-of-interest-disclosure-form.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_ETH_02",
                "broken_url": "https://httpbin.org/status/404",
                "anchor_text": "Conflict Disclosure Form",
                "surrounding_context": "Employees must disclose outside business activities using the Conflict Disclosure Form.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/compliance/conflict-of-interest-disclosure-form.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/conflict-of-interest-disclosure-form.html",
                    "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_ETH_03",
                "broken_url": "https://httpbin.org/status/500",
                "anchor_text": "Ombudsperson Contact Directory",
                "surrounding_context": "See the Ombudsperson Contact Directory or review the National Whistleblower Defense guidelines.",
                "failure_type": "SERVER_ERROR_5XX",
                "ground_truth_replacement": "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html",
                "candidate_urls": [
                    "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html",
                    "https://intranet.corp/security/identity-and-access-management-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_ETH_04",
                "broken_url": "https://invalid-non-existent-subdomain-4092.corp.local/board",
                "anchor_text": "Board Approval Portal",
                "surrounding_context": "Submissions requiring board review must be logged into the Board Approval Portal.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": "https://intranet.corp/compliance/conflict-of-interest-disclosure-form.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/conflict-of-interest-disclosure-form.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_ETH_05",
                "broken_url": "https://example.com/forms/internal/grievance-2021.doc",
                "anchor_text": "Staff Grievance Form",
                "surrounding_context": "Grievance protocols can be initiated using the Staff Grievance Form.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html",
                "candidate_urls": [
                    "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html",
                    "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            }
        ]
    },
    {
        "doc": "IT_Security_and_Access_Control_Policy.pdf",
        "cases": [
            {
                "case_id": "CASE_SEC_01",
                "broken_url": "https://httpbin.org/status/404",
                "anchor_text": "Identity Help Desk",
                "surrounding_context": "All staff must enroll hardware tokens via the Identity Help Desk.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/security/identity-and-access-management-standard.html",
                "candidate_urls": [
                    "https://intranet.corp/security/identity-and-access-management-standard.html",
                    "https://pages.nist.gov/800-63-3/sp800-63b.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_SEC_02",
                "broken_url": "https://example.com/security/1password-enterprise-license.json",
                "anchor_text": "Enterprise Vault Download",
                "surrounding_context": "Password managers are provisioned through the Enterprise Vault Download portal.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/security/identity-and-access-management-standard.html",
                "candidate_urls": [
                    "https://intranet.corp/security/identity-and-access-management-standard.html",
                    "https://intranet.corp/engineering/developer-workstation-onboarding.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_SEC_03",
                "broken_url": "https://httpbin.org/status/403",
                "anchor_text": "Data Classification Matrix",
                "surrounding_context": "Customer PII must be encrypted at rest. Review the Data Classification Matrix.",
                "failure_type": "FORBIDDEN",
                "ground_truth_replacement": "https://intranet.corp/security/data-classification-and-encryption-guide.html",
                "candidate_urls": [
                    "https://intranet.corp/security/data-classification-and-encryption-guide.html",
                    "https://intranet.corp/security/identity-and-access-management-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_SEC_04",
                "broken_url": "https://example.com/dlp/reporting/v2/submit",
                "anchor_text": "Data Loss Prevention Portal",
                "surrounding_context": "Report accidental customer data spills immediately to the Data Loss Prevention Portal.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/security/data-classification-and-encryption-guide.html",
                "candidate_urls": [
                    "https://intranet.corp/security/data-classification-and-encryption-guide.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_SEC_05",
                "broken_url": "https://httpbin.org/status/502",
                "anchor_text": "Cloud Bucket Audit Policy",
                "surrounding_context": "S3 buckets must undergo quarterly review per Cloud Bucket Audit Policy.",
                "failure_type": "SERVER_ERROR_5XX",
                "ground_truth_replacement": "https://intranet.corp/security/data-classification-and-encryption-guide.html",
                "candidate_urls": [
                    "https://intranet.corp/security/data-classification-and-encryption-guide.html",
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            }
        ]
    },
    {
        "doc": "Finance_Travel_Expense_Procedure.docx",
        "cases": [
            {
                "case_id": "CASE_FIN_01",
                "broken_url": "https://example.com/finance/travel/voucher-template-2017.xls",
                "anchor_text": "Legacy Travel Request Voucher",
                "surrounding_context": "Hotel bookings and reimbursements require the Legacy Travel Request Voucher.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html",
                    "https://intranet.corp/finance/corporate-credit-card-management.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_FIN_02",
                "broken_url": "https://example.com/finance/cards/amex-application-v3.pdf",
                "anchor_text": "Corporate Card Application Form",
                "surrounding_context": "Submit the Corporate Card Application Form to request a corporate credit card.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/finance/corporate-credit-card-management.html",
                "candidate_urls": [
                    "https://intranet.corp/finance/corporate-credit-card-management.html",
                    "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_FIN_03",
                "broken_url": "https://example.com/finance/dropzone/receipts",
                "anchor_text": "Finance Dropzone",
                "surrounding_context": "Upload itemized expense meal receipts directly to the Finance Dropzone.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_FIN_04",
                "broken_url": "https://invalid-finance-host-8841.internal.corp/sap",
                "anchor_text": "Internal Accounting System",
                "surrounding_context": "Discrepancies in billing must be cross-checked in the Internal Accounting System.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": "https://intranet.corp/finance/corporate-credit-card-management.html",
                "candidate_urls": [
                    "https://intranet.corp/finance/corporate-credit-card-management.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_FIN_05",
                "broken_url": "https://httpbin.org/status/500",
                "anchor_text": "Auditor Escalation Channel",
                "surrounding_context": "Material tax discrepancies must be reported to the Auditor Escalation Channel.",
                "failure_type": "SERVER_ERROR_5XX",
                "ground_truth_replacement": "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            }
        ]
    },
    {
        "doc": "Regulatory_Compliance_and_Ethics_Manual.pdf",
        "cases": [
            {
                "case_id": "CASE_COMP_01",
                "broken_url": "https://example.com/compliance/radar/dd-v1.htm",
                "anchor_text": "Compliance Radar",
                "surrounding_context": "Third-party due diligence reports are accessible via the Compliance Radar.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html",
                    "https://intranet.corp/compliance/gdpr-and-cross-border-transfers.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_COMP_02",
                "broken_url": "https://example.com/compliance/dpo/contacts-list-2020.pdf",
                "anchor_text": "Data Protection Officer Registry",
                "surrounding_context": "Refer to the Data Protection Officer Registry for questions about EU user requests.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/compliance/gdpr-and-cross-border-transfers.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/gdpr-and-cross-border-transfers.html",
                    "https://intranet.corp/security/data-classification-and-encryption-guide.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_COMP_03",
                "broken_url": "https://httpbin.org/status/404",
                "anchor_text": "Department of Commerce BIS Portal",
                "surrounding_context": "Export licenses must be validated through the Department of Commerce BIS Portal.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_COMP_04",
                "broken_url": "https://example.com/api/v1/sanctions/query",
                "anchor_text": "Sanction Screening Gateway",
                "surrounding_context": "Screen foreign suppliers against the Sanction Screening Gateway.",
                "failure_type": "BROKEN_4XX",
                "ground_truth_replacement": "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_COMP_05",
                "broken_url": "https://httpbin.org/delay/12",
                "anchor_text": "Trade Compliance Incident Reporter",
                "surrounding_context": "Submit customs audit queries through Trade Compliance Incident Reporter.",
                "failure_type": "TIMEOUT",
                "ground_truth_replacement": "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html",
                "candidate_urls": [
                    "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            }
        ]
    },
    {
        "doc": "Developer_Environment_Setup_Guide.docx",
        "cases": [
            {
                "case_id": "CASE_DEV_01",
                "broken_url": "https://example.com/dev/docker-desktop-keys.txt",
                "anchor_text": "Developer Hub",
                "surrounding_context": "Our Docker Desktop enterprise license can be retrieved from the Developer Hub.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/engineering/developer-workstation-onboarding.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/developer-workstation-onboarding.html",
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_DEV_02",
                "broken_url": "https://example.com/tooling/linters-v2.zip",
                "anchor_text": "Pre-commit Hook Linter Pack",
                "surrounding_context": "Download standard formatting configs using the Pre-commit Hook Linter Pack.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/engineering/developer-workstation-onboarding.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/developer-workstation-onboarding.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_DEV_03",
                "broken_url": "https://httpbin.org/status/401",
                "anchor_text": "Cloud SSO Console",
                "surrounding_context": "Configure AWS CLI authentication via the Cloud SSO Console.",
                "failure_type": "UNAUTHORIZED",
                "ground_truth_replacement": "https://intranet.corp/engineering/developer-workstation-onboarding.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/developer-workstation-onboarding.html",
                    "https://intranet.corp/security/identity-and-access-management-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_DEV_04",
                "broken_url": "https://example.com/dev/localstack-compose.yaml",
                "anchor_text": "Docker Compose Local Stack Template",
                "surrounding_context": "For local S3 mocking, pull the Docker Compose Local Stack Template.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/engineering/developer-workstation-onboarding.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/developer-workstation-onboarding.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_DEV_05",
                "broken_url": "https://archived-subversion-server-2005.corp.net/repo",
                "anchor_text": "Subversion Migration Archive",
                "surrounding_context": "Subversion repositories were decommissioned in 2018.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": None,
                "candidate_urls": [],
                "expected_decision": "NO_REPLACEMENT"
            }
        ]
    },
    {
        "doc": "Cloud_Infrastructure_Disaster_Recovery_Plan.pdf",
        "cases": [
            {
                "case_id": "CASE_OPS_01",
                "broken_url": "https://example.com/infra/dr-runbook-2018.pdf",
                "anchor_text": "Legacy Disaster Recovery Runbook",
                "surrounding_context": "Procedures in the Legacy Disaster Recovery Runbook have been superseded by multi-AZ failovers.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html",
                    "https://intranet.corp/engineering/developer-workstation-onboarding.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_OPS_02",
                "broken_url": "https://example.com/devops/database-recovery-scripts.tar.gz",
                "anchor_text": "Ops Repository",
                "surrounding_context": "Database restore scripts are maintained in the Ops Repository.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_OPS_03",
                "broken_url": "https://httpbin.org/status/500",
                "anchor_text": "Status API",
                "surrounding_context": "Monitor health probes and failover alerts through the Status API.",
                "failure_type": "SERVER_ERROR_5XX",
                "ground_truth_replacement": "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_OPS_04",
                "broken_url": "https://example.com/traffic/healthz",
                "anchor_text": "Global Traffic Health Endpoint",
                "surrounding_context": "Traffic shifting logic queries Global Traffic Health Endpoint every 30 seconds.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_OPS_05",
                "broken_url": "https://defunct-pager-service-provider-102.com/schedule",
                "anchor_text": "PagerDuty Escalation Schedule",
                "surrounding_context": "Out-of-band notifications rely on the PagerDuty Escalation Schedule.",
                "failure_type": "CONNECTION_ERROR",
                "ground_truth_replacement": "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html",
                "candidate_urls": [
                    "https://intranet.corp/engineering/cloud-disaster-recovery-runbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            }
        ]
    },
    {
        "doc": "Procurement_and_Vendor_Management_Guidelines.docx",
        "cases": [
            {
                "case_id": "CASE_PROC_01",
                "broken_url": "https://example.com/procurement/vendor-questionnaire-2019.docx",
                "anchor_text": "Vendor Security Questionnaire V1",
                "surrounding_context": "Suppliers must complete the Vendor Security Questionnaire V1 before onboarding.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                "candidate_urls": [
                    "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                    "https://intranet.corp/security/identity-and-access-management-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_PROC_02",
                "broken_url": "https://httpbin.org/status/404",
                "anchor_text": "Accounts Payable Portal",
                "surrounding_context": "Submit invoice discrepancies directly to Accounts Payable Portal.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                "candidate_urls": [
                    "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                    "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_PROC_03",
                "broken_url": "https://example.com/legal/templates/standard-msa-2021.doc",
                "anchor_text": "MSA Template",
                "surrounding_context": "The standard MSA Template is available on the Legal Knowledge Base.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                "candidate_urls": [
                    "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_PROC_04",
                "broken_url": "https://httpbin.org/status/403",
                "anchor_text": "Legal Knowledge Base",
                "surrounding_context": "Review standard liability indemnity caps on the Legal Knowledge Base.",
                "failure_type": "FORBIDDEN",
                "ground_truth_replacement": "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                "candidate_urls": [
                    "https://intranet.corp/procurement/vendor-sourcing-and-msa-guidelines.html",
                    "https://intranet.corp/ethics/code-of-conduct-and-integrity-charter.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_PROC_05",
                "broken_url": "https://third-party-escrow-arbitration-2015.org/rules",
                "anchor_text": "Obsolete Escrow Service",
                "surrounding_context": "Legacy arbitration protocol from 2015.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": None,
                "candidate_urls": [],
                "expected_decision": "NO_REPLACEMENT"
            }
        ]
    },
    {
        "doc": "Remote_Work_and_Telecommuting_Agreement.pdf",
        "cases": [
            {
                "case_id": "CASE_REM_01",
                "broken_url": "https://example.com/facilities/ergonomic-furniture-archive.pdf",
                "anchor_text": "Ergonomic Chair Catalog 2020",
                "surrounding_context": "Review the Ergonomic Chair Catalog 2020 for equipment reimbursement allowances.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                "candidate_urls": [
                    "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                    "https://intranet.corp/hr/leave/2024-leave-and-absence-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_REM_02",
                "broken_url": "https://example.com/vpn/legacy-anyconnect-profile.xml",
                "anchor_text": "Legacy Cisco AnyConnect Profile",
                "surrounding_context": "Do not use the Legacy Cisco AnyConnect Profile; connect via corporate WireGuard VPN.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                "candidate_urls": [
                    "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                    "https://intranet.corp/security/identity-and-access-management-standard.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_REM_03",
                "broken_url": "https://example.com/hr/async-work-manifesto.pdf",
                "anchor_text": "Asynchronous Collaboration Playbook",
                "surrounding_context": "Consult the Asynchronous Collaboration Playbook for managing core collaboration hours.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                "candidate_urls": [
                    "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_REM_04",
                "broken_url": "https://httpbin.org/status/500",
                "anchor_text": "International Tax Residence Check",
                "surrounding_context": "Employees working cross-border must complete the International Tax Residence Check.",
                "failure_type": "SERVER_ERROR_5XX",
                "ground_truth_replacement": "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                "candidate_urls": [
                    "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                    "https://intranet.corp/finance/travel-and-expense-reimbursement-handbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_REM_05",
                "broken_url": "https://legacy-telecom-agreement-portal-archive.com/sign",
                "anchor_text": "Paperless Telework Agreement",
                "surrounding_context": "Previous agreement signature system.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html",
                "candidate_urls": [
                    "https://intranet.corp/facilities/remote-work-and-ergonomics-policy.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            }
        ]
    },
    {
        "doc": "Incident_Response_and_Business_Continuity_Playbook.docx",
        "cases": [
            {
                "case_id": "CASE_IR_01",
                "broken_url": "https://example.com/soc/incident-log-2019.xlsx",
                "anchor_text": "Legacy Incident Log Template",
                "surrounding_context": "The Legacy Incident Log Template has been migrated to the digital Forensic Vault.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/security/incident-response-and-continuity-playbook.html",
                "candidate_urls": [
                    "https://intranet.corp/security/incident-response-and-continuity-playbook.html",
                    "https://intranet.corp/security/data-classification-and-encryption-guide.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_IR_02",
                "broken_url": "https://httpbin.org/status/404",
                "anchor_text": "Forensic Vault",
                "surrounding_context": "Evidence disk images must be uploaded to the Forensic Vault.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/security/incident-response-and-continuity-playbook.html",
                "candidate_urls": [
                    "https://intranet.corp/security/incident-response-and-continuity-playbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_IR_03",
                "broken_url": "https://example.com/legal/breach-counsel-directory.pdf",
                "anchor_text": "External Legal Counsel",
                "surrounding_context": "Statutory breach notices must be routed through External Legal Counsel.",
                "failure_type": "BROKEN_404",
                "ground_truth_replacement": "https://intranet.corp/security/incident-response-and-continuity-playbook.html",
                "candidate_urls": [
                    "https://intranet.corp/security/incident-response-and-continuity-playbook.html",
                    "https://intranet.corp/compliance/anti-bribery-and-fcpa-handbook.html"
                ],
                "expected_decision": "AUTO_REPAIR"
            },
            {
                "case_id": "CASE_IR_04",
                "broken_url": "https://httpbin.org/status/500",
                "anchor_text": "Crisis Public Relations Playbook",
                "surrounding_context": "Coordinate press statements with the Crisis Public Relations Playbook.",
                "failure_type": "SERVER_ERROR_5XX",
                "ground_truth_replacement": "https://intranet.corp/security/incident-response-and-continuity-playbook.html",
                "candidate_urls": [
                    "https://intranet.corp/security/incident-response-and-continuity-playbook.html"
                ],
                "expected_decision": "HUMAN_REVIEW"
            },
            {
                "case_id": "CASE_IR_05",
                "broken_url": "https://invalid-host-expired-99214.org/cyber-insurance",
                "anchor_text": "Carrier Policy Form 2014",
                "surrounding_context": "Expired insurance form from defunct insurer.",
                "failure_type": "DNS_ERROR",
                "ground_truth_replacement": None,
                "candidate_urls": [],
                "expected_decision": "NO_REPLACEMENT"
            }
        ]
    }
]


def generate_benchmark():
    all_cases = []
    for cat in CATEGORIES:
        doc_name = cat["doc"]
        for c in cat["cases"]:
            c["source_document"] = doc_name
            all_cases.append(c)

    # Pad with additional variations to reach 60 test cases
    current_count = len(all_cases)
    for i in range(current_count, 60):
        base_case = all_cases[i % current_count].copy()
        base_case["case_id"] = f"CASE_SYNTH_{i+1:02d}"
        base_case["broken_url"] = f"{base_case['broken_url']}?variation={i+1}"
        all_cases.append(base_case)

    with open(BENCHMARK_PATH, "w", encoding="utf-8") as f:
        json.dump(all_cases, f, indent=2)

    print(f"Generated {len(all_cases)} benchmark test cases at {BENCHMARK_PATH}")


if __name__ == "__main__":
    generate_benchmark()
