import os
from datetime import datetime, date, time
from io import StringIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT, ".env"))
API = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="ShipSense | ETA Control Tower", page_icon="📦",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background:#080e1b; color:#e8eef8; }
[data-testid="stHeader"] { background:rgba(8,14,27,.96); }
.block-container { padding-top:1.0rem; padding-bottom:2rem; max-width:1500px; }
section[data-testid="stSidebar"] { background:#0d1729; border-right:1px solid #1c2a43; }
section[data-testid="stSidebar"] * { color:#dbe6f6; }
.hero { background:linear-gradient(110deg,#101d35,#123e55); border:1px solid #244660;
        border-radius:16px; padding:20px 24px; margin-bottom:18px; }
.hero h1 { margin:0; color:#f4f8ff; font-size:1.8rem; }
.hero p { margin:.35rem 0 0; color:#a9c2d8; }
.kpi { background:#111c31; border:1px solid #22334e; border-radius:13px;
       padding:14px 16px; min-height:105px; }
.kpi-label { color:#91a6c2; font-size:.78rem; }
.kpi-value { color:#f4f8ff; font-size:1.8rem; font-weight:750; margin-top:5px; }
.kpi-note { color:#36c5bd; font-size:.72rem; margin-top:2px; }
.panel { background:#101a2d; border:1px solid #22334e; border-radius:14px;
         padding:14px 16px; margin-bottom:12px; }
.panel-title { font-size:1rem; font-weight:700; color:#eaf2ff; margin-bottom:8px; }
.muted { color:#8fa4c0; font-size:.78rem; }
div[data-testid="stMetric"] { background:#111c31; border:1px solid #22334e; border-radius:12px; padding:12px; }
div[data-testid="stMetricLabel"] { color:#91a6c2; }
div[data-testid="stMetricValue"] { color:#f4f8ff; }
.stButton>button[kind="primary"] { background:#19a7c5; border:0; color:white; font-weight:700; }
div[data-testid="stDataFrame"] { border:1px solid #22334e; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

def api_get(path, params=None):
    try:
        response = requests.get(API + path, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        st.error(f"API request failed: {exc}. Confirm FastAPI and MySQL are running.")
        return None

def api_post(path, data=None, files=None, timeout=120):
    try:
        response = requests.post(API + path, json=data, files=files, timeout=timeout)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            st.error(f"Request failed ({response.status_code}): {detail}")
            return None
        return response.json()
    except Exception as exc:
        st.error(f"Could not reach backend: {exc}")
        return None

def panel_title(title, subtitle=None):
    st.markdown(f'<div class="panel-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)

def show_kpi(col, label, value, note="Live database"):
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div>'
                 f'<div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',
                 unsafe_allow_html=True)

st.sidebar.markdown("## 📦 TOWER ETA")
st.sidebar.caption("LOGISTICS INTELLIGENCE CONTROL TOWER")
st.sidebar.markdown("---")
page = st.sidebar.radio("WORKSPACE", [
    "Overview", "Shipments", "New Shipment", "CSV Upload",
    "Synthetic Data", "Exceptions", "Data Quality"
], label_visibility="visible")
st.sidebar.markdown("---")
health = api_get("/api/health")
if health and health.get("status") == "healthy":
    st.sidebar.success("API + MySQL connected")
else:
    st.sidebar.error("Backend / database unavailable")
st.sidebar.caption("YottaFlex AI Candidate Project")
st.sidebar.caption("Synthetic data • Explainable ETA • Auditable decisions")

st.markdown('<div class="hero"><h1>ShipSense ETA Control Tower</h1>'
            '<p>Predict earlier. Explain every delay. Keep every decision traceable.</p></div>',
            unsafe_allow_html=True)

if page == "Overview":
    data = api_get("/api/analytics/overview")
    if data:
        total = int(data.get("total_shipments") or 0)
        delivered = int(data.get("delivered_count") or 0)
        delayed = int(data.get("at_risk_count") or data.get("delayed_count") or 0)
        active = int(data.get("active_count") or 0)
        ontime = float(data.get("on_time_pct") or 0)
        k = st.columns(4)
        show_kpi(k[0], "TOTAL SHIPMENTS", f"{total:,}", "All lifecycle states")
        show_kpi(k[1], "AT RISK / DELAYED", f"{delayed:,}", "Latest ETA snapshots marked medium/high risk")
        show_kpi(k[2], "ETA ERROR (MAE)", f"{float(data.get('eta_mae_minutes') or 0)/60:.1f} h", "Actual vs latest predicted ETA")
        show_kpi(k[3], "ON-TIME RATE", f"{ontime:.1f}%", f"{delivered:,} delivered")
        left, right = st.columns([1.35, 1])
        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            panel_title("Facility network", "Schematic view of facilities ranked by observed queue wait; not a geographic map.")
            facilities = api_get("/api/facilities")
            if facilities:
                fdf = pd.DataFrame(facilities).fillna({"avg_wait_minutes": 0, "max_queue": 0})
                fdf = fdf.head(18).copy()
                fdf["node_x"] = [((i % 6) * 1.0) for i in range(len(fdf))]
                fdf["node_y"] = [-(i // 6) * 1.0 for i in range(len(fdf))]
                fig = go.Figure()
                for i in range(len(fdf)-1):
                    fig.add_trace(go.Scatter(x=[fdf.iloc[i].node_x, fdf.iloc[i+1].node_x],
                        y=[fdf.iloc[i].node_y, fdf.iloc[i+1].node_y],
                        mode="lines", line=dict(color="#263a58", width=1), hoverinfo="skip", showlegend=False))
                fig.add_trace(go.Scatter(x=fdf.node_x, y=fdf.node_y, mode="markers+text",
                    text=fdf.facility_id, textposition="bottom center",
                    marker=dict(size=18, color=fdf.avg_wait_minutes, colorscale="Turbo",
                                showscale=True, colorbar=dict(title="Wait min"), line=dict(color="#dce8fa",width=1)),
                    customdata=fdf[["facility_name","city","avg_wait_minutes","max_queue"]],
                    hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Wait: %{customdata[2]} min<br>Max queue: %{customdata[3]}<extra></extra>"))
                fig.update_layout(template="plotly_dark", paper_bgcolor="#101a2d", plot_bgcolor="#101a2d",
                    height=300, margin=dict(l=5,r=5,t=5,b=30), xaxis=dict(visible=False),
                    yaxis=dict(visible=False), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            panel_title("Shipment risk intelligence", "Latest ETA snapshots grouped into LOW, MEDIUM and HIGH risk")
            distribution = api_get("/api/analytics/risk-distribution")
            if distribution:
                risk_counts = {row["risk_level"]: int(row["shipment_count"]) for row in distribution}
                r1, r2, r3 = st.columns(3)
                r1.metric("LOW", f"{risk_counts.get('LOW', 0):,}")
                r2.metric("MEDIUM", f"{risk_counts.get('MEDIUM', 0):,}")
                r3.metric("HIGH", f"{risk_counts.get('HIGH', 0):,}")
            selected_risk = st.selectbox(
                "Risk category", ["ALL", "LOW", "MEDIUM", "HIGH"],
                index=0, key="overview_risk_filter"
            )
            risk_params = {"limit": 1000}
            if selected_risk != "ALL":
                risk_params["risk_level"] = selected_risk
            risk = api_get("/api/analytics/high-risk", params=risk_params)
            if risk:
                rdf = pd.DataFrame(risk)
                columns = ["shipment_id", "service_name", "predicted_eta",
                           "predicted_delay_minutes", "risk_level"]
                st.dataframe(rdf[columns], use_container_width=True, hide_index=True)
                if not rdf.empty:
                    chosen = st.selectbox("Inspect shipment", rdf.shipment_id.tolist(), key="risk_ship")
                    detail = api_get(f"/api/shipments/{chosen}")
                    if detail and detail.get("etas"):
                        eta = detail["etas"][0]
                        st.metric("Predicted delay", f"{eta['predicted_delay_minutes']} min",
                                  f"Risk: {eta['risk_level']}")
            else:
                st.info(f"No shipments currently match {selected_risk} risk.")
            st.markdown('</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            panel_title("Why shipments run late", "Derived from recorded delay assessments")
            reasons = api_get("/api/analytics/delay-reasons")
            if reasons:
                rdf = pd.DataFrame(reasons)
                if not rdf.empty:
                    st.plotly_chart(px.bar(rdf, x="reason_code", y="count", color="reason_code",
                        template="plotly_dark", color_discrete_sequence=["#27b8d1","#6c83e8","#35c7b2","#d77ca9"]),
                        use_container_width=True)
                else: st.info("No assessed delay reasons yet.")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            panel_title("Network snapshot")
            st.metric("Active shipments", f"{active:,}")
            st.metric("Delivered shipments", f"{delivered:,}")
            st.metric("Average delivery variance", f"{float(data.get('eta_mae_minutes') or 0):,.0f} minutes")
            st.markdown('</div>', unsafe_allow_html=True)
        st.caption("ETA is a rule-based estimate. Synthetic inputs are not live carrier or weather feeds.")
    else:
        st.info("No overview data returned. Check the backend and database.")

elif page == "Shipments":
    st.subheader("Shipment visibility")
    c1, c2 = st.columns([1, 2])
    status = c1.selectbox("Lifecycle status", ["All","CREATED","PICKED_UP","IN_TRANSIT","OUT_FOR_DELIVERY","DELIVERED","DELAYED","EXCEPTION"])
    search = c2.text_input("Search shipment ID", placeholder="SHP-2026-000001")
    params = {"limit": 500}
    if status != "All": params["status"] = status
    if search: params["search"] = search
    rows = api_get("/api/shipments", params=params)
    if rows is not None:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        if not df.empty:
            sid = st.selectbox("Open shipment record", df.shipment_id.tolist())
            detail = api_get(f"/api/shipments/{sid}")
            if detail:
                a,b = st.columns(2)
                a.write("Shipment record"); a.json(detail["shipment"])
                b.write("Legs"); b.dataframe(pd.DataFrame(detail["legs"]), use_container_width=True, hide_index=True)
                st.markdown("#### Tracking event timeline")
                st.dataframe(pd.DataFrame(detail["events"]), use_container_width=True, hide_index=True)
                st.markdown("#### Immutable ETA snapshots")
                st.dataframe(pd.DataFrame(detail["etas"]), use_container_width=True, hide_index=True)

elif page == "New Shipment":
    st.subheader("Create shipment & predict ETA")
    st.caption("Enter operational inputs. ShipSense validates parent IDs, creates the shipment/leg/event, calculates an explainable ETA and persists the snapshot.")
    meta = api_get("/api/meta/options")
    if meta and meta.get("facilities") and meta.get("carriers") and meta.get("service_levels"):
        facilities = meta["facilities"]
        facility_labels = {f"{f['facility_id']} · {f['city']}": f["facility_id"] for f in facilities}
        carrier_labels = {f"{c['carrier_name']} ({c['carrier_id']})": c["carrier_id"] for c in meta["carriers"]}
        service_labels = {f"{s['service_name']} · SLA {s['sla_hours']}h": s["service_level_id"] for s in meta["service_levels"]}
        with st.form("new_shipment_form"):
            x1,x2,x3 = st.columns(3)
            origin_label = x1.selectbox("Origin facility", list(facility_labels))
            dest_options = [x for x in facility_labels if facility_labels[x] != facility_labels[origin_label]]
            dest_label = x2.selectbox("Destination facility", dest_options)
            carrier_label = x3.selectbox("Carrier", list(carrier_labels))
            x4,x5,x6 = st.columns(3)
            service_label = x4.selectbox("Service level", list(service_labels))
            distance = x5.number_input("Route distance (km)", min_value=1.0, max_value=10000.0, value=570.0, step=10.0)
            priority = x6.selectbox("Priority", ["LOW","MEDIUM","HIGH"], index=1)
            x7,x8,x9 = st.columns(3)
            weather = x7.selectbox("Weather condition", ["CLEAR","LIGHT_RAIN","HEAVY_RAIN","FOG","STORM","FLOODING"])
            queue_wait = x8.number_input("Facility queue wait (minutes)", min_value=0, max_value=10080, value=30, step=5)
            promise_date = x9.date_input("Promised delivery date", value=date.today())
            promise_time = st.time_input("Promised delivery time (UTC)", value=time(18,0))
            submitted = st.form_submit_button("Create shipment & predict ETA", type="primary", use_container_width=True)
        if submitted:
            payload = {
                "origin_facility_id": facility_labels[origin_label],
                "destination_facility_id": facility_labels[dest_label],
                "carrier_id": carrier_labels[carrier_label],
                "service_level_id": service_labels[service_label],
                "promised_delivery_at": datetime.combine(promise_date,promise_time).isoformat(),
                "total_distance_km": distance, "weather_condition": weather,
                "facility_wait_minutes": queue_wait, "priority": priority
            }
            result = api_post("/api/shipments", payload)
            if result:
                st.success(f"Shipment {result['shipment_id']} created and ETA snapshot saved.")
                a,b,c = st.columns(3)
                a.metric("Predicted ETA", str(result["predicted_eta"]))
                b.metric("Predicted delay", f"{result['predicted_delay_minutes']} min")
                c.metric("Delay risk", result["risk_level"])
                st.markdown("#### Explainable ETA adjustments")
                st.json(result["adjustments_minutes"])
                st.info(result["explanation"])
                st.code(f"Shipment ID: {result['shipment_id']}\nETA ID: {result['eta_id']}")
    else:
        st.warning("Master data is missing. Generate/load the starter synthetic dataset first.")

elif page == "CSV Upload":
    st.subheader("Bulk shipment ingestion")
    st.write("Upload a UTF-8 CSV. Each valid row creates a shipment, route leg, initial event and ETA snapshot. Invalid rows are reported without stopping valid rows.")
    meta = api_get("/api/meta/options")
    if meta and meta.get("facilities") and meta.get("carriers") and meta.get("service_levels"):
        f0, f1 = meta["facilities"][0], meta["facilities"][1]
        c0, s0 = meta["carriers"][0], meta["service_levels"][0]
        template = pd.DataFrame([{
            "origin_facility_id":f0["facility_id"],"destination_facility_id":f1["facility_id"],
            "carrier_id":c0["carrier_id"],"service_level_id":s0["service_level_id"],
            "promised_delivery_at":datetime.utcnow().replace(hour=18,minute=0,second=0,microsecond=0).isoformat(sep=" "),
            "total_distance_km":570,"weather_condition":"HEAVY_RAIN","facility_wait_minutes":45,"priority":"HIGH"
        }])
        st.download_button("Download CSV template", template.to_csv(index=False).encode("utf-8"),
                           file_name="shipsense_shipment_template.csv", mime="text/csv")
        uploaded = st.file_uploader("Choose shipment CSV", type=["csv"])
        if uploaded and st.button("Validate & import CSV", type="primary"):
            result = api_post("/api/shipments/import", files={"file":(uploaded.name,uploaded.getvalue(),"text/csv")}, timeout=300)
            if result:
                a,b = st.columns(2)
                a.metric("Created shipments", result["created_count"])
                b.metric("Rows with errors", result["error_count"])
                if result["created"]:
                    st.dataframe(pd.DataFrame(result["created"]), use_container_width=True, hide_index=True)
                if result["errors"]:
                    st.error("Some rows need correction.")
                    st.dataframe(pd.DataFrame(result["errors"]), use_container_width=True, hide_index=True)

elif page == "Synthetic Data":
    st.subheader("Reproducible synthetic data generator")
    st.warning("Replacing the database deletes existing shipment, ETA, event, route and synthetic master records, including manually entered shipments. Download/export anything you need first.")
    with st.form("synthetic_form"):
        size = st.selectbox("Dataset scale", ["starter","medium","full"])
        seed = st.number_input("Fixed random seed", min_value=1, max_value=999999999, value=20261022)
        confirm = st.checkbox("I understand this replaces the current ShipSense database dataset.")
        run = st.form_submit_button("Generate & load synthetic dataset", type="primary", use_container_width=True)
    if run:
        if not confirm:
            st.error("Please confirm database replacement before proceeding.")
        else:
            with st.spinner("Generating deterministic data and loading MySQL. Full scale may take several minutes..."):
                result = api_post(f"/api/synthetic/generate?size={size}&seed={int(seed)}&replace_existing=true",
                                  data={}, timeout=1200)
            if result:
                st.success("Synthetic dataset generated and loaded.")
                st.json(result["manifest"])
                st.code(result["loader_output"])
    st.info("For a non-destructive generation of CSV/JSON files only, run in the project terminal: python -m generator.generate --size starter --seed 20261022")

elif page == "Exceptions":
    st.subheader("Exception register")
    rows = api_get("/api/anomalies")
    if rows is not None:
        df = pd.DataFrame(rows)
        st.metric("Flagged data-quality exceptions", len(df))
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.plotly_chart(px.histogram(df, x="issue_type", color="severity", template="plotly_dark"),
                            use_container_width=True)
        else:
            st.info("No exceptions are currently recorded.")

elif page == "Data Quality":
    st.subheader("Data quality & reproducibility")
    rows = api_get("/api/anomalies")
    if rows is not None:
        a,b = st.columns(2)
        a.metric("Recorded exceptions", len(rows))
        b.metric("Ground-truth file kept separate", "Yes")
        st.markdown("#### Validation commands")
        st.code("python -m validation.validate_data\npython -m validation.reproducibility\npytest -v", language="powershell")
        st.caption("Run these checks from the project root in an activated virtual environment. The validation output is generated locally by the validator.")
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.caption("ShipSense • Synthetic logistics intelligence • UTC timestamps • Explainable ETA rules v2.0 • Ground truth is not used as a prediction feature.")
