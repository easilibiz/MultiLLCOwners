# Master specification — applies above every MSA

The authoritative cross-market requirements document is:

`LLC_Portfolio_Identification_and_Mailing_Master_Specification.docx`

This document governs NYC, Chicago, and every future MSA folder. Market folders contain local source mappings, evidence, processing work, and outputs; they do not replace the master rules.

Mandatory campaign controls include:

- select all parcel records whose normalized legal owner name ends in LLC, without a property-type or unit-count prefilter;
- cluster different LLCs by normalized owner mailing address, never by property address;
- require at least two distinct LLCs and two distinct properties;
- keep intermediary evidence in the research audit but exclude lawyers, agents, CPAs/accountants, filing services, care-of destinations, flagged property-address substitutions, low-confidence records, and manual-review records from the automated mailing list;
- consolidate to exactly one outbound row and one postcard per normalized owner mailing address; and
- require USPS CASS/DPV, applicable suppressions, and a dated print authorization before release.

The `support` folder contains the document builder and render-verification material. MSA-specific requirements should be implemented as adapters below this master specification.
