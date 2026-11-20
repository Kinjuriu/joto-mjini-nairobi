# Joto Mjini Nairobi: workshop plan, checklist and handover

Written 20 November 2026 for the next build chat. Save this file and the three email screenshots in `~/Desktop/joto-mjini/prompts/v4/` (screenshots in `prompts/v4/emails/`).

## 0. Message for the new chat (paste this first)

> Hi. You are continuing my Nairobi urban heat storyboard, Joto Mjini Nairobi, in `~/Desktop/joto-mjini` (GitHub: Kinjuriu/joto-mjini-nairobi). I am presenting it at the Earthna and CIFF workshop "Land, Food and Heat Resilience in Africa's Arid Regions" on Thursday 26 November 2026, and my slides are due on Monday 23 November. Read, in this order: `CLAUDE.md`, `DESIGN_RULES.md` (including the Joto Mjini palette at the bottom), `DECISIONS.md` up to the latest entry, `QUESTIONS.md`, `prompts/v3/REPORT_opus_schools_census.md`, `prompts/v3/NEXT_SESSION_TODO.md`, and then this plan, `prompts/v4/WORKSHOP_PLAN.md`, with the email screenshots in `prompts/v4/emails/`. This plan replaces the order of work in NEXT_SESSION_TODO where they differ. Work through section 5 in order, ask me the questions in section 9 before you build anything that depends on them, and check every change in the browser at 1440 px and 375 px. Plain English, no em dashes, no "not X, but Y", and every number on the page comes from `analysis/results*.json`. Do not push to GitHub without asking me.

## 1. The workshop (from the emails in `prompts/v4/emails/`)

- **Event:** Land, Food and Heat Resilience in Africa's Arid Regions, hosted by the Earthna Center for a Sustainable Future (Qatar Foundation) with the Children's Investment Fund Foundation (CIFF).
- **When and where:** Thursday 26 November 2026, 08:30 to 16:00, Sankara Nairobi (Autograph Collection), Westlands. Stephane has confirmed her place; everyone must stay the full day.
- **Why they are meeting:** Earthna and CIFF have a partnership to identify, test and scale models in hot and arid African countries in two areas. One is "reducing heat stress in arid urban settings: improving health and productivity through nature-based solutions, efficient technologies and localized urban design, with a focus on children and young people". The concept note also says that in cities, extreme heat affects wellbeing and productivity, "including in schools and health facilities".
- **Expected outcomes:** a shared overview of effective approaches, a network of implementing organisations engaged with the programme, and a summary report. 40 to 50 participants from NGOs, community organisations, research institutions and Pan-African bodies.
- **Presentation rules:** a one-minute brief about your organisation, then one project on a workshop theme (ours: urban heat resilience and cooling, with a link to children). **Five minutes maximum, strictly timed. Three slides maximum. No title slide and no end slide. Name and organisation on every slide. Slides due Monday 23 November.**
- **Affiliation:** Stephane does not work for WBA, so it must not appear. Present as an independent researcher, or under Faniki (her own organisation) if she chooses; a simple Faniki website can come after the workshop.

## 2. The question the storyboard answers

**Main question:** Where does Nairobi's heat fall, and how many school-age children (and adults) live and learn on the hot side of the city?

What the audience should leave knowing:
1. Nairobi has a hot side and a cool side, and the gap is large (the five hottest wards where people live average 41.9 °C at the ground on hot mornings; the five coolest 35.0 °C).
2. Most schools, and most of the city's children, are on the hot side.
3. Heat during the school day harms learning and health (research in section 8), and Term 1 (5 January to 2 April) falls in the hot dry season.
4. Trees and better roofs are the cooling that works; where the forests are, the ground is cooler.
5. Which side of Nairobi they themselves live on (the explorer), since most people in the room are adults who live in the city.

## 3. Numbers we already have, and one to get right

From `analysis/results.json`, `results_extra.json` and Opus's report:

- County median ground temperature, January to March mornings 2023 to 2026: 38.7 °C; hottest tenth of the land 44.9 °C; coolest tenth 29.3 °C.
- Industrial Area 41.5 °C and city centre 37.8 °C, against Karura Forest and the Arboretum 27.6 °C (gaps 13.9 °C and 10.2 °C).
- People on the hottest fifth of the land: about 827,000 (14.6 % of the county).
- Ten hottest wards where people live: about 412,000 people, none with more than 14.1 % tree cover.
- Schools mapped: 3,714 (3,712 with a temperature), from the Ministry list via the World Bank and OpenStreetMap; about 1,480 Ministry points may be up to 300 m off.
- **Careful:** 567 schools (15.3 %) are on the hottest fifth of the land, which is *less* than that fifth's 20 % share of land, because much of the hottest ground is bare open land (Ruai, the airport) with few schools. So we must not say schools are "disproportionately on the hottest land". The honest and still strong figure: **72.6 % of schools sit on ground hotter than the city median, against half of the land.** Kangemi has 92 of its 127 schools on the hottest fifth; Viwandani 33 of 40.
- We have no pupil numbers per school. Say "schools" and "school-age children living in…", never "children in each school", until the school register (KEMIS or NEMIS) is available.

## 4. Data to add

### 4.1 School-age children by age (the most important new number)

What exists already:
- **Census Volume III** (in Stephane's public repo Kinjuriu/kenya-2019-census-csv): population by single year of age and sex for every county and sub-county, and school-age counts by sub-county for ages 4 to 5, 6 to 11, 12 to 14 and 15 to 17 (the Competency-Based Curriculum entry ages). Nairobi 2019: 1,107,673 children aged 4 to 17, a quarter of the county; Njiru (28.0 %) and Kibra (27.7 %) have the highest shares.
- **Census Volume IV** (extracted by Opus, committed in the census repo but **not pushed**, so it is only on the Mac): Table 2.2 school attendance (attending now, left school, never attended) by sub-county; Table 2.3 attending now by level; Table 2.6b attendance by special age groups (county only); Table 2.12 roofing material by sub-county.
- These stop at the census sub-county level (11 in Nairobi). They cannot say which ward, or which hot or cool ground, a child lives on.

What to download (free):
- **WorldPop age and sex structures, Kenya, 100 m** (WorldPop Global2 R2025A, constrained, the same release as our total population layer): rasters of people by five-year age band and sex. Use the bands 5 to 9, 10 to 14 and 15 to 19 (and 0 to 4 if useful). Check the licence (CC BY 4.0) and record it in `data/SOURCES.md`.

What to compute:
1. Overlay the age-band rasters on the hot-season ground temperature (same 30 m grid as the analysis) and count children by age band on: the hottest fifth of the land; ground hotter than the median; ground cooler than the median; the coolest fifth.
2. Scale the WorldPop age totals in each census sub-county to the 2019 census school-age counts grown to 2025 (state the growth rate and its source), so the totals match the census; keep the unscaled numbers beside them.
3. From Volume IV, take the share "attending now" by sub-county and apply it to estimate **school-going** children (label it as an estimate).
4. Output: `analysis/tables/children_by_heat.csv`, keys under `children` in `results_extra.json`, and a short note in DECISIONS.md. Plain sentences such as "About X children aged 5 to 14 live on ground hotter than the city median, Y % of the county's children in that age group."

### 4.2 Everyone, by hot and cool side (for the adults in the room)

- People in each fifth of the land by temperature (a simple bar chart, coolest fifth to hottest fifth), and people on the hot half versus the cool half. Add both to `results_extra.json` under `people_by_heat`.
- Ward ranking table (all 85 wards) downloadable in Resources, so anyone can find their ward.

### 4.3 Trees near schools (cooling that works)

- For each school, tree cover within 200 m (from ESA WorldCover or the 30 m tree fraction). Then compare schools on the hot half with schools on the cool half. Output under `schools.trees_200m` in `results_extra.json`.

### 4.4 Roofs

- Volume IV Table 2.12 (already extracted): share of households with iron sheet roofs by sub-county (Nairobi 51.3 % in 2019; 38.0 % in Embakasi to 80.6 % in Dagoretti). Use as context only; it does not correct the satellite readings.

## 5. What to build, in order

### Step 1. Restructure the story around children (no rebuild; reorder and trim)

New order of the page:
1. **Opening:** headline about the heat divide and schools (Stephane chooses; options in section 9), one plain paragraph on why it matters now (Term 1 is the hot dry season; Landsat passes at about 10:43, during the school day).
2. **The heat divide (keep, three steps):** Nairobi from space; the heat divide with the pulsing circles; "Five hot wards, five cool wards".
3. **Forests and tree cover (keep, one step):** the forests chapter with Karura, the Arboretum and Ngong Road Forest outlined, plus the tree cover layer, framed as the city's cool islands. Merge the false-colour "Where the trees are" step into it.
4. **Who lives on the hot side (keep and extend):** the existing "Who lives on the hottest ground" step, then the new bar chart of people by heat band (4.2).
5. **Where children live and learn (new):**
   - school-age children by age band on the hot and cool sides (4.1), as a simple bar or dot chart with direct labels;
   - all schools as dots coloured by ground temperature over the satellite map;
   - "72.6 % of schools are on the hotter half" (filter or highlight);
   - zoom to Kangemi (92 of 127 schools on the hottest fifth) and Viwandani (33 of 40), then Karen for contrast;
   - trees within 200 m of schools, hot side against cool side (4.3).
6. **When it is hottest:** the day-of-heat chart with the school day shaded and labelled, and one line on Term 1 falling in the hot dry season.
7. **What it means:** three or four plain sentences drawing on the research in section 8 (learning, children's bodies, metal roofs), each with its source.
8. **What could help and what is needed next:** trees near schools, cooler roofs, classroom temperature sensors, and pupil numbers by school from the register; what Stephane would test with partners.
9. **Explore the map:** add a "Schools" layer (dots coloured by ground temperature), school counts and school-age children in the ward panel, and keep "Find your ward" prominent; consider a short line near the top: "Find out which side of Nairobi you live on" linking to the explorer.
10. **More on Nairobi's climate (moved down):** the El Niño air temperature chart, the monthly table, the season animations, the hot mornings animation, Nairobi grows (Stephane loves it; keep it here or in the main story if time allows), the land cover table.
11. **Resources and Methods:** add the census, WorldPop age-sex, schools sources and the research papers in section 8.

### Step 2. Writing

- Fill every `[[COPY: …]]` placeholder (list in NEXT_SESSION_TODO section A), as drafts for Stephane to edit, in her style (skill `stephane-writing-style`).
- Byline: Stephane's name, "independent researcher" or Faniki (her choice), dates, the live URL.
- Retire the pooled 13.5 °C gap (`q2.gap_c`) everywhere (NEXT_SESSION_TODO item 9).

### Step 3. Go live

- Switch on GitHub Pages for Kinjuriu/joto-mjini-nairobi, built with the Mapbox token supplied at build time (never committed). Add the live address to the Mapbox token's URL restrictions. Check the live page on a phone.
- Push the census repo Volume IV only after Stephane has looked at it.

### Step 4. Slides (due Monday 23 November)

Three slides, no title or end slide, "Stephane [surname], [independent researcher or Faniki]" on each, 16:9, the site's colours and fonts, one idea per slide:
1. **Nairobi's heat divide:** the ward heat map from the storyboard, with the hottest and coolest wards' numbers and the five hot and five cool wards.
2. **Children and schools on the hot side:** the schools map, the share of schools on the hotter half (72.6 %), school-age children on the hot side by age band, Kangemi and Viwandani, Term 1 timing.
3. **What it means and what's next:** the evidence on learning and metal roofs (two short lines with sources), what Stephane proposes to test with partners (for example classroom sensors and tree planting at the hottest schools), and a QR code to the live storyboard.

A speaking script timed to five minutes: one minute on who Stephane is and why she built this, about 1.5 minutes per slide. Export as PPTX and PDF; send to the organisers by Monday. Keep static screenshots of every key map as an offline backup.

### Step 5. Rehearse and back up

- Re-record the offline walkthrough video (`outputs/demo/`) once the text is in.
- Time the talk to under five minutes.
- Put the slides, video and screenshots on the Mac desktop and a USB stick.

## 6. Checklist

- [ ] Stephane answers the questions in section 9
- [ ] WorldPop age and sex rasters downloaded, licence recorded
- [ ] Children by age band on hot and cool ground computed, scaled to the census, checks pass
- [ ] People by heat band computed
- [ ] Trees within 200 m of schools computed
- [ ] Story reordered (section 5, step 1); climate material moved to "More on Nairobi's climate"
- [ ] Forests and tree cover chapter merged and kept
- [ ] Schools chapters built (dots map, 72.6 %, Kangemi, Viwandani, Karen, trees near schools)
- [ ] Day-of-heat chart shows the school day; Term 1 line added
- [ ] "What it means" and "What could help" written with sources
- [ ] Explorer: schools layer, school counts and children in the ward panel
- [ ] All `[[COPY]]` placeholders drafted; Stephane edits them
- [ ] Pooled 13.5 °C gap retired; headline chosen
- [ ] Byline, affiliation (no WBA), dates and URL in
- [ ] Methods, Resources and the research list (section 8) updated
- [ ] Build passes, no `{{` or `[[COPY` left, analysis checks pass
- [ ] QA at 375 px and 1440 px: every chapter, explorer, videos, keyboard, reduced motion
- [ ] Live on GitHub Pages and checked on a phone
- [ ] Three slides and a five-minute script; sent by Monday 23 November
- [ ] Offline video and screenshots ready; talk rehearsed under five minutes

## 7. Requirements and rules

- Follow `DESIGN_RULES.md` and the no-vibe-coding rules: white page, brand blue #3F79AD, line chart #3E0751 with highlight #79C1E9, data animations with the #3E4DB7 cool end; title, subtitle, source and date on every chart; direct labels; nothing hover-only; works at 375 px.
- Writing: plain English, long connected sentences, no em dashes, no "not X, but Y", no seesaw sentences, define every term, tie each claim to a number on the page.
- Honesty: land surface temperature is the heat of the ground, roofs and roads, not air or classroom temperature; WorldPop is modelled and misplaces people inside Kibra and Kangemi (Woodley); school locations are a broad map; children counts are estimates.
- Do not touch the census repo's public history without asking; do not push without asking; never print or commit the Mapbox token, the Esri key or the Copernicus secret.

## 8. Research papers and reports to cite

Learning and heat
1. Park, R. J., Goodman, J., Hurwitz, M. and Smith, J. (2020). Heat and Learning. *American Economic Journal: Economic Policy* 12(2): 306 to 339. https://doi.org/10.1257/pol.20180612. Ten million US students: without air conditioning, a 1 °F hotter school year reduces that year's learning by about 1 %; effects larger for low-income and minority students.
2. Park, R. J., Behrer, A. P. and Goodman, J. (2021). Learning is inhibited by heat exposure, both internationally and within the United States. *Nature Human Behaviour* 5: 19 to 27. https://doi.org/10.1038/s41562-020-00959-9. Achievement data for more than 144 million students aged 15 to 19 in 58 countries; heat reduces learning across climates and income levels, with worse effects for more vulnerable students.

Children, heat and schools in Africa
3. UNICEF (2025). Learning Interrupted: Global Snapshot of Climate-Related School Disruptions in 2024. Press release: https://www.unicef.org/kenya/press-releases/nearly-quarter-billion-childrens-schooling-was-disrupted-climate-crises-2024. At least 242 million students in 85 countries had schooling disrupted in 2024; heatwaves were the main hazard; children heat up faster, sweat less efficiently and cool down more slowly than adults.
4. UNICEF and Dalberg (2026). Protecting Children's Learning Futures: Quantifying Climate-Related Loss and Damage in Eastern and Southern Africa. Press release, Nairobi, 20 April 2026: https://www.unicef.org/esa/press-releases/unicef-warns-climate-impacts-education. Learning disrupted for 130 million children; Kenya among the case countries.
5. Impact of roofing materials on school temperatures in tropical Africa (2025). *Buildings and Cities*. https://doi.org/10.5334/bc.581 (open access: https://reference-global.com/article/10.5334/bc.581). Sixteen classrooms in Accra over 389 days: metal-roofed classrooms reached up to 39.8 °C, up to 5.9 °C above outdoors, overheated for 72.5 % of school hours; concrete-roofed classrooms up to 5.8 °C cooler. Check the author list on the paper before citing.
6. Bidassey-Manilal, S., Wright, C. Y. et al. (2016). Students' perceived heat-health symptoms increased with warmer classroom temperatures. *International Journal of Environmental Research and Public Health* 13: 566. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4924023/. South African high schools: hotter classrooms (prefabricated and iron-roofed) and more reported heat symptoms.
7. Dapi, L. N. et al. (2010). Heat impact on schoolchildren in Cameroon, Africa: potential health threat from climate change. *Global Health Action* 3: 5610. https://doi.org/10.3402/gha.v3i0.5610.

Nairobi heat
8. Scott, A. A., Misiani, H. et al. (2017). Temperature and heat in informal settlements in Nairobi. *PLOS ONE* 12(11): e0187300. https://doi.org/10.1371/journal.pone.0187300. Measured air temperature and heat index in Kibera, Mathare and Mukuru; informal settlements run hotter.
9. Nkugwa and Loyo (2026). Spatiotemporal dynamics of informal settlement thermal environments and their driving factors in Nairobi, Kenya. *Discover Cities*. https://link.springer.com/article/10.1007/s44327-026-00408-8. Three Landsat scenes (2015, 2020, 2025), twelve informal settlements; does not look at schools, services or park cooling, which is the gap our work fills.
10. Kenya Ministry of Education (2025). 2026 school calendar: Term 1 from 5 January to 2 April 2026 (circular of 9 October 2025), reported by Kenyans.co.ke: https://www.kenyans.co.ke/news/119464-school-reopening-dates-academic-calendar-2026.

Data sources (already in Methods, plus the new ones)
- USGS Landsat 8 and 9 Collection 2 via Microsoft Planetary Computer; ESA WorldCover 2021; WorldPop Global2 R2025A (total and age-sex); GHSL GHS-BUILT-S R2023A; Overture buildings; IEBC wards via American Red Cross and HDX; OpenStreetMap; Copernicus hourly LST (CLMS); EOxCloudless 2025; KNBS 2019 Kenya Population and Housing Census Volumes II to IV (Kinjuriu/kenya-2019-census-csv); Ministry of Education school list via the World Bank.

## 9. Questions for Stephane (ask before building what depends on them)

1. **Affiliation on the slides and the byline:** "Independent researcher" or "Faniki"? (No WBA.) Your surname as it should appear.
2. **Headline:** (a) "Nearly three in four of Nairobi's schools sit on the hotter half of the city", (b) the Industrial Area gap (13.9 °C hotter than the forests), or (c) a children number once 4.1 is computed.
3. **Ward populations:** keep WorldPop with a note, or scale to census locations first (fixes Woodley and Kangemi but takes time)? For the workshop, keeping WorldPop with a clear note is the safer choice.
4. **Census Volume IV:** may it be pushed to the public census repo?
5. **School register:** can you get KEMIS or NEMIS data to check the school map and add pupil numbers?
6. **Esri imagery:** is `VITE_ESRI_KEY` saved in `site/.env.local` yet?

## 10. Update, 20 November evening (Stephane's answers and the new order)

- **Affiliation:** Independent Researcher. Name line on every slide: "Stephane Ngugi, Senior Data Analyst & Researcher, Independent Researcher", with her GitHub (github.com/Kinjuriu) and LinkedIn.
- **Order of work changed:** numbers first (done, D59), then the slides and a basic live site with the schools map by Monday 23 November so the link in the email works, then the rest of section 5 from Monday to Wednesday.
- **WorldPop age layers were blocked;** children are estimated from the census age mix (D59). Section 4.1's steps 1 and 2 are replaced by that method.
- **"Disproportionately":** children are not over-represented on the hot side compared with adults (69.6 % against 68.4 %). The clear gap is trees: schools on the hotter half have a median 2.5 % tree cover within 200 m, against 21.9 % on the cooler half. Lead with that, and with "about seven in ten of Nairobi's school-age children live on the hotter half".
- **Ages:** report by school level (pre-primary 4 to 5, primary 6 to 11, junior school 12 to 14, senior school 15 to 17), not five-year bands.
- **During the talk:** stay in the slides; use a short screen recording of the storyboard on slide 2 and a QR code on slide 3 instead of opening the live site.
- **Cut first if short of time:** the explorer's schools layer.
