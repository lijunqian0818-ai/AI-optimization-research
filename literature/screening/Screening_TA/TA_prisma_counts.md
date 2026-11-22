# PRISMA 2020 counts - title/abstract stage

```mermaid
flowchart TD
  I["Records identified from databases (n = 156)<br/>candidates_for_screening n = 156"]
  R["Records removed before screening:<br/>duplicate records (n = 0)"]
  S["Records screened (n = 156)"]
  X["Records excluded (n = 3)<br/>E2 Meets none of the topic conditions T1-T7: 2<br/>E5 High-frequency order-book / market-making engineering without an informed-trading model: 1"]
  F["Reports sought for retrieval (n = 153)"]
  I --> R
  I --> S
  S --> X
  S --> F
```

```json
{
 "stage": "ta",
 "tool": "sr-screener 1.0.0",
 "complete": true,
 "pending_records": 0,
 "state_problems": [],
 "identified_by_database": {
  "candidates_for_screening": 156
 },
 "identified_total": 156,
 "duplicates_removed": 0,
 "records_screened": 156,
 "records_to_screen": 156,
 "records_excluded": 3,
 "excluded_by_code": {
  "E2": 2,
  "E5": 1
 },
 "reports_sought_for_retrieval": 153,
 "advanced_include": 111,
 "advanced_unclear": 42,
 "advanced_outside_allowed_languages": 0,
 "agreement": {
  "n": 156,
  "both_advance": 143,
  "both_exclude": 5,
  "a_only_advance": 6,
  "b_only_advance": 2,
  "observed_agreement": 0.9487,
  "kappa": 0.53,
  "pabak": 0.897,
  "conflicts": 8,
  "resolved_by": {
   "A+B": 146,
   "ADJ": 8,
   "QC": 2
  }
 },
 "decided_by": {
  "A+B": 146,
  "ADJ": 8,
  "QC": 2
 }
}
```
