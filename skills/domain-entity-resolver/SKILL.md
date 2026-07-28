---
name: domain-entity-resolver
title: HR Cloud Domain and Entity Resolver
description: "Use this skill to resolve the legal and operating identity of scraped HR Cloud prospects. It distinguishes employer domains from ATS, CDN, document, facility, subsidiary, franchise, and parent domains; applies a deterministic verification protocol; deduplicates entities; and returns a status that downstream scoring can trust."
category: Prospecting
---

# HR Cloud Domain and Entity Resolver

## Purpose

Prevent the scraper from attaching valid evidence to the wrong company.

This matters because HR Cloud prospects often have:

- facility-level sites;
- parent health systems;
- school district and school domains;
- franchise locations;
- government departments;
- ATS subdomains;
- document hosts;
- acquired brands;
- holding companies.

## Inputs

```yaml
raw_company_name:
raw_domain:
source_url:
source_title:
source_excerpt:
vertical:
location:
known_parent:
company_linkedin:
```

## Output

```yaml
canonical_company_name:
canonical_domain:
entity_type:
parent_company:
parent_domain:
facility_or_subsidiary:
facility_domain:
domain_status:
identity_confidence:
verification_evidence:
dedupe_key:
notes:
```

## Domain Statuses

- `verified`
- `verified_parent_only`
- `facility_no_unique_domain`
- `subsidiary_verified`
- `government_entity_verified`
- `school_or_district_verified`
- `franchise_parent_verified`
- `unresolved`
- `non_employer_host`
- `duplicate`

## Seven-Step Verification Protocol

### 1. Normalize the URL

- extract hostname;
- lowercase;
- strip protocol;
- strip `www`;
- remove tracking parameters;
- normalize Unicode and punctuation.

### 2. Correct ATS and hosted-career domains

Examples:

- Workday;
- Greenhouse;
- Lever;
- iCIMS;
- Paylocity;
- ADP Recruiting;
- UKG;
- government job portals.

Use page content, linked company site, structured data, and ATS tenant identity
to resolve the employer.

Never export the ATS host as the employer domain.

### 3. Reject non-employer hosts

Examples:

- S3;
- CloudFront;
- SharePoint document links;
- WordPress media hosts;
- Squarespace CDN;
- Google Drive;
- Dropbox;
- generic PDF hosts;
- job aggregators.

Retain them as evidence URLs but not canonical company domains.

### 4. Reject job boards, directories, and social networks

Examples:

- Indeed;
- LinkedIn;
- Glassdoor;
- ZipRecruiter;
- state job boards;
- association directories.

Use them to find the employer, not as the employer identity.

### 5. Collapse to registrable root carefully

Use public suffix logic.

Do not incorrectly collapse:

- government subdomains where agency identity matters;
- school district subdomains;
- country-specific suffixes;
- health-system facility domains.

### 6. Resolve parent, subsidiary, facility, and franchise

Determine:

- who employs the staff;
- who owns HR technology;
- who buys software;
- whether the signal is local or centralized;
- whether a facility has its own domain;
- whether the parent should be scored instead.

A facility without a unique domain may remain a record if:

- facility identity is clear;
- parent is verified;
- evidence is facility-specific;
- buying ownership is marked unknown or parent-owned.

### 7. Return status and evidence

A status without verification evidence is invalid.

## Entity Matching Priority

Use:

1. canonical domain;
2. official LinkedIn company URL;
3. legal/official registry;
4. official website identity;
5. parent/subsidiary relationship;
6. normalized company name plus location.

A name-only match is never enough for a high-confidence merge.

## Deduplication

Create a dedupe key from:

- canonical domain;
- parent domain;
- entity type;
- facility identifier;
- jurisdiction where needed.

Rules:

- Do not merge distinct facilities when their signal is local and ownership
  differs.
- Do not count a parent and subsidiary as two independent accounts when the
  same buying team owns both.
- Preserve aliases and acquired names.
- Mark evidence provenance before merging.

## Vertical Rules

### Healthcare

Resolve:

- brand;
- facility;
- parent system;
- NPI or CMS identity where relevant;
- location;
- centralized versus local HR.

### Education

Resolve:

- school;
- district;
- charter network;
- management organization;
- college system.

### Government

Resolve:

- agency;
- department;
- municipality;
- county;
- special district;
- procurement issuer.

### Manufacturing

Resolve:

- operating company;
- plant;
- division;
- parent;
- acquired brand.

### Retail and Hospitality

Resolve:

- corporate operator;
- franchisee;
- brand owner;
- management company.

## Failure Handling

Retry identity resolution once with:

- company name plus location;
- source title;
- ATS tenant;
- official registry;
- LinkedIn company page.

After retry:

- return `unresolved`;
- retain the candidate in a research queue;
- do not score or export as outreach-ready.

## Tests

Required test cases:

- company ATS subdomain;
- PDF on S3;
- school versus district;
- healthcare facility versus parent;
- franchise location;
- acquired company;
- government department;
- same-name companies in different states;
- domain redirect;
- dead domain;
- parent-only identity;
- facility with no unique domain.
