# The Democratic Funnel

**Where local democracy leaks before the 4 November 2026 local government elections**

Team UL, University of Limpopo · DIRISA Student Datathon Challenge 2026

---

## In one paragraph

South Africans vote for their local councils on **4 November 2026**. To vote, an adult first has to **register**, and then has
to **turn up and vote**. People drop out at both steps, like water leaking from a funnel. This project measures both leaks in
every one of South Africa's **213 municipalities**. It shows which leak is the bigger problem in each place and estimates
turnout for 2026. Everything is presented in an **interactive website (dashboard)** that anyone can use without technical
knowledge.

---

## Contents

1. [The problem we looked at](#1-the-problem-we-looked-at)
2. [What we found](#2-what-we-found)
3. [The dashboard: what you can do with it](#3-the-dashboard-what-you-can-do-with-it)
4. [How we did it, in plain words](#4-how-we-did-it-in-plain-words)
5. [Where the data comes from](#5-where-the-data-comes-from)
6. [Limitations](#6-limitations)
7. [What is in this folder](#7-what-is-in-this-folder)
8. [How to open the dashboard on your own computer](#8-how-to-open-the-dashboard-on-your-own-computer)
9. [For technical readers: reproducing the full analysis](#9-for-technical-readers-reproducing-the-full-analysis)
10. [Privacy](#10-privacy)
11. [The team](#11-the-team)

---

## 1. The problem we looked at

News reports usually quote **turnout**: the share of *registered* voters who voted. That number hides a second problem.
Adults who never registered are not counted at all.

We call this the **democratic funnel**:

```
   All adults who may vote        100 people
            │
            ▼   leak 1: never registered
   Registered voters               65 people
            │
            ▼   leak 2: registered, but did not vote
   People who actually voted       30 people
```
*(National figures for the 2021 local elections, per 100 adults.)*

The two leaks need **different fixes**:

| Leak | Who is lost | What helps |
|---|---|---|
| **Registration leak** | Adults who are not on the voters' roll | Registration drives |
| **Turnout leak** | Registered voters who stay home | Voter education and mobilisation |

A municipality with good turnout can still have a serious problem if many of its adults never registered. The
opposite is also true. Looking at both leaks together shows **what kind of help each municipality needs**.

---

## 2. What we found

**Nationally (2021 local elections)**
- About **35 of every 100 adults** who could vote were **not registered**.
- Another **35 of every 100** were registered but **did not vote**.
- Only about **30 of every 100 adults** voted. The official turnout figure (46%) only shows the second leak.

**Young people are the biggest registration gap**
- Only **46%** of adults aged 18–29 are registered, compared with **84%** of older adults.
- Young people make up about **6 in 10** of all unregistered adults: roughly **6.5 million** people.

**Every municipality falls into one of four groups**, compared with a typical South African municipality:

| Group | What it means | Municipalities | Suggested response |
|---|---|---|---|
| 🟢 **Healthy** | At or above typical on both registration and turnout | 68 | Nothing urgent |
| 🔵 **Low registration** | Fewer adults registered, but those who are registered do vote | 39 | Registration drive |
| 🟡 **Low turnout** | Well registered, but fewer registered voters turn out | 39 | Voter mobilisation |
| 🔴 **Both low** | Below typical at both steps | 67 | Both |

**2026 outlook**
- **29.2 million** people are registered for 2026 (September 2026 roll), about **73%** of adults.
- We expect national turnout of about **46%**, most likely between **41% and 51%**.

**Where to act first.** The dashboard ranks municipalities by how far they fall below a typical municipality. The top of
the list includes Mkhondo, Msukaligwa and Thembisile Hani (Mpumalanga), Emfuleni (Gauteng) and Mafikeng (North West).
All of them are in the "Both low" group.

---

## 3. The dashboard: what you can do with it

The dashboard is a website with these pages:

| Page | What it shows |
|---|---|
| **Overview** | The national picture: how many people are lost at each step, and trends from 2011 to 2026 |
| **Map** | A map of South Africa coloured by each municipality's group. Hover over a municipality for its numbers, or click it to open its profile |
| **Municipality profile** | Look up any municipality: its own funnel, its main problem, what help to send, and its 2026 forecast |
| **Priority list** | All municipalities ranked by need, with the gap split into its registration part and turnout part. Can be downloaded |
| **Electoral participation** | Registration and turnout from 2011 to 2026 by province and municipality, who registers, and what tends to go with low turnout |
| **Recommendations** | For each type of gap: what the data shows, the evidence, a possible response, and what further evidence is needed |
| **Voter education** | Neutral, practical information on how to register and vote on 4 November 2026. No political persuasion |
| **About** | The method, data sources and limitations |
| **Our team** | The people who built it |

It works on phones and computers, and it has a light mode and a dark mode.

---

## 4. How we did it, in plain words

1. **Collected public data.** We used election results, voter registration figures, the 2022 Census and municipal maps.
   All of it is published by official sources (see section 5).
2. **Cleaned and joined it.** Each source was tidied up and matched to today's 213 municipalities. Some municipal
   boundaries changed in 2016, so the 2011 results were moved onto today's boundaries by area.
3. **Measured the two leaks** for each municipality:
   - **Registration rate** = registered voters ÷ adults who may vote
   - **Turnout** = votes cast ÷ registered voters
   - **Real participation** = registration rate × turnout (the share of *all* adults who voted)
4. **Compared each municipality with a typical one.** "Typical" is the middle municipality (the median). Being above or
   below typical on each rate places a municipality in one of the four groups.
5. **Forecast 2026 turnout.** We took each municipality's 2021 turnout and added the national change in turnout seen
   in the 2024 national election.
   - We also tested a more complex statistical model that tried to predict each municipality separately. When we tested
     it fairly (training on 2011→2016 and checking against 2016→2021), it was **not more accurate** than the simple
     approach. We therefore kept the simple method and said so openly.
   - Every forecast comes with a **range**, not a single number. When we tested the method on 2021, about 8 in 10
     municipalities fell inside their range.
6. **Built the dashboard** so the results can be explored without any technical skills.

The work is split into numbered steps (notebooks), run in order:

| Step | What it does |
|---|---|
| 00 | Setup: checks the tools and folders |
| 01 | Cleans municipal election results (2011, 2016, 2021) |
| 02 | Cleans voter registration figures |
| 03 | Cleans national election results (2019, 2024) |
| 04 | Cleans Census 2022 figures (adults who may vote, services, education) |
| 05 | Prepares municipal boundaries and maps |
| 06 | Joins everything into one master table (one row per municipality) |
| 07 | Explores the data: charts and patterns |
| 08 | Builds and tests the 2026 turnout forecast |
| 09 | Prepares the small files the dashboard reads |

---

## 5. Where the data comes from

All data is **public**. The exact web addresses and download dates are listed in `docs/sources.csv`.

| Source | What we used it for |
|---|---|
| Electoral Commission of South Africa (IEC): municipal election results 2011, 2016, 2021 | Registered voters, votes cast, turnout |
| IEC: national election results 2019, 2024 | The expected national change in turnout for 2026, and recovery after COVID |
| IEC: voter registration statistics, September 2026 | The 2026 voters' roll, including ages 18–29 |
| Statistics South Africa: Census 2022 | Number of adults who may vote (citizens aged 18+), services, education |
| Municipal Demarcation Board | Municipal boundaries, area, neighbours |
| IEC municipal results atlas | Moving 2011 results onto today's boundaries |

---

## 6. Limitations

- **A link is not proof of a cause.** Patterns across municipalities cannot show *why* individual people do or do not vote.
- **Youth figures cover registration only.** The IEC does not publish turnout by age for each municipality.
- **Census counts are not perfect.** In 10 small municipalities, more people are registered than the Census counted as
  adults. Their registration rate is flagged and treated as 100%.
- **2021 was a COVID election.** Its low turnout was partly a one-off, which is why 2026 is given as a range.
- **Boundaries changed in 2016.** 2011 results were estimated for today's boundaries using area shares.
- **Registration is a snapshot** from September 2026. It will change until the voters' roll closes.
- **Small sample.** There are 213 municipalities and only two past election-to-election changes to learn from.

---

## 7. What is in this folder

```
README.md          this file
web/               the dashboard website (start here to see the results)
app/artifacts/     the two data files the dashboard reads (finished results, ready to use)
notebooks/         the analysis, step by step (00 to 09)
src/               small helper code shared by the notebooks
docs/sources.csv   every data source, with its web address and download date
data/              raw and cleaned data (empty here: kept on the team's shared Google Drive)
models/            saved models (empty here)
reports/figures/   charts for the presentation (empty here)
requirements.txt   the software the notebooks need
render.yaml        settings for putting the dashboard online (Render)
```

---

## 8. How to open the dashboard on your own computer

You need **Python** (version 3.10 or newer), which is free from https://www.python.org/downloads/. You do **not** need
the raw data; the dashboard uses the finished files in `app/artifacts/`.

1. Unzip the project folder.
2. Open a terminal in that folder. On Windows, open the folder in File Explorer, click the address bar, type `cmd`
   and press Enter.
3. Install what the dashboard needs (only the first time):
   ```
   pip install -r web/requirements.txt
   ```
4. Start the dashboard:
   ```
   python web/app.py
   ```
5. Open a web browser and go to **http://localhost:5000**

To stop the dashboard, go back to the terminal and press `Ctrl + C`.

---

## 9. For technical readers: reproducing the full analysis

**Folder paths.** `src/config.py` finds the data folder automatically, in this order:
1. The `DIRISA_ROOT` environment variable, if set (e.g. the Google Drive for Desktop folder `G:/My Drive/DIRISA_SDC`)
2. On Google Colab: `/content/drive/MyDrive/DIRISA_SDC`
3. Otherwise: this project folder, with the data placed in `data/`

**Local setup (Windows; macOS/Linux commands in comments)**
```bash
python -m venv .venv
.venv\Scripts\activate                                # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
setx DIRISA_ROOT "G:\My Drive\DIRISA_SDC"             # optional; macOS/Linux: export DIRISA_ROOT=...
```

**Google Colab.** Open `notebooks/00_setup.ipynb` and run all cells. This needs a one-time shortcut to the
`DIRISA_SDC` folder in My Drive.

**Steps**
1. Download each source listed in `docs/sources.csv` into `data/raw/<raw_folder>/`.
2. Run the notebooks in number order, from `00_setup` to `09_dashboard_prep`.
3. `09_dashboard_prep` writes `app/artifacts/dashboard.csv` and `app/artifacts/municipalities.geojson`, which the
   dashboard reads.
4. The exact package versions used are recorded in `environment.json` by `00_setup`.

**Dashboard technology.** Python Flask serves the data. The pages use HTML and JavaScript, with Chart.js for the charts
and Leaflet for the map. For online hosting, `render.yaml` runs it with gunicorn; `/healthz` is the health check.

---

## 10. Privacy

All data is publicly available. Candidate lists contain personal information. Those personal columns are removed as
soon as the files are loaded (`src/privacy.py`), only totals are kept, and the raw files are never stored in this
project.

---

## 11. The team

**Team UL, University of Limpopo**: Eshley, Morongwa, Mthokozisi, Nkululeko, Khwathisedzo and Thato.

Built for the **DIRISA Student Datathon Challenge 2026**.
