"""
Tests for scrapers/shared/verifier.py — DomainResolution structured object.
- ATS subdomain (company.greenhouse.io → unresolved with employer name)
- CDN (s3.amazonaws.com → non_employer_host)
- k12 domain → school_or_district_verified
- .gov domain → government_entity_verified
- jobs.company.com → corrects to company.com
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from scrapers.shared.verifier import resolve_domain, DomainResolution


class TestDomainEntityResolver:
    def test_ats_subdomain_greenhouse_unresolved_with_employer_name(self):
        """company.greenhouse.io → unresolved (employer domain not confirmed), company name extracted."""
        result = resolve_domain("https://acmecorp.greenhouse.io/jobs/12345")
        # The employer name 'acmecorp' is extracted but no confirmed domain
        assert result.domain_status == "unresolved", (
            f"Expected 'unresolved' for ATS subdomain, got '{result.domain_status}'"
        )
        assert result.canonical_company_name == "acmecorp" or "acmecorp" in result.notes.lower(), (
            f"Expected employer name 'acmecorp' in resolution, got: "
            f"company_name='{result.canonical_company_name}', notes='{result.notes}'"
        )

    def test_cdn_s3_returns_non_employer_host(self):
        """s3.amazonaws.com URL → non_employer_host status."""
        result = resolve_domain("https://s3.amazonaws.com/company-docs/new-hire-packet.pdf")
        assert result.domain_status == "non_employer_host", (
            f"Expected 'non_employer_host' for S3 URL, got '{result.domain_status}'"
        )

    def test_k12_domain_returns_school_district_verified(self):
        """k12 domain → school_or_district_verified."""
        result = resolve_domain("https://hr.isd.k12.tx.us/new-hire-packet.pdf")
        assert result.domain_status == "school_or_district_verified", (
            f"Expected 'school_or_district_verified', got '{result.domain_status}'"
        )
        assert result.entity_type == "district"

    def test_gov_domain_returns_government_entity_verified(self):
        """*.gov domain → government_entity_verified."""
        result = resolve_domain("https://hr.countygov.gov/new-hire-forms.pdf")
        assert result.domain_status == "government_entity_verified", (
            f"Expected 'government_entity_verified', got '{result.domain_status}'"
        )
        assert result.entity_type == "government"

    def test_jobs_subdomain_corrected_to_root_domain(self):
        """jobs.company.com → canonical_domain corrected to company.com."""
        result = resolve_domain("https://jobs.acmecorp.com/apply")
        assert result.canonical_domain == "acmecorp.com", (
            f"Expected 'acmecorp.com', got '{result.canonical_domain}'"
        )
        assert result.domain_status == "verified"

    def test_careers_subdomain_corrected(self):
        """careers.company.com → corrected to company.com."""
        result = resolve_domain("https://careers.example.com/jobs")
        assert result.canonical_domain == "example.com"

    def test_linkedin_returns_non_employer_host(self):
        """LinkedIn → non_employer_host."""
        result = resolve_domain("https://linkedin.com/company/acmecorp")
        assert result.domain_status == "non_employer_host"

    def test_indeed_returns_non_employer_host(self):
        """Indeed → non_employer_host."""
        result = resolve_domain("https://indeed.com/cmp/acme/jobs")
        assert result.domain_status == "non_employer_host"

    def test_normal_employer_domain_verified(self):
        """Regular company domain → verified."""
        result = resolve_domain("https://acmehealthcare.com/careers/apply")
        assert result.domain_status == "verified"
        assert result.canonical_domain == "acmehealthcare.com"
        assert result.entity_type == "employer"

    def test_empty_url_returns_unresolved(self):
        """Empty URL → unresolved."""
        result = resolve_domain("")
        assert result.domain_status == "unresolved"

    def test_www_stripped(self):
        """www prefix is stripped from canonical domain."""
        result = resolve_domain("https://www.acmecorp.com/hr")
        assert "www" not in result.canonical_domain

    def test_dedupe_key_set_for_verified_domain(self):
        """Verified domain should have a dedupe_key."""
        result = resolve_domain("https://acmecorp.com/hr")
        assert result.dedupe_key != ""
        assert result.dedupe_key == "acmecorp.com"

    def test_lever_ats_subdomain(self):
        """company.lever.co → treated as ATS, returns unresolved or non_employer_host."""
        result = resolve_domain("https://jobs.lever.co/acmecorp/12345")
        # lever.co is in ATS_HOSTS so should be blocked
        assert result.domain_status in ("non_employer_host", "unresolved"), (
            f"Expected non_employer_host or unresolved, got '{result.domain_status}'"
        )
