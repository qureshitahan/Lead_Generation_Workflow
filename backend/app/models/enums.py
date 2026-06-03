"""Status constants and shared vocabularies used across models.

Kept as plain string classes (not DB enums) so values are easy to extend
without migrations during the MVP phase.
"""
from __future__ import annotations


class JobSource:
    BRIGHTDATA = "brightdata"
    APIFY = "apify"
    MANUAL = "manual"


class JobStatus:
    """Lifecycle of a normalized job as it moves through the workflow."""

    NEW = "new"                # just imported + normalized
    REVIEW = "review"          # classified, awaiting human decision
    APPROVED = "approved"      # human approved to pursue
    REJECTED = "rejected"      # human rejected
    MATCHED = "matched"        # at least one candidate matched
    OUTREACH = "outreach"      # outreach in progress
    CLOSED = "closed"          # done / archived


class EmploymentType:
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    OTHER = "other"


class EnrichmentStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ENRICHED = "enriched"
    FAILED = "failed"
    SKIPPED = "skipped"


class EmailStatus:
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    BOUNCED = "bounced"
    NOT_INTERESTED = "not_interested"
    FOLLOW_UP_NEEDED = "follow_up_needed"


class CallStatus:
    QUEUED = "queued"
    APPROVED = "approved"
    DIALING = "dialing"
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    HANDOFF_NEEDED = "handoff_needed"
    MEETING_REQUESTED = "meeting_requested"
    FAILED = "failed"


class ApprovalStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SuppressionScope:
    CONTACT = "contact"
    COMPANY = "company"
    DOMAIN = "domain"
    EMAIL = "email"


class AuditAction:
    """High-level categories for the audit log."""

    IMPORT = "import"
    NORMALIZE = "normalize"
    CLASSIFY_RELEVANCE = "classify_relevance"
    CLASSIFY_EMPLOYER = "classify_employer"
    JOB_APPROVAL = "job_approval"
    ENRICHMENT = "enrichment"
    CONTACT_APPROVAL = "contact_approval"
    MATCH = "match"
    EMAIL_DRAFT = "email_draft"
    EMAIL_APPROVAL = "email_approval"
    EMAIL_SEND = "email_send"
    CALL_SCRIPT = "call_script"
    CALL_APPROVAL = "call_approval"
    CALL_PLACED = "call_placed"
    SUPPRESSION = "suppression"
