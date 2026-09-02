import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------------------------------------------------------------------
# 1. SETUP THE PAGE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="European Bank Churn Analytics Dashboard",
    page_icon="🇪🇺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------------------------
# 2. HELPER FUNCTION TO GENERATE DEMO DATA
# ------------------------------------------------------------------------------
@st.cache_data
def generate_fake_data():
    np.random.seed(42)
    n_samples = 1000

    surnames = [
        "Smith", "Dupont", "Garcia", "Mueller", "Novak",
        "Ferrari", "Sanz", "Berger", "Martin", "Rossi"
    ]
    countries = ["France", "Germany", "Spain"]
    genders = ["Female", "Male"]

    data = {
        "CustomerId": range(10000001, 10000001 + n_samples),
        "Surname": np.random.choice(surnames, n_samples),
        "CreditScore": np.random.randint(400, 850, n_samples),
        "Geography": np.random.choice(countries, n_samples, p=[0.5, 0.25, 0.25]),
        "Gender": np.random.choice(genders, n_samples),
        "Age": np.random.randint(18, 85, n_samples),
        "Tenure": np.random.randint(0, 11, n_samples),
        "Balance": np.round(
            np.where(np.random.rand(n_samples) > 0.3, np.random.uniform(5000, 250000, n_samples), 0.0), 2
        ),
        "NumOfProducts": np.random.choice([1, 2, 3, 4], n_samples, p=[0.5, 0.45, 0.04, 0.01]),
        "HasCrCard": np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),
        "IsActiveMember": np.random.choice([0, 1], n_samples, p=[0.5, 0.5]),
        "EstimatedSalary": np.round(np.random.uniform(10000, 200000, n_samples), 2),
    }

    df = pd.DataFrame(data)

    churn_prob = 0.15
    churn_prob += np.where(df["Age"] > 45, 0.2, 0.0)
    churn_prob += np.where(df["Geography"] == "Germany", 0.15, 0.0)
    churn_prob += np.where(df["IsActiveMember"] == 0, 0.1, 0.0)
    churn_prob += np.where(df["NumOfProducts"] >= 3, 0.3, 0.0)
    churn_prob = np.clip(churn_prob, 0.0, 1.0)
    df["Exited"] = np.random.binomial(1, churn_prob)

    return df


# ------------------------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------------------------
st.sidebar.title("🎒 School Bag (Controls)")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "📂 Upload your CSV file here!",
    type=["csv"],
    help="If you have your bank customer data in a CSV file, drop it here! Otherwise, we will use our friendly demo data.",
)

required_columns = {
    "CustomerId", "Surname", "CreditScore", "Geography", "Gender", "Age",
    "Tenure", "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember",
    "EstimatedSalary", "Exited",
}

if uploaded_file is not None:
    try:
        uploaded_data = pd.read_csv(uploaded_file)
        missing_columns = sorted(required_columns - set(uploaded_data.columns))
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        df_raw = uploaded_data
        st.sidebar.success("🎉 Loaded your file successfully!")
    except Exception as e:
        st.sidebar.error(f"⚠️ Oh no! There was an error reading your file: {e}")
        df_raw = generate_fake_data()
else:
    df_raw = generate_fake_data()
    st.sidebar.info("💡 Using high-quality Demo Data. Upload your own CSV above anytime!")


# ------------------------------------------------------------------------------
# 4. DATA CLEANING & PREPARATION
# ------------------------------------------------------------------------------
df = df_raw.copy()

age_bins = [0, 30, 45, 60, 120]
age_labels = ["<30 (Young)", "30–45 (Adults)", "46–60 (Middle-aged)", "60+ (Seniors)"]
df["AgeGroup"] = pd.cut(df["Age"], bins=age_bins, labels=age_labels)

credit_bins = [0, 580, 670, 1000]
credit_labels = ["Low Credit Score", "Medium Credit Score", "High Credit Score"]
df["CreditScoreBand"] = pd.cut(df["CreditScore"], bins=credit_bins, labels=credit_labels)

tenure_bins = [-1, 2, 6, 12]
tenure_labels = ["New Customers (0-2 yrs)", "Mid-term Customers (3-6 yrs)", "Long-term Customers (7+ yrs)"]
df["TenureGroup"] = pd.cut(df["Tenure"], bins=tenure_bins, labels=tenure_labels)


def segment_balance(bal):
    if bal == 0:
        return "Zero Balance"
    elif bal < 100000:
        return "Low Balance (<100k)"
    else:
        return "High Balance (100k+)"


df["BalanceSegment"] = df["Balance"].apply(segment_balance)
df["Status"] = df["Exited"].map({1: "Left (Churn)", 0: "Stayed (Active)"})


# ------------------------------------------------------------------------------
# 5. SIDEBAR FILTERS
# ------------------------------------------------------------------------------
st.sidebar.markdown("### 🔍 Filter the Customers")

geo_list = df["Geography"].unique().tolist()
selected_geo = st.sidebar.multiselect("📍 Choose Countries", options=geo_list, default=geo_list)

gender_list = df["Gender"].unique().tolist()
selected_gender = st.sidebar.multiselect("👫 Choose Genders", options=gender_list, default=gender_list)

age_list = df["AgeGroup"].cat.categories.tolist()
selected_age = st.sidebar.multiselect("🎂 Choose Age Groups", options=age_list, default=age_list)

df_filtered = df[
    (df["Geography"].isin(selected_geo))
    & (df["Gender"].isin(selected_gender))
    & (df["AgeGroup"].isin(selected_age))
]

if df_filtered.empty:
    st.error("😭 Oops! No customers match your filter selections. Please select more options in the sidebar!")
    st.stop()


# ------------------------------------------------------------------------------
# 6. HEADER & METRIC CARDS
# ------------------------------------------------------------------------------
st.title("🇪🇺 Customer Churn & Segmentation Dashboard")
st.markdown("""
Welcome to the Bank Churn Dashboard! This page helps bank managers understand **why customers leave the bank** and what makes them stay.
Use the filters on the left (the sidebar) to slice and dice the data, like a scientist looking through a microscope! 🔬
""")

total_customers = len(df_filtered)
churned_customers = df_filtered["Exited"].sum()
overall_churn_rate = (churned_customers / total_customers) * 100

high_value_df = df_filtered[df_filtered["BalanceSegment"] == "High Balance (100k+)"]
if not high_value_df.empty:
    hv_total = len(high_value_df)
    hv_churned = high_value_df["Exited"].sum()
    hv_churn_rate = (hv_churned / hv_total) * 100
    hv_risk_amount = high_value_df[high_value_df["Exited"] == 1]["Balance"].sum()
else:
    hv_churn_rate = 0.0
    hv_risk_amount = 0.0

active_churn_rate = (df_filtered[df_filtered["IsActiveMember"] == 1]["Exited"].mean()) * 100
inactive_churn_rate = (df_filtered[df_filtered["IsActiveMember"] == 0]["Exited"].mean()) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="👥 Total Customers",
        value=f"{total_customers:,}",
        help="This is the total number of customers we are looking at.",
    )

with col2:
    st.metric(
        label="📉 Overall Churn Rate",
        value=f"{overall_churn_rate:.2f}%",
        delta=f"{churned_customers:,} left the bank",
        delta_color="inverse",
        help="This is the percentage of customers who decided to leave the bank.",
    )

with col3:
    st.metric(
        label="💎 High-Value Churn Rate",
        value=f"{hv_churn_rate:.2f}%",
        delta=f"€{hv_risk_amount:,.0f} lost",
        delta_color="inverse",
        help="This is the churn rate specifically for customers with high savings (more than €100,000).",
    )

with col4:
    gap = inactive_churn_rate - active_churn_rate
    st.metric(
        label="⚡ Activity Impact Gap",
        value=f"{gap:+.2f}%",
        delta="Inactive are riskier!",
        delta_color="off",
        help="This is how much more likely inactive customers are to leave compared to active members.",
    )

st.markdown("---")


# ------------------------------------------------------------------------------
# 7. DASHBOARD TABS
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overall Churn",
    "🗺️ Geographic Risk",
    "🎂 Age & Tenure",
    "💎 High-Value Churn Explorer",
])

with tab1:
    st.header("📊 Overall Churn Analysis")
    st.write("""
    Let's look at the big picture! Customer **churn** is a fancy word for when a customer leaves the bank.
    Losing customers costs money because it is hard to find new ones, and the bank loses the fees and savings they had.
    """)

    col_pie, col_bar = st.columns(2)

    with col_pie:
        st.subheader("How many stayed vs. left?")
        status_counts = df_filtered["Status"].value_counts().reset_index()
        fig_pie = px.pie(
            status_counts,
            values="count",
            names="Status",
            color="Status",
            color_discrete_map={"Stayed (Active)": "#2b5c8f", "Left (Churn)": "#ff4b4b"},
            hole=0.4,
        )
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        st.subheader("Do credit cards help keep customers?")
        cc_data = df_filtered.groupby(["HasCrCard", "Status"]).size().reset_index(name="Count")
        cc_data["Credit Card"] = cc_data["HasCrCard"].map({1: "Has Credit Card", 0: "No Credit Card"})

        fig_cc = px.bar(
            cc_data,
            x="Credit Card",
            y="Count",
            color="Status",
            barmode="group",
            color_discrete_map={"Stayed (Active)": "#2b5c8f", "Left (Churn)": "#ff4b4b"},
            labels={"Count": "Number of Customers"},
        )
        st.plotly_chart(fig_cc, use_container_width=True)

    st.info("""
    💡 **Did you know?** Banks often find that active members who use multiple products and credit cards are much less likely to leave!
    """)

with tab2:
    st.header("🗺️ Geography-wise Churn Analysis")
    st.write("""
    Does where you live affect if you leave the bank? Let's check how France, Germany, and Spain compare.
    """)

    geo_stats = df_filtered.groupby("Geography").agg(
        Total_Customers=("CustomerId", "count"),
        Churned_Customers=("Exited", "sum"),
    ).reset_index()
    geo_stats["Churn Rate (%)"] = (geo_stats["Churned_Customers"] / geo_stats["Total_Customers"]) * 100

    col_geo_left, col_geo_right = st.columns(2)

    with col_geo_left:
        st.subheader("Churn Rate by Country 🗺️")
        fig_geo = px.bar(
            geo_stats,
            x="Geography",
            y="Churn Rate (%)",
            color="Geography",
            color_discrete_sequence=["#4A90E2", "#E28743", "#50B432"],
            text=geo_stats["Churn Rate (%)"].apply(lambda x: f"{x:.1f}%"),
            labels={"Geography": "Country", "Churn Rate (%)": "Churn Rate (How many left out of 100)"},
        )
        fig_geo.update_traces(textposition="outside")
        st.plotly_chart(fig_geo, use_container_width=True)

    with col_geo_right:
        st.subheader("Customer Counts and Leaving Rates")
        geo_table = geo_stats.copy()
        geo_table.columns = ["Country 📍", "Total Customers 👥", "Left the Bank 📉", "Leaving Rate 📊"]
        geo_table["Leaving Rate 📊"] = geo_table["Leaving Rate 📊"].apply(lambda x: f"{x:.2f}%")
        st.dataframe(geo_table, use_container_width=True, hide_index=True)

    st.warning("""
    ⚠️ **Action Insight:** If Germany's churn rate is higher, the bank should check if German customers have fewer branch offices,
    or if competitors in Germany are offering better deals.
    """)

with tab3:
    st.header("🎂 Age and Tenure Analysis")
    st.write("""
    Let's see if age or how long a customer has been with the bank makes a difference.
    """)

    col_age, col_tenure = st.columns(2)

    with col_age:
        st.subheader("Do older or younger people leave more?")
        age_stats = df_filtered.groupby("AgeGroup", observed=False).agg(
            Total_Customers=("CustomerId", "count"),
            Churned_Customers=("Exited", "sum"),
        ).reset_index()
        age_stats["Churn Rate (%)"] = (age_stats["Churned_Customers"] / age_stats["Total_Customers"]) * 100

        fig_age = px.bar(
            age_stats,
            x="AgeGroup",
            y="Churn Rate (%)",
            color="AgeGroup",
            color_discrete_sequence=px.colors.sequential.Reds_r,
            text=age_stats["Churn Rate (%)"].apply(lambda x: f"{x:.1f}%"),
            labels={"AgeGroup": "Age Group 🎂", "Churn Rate (%)": "Leaving Rate (%)"},
        )
        fig_age.update_traces(textposition="outside")
        st.plotly_chart(fig_age, use_container_width=True)

    with col_tenure:
        st.subheader("Does the length of time they stayed matter?")
        ten_stats = df_filtered.groupby("TenureGroup", observed=False).agg(
            Total_Customers=("CustomerId", "count"),
            Churned_Customers=("Exited", "sum"),
        ).reset_index()
        ten_stats["Churn Rate (%)"] = (ten_stats["Churned_Customers"] / ten_stats["Total_Customers"]) * 100

        fig_ten = px.line(
            ten_stats,
            x="TenureGroup",
            y="Churn Rate (%)",
            markers=True,
            labels={"TenureGroup": "Years with Bank Group ⏳", "Churn Rate (%)": "Leaving Rate (%)"},
        )
        fig_ten.update_traces(line_color="#ff4b4b", line_width=4, marker=dict(size=10, color="#2b5c8f"))
        st.plotly_chart(fig_ten, use_container_width=True)

    st.info("""
    📈 **What we see here:** Often, seniors (60+) or middle-aged people (46-60) might have higher churn rates.
    """)

with tab4:
    st.header("💎 High-Value Customer Churn Explorer")
    st.write("""
    Losing customers is bad, but **losing rich customers is a catastrophe**!
    """)

    high_value_total = df_filtered[df_filtered["Balance"] > 100000]

    if high_value_total.empty:
        st.info("No customers with more than €100,000 balance found in the filtered data.")
    else:
        col_hv_intro, col_hv_calc = st.columns([2, 1])

        with col_hv_intro:
            st.write(f"""
            We have **{len(high_value_total)}** customers who are **High-Value** (meaning they have more than €100,000 saved).
            Below is a scatter chart showing their annual salary vs. how much money they have in the bank.
            Red dots are customers who **left**, and blue dots are those who **stayed**.
            """)

        with col_hv_calc:
            total_money_in_bank = high_value_total["Balance"].sum()
            lost_money = high_value_total[high_value_total["Exited"] == 1]["Balance"].sum()
            loss_percent = (lost_money / total_money_in_bank) * 100 if total_money_in_bank > 0 else 0

            st.metric(
                label="💰 Total Wealth Lost from Churn",
                value=f"€{lost_money:,.2f}",
                delta=f"{loss_percent:.1f}% of High-Value Wealth",
                delta_color="inverse",
            )

        fig_scatter = px.scatter(
            high_value_total,
            x="EstimatedSalary",
            y="Balance",
            color="Status",
            hover_data=["Surname", "Age", "Geography"],
            color_discrete_map={"Stayed (Active)": "#2b5c8f", "Left (Churn)": "#ff4b4b"},
            labels={"EstimatedSalary": "Estimated Annual Salary (€)", "Balance": "Bank Balance (€)"},
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("🔍 Drill-down: Search Rich Customers Who Left")
        st.write("This table shows our most valuable customers who have left the bank. We should call them to ask why! 📞")

        hv_left_table = high_value_total[high_value_total["Exited"] == 1][
            ["CustomerId", "Surname", "Geography", "Gender", "Age", "Balance", "EstimatedSalary", "NumOfProducts"]
        ].sort_values(by="Balance", ascending=False)

        hv_left_table["Balance"] = hv_left_table["Balance"].apply(lambda x: f"€{x:,.2f}")
        hv_left_table["EstimatedSalary"] = hv_left_table["EstimatedSalary"].apply(lambda x: f"€{x:,.2f}")

        st.dataframe(hv_left_table, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------------------
# 8. HOW TO RUN THIS CODE (Footer)
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🎓 Kid-Friendly Guide: How to run this dashboard on your home computer!")
st.markdown("""
Follow these three simple steps to start your web app:
1. **Save this file** as `app.py` in a folder on your computer.
2. **Install Streamlit & Plotly** using your terminal:
   ```bash
   pip install streamlit pandas numpy plotly
   ```
3. **Run the app**:
   ```bash
   streamlit run app.py
   ```
And boom! Your banking project dashboard will open up like magic! 🎩✨
""")
