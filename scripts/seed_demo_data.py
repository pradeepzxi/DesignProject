"""Synthetic Demo Data Seeder for Link Integrity Management Framework.

Generates:
- 10 realistic synthetic enterprise documents (5 PDFs, 5 DOCXs)
- 110+ hyperlinks embedded with rich context (anchor text, paragraphs, headings)
- 25+ broken links (404, 410, 500, 503, invalid syntax)
- 12+ redirected links (301, 302, HTTP to HTTPS upgrades)
- 65+ valid links (standards, documentation, public resources)
- 10+ timeout and connection error cases
- Full database records across documents, links, link_context, scan_runs, and audit_logs.
"""

import sys
import os
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pymupdf
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models.document import Document
from backend.app.models.link import Link
from backend.app.models.link_context import LinkContext
from backend.app.models.scan_run import ScanRun
from backend.app.models.audit_log import AuditLog
from backend.app.services.link_context_service import LinkContextService
from backend.app.utils.url_utils import normalize_url

# Ensure target directories exist
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


def get_utc_now():
    return datetime.now(timezone.utc)


# Synthetic Document Definitions
DOCUMENT_SPECS = [
    {
        "filename": "HR_Leave_and_Absence_Policy_2024.pdf",
        "type": "pdf",
        "title": "Enterprise Employee Leave and Absence Policy 2024",
        "sections": [
            {
                "heading": "1.0 Annual and Sick Leave Entitlements",
                "content": (
                    "Employees are granted 25 days of paid annual leave. For statutory sick leave guidelines, "
                    "review the standard statutory sick leave schedule. Inquiries regarding family leave "
                    "must be submitted through the personnel portal."
                ),
                "links": [
                    {
                        "anchor": "statutory sick leave schedule",
                        "url": "https://httpbin.org/status/404",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "personnel portal",
                        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Department of Labor Guidelines",
                        "url": "https://httpbin.org/status/301",
                        "final_url": "https://httpbin.org/get",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                ],
            },
            {
                "heading": "2.0 Sabbatical and Unpaid Leave Application",
                "content": (
                    "Sabbatical applications require VP approval. The legacy application portal at "
                    "the archived leave repository is no longer maintained. Use the updated HR benefits site instead."
                ),
                "links": [
                    {
                        "anchor": "archived leave repository",
                        "url": "https://example.com/archived/hr/leave-system-v1.php",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "updated HR benefits site",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Unpaid Leave Calculation Spreadsheet",
                        "url": "https://httpbin.org/delay/15",
                        "status": "TIMEOUT",
                        "code": None,
                        "type": "timeout",
                    },
                ],
            },
            {
                "heading": "3.0 Public Holidays and Floating Leave",
                "content": (
                    "The national holiday calendar can be synced via the corporate calendar feed. "
                    "Floating holidays must be logged before Q4."
                ),
                "links": [
                    {
                        "anchor": "corporate calendar feed",
                        "url": "http://httpbin.org/redirect-to?url=https://httpbin.org/get",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Holiday Scheduling Standard",
                        "url": "https://en.wikipedia.org/wiki/Public_holiday",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Legacy Payroll Timesheet Link",
                        "url": "https://httpbin.org/status/410",
                        "status": "BROKEN_4XX",
                        "code": 410,
                        "type": "broken",
                    },
                    {
                        "anchor": "State Labor Compliance Index",
                        "url": "https://www.iana.org/domains/reserved",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Benefits Escalation Helpdesk",
                        "url": "https://httpbin.org/status/503",
                        "status": "SERVER_ERROR_5XX",
                        "code": 503,
                        "type": "broken",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Employee_Code_of_Conduct_Handbook.docx",
        "type": "docx",
        "title": "Corporate Code of Conduct and Workplace Ethics Handbook",
        "sections": [
            {
                "heading": "1.0 Workplace Mutual Respect and Anti-Harassment",
                "content": (
                    "Every staff member is entitled to a professional work environment. Our anti-harassment policy "
                    "is detailed in the Global Ethics Charter. Anonymous reporting is handled by the Integrity Line."
                ),
                "links": [
                    {
                        "anchor": "Global Ethics Charter",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Integrity Line",
                        "url": "https://example.com/ethics/whistleblower-v2019.aspx",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Equal Opportunity Employment Guidelines",
                        "url": "http://httpbin.org/status/302",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                ],
            },
            {
                "heading": "2.0 Conflict of Interest and External Engagements",
                "content": (
                    "Employees must disclose outside business activities using the Conflict Disclosure Form. "
                    "Gifts exceeding $100 must be declared in the corporate gifts register."
                ),
                "links": [
                    {
                        "anchor": "Conflict Disclosure Form",
                        "url": "https://httpbin.org/status/404",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "corporate gifts register",
                        "url": "https://www.w3.org/Protocols/rfc2616/rfc2616.html",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Board Approval Portal",
                        "url": "https://invalid-non-existent-subdomain-4092.corp.local/board",
                        "status": "DNS_ERROR",
                        "code": None,
                        "type": "dns_error",
                    },
                ],
            },
            {
                "heading": "3.0 Whistleblower Protection and Reporting Protocol",
                "content": (
                    "Retaliation is strictly prohibited under federal standards. See the Ombudsperson Contact Directory "
                    "or review the National Whistleblower Defense guidelines."
                ),
                "links": [
                    {
                        "anchor": "Ombudsperson Contact Directory",
                        "url": "https://httpbin.org/status/500",
                        "status": "SERVER_ERROR_5XX",
                        "code": 500,
                        "type": "broken",
                    },
                    {
                        "anchor": "National Whistleblower Defense guidelines",
                        "url": "https://www.python.org",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Ethics Advisory Committee",
                        "url": "http://httpbin.org/redirect/1",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Staff Grievance Form",
                        "url": "https://example.com/forms/internal/grievance-2021.doc",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Corporate Conduct Standards Reference",
                        "url": "https://en.wikipedia.org/wiki/Code_of_conduct",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
        ],
    },
    {
        "filename": "IT_Security_and_Access_Control_Policy.pdf",
        "type": "pdf",
        "title": "Enterprise Information Security and Access Control Architecture",
        "sections": [
            {
                "heading": "1.0 Multi-Factor Authentication Requirements",
                "content": (
                    "All staff must enroll hardware tokens via the MFA Enrollment Portal. Security keys must comply with "
                    "the FIDO2 Alliance Standards. For backup SMS passcodes, consult the Identity Help Desk."
                ),
                "links": [
                    {
                        "anchor": "MFA Enrollment Portal",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "FIDO2 Alliance Standards",
                        "url": "https://fidoalliance.org/fido2/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Identity Help Desk",
                        "url": "https://httpbin.org/status/404",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Password Hygiene and Rotation Protocols",
                "content": (
                    "Passwords must meet NIST 800-63B standards. Check the NIST Special Publication repository. "
                    "Password managers are provisioned through the Enterprise Vault Download."
                ),
                "links": [
                    {
                        "anchor": "NIST Special Publication repository",
                        "url": "https://pages.nist.gov/800-63-3/sp800-63b.html",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Enterprise Vault Download",
                        "url": "https://example.com/security/1password-enterprise-license.json",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Legacy Active Directory Self-Service",
                        "url": "http://httpbin.org/status/301",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                ],
            },
            {
                "heading": "3.0 Data Classification and Confidentiality",
                "content": (
                    "Customer PII must be encrypted at rest. Review the Data Classification Matrix and the "
                    "Cryptographic Standards Guide. Report accidental spills immediately."
                ),
                "links": [
                    {
                        "anchor": "Data Classification Matrix",
                        "url": "https://httpbin.org/status/403",
                        "status": "FORBIDDEN",
                        "code": 403,
                        "type": "broken",
                    },
                    {
                        "anchor": "Cryptographic Standards Guide",
                        "url": "https://en.wikipedia.org/wiki/Advanced_Encryption_Standard",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Data Loss Prevention Portal",
                        "url": "https://example.com/dlp/reporting/v2/submit",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Cloud Bucket Audit Policy",
                        "url": "https://httpbin.org/status/502",
                        "status": "SERVER_ERROR_5XX",
                        "code": 502,
                        "type": "broken",
                    },
                    {
                        "anchor": "OWASP Top Ten Security Reference",
                        "url": "https://owasp.org/www-project-top-ten/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Finance_Travel_Expense_Procedure.docx",
        "type": "docx",
        "title": "Corporate Travel, Entertainment, and Expense Reimbursement Procedure",
        "sections": [
            {
                "heading": "1.0 Per Diem Rates and Lodging Thresholds",
                "content": (
                    "Domestic travel adheres to federal per diem limits. Consult the GSA Per Diem Table. "
                    "Hotel bookings must be executed through Concur Travel."
                ),
                "links": [
                    {
                        "anchor": "GSA Per Diem Table",
                        "url": "https://www.gsa.gov/travel/plan-book/per-diem-rates",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Concur Travel",
                        "url": "http://httpbin.org/redirect-to?url=https://httpbin.org/get",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Legacy Travel Request Voucher",
                        "url": "https://example.com/finance/travel/voucher-template-2017.xls",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Corporate Credit Card Utilization",
                "content": (
                    "Corporate Amex statements must be reconciled monthly via the Card Reconciliation Gateway. "
                    "Personal expenditures on corporate cards will trigger an audit flag."
                ),
                "links": [
                    {
                        "anchor": "Card Reconciliation Gateway",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Corporate Card Application Form",
                        "url": "https://example.com/finance/cards/amex-application-v3.pdf",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Currency Conversion Calculator",
                        "url": "https://www.xe.com",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
            {
                "heading": "3.0 Meal and Entertainment Receipts",
                "content": (
                    "Itemized receipts are required for all meals above $25. Review the IRS Business Expense Guide "
                    "and submit digital scans to the Finance Dropzone."
                ),
                "links": [
                    {
                        "anchor": "IRS Business Expense Guide",
                        "url": "https://httpbin.org/status/301",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Finance Dropzone",
                        "url": "https://example.com/finance/dropzone/receipts",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Internal Accounting System",
                        "url": "https://invalid-finance-host-8841.internal.corp/sap",
                        "status": "DNS_ERROR",
                        "code": None,
                        "type": "dns_error",
                    },
                    {
                        "anchor": "Travel Safety Advisory Board",
                        "url": "https://travel.state.gov",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Auditor Escalation Channel",
                        "url": "https://httpbin.org/status/500",
                        "status": "SERVER_ERROR_5XX",
                        "code": 500,
                        "type": "broken",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Regulatory_Compliance_and_Ethics_Manual.pdf",
        "type": "pdf",
        "title": "Global Regulatory Compliance, Anti-Bribery, and Ethics Manual",
        "sections": [
            {
                "heading": "1.0 Foreign Corrupt Practices Act (FCPA) Compliance",
                "content": (
                    "Employees and international partners must adhere strictly to the FCPA Enforcement Guide. "
                    "Third-party due diligence reports are accessible via the Compliance Radar."
                ),
                "links": [
                    {
                        "anchor": "FCPA Enforcement Guide",
                        "url": "https://www.justice.gov/criminal/criminal-fraud/foreign-corrupt-practices-act",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Compliance Radar",
                        "url": "https://example.com/compliance/radar/dd-v1.htm",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "International Transparency Index",
                        "url": "http://httpbin.org/status/302",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                ],
            },
            {
                "heading": "2.0 GDPR and Cross-Border Data Transfers",
                "content": (
                    "Data transfers outside the EEA require Standard Contractual Clauses (SCCs). Refer to the "
                    "European Commission SCC Templates and the Data Protection Officer Registry."
                ),
                "links": [
                    {
                        "anchor": "European Commission SCC Templates",
                        "url": "https://ec.europa.eu/info/law/law-topic/data-protection_en",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Data Protection Officer Registry",
                        "url": "https://example.com/compliance/dpo/contacts-list-2020.pdf",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "GDPR Compliance Checkpoint",
                        "url": "https://gdpr-info.eu/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
            {
                "heading": "3.0 Trade Sanctions and Export Controls",
                "content": (
                    "Screen all foreign counterparties against the OFAC Specially Designated Nationals List. "
                    "Export licenses must be validated through the Department of Commerce BIS Portal."
                ),
                "links": [
                    {
                        "anchor": "OFAC Specially Designated Nationals List",
                        "url": "https://ofac.treasury.gov/specially-designated-nationals-list-data-formats-data-schemas",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Department of Commerce BIS Portal",
                        "url": "https://httpbin.org/status/404",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Sanction Screening Gateway",
                        "url": "https://example.com/api/v1/sanctions/query",
                        "status": "BROKEN_4XX",
                        "code": 400,
                        "type": "broken",
                    },
                    {
                        "anchor": "Export Control Regulatory Matrix",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Trade Compliance Incident Reporter",
                        "url": "https://httpbin.org/delay/12",
                        "status": "TIMEOUT",
                        "code": None,
                        "type": "timeout",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Developer_Environment_Setup_Guide.docx",
        "type": "docx",
        "title": "Software Engineering Developer Environment Setup Guide",
        "sections": [
            {
                "heading": "1.0 Toolchain Installation and Prerequisites",
                "content": (
                    "Engineers must install Python 3.11+ from python.org and Node.js LTS from the official repository. "
                    "Our Docker Desktop enterprise license can be retrieved from the Developer Hub."
                ),
                "links": [
                    {
                        "anchor": "Python 3.11+ from python.org",
                        "url": "https://www.python.org/downloads/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Node.js LTS",
                        "url": "https://nodejs.org/en/download",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Developer Hub",
                        "url": "https://example.com/dev/docker-desktop-keys.txt",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Git Workflow and Pre-Commit Hooks",
                "content": (
                    "All repositories require signing commits. Follow the Git Signing Tutorial. "
                    "Internal code reviews take place on our GitHub Enterprise Instance."
                ),
                "links": [
                    {
                        "anchor": "Git Signing Tutorial",
                        "url": "https://docs.github.com/en/authentication/managing-commit-signature-verification",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "GitHub Enterprise Instance",
                        "url": "http://httpbin.org/status/301",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Pre-commit Hook Linter Pack",
                        "url": "https://example.com/tooling/linters-v2.zip",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "3.0 Cloud Sandbox and Local Kubernetes Setup",
                "content": (
                    "Developers receive a personal AWS Sandbox. Configure AWS CLI via the Cloud SSO Console. "
                    "For Minikube and local cluster instructions, read the Kubernetes Documentation."
                ),
                "links": [
                    {
                        "anchor": "Cloud SSO Console",
                        "url": "https://httpbin.org/status/401",
                        "status": "UNAUTHORIZED",
                        "code": 401,
                        "type": "broken",
                    },
                    {
                        "anchor": "Kubernetes Documentation",
                        "url": "https://kubernetes.io/docs/home/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Terraform Module Registry",
                        "url": "https://registry.terraform.io/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Docker Compose Local Stack Template",
                        "url": "https://example.com/dev/localstack-compose.yaml",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Engineering Architecture Decision Records",
                        "url": "http://httpbin.org/redirect-to?url=https://httpbin.org/get",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Cloud_Infrastructure_Disaster_Recovery_Plan.pdf",
        "type": "pdf",
        "title": "Cloud Infrastructure Resilience and Disaster Recovery Playbook",
        "sections": [
            {
                "heading": "1.0 Recovery Time Objective (RTO) and RPO Targets",
                "content": (
                    "Critical services have an RTO of 1 hour and RPO of 15 minutes. High-availability architecture "
                    "is documented in the AWS Well-Architected Reliability Pillar. "
                    "Failover drills are coordinated on the Incident Dashboard."
                ),
                "links": [
                    {
                        "anchor": "AWS Well-Architected Reliability Pillar",
                        "url": "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Incident Dashboard",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Legacy Disaster Recovery Runbook",
                        "url": "https://example.com/infra/dr-runbook-2018.pdf",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Database Backup Replication and Snapshotting",
                "content": (
                    "PostgreSQL snapshots are replicated across secondary availability zones. Monitor replication lag "
                    "using Prometheus Metrics Portal. Restore scripts are maintained in the Ops Repository."
                ),
                "links": [
                    {
                        "anchor": "Prometheus Metrics Portal",
                        "url": "http://httpbin.org/status/301",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Ops Repository",
                        "url": "https://example.com/devops/database-recovery-scripts.tar.gz",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "PostgreSQL Documentation",
                        "url": "https://www.postgresql.org/docs/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
            {
                "heading": "3.0 DNS Failover and Traffic Shifting",
                "content": (
                    "Route53 health checks trigger automated global DNS switching. Read the Cloudflare DDoS Mitigation "
                    "protocols and test health probe endpoints through the Status API."
                ),
                "links": [
                    {
                        "anchor": "Cloudflare DDoS Mitigation",
                        "url": "https://www.cloudflare.com/ddos/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Status API",
                        "url": "https://httpbin.org/status/500",
                        "status": "SERVER_ERROR_5XX",
                        "code": 500,
                        "type": "broken",
                    },
                    {
                        "anchor": "Global Traffic Health Endpoint",
                        "url": "https://example.com/traffic/healthz",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Multi-Region VPC Peering Guide",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "On-Call PagerDuty Escalation Schedule",
                        "url": "http://httpbin.org/redirect/2",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Procurement_and_Vendor_Management_Guidelines.docx",
        "type": "docx",
        "title": "Corporate Procurement, Vendor Evaluation, and Contract Sourcing Guidelines",
        "sections": [
            {
                "heading": "1.0 Supplier Onboarding and Risk Assessment",
                "content": (
                    "Suppliers exceeding $50k annual spend must complete the SOC2 Compliance Review. "
                    "Vendors must register via the Coupa Supplier Portal."
                ),
                "links": [
                    {
                        "anchor": "SOC2 Compliance Review",
                        "url": "https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Coupa Supplier Portal",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Vendor Security Questionnaire V1",
                        "url": "https://example.com/procurement/vendor-questionnaire-2019.docx",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Purchase Orders and Authorization Matrix",
                "content": (
                    "PO thresholds require managerial sign-off. Refer to the Procurement Delegation of Authority "
                    "chart. Submit invoice discrepancies directly to Accounts Payable."
                ),
                "links": [
                    {
                        "anchor": "Procurement Delegation of Authority",
                        "url": "http://httpbin.org/status/301",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Accounts Payable Portal",
                        "url": "https://httpbin.org/status/404",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Uniform Commercial Code Guidelines",
                        "url": "https://www.law.cornell.edu/ucc",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
            {
                "heading": "3.0 Master Services Agreement (MSA) Negotiations",
                "content": (
                    "Legal must approve liability caps under Section 8. The standard MSA Template is available on "
                    "the Legal Knowledge Base. Non-disclosure agreements must be executed on DocuSign."
                ),
                "links": [
                    {
                        "anchor": "MSA Template",
                        "url": "https://example.com/legal/templates/standard-msa-2021.doc",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Legal Knowledge Base",
                        "url": "https://httpbin.org/status/403",
                        "status": "FORBIDDEN",
                        "code": 403,
                        "type": "broken",
                    },
                    {
                        "anchor": "DocuSign Electronic Signature Portal",
                        "url": "https://www.docusign.com",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Vendor Contract Expiration Radar",
                        "url": "http://httpbin.org/redirect/1",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Procurement Dispute Resolution Protocol",
                        "url": "https://www.adr.org",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Remote_Work_and_Telecommuting_Agreement.pdf",
        "type": "pdf",
        "title": "Enterprise Telecommuting, Remote Work, and Ergonomic Policy",
        "sections": [
            {
                "heading": "1.0 Home Office Ergonomics and Stipend",
                "content": (
                    "Eligible employees receive an annual $500 equipment stipend. Review the OSHA Computer Workstation "
                    "Ergonomics Guide. Stipend reimbursements are processed via Expensify."
                ),
                "links": [
                    {
                        "anchor": "OSHA Computer Workstation Ergonomics Guide",
                        "url": "https://www.osha.gov/etools/computer-workstations",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Expensify Stipend Portal",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Ergonomic Chair Catalog 2020",
                        "url": "https://example.com/facilities/ergonomic-furniture-archive.pdf",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Secure Home Wi-Fi and VPN Connectivity",
                "content": (
                    "Remote devices must not use unsecured public Wi-Fi. Always connect to the Corporate WireGuard VPN. "
                    "For home router security recommendations, see the FTC Home Network Guidance."
                ),
                "links": [
                    {
                        "anchor": "Corporate WireGuard VPN",
                        "url": "http://httpbin.org/status/301",
                        "status": "REDIRECT",
                        "code": 301,
                        "type": "redirect",
                    },
                    {
                        "anchor": "FTC Home Network Guidance",
                        "url": "https://consumer.ftc.gov/articles/how-secure-your-home-wi-fi-network",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Legacy Cisco AnyConnect Profile",
                        "url": "https://example.com/vpn/legacy-anyconnect-profile.xml",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "3.0 Working Across Time Zones and Core Hours",
                "content": (
                    "Core collaboration hours are 10 AM to 3 PM EST. Use the World Time Clock to coordinate "
                    "cross-region meetings. Document asynchronous updates in Notion Workspace."
                ),
                "links": [
                    {
                        "anchor": "World Time Clock",
                        "url": "https://www.timeanddate.com/worldclock/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Notion Workspace",
                        "url": "https://www.notion.so",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Asynchronous Collaboration Playbook",
                        "url": "https://example.com/hr/async-work-manifesto.pdf",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "International Tax Residence Check",
                        "url": "https://httpbin.org/status/500",
                        "status": "SERVER_ERROR_5XX",
                        "code": 500,
                        "type": "broken",
                    },
                    {
                        "anchor": "Telecommuting Agreement Sign-off",
                        "url": "https://httpbin.org/status/200",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
        ],
    },
    {
        "filename": "Incident_Response_and_Business_Continuity_Playbook.docx",
        "type": "docx",
        "title": "Cybersecurity Incident Response and Critical Operations Continuity Playbook",
        "sections": [
            {
                "heading": "1.0 Incident Severity Classification (SEV 1 - SEV 4)",
                "content": (
                    "SEV-1 security events involve active data exfiltration. Consult the CISA Cyber Incident Response Guide. "
                    "The War Room Bridge is hosted on the Secure Zoom Facility."
                ),
                "links": [
                    {
                        "anchor": "CISA Cyber Incident Response Guide",
                        "url": "https://www.cisa.gov/cyber-incident-response",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Secure Zoom Facility",
                        "url": "http://httpbin.org/status/302",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Legacy Incident Log Template",
                        "url": "https://example.com/soc/incident-log-2019.xlsx",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                ],
            },
            {
                "heading": "2.0 Containment, Eradication, and Forensics",
                "content": (
                    "Isolate compromised VM instances immediately. Refer to the SANS Incident Handler's Handbook. "
                    "Evidence disk images must be uploaded to the Forensic Vault."
                ),
                "links": [
                    {
                        "anchor": "SANS Incident Handler's Handbook",
                        "url": "https://www.sans.org/white-papers/33901/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Forensic Vault",
                        "url": "https://httpbin.org/status/404",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Memory Forensics Volatility Framework",
                        "url": "https://volatilityfoundation.org/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                ],
            },
            {
                "heading": "3.0 Post-Incident Retrospective and Regulatory Notification",
                "content": (
                    "Post-mortems are published within 72 hours. Check the Blameless Post-Mortem Guidelines. "
                    "Statutory breach notices must be routed through External Legal Counsel."
                ),
                "links": [
                    {
                        "anchor": "Blameless Post-Mortem Guidelines",
                        "url": "https://sre.google/sre-book/postmortem-culture/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "External Legal Counsel",
                        "url": "https://example.com/legal/breach-counsel-directory.pdf",
                        "status": "BROKEN_404",
                        "code": 404,
                        "type": "broken",
                    },
                    {
                        "anchor": "Cyber Insurance Carrier Notice Form",
                        "url": "http://httpbin.org/redirect/1",
                        "status": "REDIRECT",
                        "code": 302,
                        "type": "redirect",
                    },
                    {
                        "anchor": "Threat Intelligence Feed (MISP)",
                        "url": "https://www.misp-project.org/",
                        "status": "VALID",
                        "code": 200,
                        "type": "valid",
                    },
                    {
                        "anchor": "Crisis Public Relations Playbook",
                        "url": "https://httpbin.org/status/500",
                        "status": "SERVER_ERROR_5XX",
                        "code": 500,
                        "type": "broken",
                    },
                ],
            },
        ],
    },
]


def create_synthetic_pdf(spec: dict, filepath: Path):
    """Generate a valid, structured PDF document with PyMuPDF."""
    doc = pymupdf.open()
    doc.set_metadata({
        "title": spec["title"],
        "author": "Enterprise Systems Governance",
        "subject": "Link Integrity Research Demo Dataset",
    })

    # Page 1: Cover and Intro
    page = doc.new_page(width=595, height=842)  # A4
    y = 50

    # Title
    page.insert_text(
        pymupdf.Point(50, y),
        spec["title"],
        fontsize=16,
        fontname="helv",
        color=(0.1, 0.2, 0.5),
    )
    y += 40

    page_num = 1
    for sec_idx, sec in enumerate(spec["sections"]):
        if y > 700:
            page = doc.new_page(width=595, height=842)
            page_num += 1
            y = 50

        # Section Heading
        page.insert_text(
            pymupdf.Point(50, y),
            sec["heading"],
            fontsize=12,
            fontname="helv",
            color=(0.15, 0.15, 0.15),
        )
        y += 25

        # Section Content
        rect = pymupdf.Rect(50, y, 545, y + 60)
        page.insert_textbox(rect, sec["content"], fontsize=10, fontname="helv")
        y += 75

        # Insert Links with Annotations
        for link in sec["links"]:
            if y > 750:
                page = doc.new_page(width=595, height=842)
                page_num += 1
                y = 50

            anchor = f"Reference: {link['anchor']}"
            link_rect = pymupdf.Rect(50, y - 10, 500, y + 5)

            # Insert visible link text
            page.insert_text(
                pymupdf.Point(50, y),
                anchor,
                fontsize=9,
                fontname="helv",
                color=(0.0, 0.35, 0.75),
            )

            # Add interactive PDF link annotation
            page.insert_link({
                "kind": pymupdf.LINK_URI,
                "from": link_rect,
                "uri": link["url"],
            })
            y += 22

        y += 20

    doc.save(filepath)
    doc.close()


def add_hyperlink_to_docx(paragraph, url, text, color="004B91", underline=True):
    """Add a functioning XML hyperlink to a python-docx paragraph."""
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    if color:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), color)
        rPr.append(c)

    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

    new_run.append(rPr)
    text_elem = OxmlElement("w:t")
    text_elem.text = text
    new_run.append(text_elem)
    hyperlink.append(new_run)

    paragraph._element.append(hyperlink)


def create_synthetic_docx(spec: dict, filepath: Path):
    """Generate a valid, structured Word DOCX document with python-docx."""
    doc = docx.Document()
    doc.core_properties.title = spec["title"]
    doc.core_properties.author = "Enterprise Document Repository Service"

    # Title
    title_p = doc.add_heading(spec["title"], level=0)
    title_p.runs[0].font.color.rgb = RGBColor(16, 44, 87)

    for sec in spec["sections"]:
        doc.add_heading(sec["heading"], level=1)
        doc.add_paragraph(sec["content"])

        for link in sec["links"]:
            p = doc.add_paragraph()
            p.add_run("External Resource: ").bold = True
            add_hyperlink_to_docx(p, link["url"], link["anchor"])

    doc.save(filepath)


def seed_database():
    """Seed documents, parse links, run initial validation, and build audit trail."""
    print("=" * 70)
    print("Seeding Synthetic Enterprise Documents & Links for Research Platform")
    print("=" * 70)

    # Initialize tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Clear existing data for clean reproducible run
        db.query(AuditLog).delete()
        db.query(LinkContext).delete()
        db.query(Link).delete()
        db.query(ScanRun).delete()
        db.query(Document).delete()
        db.commit()

        total_docs_created = 0
        total_links_created = 0
        total_broken_created = 0
        total_redirect_created = 0
        total_valid_created = 0

        for doc_idx, spec in enumerate(DOCUMENT_SPECS):
            filename = spec["filename"]
            filepath = settings.DOCUMENTS_DIR / filename

            # 1. Generate Physical Document File
            if spec["type"] == "pdf":
                create_synthetic_pdf(spec, filepath)
            else:
                create_synthetic_docx(spec, filepath)

            file_size = filepath.stat().st_size
            upload_time = get_utc_now() - timedelta(days=random.randint(1, 30), hours=random.randint(1, 12))

            # 2. Register Document
            doc = Document(
                filename=filename,
                file_type=spec["type"],
                file_size=file_size,
                upload_timestamp=upload_time,
                version=1,
                processing_status="COMPLETED",
                document_title=spec["title"],
                storage_path=str(filepath),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            total_docs_created += 1

            AuditLog_doc = AuditLog(
                document_id=doc.document_id,
                action_type="DOCUMENT_UPLOADED",
                status="SUCCESS",
                reason=f"Ingested {filename} ({file_size} bytes)",
                timestamp=upload_time,
                actor="SYSTEM_SEEDER",
            )
            db.add(AuditLog_doc)

            # 3. Create Links & Contexts
            doc_links = []
            valid_count = 0
            broken_count = 0
            redirect_count = 0
            failed_count = 0

            scan_start_time = upload_time + timedelta(minutes=5)

            for sec_idx, sec in enumerate(spec["sections"]):
                heading = sec["heading"]
                for link_idx, link_info in enumerate(sec["links"]):
                    orig_url = link_info["url"]
                    try:
                        norm_url = normalize_url(orig_url)
                    except Exception:
                        norm_url = orig_url

                    status = link_info["status"]
                    code = link_info.get("code")
                    final_url = link_info.get("final_url", orig_url if status != "REDIRECT" else orig_url.replace("http://", "https://"))
                    resp_time = round(random.uniform(45.0, 380.0), 2) if status != "TIMEOUT" else 10000.0
                    content_type = "text/html; charset=utf-8" if status in ["VALID", "REDIRECT"] else None
                    error_msg = None

                    if status == "BROKEN_404":
                        error_msg = "HTTP 404: Not Found on remote server"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "BROKEN_4XX":
                        error_msg = f"HTTP {code}: Client Error"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "SERVER_ERROR_5XX":
                        error_msg = f"HTTP {code}: Internal Server Error"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "TIMEOUT":
                        error_msg = "Connection timed out after 10.0 seconds"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "DNS_ERROR":
                        error_msg = "DNS resolution failed: Hostname does not exist"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "FORBIDDEN":
                        error_msg = "HTTP 403: Forbidden - Access denied"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "UNAUTHORIZED":
                        error_msg = "HTTP 401: Unauthorized - Authentication required"
                        broken_count += 1
                        total_broken_created += 1
                    elif status == "REDIRECT":
                        redirect_count += 1
                        total_redirect_created += 1
                    elif status == "VALID":
                        valid_count += 1
                        total_valid_created += 1
                    else:
                        failed_count += 1

                    check_time = scan_start_time + timedelta(seconds=random.randint(10, 180))

                    page_no = (sec_idx + 1) if spec["type"] == "pdf" else None
                    loc_desc = (
                        f"Page {page_no}, Section '{heading}'"
                        if page_no
                        else f"Section '{heading}', Resource {link_idx + 1}"
                    )

                    db_link = Link(
                        document_id=doc.document_id,
                        original_url=orig_url,
                        normalized_url=norm_url,
                        status=status,
                        status_code=code,
                        final_url=final_url,
                        response_time_ms=resp_time,
                        content_type=content_type,
                        last_checked=check_time,
                        error_message=error_msg,
                        page_number=page_no,
                        location_description=loc_desc,
                    )
                    db.add(db_link)
                    db.commit()
                    db.refresh(db_link)

                    # Build Context
                    ctx = LinkContextService.build_structured_context(
                        url=norm_url,
                        anchor_text=link_info["anchor"],
                        paragraph_text=sec["content"],
                        section_heading=heading,
                        document_title=spec["title"],
                    )

                    db_context = LinkContext(
                        link_id=db_link.link_id,
                        anchor_text=ctx["anchor_text"],
                        surrounding_text=ctx["surrounding_text"],
                        paragraph_text=ctx["paragraph_text"],
                        section_heading=ctx["section_heading"],
                        document_title=ctx["document_title"],
                        url_tokens=ctx["url_tokens"],
                        keywords=ctx["keywords"],
                    )
                    db.add(db_context)

                    # Audit trail for extraction and validation
                    db.add(AuditLog(
                        document_id=doc.document_id,
                        link_id=db_link.link_id,
                        action_type="LINK_EXTRACTED",
                        old_url=orig_url,
                        status="PENDING",
                        timestamp=upload_time + timedelta(seconds=1),
                        reason=f"Extracted from {loc_desc}",
                        actor="SYSTEM",
                    ))

                    db.add(AuditLog(
                        document_id=doc.document_id,
                        link_id=db_link.link_id,
                        action_type="LINK_VALIDATED",
                        old_url=orig_url,
                        new_url=final_url if final_url != orig_url else None,
                        status=status,
                        timestamp=check_time,
                        reason=error_msg or f"HTTP {code}",
                        actor="SYSTEM",
                    ))

                    if status in ["BROKEN_404", "BROKEN_4XX", "SERVER_ERROR_5XX", "TIMEOUT", "DNS_ERROR", "FORBIDDEN", "UNAUTHORIZED"]:
                        db.add(AuditLog(
                            document_id=doc.document_id,
                            link_id=db_link.link_id,
                            action_type="LINK_BROKEN",
                            old_url=orig_url,
                            status=status,
                            timestamp=check_time,
                            reason=error_msg,
                            actor="SYSTEM",
                        ))
                    elif status == "REDIRECT":
                        db.add(AuditLog(
                            document_id=doc.document_id,
                            link_id=db_link.link_id,
                            action_type="LINK_REDIRECTED",
                            old_url=orig_url,
                            new_url=final_url,
                            status="REDIRECT",
                            timestamp=check_time,
                            reason="Permanent or temporary HTTP redirect target",
                            actor="SYSTEM",
                        ))

                    total_links_created += 1

            # 4. Scan Run Record
            total_doc_links = valid_count + broken_count + redirect_count + failed_count
            scan_run = ScanRun(
                document_id=doc.document_id,
                started_at=scan_start_time,
                completed_at=scan_start_time + timedelta(seconds=len(spec["sections"]) * 15),
                total_links=total_doc_links,
                valid_links=valid_count,
                broken_links=broken_count,
                redirected_links=redirect_count,
                failed_links=failed_count,
                scan_status="COMPLETED",
            )
            db.add(scan_run)

            db.add(AuditLog(
                document_id=doc.document_id,
                action_type="SCAN_COMPLETED",
                status="COMPLETED",
                timestamp=scan_run.completed_at,
                reason=f"Scan finished: {valid_count} valid, {broken_count} broken, {redirect_count} redirected",
                actor="SYSTEM",
            ))

            db.commit()
            print(f"[{doc_idx+1}/10] Created Document: {filename} ({total_doc_links} links: {valid_count} valid, {broken_count} broken, {redirect_count} redirect)")

        print("-" * 70)
        print("SEEDING SUMMARY:")
        print(f"Total Synthetic Documents: {total_docs_created}")
        print(f"Total Hyperlinks:          {total_links_created}")
        print(f"  - Valid Links:           {total_valid_created}")
        print(f"  - Broken Links:          {total_broken_created}")
        print(f"  - Redirects:             {total_redirect_created}")
        print("Database seeded successfully with research-grade telemetry!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
