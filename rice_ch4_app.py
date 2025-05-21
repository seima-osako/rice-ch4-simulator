from __future__ import annotations
import math

import geopandas as gpd
import streamlit as st
from st_on_hover_tabs import on_hover_tabs
import xarray as xr
from branca.colormap import linear
from folium import Map, TileLayer, GeoJson, LayerControl, GeoJsonTooltip
from shapely.geometry import box, Point
from streamlit_folium import st_folium

import rice_ch4_params as params

# ------------ Page settings ------------
st.set_page_config(
    page_title="Rice CH₄ Dashboard",
    page_icon="🌾",
    layout="wide",
)
# ------------ Sidebar Tabs ------------
st.markdown(
    """
    <style>
    section[data-testid='stSidebar'] .stSelectbox > label,
    section[data-testid='stSidebar'] .stNumberInput > label,
    section[data-testid='stSidebar'] .stRadio > label {
        color: #fff !important;
    }

    section[data-testid='stSidebar'] .stSelectbox ul li,
    section[data-testid='stSidebar'] [data-baseweb="select"] ul li,
    section[data-testid='stSidebar'] [data-baseweb="select"] [role="option"],
    section[data-testid='stSidebar'] div[role="listbox"] li {
        color: #000 !important;
    }

    section[data-testid='stSidebar'] button span,
    section[data-testid='stSidebar'] button p {
        color: #000 !important;
    }

    section[data-testid='stSidebar'] [data-testid='stMetric'] label,
    section[data-testid='stSidebar'] [data-testid='stMetric']
    div[data-testid='stMetricValue'] {
        color: #fff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
with open("./style.css") as f:
    css_style = f.read()
st.markdown(f"<style>{css_style}</style>", unsafe_allow_html=True)
with st.sidebar:
    tab = on_hover_tabs(
        tabName=["Home", "Map"], iconName=["home", "map"], default_choice=0
    )
if tab == "Home":
    with open("markdown/home_content.md", encoding="utf-8") as f:
        home_md = f.read()
    st.markdown(home_md, unsafe_allow_html=True)
elif tab == "Map":
    # ------------ File paths and range ------------
    NC_PATH = "./data/inten_phsc_2021.nc"
    GEOJSON_PATH = "./data/prefectures.geojson"
    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 24.0, 46.0, 122.0, 154.0

    # ------------ Multilingual dictionary ------------
    LANGS = {
        "ja": {
            "title": "🌾 水田 CH₄ 排出簡易シミュレーション",
            "subtitle": "中干し延長によるポテンシャル削減効果の試算",
            "sidebar_header": "入力パラメータ",
            "prefecture": "都道府県",
            "drainage_class": "排水性クラス",
            "straw_removal": "稲わら持ち出し量 (kg/10a)",
            "calc": "計算する",
            "select_area": "選択水田面積",
            "no_selection": "ポリゴンをクリックして面積を選択してください",
            "loading_map_text": "地図を読み込んでいます...",
            "no_map_data_warning": (
                "{pref_name} には表示可能な水田データがありません。"
            ),
        },
        "en": {
            "title": "🌾 Simplified Rice Paddy CH₄ Emission Simulation",
            "subtitle": (
                "Estimating Potential Reduction Effects from "
                "Extended Mid‑season Drainage"
            ),
            "sidebar_header": "Input Parameters",
            "prefecture": "Prefecture",
            "drainage_class": "Drainage Class",
            "straw_removal": "Straw Removal (kg/10a)",
            "calc": "Calculate",
            "select_area": "Selected Rice Paddy Area",
            "no_selection": "Click a polygon to select area",
            "loading_map_text": "Loading map...",
            "no_map_data_warning": ("No rice paddy data available for {pref_name}."),
        },
    }

    def t(key: str, **kwargs) -> str:
        lang = st.session_state.get("lang", "ja")
        text_template = LANGS[lang].get(key, f"[{lang}:{key}]")
        return text_template.format(**kwargs) if kwargs else text_template

    # ------------ CH₄ calculation function ------------
    PREF_TO_REGION, COEFF, PREF_TO_STRAW = (
        params.PREF_TO_REGION,
        params.COEFF,
        params.PREF_TO_STRAW,
    )
    DRAINAGE_CLASSES = params.DRAINAGE_CLASSES

    def compute_ch4(
        area_ha: float,
        prefecture: str,
        drainage_class: str,
        straw_removal_kg_10a: float,
        compost_rate: float,
    ):
        try:
            region = PREF_TO_REGION[prefecture]
        except KeyError:
            raise ValueError(f"Unsupported prefecture: {prefecture}")

        key = f"{region}{drainage_class}"
        try:
            coeffs = COEFF[key]
        except KeyError:
            raise ValueError(f"Coefficient not defined for: {key}")

        straw_prod = PREF_TO_STRAW[prefecture]
        incorporation_percent = max(
            0,
            min(
                90,
                100 * (1 - straw_removal_kg_10a / straw_prod),
            ),
        )
        incorporation_rate = incorporation_percent / 90

        straw_coeff = coeffs["straw"]
        manure_coeff = coeffs["manure"]
        no_straw_coeff = coeffs["no_straw"]

        coeff_val = min(
            max(straw_coeff, manure_coeff),
            no_straw_coeff
            + (straw_coeff - no_straw_coeff) * incorporation_rate
            + (manure_coeff - no_straw_coeff) * compost_rate,
        )

        GWP_CH4 = 28
        conv_factor = 16 / 12 * GWP_CH4 * 1e-3

        coeff_baseline = coeff_val
        coeff_project = coeff_val * 0.7
        baseline_emission = area_ha * coeff_baseline * conv_factor
        project_emission = area_ha * coeff_project * conv_factor

        return {
            "baseline_emission_tCO2": round(baseline_emission, 1),
            "project_emission_tCO2": round(project_emission, 1),
            "emission_reduction_tCO2": math.floor(baseline_emission - project_emission),
        }

    # ------------ Data loading ------------
    @st.cache_data
    def load_netcdf(path):
        da = xr.open_dataset(path)
        var = "area" if "area" in da.data_vars else list(da.data_vars)[0]
        da = da[var]
        return da.where(
            (da.lat >= LAT_MIN)
            & (da.lat <= LAT_MAX)
            & (da.lon >= LON_MIN)
            & (da.lon <= LON_MAX),
            drop=True,
        )

    @st.cache_data
    def load_pref(path):
        gdf = gpd.read_file(path).to_crs(4326)
        return gdf[["name", "geometry"]]

    da, gdf_pref = load_netcdf(NC_PATH), load_pref(GEOJSON_PATH)

    # ------------ Session initialization ------------
    for k, v in {
        "lang": "ja",
        "sel_uid": None,
        "sel_area": None,
        "sel_pref": "茨城県",
        "out": None,
    }.items():
        st.session_state.setdefault(k, v)

    # ------------ Sidebar UI ------------

    st.sidebar.selectbox(
        "Language / 言語",
        {"日本語": "ja", "English": "en"},
        index=0 if st.session_state.lang == "ja" else 1,
        on_change=lambda: st.session_state.update(
            lang="en" if st.session_state.lang == "ja" else "ja"
        ),
    )

    pref_list = gdf_pref["name"].tolist()
    if "_prev_pref" not in st.session_state:
        st.session_state._prev_pref = st.session_state.sel_pref

    selected_pref_name_from_selectbox = st.sidebar.selectbox(
        t("prefecture"),
        pref_list,
        index=pref_list.index(st.session_state.sel_pref),
    )

    # Check if the prefecture has changed
    if selected_pref_name_from_selectbox != st.session_state.sel_pref:
        st.session_state.sel_pref = selected_pref_name_from_selectbox
        if "map_center" in st.session_state:
            del st.session_state.map_center
        if "map_zoom" in st.session_state:
            del st.session_state.map_zoom
        st.session_state.sel_uid = None
        st.session_state.sel_area = None
        st.session_state.out = None
        st.session_state["_warn_no_area"] = False

    sel_drain = st.sidebar.selectbox(t("drainage_class"), DRAINAGE_CLASSES, index=2)
    sel_straw = st.sidebar.number_input(t("straw_removal"), 0.0, 2000.0, 0.0, 10.0)
    sel_comp = 0.5

    if st.session_state.sel_area:
        st.sidebar.metric(t("select_area"), f"{st.session_state.sel_area:.2f} ha")
    else:
        st.sidebar.warning(t("no_selection"))

    def _on_calc():
        if st.session_state.sel_area is None:
            st.session_state.out = None
            st.session_state["_warn_no_area"] = True
            return
        st.session_state["_warn_no_area"] = False
        st.session_state.out = compute_ch4(
            area_ha=st.session_state.sel_area,
            prefecture=st.session_state.sel_pref,
            drainage_class=sel_drain,
            straw_removal_kg_10a=sel_straw,
            compost_rate=sel_comp,
        )

    st.sidebar.button(t("calc"), on_click=_on_calc)

    # ------------ Main title ------------
    st.markdown(f"## {t('title')}")
    st.markdown(f"### {t('subtitle')}")

    # ------------ Calculation result display ------------
    if st.session_state.get("_warn_no_area"):
        st.warning(t("no_selection"))
    elif st.session_state.out:
        c1, c2, c3 = st.columns(3)
        c1.metric("Project (t‑CO₂)", st.session_state.out["project_emission_tCO2"])
        c2.metric("Baseline (t‑CO₂)", st.session_state.out["baseline_emission_tCO2"])
        c3.metric("Reduction (t‑CO₂)", st.session_state.out["emission_reduction_tCO2"])

    # ---------------- Map generation & click handling ----------------
    with st.spinner(t("loading_map_text")):
        # Get prefecture polygon
        selected_pref_name = st.session_state.sel_pref
        sel_poly = gdf_pref.loc[gdf_pref.name == selected_pref_name, "geometry"].iloc[0]

        # Extract only bbox of the prefecture from NetCDF
        @st.cache_data
        def grid_for_pref(pref_name: str) -> gpd.GeoDataFrame:
            poly = gdf_pref.loc[gdf_pref.name == pref_name, "geometry"].iloc[0]
            minx, miny, maxx, maxy = poly.bounds
            # Check lat axis direction
            lat_desc = float(da.lat[0]) > float(da.lat[-1])
            lat_slice = slice(maxy, miny) if lat_desc else slice(miny, maxy)
            sub = da.sel(lat=lat_slice, lon=slice(minx, maxx))
            if sub.size == 0:
                return gpd.GeoDataFrame(columns=["area", "lat", "lon", "geometry"])
            dlat = abs(float(sub.lat[1] - sub.lat[0]))
            dlon = abs(float(sub.lon[1] - sub.lon[0]))
            df = sub.to_dataframe("area").reset_index()
            # Remove rows where area is NaN
            df = df.dropna(subset=["area"])
            boxes = [
                box(
                    r.lon - dlon / 2,
                    r.lat - dlat / 2,
                    r.lon + dlon / 2,
                    r.lat + dlat / 2,
                )
                for r in df.itertuples()
            ]
            gdf = gpd.GeoDataFrame(df, geometry=boxes, crs=4326)
            gdf = gdf[(gdf["area"] > 0) & (gdf.geometry.within(poly))]
            return gdf

        gdf_clip = grid_for_pref(st.session_state.sel_pref)

        if gdf_clip.empty:
            st.warning(t("no_map_data_warning", pref_name=selected_pref_name))
        else:
            gdf_clip = gdf_clip.copy()
            gdf_clip["uid"] = gdf_clip.index.astype(str)

            # Color map
            vmin, vmax = gdf_clip["area"].min(), gdf_clip["area"].max()
            if vmin == vmax:
                vmin -= 0.01
                vmax += 0.01
            cmap = linear.YlGnBu_09.scale(vmin, vmax).to_step(9)
            cmap.colors = cmap.colors[::-1]
            cmap.caption = "Rice Area (ha)"

            # Map centroid & zoom
            current_pref_for_map = st.session_state.sel_pref
            sel_poly_for_map_init = sel_poly

            if (
                "map_center" not in st.session_state
                or st.session_state.get("_prev_pref_for_map_init")
                != current_pref_for_map
            ):
                st.session_state.map_center = [
                    sel_poly_for_map_init.centroid.y,
                    sel_poly_for_map_init.centroid.x,
                ]
                st.session_state.map_zoom = 9
                st.session_state._prev_pref_for_map_init = current_pref_for_map

            m = Map(
                location=st.session_state.map_center,
                zoom_start=st.session_state.map_zoom,
                tiles=None,
                control_scale=True,
            )

            TileLayer(
                "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&hl=en",
                name="Google Satellite",
                attr="Google",
            ).add_to(m)

            def style_fn(feat):
                props = feat["properties"]
                uid = str(props.get("uid"))
                area = props.get("area")
                sel = uid == str(st.session_state.sel_uid)
                fill_color = "#cccccc"
                try:
                    if area is not None:
                        fill_color = cmap(area)
                except Exception:
                    fill_color = "#cccccc"
                return {
                    "fillColor": fill_color,
                    "fillOpacity": 0.4,
                    "color": "red" if sel else "transparent",
                    "weight": 2 if sel else 0,
                }

            tooltip_fields = ["area", "uid"]
            tooltip_aliases = ["ha:", "ID:"]
            GeoJson(
                gdf_clip,
                style_function=style_fn,
                tooltip=GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases),
                name="Grid",
            ).add_to(m)

            GeoJson(
                sel_poly,
                style_function=lambda _: {
                    "color": "black",
                    "weight": 2,
                    "fillOpacity": 0,
                },
                name=st.session_state.sel_pref,
            ).add_to(m)
            LayerControl(collapsed=False).add_to(m)
            m.add_child(cmap)

            result = st_folium(
                m,
                key="folium_map",
                width="100%",
                height=700,
                returned_objects=["last_clicked"],
            )

            if last := result.get("last_clicked"):
                pt = Point(last["lng"], last["lat"])
                if not gdf_clip.empty:
                    sel_df = gdf_clip[gdf_clip.geometry.contains(pt)]
                    if not sel_df.empty:
                        row = sel_df.iloc[0]
                        new_uid = str(row.uid)
                        new_area = float(row.area)
                        # Reset calculation result if a different polygon is selected
                        if new_uid != st.session_state.get("sel_uid"):
                            st.session_state.out = None
                        st.session_state.sel_uid = new_uid
                        st.session_state.sel_area = new_area
                        centroid = row.geometry.centroid
                        st.session_state.map_center = [centroid.y, centroid.x]
                        st.session_state.map_zoom = 12
                        st.rerun()
