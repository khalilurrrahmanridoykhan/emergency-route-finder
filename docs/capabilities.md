# Facility capabilities and emergency types

Everything here is an **assumption**, editable in `config/`. Public data does not say which facility has antivenom, a surgeon or an obstetric theatre. Outputs must not be read as verified. Only `yes` makes a facility a destination; `basic only` and `first aid only` do not qualify.

## Capability table (`config/capabilities.csv`)

| Facility level | Minor illness | Childbirth complication | Snakebite | Snakebite (district level and above only) | Injury or drowning |
|---|---|---|---|---|---|
| community_clinic | yes | no | no | no | first aid only |
| union_health_family_welfare_centre | yes | basic only | no | no | first aid only |
| upazila_health_complex | yes | yes | yes | no | yes |
| district_general_hospital | yes | yes | yes | yes | yes |
| medical_college_hospital | yes | yes | yes | yes | yes |
| private_or_unclassified | yes | no | no | no | first aid only |

The "district level and above only" column is a strict sensitivity case for snakebite, because not every upazila hospital is known to stock antivenom.

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

1. Laboratories, diagnostic centres, eye hospitals and veterinary features are excluded (`excluded` rules in `config/facility_rules.csv`).
2. A manual override in `config/facility_overrides.csv` (by OSM id, with a reason) wins.
3. Otherwise the first matching keyword in `config/facility_rules.csv` (English and Bangla, including common OSM misspellings).
4. Otherwise the facility is `private_or_unclassified`, which qualifies only for minor illness.

Facilities must lie inside an official upazila polygon. Duplicate OSM nodes are merged (same or similar name close together, or an unnamed node beside a named one); different hospitals next to each other are kept.

## Facilities by level (131)

| Level | Count |
|---|---|
| community_clinic | 13 |
| district_general_hospital | 5 |
| medical_college_hospital | 8 |
| private_or_unclassified | 62 |
| union_health_family_welfare_centre | 6 |
| upazila_health_complex | 37 |

The list below covers the public-sector and named higher-level facilities. The full list, including the 62 private or unclassified facilities and each facility's catchment, is in `results/e3_facility_levels.csv`.

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
| Habiganj General Hospital | 2332892996 | district_general_hospital | override |
| Moulvibaza Sadar Hospital | 2332892999 | district_general_hospital | rule: sadar hospital |
| Netrokona Sadar Hospital | 3558445437 | district_general_hospital | rule: sadar hospital |
| OSM 8311261 (bangla name) | 8311261 | district_general_hospital | override |
| Sunamganj General Hospital | 2332856927 | district_general_hospital | override |
| Habiganj Medical College | 1350003313 | medical_college_hospital | rule: medical college |
| Jalalabad Ragib Rabeya Medical  College  & Hospital | 9812388576 | medical_college_hospital | rule: medical college |
| Jalalabad Ragib-Rabeya Medical College and Hospital | 1352899133 | medical_college_hospital | rule: medical college |
| Johurul Islam Medical College and Hospital | 656888387 | medical_college_hospital | rule: medical college |
| M.A.G Osmani Medical College Hospital, Sylhet | 265945386 | medical_college_hospital | rule: medical college |
| North East Medical College Hospital | 986184679 | medical_college_hospital | rule: medical college |
| OSM 13846497403 (bangla name) | 13846497403 | medical_college_hospital | rule: medical college |
| Parkview Medical College | 10791274805 | medical_college_hospital | rule: medical college |
| Dighalbak Union Family Clinic & Health Center | 795286625 | union_health_family_welfare_centre | rule: union |
| Health & Family Wlfare Center | 3702053369 | union_health_family_welfare_centre | rule: family wlfare |
| Sastho Poribar Kollan Kendro | 5781372419 | union_health_family_welfare_centre | override |
| Sreepur Health Complex | 6124467111 | union_health_family_welfare_centre | override |
| Union health and family welfare center | 6124500176 | union_health_family_welfare_centre | rule: family welfare |
| Vojendroganj up health and family welfare centre | 6124500126 | union_health_family_welfare_centre | rule: family welfare |
| Ajmiriganj Upazila Health Complex | 2332892994 | upazila_health_complex | rule: upazila health complex |
| Atpara Upazila Health Complex | 5892085937 | upazila_health_complex | rule: upazila health complex |
| Balaganj Upazila Health Complex | 9692896252 | upazila_health_complex | rule: upazila health complex |
| Baniachang Upazila Health Complex | 2332892995 | upazila_health_complex | rule: ঊপজেলা স্বাস্থ্য কমপ্লেক্স |
| Belabo Upazila Health Complex | 9692137611 | upazila_health_complex | rule: upazila health complex |
| Bishwamvarpur Upazila Health Complex | 1075303043 | upazila_health_complex | rule: upazila health complex |
| Companygonj Upazila Health Complex | 558368069 | upazila_health_complex | rule: upazila health complex |
| Dowarbazar Upazila Health Complex | 2332856879 | upazila_health_complex | rule: upazila health complex |
| Durgapur Upazila Health Complex | 2332856882 | upazila_health_complex | rule: upazila health complex |
| Gowainghat Upazila Health Complex | 1093202023 | upazila_health_complex | rule: upazila health complex |
| Hossainpur Upazila Health Complex | 5863662519 | upazila_health_complex | rule: upazila health complex |
| Ishwarganj Upazila Health Complex | 5611158563 | upazila_health_complex | rule: upazila health complex |
| Jagannathpur Upazila Health Complex | 2332872337 | upazila_health_complex | rule: upazila health complex |
| Jamalganj Upazila Health Complex | 2332872344 | upazila_health_complex | rule: upazila health complex |
| Kalmakanda Upazila Health Complex | 2332856898 | upazila_health_complex | rule: upazila health complex |
| Kamalganj Upazila Health Complex | 2332892997 | upazila_health_complex | rule: upazila health complex |
| Karimganj Upazilla Health Complex | 2332679003 | upazila_health_complex | rule: upazilla health complex |
| Katiyadi Upazilla Health Complex | 2332679004 | upazila_health_complex | rule: upazilla health complex |
| Kendua Upazila Health Complex | 5741962598 | upazila_health_complex | rule: upazila health complex |
| Kuliarchar Upazila Health Complex | 6163500243 | upazila_health_complex | rule: upazila health complex |
| Madan Upazilla Health Complex | 3559113604 | upazila_health_complex | rule: upazilla health complex |
| Madhabpur Upazila Health Complex | 2333151684 | upazila_health_complex | rule: upazila health complex |
| Mithamoin Upazila Health Complex | 5866203323 | upazila_health_complex | rule: upazila health complex |
| Mohanganj Upazila Health Complex | 2332872347 | upazila_health_complex | rule: upazila health complex |
| Nabiganj Upazila Health Complex | 5619077147 | upazila_health_complex | rule: upazila health complex |
| Nandail Upazilla Health Complex | 2332679006 | upazila_health_complex | rule: upazilla health complex |
| Nasirnagar Upazila Health Complex | 2332919089 | upazila_health_complex | rule: upazila health complex |
| Nikli Upazilla Health Complex | 2332679007 | upazila_health_complex | rule: upazilla health complex |
| OSM 2332872329 (bangla name) | 2332872329 | upazila_health_complex | rule: উপজেলা স্বাস্থ্য কমপ্লেক্স |
| OSM 6574122409 (bangla name) | 6574122409 | upazila_health_complex | rule: উপজেলা স্বাস্থ্য কমপ্লেক্স |
| Pakundia Upazilla Health Complex | 2332679008 | upazila_health_complex | rule: upazilla health complex |
| Rajanagar Upazila Health Complex | 2332893000 | upazila_health_complex | rule: upazila health complex |
| Sarail Upazila Health Complex | 4710195981 | upazila_health_complex | rule: upazila health complex |
| Sreemangal Upazila Health Complex | 2332919090 | upazila_health_complex | rule: upazila health complex |
| Tahirpur Upazila Health Complex | 2332856931 | upazila_health_complex | rule: upazila health complex |
| Tarail Upazila Health Complex l | 6162814797 | upazila_health_complex | rule: upazila health complex |
| Upazila Fenchugonj Health Complex | 1085835916 | upazila_health_complex | rule: health complex |
