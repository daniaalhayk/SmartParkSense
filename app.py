import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import database
import config
import time
from datetime import timedelta

st.set_page_config(page_title="ParkSense AI", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;700;900&display=swap');

html, body, [class*="css"], .stApp { 
    font-family: 'Cairo', sans-serif; 
    direction: rtl;
    text-align: right;
    background-color: #000000 !important;
}

.stApp { 
    background-color: #000000 !important; 
    color: #FFFFFF !important; 
}

/* إصلاح الشريط العلوي لستريملت */
header[data-testid="stHeader"] { background: transparent !important; }

h1, h2, h3 { 
    color: #FFFFFF !important; 
    font-weight: 900 !important;
}

.header-container {
    padding: 20px 0 40px 0;
    border-bottom: 1px solid #27272A;
    margin-bottom: 40px;
}

.header-title {
    font-size: 2.8rem;
    font-weight: 900;
    background: -webkit-linear-gradient(45deg, #38BDF8, #818CF8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
}

.subtitle {
    color: #A1A1AA;
    font-size: 1.2rem;
    font-weight: 500;
}

/* بطاقات الإحصائيات الفاخرة */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 40px;
}

.kpi-card {
    background: linear-gradient(145deg, #18181B 0%, #09090B 100%);
    border: 1px solid #27272A;
    border-radius: 16px;
    padding: 30px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.5), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.kpi-card:hover {
    transform: translateY(-5px);
    border-color: #3F3F46;
    box-shadow: 0 20px 40px -15px rgba(0,0,0,0.5);
}

.kpi-card:hover::before { opacity: 1; }

.kpi-label { 
    color: #A1A1AA; 
    font-size: 1.1rem; 
    font-weight: 600; 
    margin-bottom: 15px; 
    text-transform: uppercase;
    letter-spacing: 1px;
}

.kpi-value { 
    font-size: 3.5rem; 
    font-weight: 900; 
    line-height: 1; 
    color: #FAFAFA;
}

.val-free { background: -webkit-linear-gradient(45deg, #34D399, #10B981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.val-busy { background: -webkit-linear-gradient(45deg, #F87171, #EF4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.val-accent { background: -webkit-linear-gradient(45deg, #60A5FA, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

/* تنسيق المربعات في المواقف */
.slots-container {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-top: 30px;
    padding: 20px;
    background: #09090B;
    border: 1px solid #27272A;
    border-radius: 16px;
}

.slot {
    width: 80px;
    height: 80px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    font-weight: 900;
    color: #FFFFFF;
    transition: all 0.2s ease;
    border: 1px solid rgba(255,255,255,0.1);
}

.slot:hover { transform: scale(1.05); }
.slot-free { 
    background: rgba(16, 185, 129, 0.1); 
    color: #34D399;
    border-color: rgba(16, 185, 129, 0.3);
    box-shadow: inset 0 0 20px rgba(16, 185, 129, 0.05);
}
.slot-busy { 
    background: rgba(239, 68, 68, 0.1); 
    color: #F87171;
    border-color: rgba(239, 68, 68, 0.3);
    box-shadow: inset 0 0 20px rgba(239, 68, 68, 0.05);
}

/* تنسيق التبويبات */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 4px 4px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
    color: #A1A1AA;
    font-weight: 700;
    font-size: 1.1rem;
}
.stTabs [aria-selected="true"] {
    color: #FAFAFA !important;
    border-bottom-color: #38BDF8 !important;
}

</style>
""", unsafe_allow_html=True)

# توليد بيانات وهمية لباقي الاسبوع بناءا على يوم واحد
def generate_weekly_data(base_df):
    if base_df.empty: return base_df
    
    first_day = base_df.iloc[0]['ts'].date()
    daily_data = base_df[base_df['ts'].dt.date == first_day].copy()
    
    all_data = []
    for i in range(7):
        new_day = daily_data.copy()
        new_day['ts'] = new_day['ts'] + timedelta(days=i)
        
        if i > 0:
            noise = np.random.uniform(0.85, 1.15, len(new_day))
            new_day['occupied'] = (new_day['occupied'] * noise).astype(int).clip(0, new_day['total'].iloc[0])
            new_day['ratio'] = new_day['occupied'] / new_day['total']
            
        all_data.append(new_day)
        
    return pd.concat(all_data, ignore_index=True)

# تشغيل واجهة النظام
def main():
    df = database.load_snapshots("video")

    st.markdown("""
    <div class='header-container'>
        <div class='header-title'>نظام المراقبة الذكي</div>
        <div class='subtitle'>لوحة تحكم إدارية احترافية لمراقبة إشغال المواقف وتحليل البيانات المتقدم</div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("البيانات غير متوفرة. يرجى معالجة الفيديو أولاً.")
        st.stop()

    current_state = df.iloc[-1]
    total_spaces = int(current_state["total"])
    occupied_spaces = int(current_state["occupied"])
    free_spaces = total_spaces - occupied_spaces
    occupancy_rate = occupied_spaces / max(1, total_spaces)

    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">المواقف الشاغرة</div>
            <div class="kpi-value val-free">{free_spaces}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">المواقف المشغولة</div>
            <div class="kpi-value val-busy">{occupied_spaces}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">نسبة الإشغال</div>
            <div class="kpi-value val-accent">{occupancy_rate:.0%}</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["البث المباشر", "التحليلات الأسبوعية", "حالة المواقف"])

    with tab1:
        if config.LATEST_FRAME.exists():
            st.image(str(config.LATEST_FRAME), use_container_width=True)

    with tab2:
        st.markdown("<h3 style='margin-bottom: 20px; color: #FAFAFA;'>تحليلات الإشغال لمدار الأسبوع</h3>", unsafe_allow_html=True)
        
        weekly_df = generate_weekly_data(df)
        weekly_df["pct"] = weekly_df["ratio"] * 100
        
        fig = px.area(weekly_df, x="ts", y="pct",
                      labels={"pct": "نسبة الإشغال (%)", "ts": "التاريخ والوقت"},
                      color_discrete_sequence=["#38BDF8"])
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Cairo", color="#A1A1AA"),
            xaxis=dict(gridcolor="#27272A", showline=False, zeroline=False),
            yaxis=dict(gridcolor="#27272A", range=[0, 100], showline=False, zeroline=False),
            margin=dict(t=20, b=20, l=20, r=20),
            hovermode="x unified"
        )
        # جعل التعبئة متدرجة
        fig.update_traces(fillcolor='rgba(56, 189, 248, 0.2)', line=dict(width=3))
        
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("<h3 style='margin-bottom: 10px; color: #FAFAFA;'>خريطة المواقف المباشرة</h3>", unsafe_allow_html=True)
        spaces_df = database.latest_space_states("video")
        
        if not spaces_df.empty:
            slots_html = "<div class='slots-container'>"
            for row in spaces_df.itertuples():
                status_class = "slot-busy" if row.occupied else "slot-free"
                slots_html += f"<div class='slot {status_class}'>{row.space_id}</div>"
            slots_html += "</div>"
            st.markdown(slots_html, unsafe_allow_html=True)

    auto_refresh = st.sidebar.checkbox("تحديث تلقائي مستمر")
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
