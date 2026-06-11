"""Tests for direct-employer vs staffing classification."""
from app.services.classification.direct_employer import classify_direct_employer

SMBc_DESCRIPTION = """
SMBC Group is a top-tier global financial group. The Business Analyst is part of the
Cash Management/Transaction Banking group within Corporate Banking. We are rebuilding
our Corporate Cash Management and Transaction Banking application.
"""

STAFFING_DESCRIPTION = """
Our client is seeking a Software Engineer for a 6-month contract. On behalf of our
client, we are hiring for a fintech startup in NYC. This is a contract staffing role.
"""


def test_smbc_corporate_banking_not_staffing():
    """'rpo' must not match inside 'corporate' (regression for SMBC job)."""
    result = classify_direct_employer(
        company_name="SMBC Group",
        description=SMBc_DESCRIPTION,
        industry="Banking, Financial Services, and IT Services and IT Consulting",
    )
    assert result.is_direct_employer is True
    assert result.is_staffing_or_recruiting is False
    assert "rpo" not in result.explanation.lower()


def test_real_staffing_agency_posting():
    result = classify_direct_employer(
        company_name="Apex Talent Solutions",
        description=STAFFING_DESCRIPTION,
        industry="Staffing and Recruiting",
    )
    assert result.is_staffing_or_recruiting is True
    assert result.is_direct_employer is False


def test_rpo_acronym_still_flags_staffing():
    result = classify_direct_employer(
        company_name="HR Partners",
        description="We provide RPO services to Fortune 500 clients.",
        industry="Human Resources Services",
    )
    assert result.is_staffing_or_recruiting is True


def test_jpmorgan_financial_services_direct():
    result = classify_direct_employer(
        company_name="JPMorganChase",
        description="Join our Corporate Investment Banking team in New York.",
        industry="Financial Services",
    )
    assert result.is_direct_employer is True
    assert result.is_staffing_or_recruiting is False


def test_staffing_company_name():
    result = classify_direct_employer(
        company_name="Robert Half Staffing",
        description="Great opportunity for an analyst.",
        industry="Staffing and Recruiting",
    )
    assert result.is_staffing_or_recruiting is True
