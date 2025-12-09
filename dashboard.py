import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(layout="wide", page_title="Employee Assessment Dashboard", page_icon="📊")

# Custom CSS for Premium Look
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #1e3a8a; /* Dark Blue */
        font-family: 'Helvetica', sans-serif;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .css-1d391kg {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("employee_data.csv")
    except Exception as e:
        return pd.DataFrame() # fail gracefully
        
    # Filter out invalid rows
    if 'Employee Name' in df.columns:
        df = df[df['Employee Name'].notna()]
        df = df[df['Employee Name'].str.strip() != '']
        df = df[df['Employee Name'].str.lower() != 'employee name']
    
    # Ensure numeric columns are float
    cols = ['Quality Score', 'Productivity Score', 'Attendance Score', 'Skill Score', 'Teamwork Score', 'Weighted Score', 'Salary Increase']
    for c in cols:
        if c in df.columns:
            # Force conversion to numeric, coercing errors to NaN
            df[c] = pd.to_numeric(df[c], errors='coerce')
            # Fill NaN with 0.0
            df[c] = df[c].fillna(0.0)
            # Explicitly cast to float
            df[c] = df[c].astype(float)
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Data file 'employee_data.csv' not found. Please run extract_data.py first.")
    st.stop()

# Header
st.title("📊 Annual Employee Assessment Dashboard")
st.markdown("Interactive analysis of performance reviews, salary recommendations, and team metrics.")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("Filter Options")
all_teams = sorted(list(set(df['Team'].dropna())))
selected_teams = st.sidebar.multiselect("Select Teams", all_teams, default=all_teams)

all_employees = sorted(list(df['Employee Name'].unique()))
selected_employee = st.sidebar.selectbox("Select Employee for Detail View", ["All"] + all_employees)

# Filter Data
filtered_df = df[df['Team'].isin(selected_teams)]

# Key Metrics Row
c1, c2, c3, c4 = st.columns(4)
avg_score = filtered_df['Weighted Score'].mean()
avg_salary = filtered_df['Salary Increase'].mean()
top_performer = filtered_df.loc[filtered_df['Weighted Score'].idxmax()]['Employee Name'] if not filtered_df.empty else "N/A"
best_team = filtered_df.groupby('Team')['Weighted Score'].mean().idxmax() if not filtered_df.empty else "N/A"

c1.metric("Average Score", f"{avg_score:.2f} / 5.0")
c2.metric("Avg Salary Increase", f"{avg_salary:.2f}%")
c3.metric("Top Performer", top_performer)
c4.metric("Best Performing Team", best_team)

st.markdown("---")

# --- Plot 5: Team Analysis (High Level) ---
st.subheader("🏆 Team Performance Analysis")
col_team1, col_team2 = st.columns([2, 1])

with col_team1:
    # Bar chart of scores by team
    fig_team = px.box(filtered_df, x="Team", y="Weighted Score", points="all", color="Team",
                      title="Distribution of Scores by Team",
                      color_discrete_sequence=px.colors.qualitative.Prism)
    st.plotly_chart(fig_team, use_container_width=True)

with col_team2:
    st.info(f"**Best Performing Team: {best_team}**")
    st.markdown("This team has the highest average weighted score. Analysis suggests strong leadership and consistent high performance across members.")
    team_stats = filtered_df.groupby('Team')['Weighted Score'].agg(['mean', 'count']).reset_index()
    team_stats.columns = ['Team', 'Avg Score', 'Count']
    st.dataframe(team_stats, hide_index=True)

st.markdown("---")

# --- Plot 3: Performance Leaderboard ---
st.subheader("📈 Performance Leaderboard")
# Sorted Bar Chart
fig_leader = px.bar(filtered_df.sort_values('Weighted Score'), x="Weighted Score", y="Employee Name", orientation='h',
                    color="Team", text="Weighted Score", title="Employees Ranked by Weighted Score",
                    color_discrete_sequence=px.colors.qualitative.Safe)
fig_leader.update_layout(height=500)
st.plotly_chart(fig_leader, use_container_width=True)

st.markdown("---")

# --- Plot 2: Salary Recommendation ---
st.subheader("💰 Salary Increase Recommendations")
fig_salary = px.scatter(filtered_df, x="Weighted Score", y="Salary Increase", size="Salary Increase", color="Team",
                        hover_data=["Employee Name"], title="Salary Increase vs Performance Score",
                        labels={"Salary Increase": "Recommended Increase (%)"},
                        size_max=20)
# Add a trendline? Scatter is better to show correlation
st.plotly_chart(fig_salary, use_container_width=True)


st.markdown("---")

# --- Individual Employee Analysis (Plot 1 & 4 & 6) ---
st.subheader("🧑‍💼 Individual Details")

if selected_employee == "All":
    st.markdown("*Select an employee from the sidebar to view detailed breakdown.*")
    # Show aggregate Radar Chart for teams?
    categories = ['Quality Score', 'Productivity Score', 'Attendance Score', 'Skill Score', 'Teamwork Score']
    team_avg = filtered_df.groupby('Team')[categories].mean().reset_index()
    team_avg_melted = team_avg.melt(id_vars='Team', var_name='Category', value_name='Score')
    fig_radar_team = px.line_polar(team_avg_melted, r='Score', theta='Category', color='Team', line_close=True,
                                   title="Average Capabilities by Team")
    st.plotly_chart(fig_radar_team, use_container_width=True)
else:
    emp_data = df[df['Employee Name'] == selected_employee].iloc[0]
    
    # Plot 6: Best Employee Highlights / Header
    col_profile, col_radar = st.columns([1, 2])
    
    with col_profile:
        st.markdown(f"### {emp_data['Employee Name']}")
        st.markdown(f"**Role:** {emp_data['Role']}")
        st.markdown(f"**Team:** {emp_data['Team']}")
        st.metric("Final Score", f"{emp_data['Weighted Score']}")
        st.metric("Recommended Raise", f"{emp_data['Salary Increase']}%")
        
        if emp_data['Weighted Score'] >= 4.5:
            st.success("🌟 **Star Performer**")
        elif emp_data['Weighted Score'] >= 3.8:
             st.info("👍 **Strong Performer**")
        
    with col_radar:
        # Plot 1: Radar Chart
        categories = ['Quality Score', 'Productivity Score', 'Attendance Score', 'Skill Score', 'Teamwork Score']
        scores = [emp_data[c] for c in categories]
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=scores,
            theta=[c.replace(' Score', '') for c in categories],
            fill='toself',
            name=emp_data['Employee Name']
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False, 
                                title=f"Competency Profile: {emp_data['Employee Name']}")
        st.plotly_chart(fig_radar, use_container_width=True)

    # Plot 4: Management Notes
    st.subheader("📝 Management Insights & Notes")
    st.markdown(f"> {emp_data['Manager Notes']}")
    
    # Detailed notes table
    note_data = {
        "Category": ["Quality", "Productivity", "Attendance", "Skill", "Teamwork"],
        "Notes": [emp_data.get('Quality Notes', ''), emp_data.get('Productivity Notes', ''), 
                  emp_data.get('Attendance Notes', ''), emp_data.get('Skill Notes', ''), 
                  emp_data.get('Teamwork Notes', '')]
    }
    st.table(pd.DataFrame(note_data).set_index("Category"))

