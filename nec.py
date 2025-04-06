# voetbalplanner_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import random
import itertools
from collections import defaultdict, Counter

# ========== PAGINA-INSTELLINGEN ==========
st.set_page_config(page_title="Voetbalseizoen Planner", layout="wide")

# ========== CONSTANTEN ==========
personen = ["Seppie", "Rob", "Reinout", "Laurens", "Tobias"]
dagtypes = ["vr", "za", "zo"]
top_teams = ["Ajax", "PSV", "Feyenoord", "Maakt me niet uit"]
eredivisie_teams = ["Ajax", "PSV", "Feyenoord", "AZ", "Twente", "Heerenveen", "Sparta", "NEC", "Go Ahead Eagles", "Fortuna Sittard", "Utrecht", "PEC Zwolle", "RKC Waalwijk", "Heracles Almelo", "Volendam", "Vitesse", "Almere City"]

# ========== INITIATIE ==========
if "df" not in st.session_state:
    wedstrijden = [
        {
            "Datum": f"2025-{str((i//4)+8).zfill(2)}-{str((i%4)*7 + 3).zfill(2)}",
            "Tijd": "14:30",
            "Tegenstander": eredivisie_teams[i % len(eredivisie_teams)],
            "Dagtype": dagtypes[i % len(dagtypes)],
            "IsTopper": eredivisie_teams[i % len(eredivisie_teams)] in ["Ajax", "PSV", "Feyenoord"],
            **{persoon: "" for persoon in personen},
            "Toegewezen": "",
            "Afmeldingen": []
        }
        for i in range(17)
    ]
    st.session_state.df = pd.DataFrame(wedstrijden)

# ========== ZIJBALK ==========
pagina = st.sidebar.radio("📂 Ga naar", ["🗓️ Beschikbaarheid", "📋 Planner & voorstel", "📊 Overzicht", "📌 Definitief schema"])
df = st.session_state.df.copy()

# ========== PAGINA: OVERZICHT ==========
if pagina == "📊 Overzicht":
    st.header("📊 Inzichten en Verdeling")
    bron_df = st.session_state.get("definitief_df", st.session_state.get("voorstel_df", st.session_state.df))

    toegewezen_df = bron_df[bron_df["Toegewezen"].str.len() > 0].copy()
    if toegewezen_df.empty:
        st.info("Er zijn nog geen toegewezen wedstrijden. Genereer eerst een voorstel bij 📋 Planner & voorstel.")
    else:
        # Samen-indelingen
        combi_telling = Counter()
        for row in toegewezen_df.itertuples():
            spelers = row.Toegewezen.split(", ")
            for combi in itertools.combinations(sorted(spelers), 2):
                combi_telling[combi] += 1

        if combi_telling:
            combi_df = pd.DataFrame([{"Combinatie": f"{a} & {b}", "Aantal": v} for (a, b), v in combi_telling.items()])
            st.plotly_chart(px.bar(combi_df, x="Combinatie", y="Aantal", title="Hoe vaak samen gespeeld"))

        # Aantal wedstrijden per persoon
        telling = Counter()
        for row in toegewezen_df.itertuples():
            for p in row.Toegewezen.split(", "):
                telling[p] += 1
        if telling:
            count_df = pd.DataFrame.from_dict(telling, orient="index", columns=["Aantal wedstrijden"])
            st.bar_chart(count_df)

        # Dagtype per persoon
        dagtype_data = []
        for p in personen:
            rows = toegewezen_df[toegewezen_df["Toegewezen"].str.contains(p, na=False)]
            for dag, aantal in rows["Dagtype"].value_counts().items():
                dagtype_data.append({"Persoon": p, "Dagtype": dag, "Aantal": aantal})
        dagtype_df = pd.DataFrame(dagtype_data)
        if not dagtype_df.empty:
            st.plotly_chart(px.bar(dagtype_df, x="Persoon", y="Aantal", color="Dagtype", barmode="stack", title="Verdeling per Dagtype"))

        # Toppers per persoon
        topper_data = []
        for p in personen:
            rows = toegewezen_df[toegewezen_df["Toegewezen"].str.contains(p, na=False)]
            toppers = rows["IsTopper"].sum()
            topper_data.append({"Persoon": p, "Toppers": toppers})
        topper_df = pd.DataFrame(topper_data)
        if not topper_df.empty:
            st.plotly_chart(px.bar(topper_df, x="Persoon", y="Toppers", title="Topwedstrijden per Persoon"))

# 📅 Beschikbaarheid
if pagina == "🗓️ Beschikbaarheid":
    st.title("🙋 Beschikbaarheid & Afmelden")

    if st.button("✨ Genereer fictieve data (75%)"):
        voorkeur_topper = {}
        for persoon in personen:
            df[persoon] = df[persoon].apply(lambda x: "v" if random.random() < 0.75 else "")
            voorkeur_topper[persoon] = random.choice(top_teams)
        st.session_state.df = df
        st.session_state.voorkeur_topper = voorkeur_topper
        st.success("Fictieve beschikbaarheid én topclubvoorkeuren gegenereerd.")

    voorkeur_topper = st.session_state.get("voorkeur_topper", {persoon: None for persoon in personen})
    with st.expander("🎯 Topwedstrijdvoorkeur instellen"):
        for persoon in personen:
            voorkeur_topper[persoon] = st.selectbox(f"Voorkeur voor {persoon}", [""] + top_teams, key=f"voorkeur_{persoon}")
    st.session_state.voorkeur_topper = voorkeur_topper

    for persoon in personen:
        with st.expander(f"📅 Beschikbaarheid: {persoon}", expanded=False):
            for i, row in df.iterrows():
                col1, col2 = st.columns([2, 2])
                with col1:
                    beschikbaar = st.checkbox(
                        f"{row['Datum']} {row['Tijd']} - {row['Tegenstander']}{' ⭐' if row['IsTopper'] else ''}",
                        value=row[persoon] == "v",
                        key=f"{persoon}_{i}_beschikbaar")
                with col2:
                    afgemeld = st.checkbox("❌ Afmelden",
                                           key=f"{persoon}_{i}_afmelden",
                                           value=persoon in row["Afmeldingen"])
                df.at[i, persoon] = "v" if beschikbaar else ""
                afmeldingen = set(row["Afmeldingen"])
                if afgemeld:
                    afmeldingen.add(persoon)
                else:
                    afmeldingen.discard(persoon)
                df.at[i, "Afmeldingen"] = list(afmeldingen)
    st.session_state.df = df

# 📋 Planner
elif pagina == "📋 Planner & voorstel":
    st.title("📋 Rooster Genereren")

    if st.button("💾 Genereer nieuw voorstel"):
        df = st.session_state.df.copy()
        voorstel_df = df.copy()
        tellingen = Counter()
        toppers = Counter()
        dagtypes_persoon = defaultdict(Counter)
        samenstellingen = Counter()
        toewijzingen = []

        for i, row in voorstel_df.iterrows():
            afwezig = set(row["Afmeldingen"])
            beschikbaar = [p for p in personen if row[p] == "v" and p not in afwezig]
            beste_groep, beste_score = None, float("inf")

            for groep_size in [3, 2]:
                if len(beschikbaar) >= groep_size:
                    for groep in itertools.combinations(beschikbaar, groep_size):
                        score = sum(tellingen[p] for p in groep)
                        if row["IsTopper"]:
                            score += sum(toppers[p] for p in groep) * 10
                            for p in groep:
                                if st.session_state.voorkeur_topper.get(p) == row["Tegenstander"]:
                                    score -= 15
                        for p in groep:
                            score += dagtypes_persoon[p][row["Dagtype"]] * 3
                        score += samenstellingen[frozenset(groep)] * 2
                        for a, b in itertools.combinations(groep, 2):
                            combi = frozenset([a, b])
                            huidige = samenstellingen[combi]
                            if any(abs(huidige - samenstellingen[frozenset([a, x])]) > 3 for x in personen if x != b and x != a):
                                score += 50
                        if score < beste_score:
                            beste_groep, beste_score = groep, score
                if beste_groep:
                    break

            if beste_groep:
                for p in beste_groep:
                    tellingen[p] += 1
                    dagtypes_persoon[p][row["Dagtype"]] += 1
                    if row["IsTopper"]:
                        toppers[p] += 1
                samenstellingen[frozenset(beste_groep)] += 1
                toewijzingen.append(", ".join(beste_groep))
            else:
                toewijzingen.append("NIEMAND BESCHIKBAAR")

        voorstel_df["Toegewezen"] = toewijzingen
        st.session_state.voorstel_df = voorstel_df
        st.session_state.df = voorstel_df
        st.success("Nieuw voorstel gegenereerd.")
        st.dataframe(voorstel_df[["Datum", "Tegenstander", "Toegewezen"]])


# ========== PAGINA: DEFINITIEF SCHEMA ==========
elif pagina == "📌 Definitief schema":
    st.title("📌 Definitieve Planning & Vervangingen")

    if "definitief_df" not in st.session_state:
        st.session_state.definitief_df = df.copy()

    def_df = st.session_state.definitief_df.copy()
    vervangingsvoorstellen = st.session_state.get("vervangingsvoorstellen", {})

    for i, row in def_df.iterrows():
        toegewezen = set(row["Toegewezen"].split(", ")) if row["Toegewezen"] else set()
        afwezig = set(row["Afmeldingen"])
        beschikbaar = [p for p in personen if row[p] == "v" and p not in afwezig and p not in toegewezen]

        for af in toegewezen & afwezig:
            voorstel_key = f"{i}_{af}"
            if voorstel_key not in vervangingsvoorstellen:
                min_wed = float("inf")
                vervanger = None
                for p in beschikbaar:
                    count = def_df["Toegewezen"].str.contains(p).sum()
                    if count < min_wed:
                        min_wed, vervanger = count, p
                if vervanger:
                    vervangingsvoorstellen[voorstel_key] = vervanger

            voorgesteld = vervangingsvoorstellen.get(voorstel_key)
            if voorgesteld:
                st.info(f"{af} is afgemeld voor {row['Datum']} - {row['Tegenstander']}. {voorgesteld} wordt voorgesteld als vervanger.")
                if st.button("✅ Accepteren", key=f"accepteer_{i}_{af}"):
                    toegewezen.remove(af)
                    toegewezen.add(voorgesteld)
                    st.success(f"{af} vervangen door {voorgesteld}")

        def_df.at[i, "Toegewezen"] = ", ".join(sorted(toegewezen))

    st.session_state.definitief_df = def_df
    st.dataframe(def_df[["Datum", "Tegenstander", "Toegewezen"]])

# 📊 Overzicht
elif pagina == "📊 Overzicht":
    bron_df = st.session_state.get("definitief_df", st.session_state.get("voorstel_df", st.session_state.df))
    render_overzicht(bron_df)
