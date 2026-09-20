# Facility capabilities and emergency types

Everything here is an **assumption**, editable in `config/`. Public data does not say which facility has antivenom, a surgeon or an obstetric theatre. Outputs must not be read as verified. Only `yes` makes a facility a destination; `basic only` and `first aid only` do not qualify.

## Capability table (`config/capabilities.csv`)

| Facility level | Minor illness | Childbirth complication | Snakebite | Snakebite (district hospital only) | Injury or drowning |
|---|---|---|---|---|---|
| community_clinic | yes | no | no | no | first aid only |
| union_health_family_welfare_centre | yes | basic only | no | no | first aid only |
| upazila_health_complex | yes | yes | yes | no | yes |
| district_general_hospital | yes | yes | yes | yes | yes |
| medical_college_hospital | yes | yes | yes | yes | yes |
| private_or_unclassified | yes | no | no | no | first aid only |

The "district hospital only" column is a strict sensitivity case for snakebite, because not every upazila hospital is known to stock antivenom.

## Target times (`config/emergencies.csv`)

| Emergency | Target | Basis |
|---|---|---|
| Childbirth complication | 120 min | WHO indicator: geographic access to emergency obstetric care within 2 hours of travel time (https://www.who.int/data/gho/indicator-metadata-registry/imr-details/geographic-access-to-emergency-obstetric-care-(emoc)-health-facilities-within-2-hours-of-travel-time) |
| Snakebite | 120 min | About 2 hours is the maximum ideal time to antivenom used in accessibility studies (https://pmc.ncbi.nlm.nih.gov/articles/PMC8757981/); a population standard, not a clinical limit |
| Snakebite (antivenom only at district hospitals) | 120 min | Same 2 hour basis as snakebite; strict case because not every upazila hospital has antivenom |
| Injury or drowning | 120 min | Lancet Commission on Global Surgery: 2 hours to essential surgical care such as open fracture care (https://www.thelancet.com/commissions-do/global-surgery); drowning also needs first aid at the scene |
| Minor illness | 60 min | Common 60-minute primary-care access convention in accessibility studies (e.g. https://pmc.ncbi.nlm.nih.gov/articles/PMC12557955/); not a clinical threshold |

The targets are population access standards used in accessibility studies, not clinical time limits. The sources were checked through search summaries, not read in full.

## How facilities get a level

1. A manual override in `config/facility_overrides.csv` (by OSM id, with a reason) wins.
2. Otherwise the first matching keyword in `config/facility_rules.csv` (in English and Bangla, including a common OSM misspelling).
3. Otherwise the facility is `private_or_unclassified`, which qualifies only for minor illness.

Facilities must lie inside an official upazila polygon; two "PHC" features on the border line were excluded because they lie in none.

## Facilities and levels (35)

| Name | OSM id | Level | How |
|---|---|---|---|
| Achanpur community clinic | 6281151376 | community_clinic | rule: community clinic |
| Adittopur community clinic | 6125242925 | community_clinic | rule: community clinic |
| Atgao community clinic | 6124500161 | community_clinic | rule: community clinic |
| Community Clinic Puran Varanga | 5781372420 | community_clinic | rule: community clinic |
| Kamarkandi Community Clinic | 5793761342 | community_clinic | rule: community clinic |
| Kartikpur Commuinity Clinic | 6123345380 | community_clinic | rule: commuinity clinic |
| Kashipur Community Clinic | 6124500144 | community_clinic | rule: community clinic |
| Loularchar Commuinity Clinic | 6123345342 | community_clinic | rule: commuinity clinic |
| Mamudnagar Community clinic | 6120359805 | community_clinic | rule: community clinic |
| Shamarchar commuinity Clinic | 6123345366 | community_clinic | rule: commuinity clinic |
| Srihile community clinic | 6125239779 | community_clinic | rule: community clinic |
| Uzangao community clinic | 6120359804 | community_clinic | rule: community clinic |
| Uzanyarabad community clinic | 6124500135 | community_clinic | rule: community clinic |
| Sunamganj General Hospital | 2332856927 | district_general_hospital | override |
| Khaled General Hospital | 2616255489 | private_or_unclassified | override |
| OSM 539361524 (unnamed) | 539361524 | private_or_unclassified | default |
| OSM 9916643514 (unnamed) | 9916643514 | private_or_unclassified | default |
| koitok hospital | 539203370 | private_or_unclassified | override |
| Dighalbak Union Family Clinic & Health Center | 795286625 | union_health_family_welfare_centre | rule: union |
| Sastho Poribar Kollan Kendro | 5781372419 | union_health_family_welfare_centre | override |
| Sreepur Health Complex | 6124467111 | union_health_family_welfare_centre | override |
| Union health and family welfare center | 6124500176 | union_health_family_welfare_centre | rule: family welfare |
| Vojendroganj up health and family welfare centre | 6124500126 | union_health_family_welfare_centre | rule: family welfare |
| Ajmiriganj Upazila Health Complex | 2332892994 | upazila_health_complex | rule: upazila health complex |
| Bishwamvarpur Upazila Health Complex | 1075303043 | upazila_health_complex | rule: upazila health complex |
| Dowarbazar Upazila Health Complex | 2332856879 | upazila_health_complex | rule: upazila health complex |
| Jagannathpur Upazila Health Complex | 2332872337 | upazila_health_complex | rule: upazila health complex |
| Jamalganj Upazila Health Complex | 2332872344 | upazila_health_complex | rule: upazila health complex |
| Mithamoin Upazila Health Complex | 5866203323 | upazila_health_complex | rule: upazila health complex |
| Mohanganj Upazila Health Complex | 2332872347 | upazila_health_complex | rule: upazila health complex |
| Nabiganj Upazila Health Complex | 5619077147 | upazila_health_complex | rule: upazila health complex |
| OSM 2332872329 (bangla name) | 2332872329 | upazila_health_complex | rule: উপজেলা স্বাস্থ্য কমপ্লেক্স |
| OSM 2332892995 (bangla name) | 2332892995 | upazila_health_complex | rule: ঊপজেলা স্বাস্থ্য কমপ্লেক্স |
| OSM 6574122409 (bangla name) | 6574122409 | upazila_health_complex | rule: উপজেলা স্বাস্থ্য কমপ্লেক্স |
| Tahirpur Upazila Health Complex | 2332856931 | upazila_health_complex | rule: upazila health complex |
