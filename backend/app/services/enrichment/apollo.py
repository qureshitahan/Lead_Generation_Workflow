"""Apollo.io enrichment provider (live integration).

Endpoints used (all authenticated with the `x-api-key` header):
  * GET  /organizations/enrich        -> firmographics by domain (consumes 1 credit)
  * POST /mixed_companies/search      -> find a company by name (when no domain)
  * POST /mixed_people/api_search     -> find contacts by title + domain
                                         (NOTE: requires a *master* API key; the
                                         search response does NOT include emails)

Docs:
  https://docs.apollo.io/reference/organization-enrichment
  https://docs.apollo.io/reference/organization-search
  https://docs.apollo.io/reference/people-api-search

Design notes:
  * Company enrichment works with a normal API key. If we have no domain we first
    resolve one via Organization Search by name.
  * Contact discovery (People Search) needs a master key. On a non-master/trial
    key Apollo returns a clear error; we degrade gracefully (return no contacts)
    instead of failing the whole enrichment.
  * We never reveal personal emails/phones by default (that burns credits); this
    is gated behind APOLLO_REVEAL_PERSONAL_EMAILS.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import resolve_apollo_phone_webhook_url, settings
from app.services.enrichment.base import (
    EnrichmentContact,
    EnrichmentProvider,
    EnrichmentResult,
)
from app.services.enrichment.stub import StubEnrichmentProvider

logger = logging.getLogger(__name__)

APOLLO_BASE_URL = "https://api.apollo.io/api/v1"
REQUEST_TIMEOUT = 40.0


class ApolloEnrichmentProvider(EnrichmentProvider):
    name = "apollo"

    def __init__(self) -> None:
        self.api_key = settings.apollo_api_key
        self.base_url = settings.apollo_base_url or APOLLO_BASE_URL
        self._fallback = StubEnrichmentProvider()

    # --- public interface ---------------------------------------------------

    def enrich_company(
        self,
        company_name: str,
        *,
        linkedin_url: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> EnrichmentResult:
        if not self.api_key:
            result = self._fallback.enrich_company(
                company_name, linkedin_url=linkedin_url, domain=domain
            )
            result.source = "apollo (stub fallback: no API key)"
            return result

        org: Optional[Dict[str, Any]] = None

        # 1. Prefer a direct enrich-by-domain when we already have one.
        if domain:
            org = self._enrich_by_domain(domain)

        # 2. Otherwise (or if the domain lookup found nothing) search by name.
        if org is None and company_name:
            org = self._search_company_by_name(company_name)
            # If search gave us a domain, enrich to get the full firmographic set.
            found_domain = (org or {}).get("primary_domain")
            if org is not None and found_domain:
                enriched = self._enrich_by_domain(found_domain)
                if enriched:
                    org = enriched

        if not org:
            return EnrichmentResult(
                found=False,
                source="apollo (no match)",
            )

        return self._map_organization(org)

    def find_contacts(
        self,
        company_name: str,
        *,
        domain: Optional[str] = None,
        target_titles: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[EnrichmentContact]:
        if not self.api_key:
            return self._fallback.find_contacts(
                company_name, domain=domain, target_titles=target_titles, limit=limit
            )

        # People Search keys on the company domain. Without one we cannot reliably
        # scope the search, so skip rather than return noise.
        if not domain:
            logger.info("Apollo find_contacts skipped: no domain for %s", company_name)
            return []

        per_page = limit if limit is not None else settings.apollo_contacts_per_company
        per_page = max(1, min(per_page, settings.apollo_contacts_per_company))

        # Tiered search so we return useful people for ANY company, not just
        # tech firms. Stop at the first tier that yields results.
        people = self._people_search(
            domain, per_page=per_page, person_titles=list(target_titles)[:50] if target_titles else None
        )
        if not people:
            people = self._people_search(
                domain,
                per_page=per_page,
                seniorities=[
                    "owner",
                    "founder",
                    "c_suite",
                    "partner",
                    "vp",
                    "head",
                    "director",
                    "manager",
                ],
            )
        if not people:
            people = self._people_search(domain, per_page=per_page)

        mapped = [self._map_person(p, domain=domain) for p in people if isinstance(p, dict)]
        return mapped[:per_page] if limit is not None else mapped

    def _people_search(
        self,
        domain: str,
        *,
        per_page: Optional[int] = None,
        person_titles: Optional[List[str]] = None,
        seniorities: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """One People Search call scoped to a company domain. Returns raw people."""
        page_size = per_page if per_page is not None else settings.apollo_contacts_per_company
        payload: Dict[str, Any] = {
            "q_organization_domains_list": [domain],
            "page": 1,
            "per_page": max(1, min(page_size, settings.apollo_contacts_per_company)),
        }
        if person_titles:
            payload["person_titles"] = person_titles
        if seniorities:
            payload["person_seniorities"] = seniorities

        data = self._post("/mixed_people/api_search", payload, soft_fail=True)
        if data is None:
            return []
        people = data.get("people") or data.get("contacts") or []
        return [p for p in people if isinstance(p, dict)]

    def reveal_contacts(self, contacts: List[EnrichmentContact]) -> None:
        """Fill in email (and phone, if a webhook is configured) via /people/bulk_match.

        Emails come back synchronously. Phone numbers are delivered asynchronously
        to APOLLO_PHONE_WEBHOOK_URL, so they only work when that webhook is set.
        Each matched person consumes Apollo credits, so callers should pass only the
        contacts they actually want to reach (e.g. the top-ranked ones).
        """
        if not self.api_key or not contacts:
            return

        reveal_phone = bool(
            settings.apollo_reveal_phone_number and resolve_apollo_phone_webhook_url()
        )

        # Apollo allows up to 10 people per bulk_match call.
        for batch_start in range(0, len(contacts), 10):
            batch = contacts[batch_start : batch_start + 10]
            details = [self._reveal_detail(c) for c in batch]

            payload: Dict[str, Any] = {
                "details": details,
                "reveal_personal_emails": bool(settings.apollo_reveal_personal_emails),
            }
            if reveal_phone:
                payload["reveal_phone_number"] = True
                payload["webhook_url"] = resolve_apollo_phone_webhook_url()

            data = self._post("/people/bulk_match", payload, soft_fail=True)
            if not data:
                continue

            matches = data.get("matches") or []
            for contact, match in zip(batch, matches):
                if not isinstance(match, dict):
                    continue
                self._apply_match(contact, match)

    def _reveal_detail(self, contact: EnrichmentContact) -> Dict[str, Any]:
        """Build the most specific identifier payload Apollo can match on."""
        detail: Dict[str, Any] = {}
        if contact.external_id:
            detail["id"] = contact.external_id
        if contact.name:
            detail["name"] = contact.name
        if contact.email:
            detail["email"] = contact.email
        if contact.linkedin_url:
            detail["linkedin_url"] = contact.linkedin_url
        if contact.domain:
            detail["domain"] = contact.domain
        return detail

    def _apply_match(self, contact: EnrichmentContact, match: Dict[str, Any]) -> None:
        email = match.get("email")
        # Apollo returns a placeholder when an email exists but isn't unlocked.
        if email and "email_not_unlocked" not in email:
            contact.email = email
        contact.email_status = match.get("email_status") or contact.email_status

        # Personal emails (when revealed) live in a separate array.
        if not contact.email:
            personal = match.get("personal_emails") or []
            if personal:
                contact.email = personal[0]

        # Phone numbers (only present if returned synchronously for this plan).
        phones = match.get("phone_numbers") or []
        if phones and isinstance(phones, list):
            first = phones[0]
            if isinstance(first, dict):
                contact.phone = first.get("sanitized_number") or first.get("raw_number")

        # Backfill a real last name / linkedin if search obfuscated it.
        if match.get("name"):
            contact.name = match["name"]
        if match.get("linkedin_url"):
            contact.linkedin_url = match["linkedin_url"]

    # --- HTTP helpers -------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

    def _enrich_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        clean = _clean_domain(domain)
        if not clean:
            return None
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.get(
                    f"{self.base_url}/organizations/enrich",
                    headers=self._headers(),
                    params={"domain": clean},
                )
        except httpx.HTTPError as exc:
            logger.warning("Apollo enrich_by_domain network error: %s", exc)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "Apollo enrich_by_domain failed (%s): %s",
                resp.status_code,
                resp.text[:300],
            )
            return None
        return (resp.json() or {}).get("organization")

    def _search_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        data = self._post(
            "/mixed_companies/search",
            {"q_organization_name": name, "page": 1, "per_page": 1},
            soft_fail=True,
        )
        if not data:
            return None
        orgs = data.get("organizations") or data.get("accounts") or []
        return orgs[0] if orgs else None

    def _post(
        self, path: str, payload: Dict[str, Any], *, soft_fail: bool = False
    ) -> Optional[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                resp = client.post(
                    f"{self.base_url}{path}", headers=self._headers(), json=payload
                )
        except httpx.HTTPError as exc:
            logger.warning("Apollo POST %s network error: %s", path, exc)
            if soft_fail:
                return None
            raise

        if resp.status_code >= 400:
            logger.warning("Apollo POST %s failed (%s): %s", path, resp.status_code, resp.text[:300])
            if soft_fail:
                return None
            resp.raise_for_status()
        return resp.json()

    # --- mapping ------------------------------------------------------------

    def _map_organization(self, org: Dict[str, Any]) -> EnrichmentResult:
        phone = org.get("phone")
        if not phone:
            primary = org.get("primary_phone") or {}
            phone = primary.get("number") if isinstance(primary, dict) else None

        hq_parts = [org.get("city"), org.get("state"), org.get("country")]
        headquarters = ", ".join([p for p in hq_parts if p]) or org.get("raw_address")

        funding = org.get("latest_funding_stage") or org.get("total_funding_printed")

        return EnrichmentResult(
            found=True,
            source="apollo",
            domain=org.get("primary_domain"),
            website=org.get("website_url"),
            linkedin_url=org.get("linkedin_url"),
            industry=org.get("industry"),
            employee_count=org.get("estimated_num_employees"),
            headquarters=headquarters,
            phone=phone,
            funding=funding,
            revenue=org.get("annual_revenue_printed"),
        )

    def _map_person(self, person: Dict[str, Any], *, domain: Optional[str] = None) -> EnrichmentContact:
        first = person.get("first_name") or ""
        last = person.get("last_name") or person.get("last_name_obfuscated") or ""
        name = f"{first} {last}".strip() or person.get("name") or "(unknown)"

        # People Search does not return emails; only a has_email flag. Confidence
        # reflects whether Apollo *has* an email we could later enrich.
        has_email = person.get("has_email")
        confidence = 70.0 if has_email else 45.0

        return EnrichmentContact(
            name=name,
            title=person.get("title"),
            email=person.get("email"),  # usually None from search
            phone=None,
            linkedin_url=person.get("linkedin_url"),
            confidence_score=confidence,
            external_id=person.get("id"),
            domain=domain,
        )


def _clean_domain(value: Optional[str]) -> Optional[str]:
    """Strip protocol / www / paths so Apollo gets a bare domain."""
    if not value:
        return None
    text = value.strip().lower()
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.startswith("www."):
        text = text[4:]
    text = text.split("/")[0].split("@")[-1].strip()
    return text or None
