import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Amazon Bestsellers Dashboard",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Amazon Bestsellers Dashboard")
st.caption("Explore bestseller trends, genres, prices, ratings, and customer reviews (2009–2019).")

# Load the supplied CSV by default. Users can replace it from the sidebar.
DEFAULT_FILE = Path(__file__).parent / "amazon_bestsellers.csv"

@st.cache_data
def load_data(file):
    data = pd.read_csv(file)
    required_columns = ["Name", "Author", "User Rating", "Reviews", "Price", "Year", "Genre"]
    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    for col in ["User Rating", "Reviews", "Price", "Year"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=required_columns).copy()
    data["Year"] = data["Year"].astype(int)
    data["Reviews"] = data["Reviews"].astype(int)
    data["Price"] = data["Price"].astype(float)
    data["User Rating"] = data["User Rating"].astype(float)
    data["Genre"] = data["Genre"].astype(str)
    return data

st.sidebar.header("Dashboard filters")
uploaded_file = st.sidebar.file_uploader("Upload another CSV (optional)", type=["csv"])

try:
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    elif DEFAULT_FILE.exists():
        df = load_data(DEFAULT_FILE)
    else:
        st.info("Upload amazon_bestsellers.csv using the sidebar to get started.")
        st.stop()
except Exception as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1
)
genres = sorted(df["Genre"].dropna().unique().tolist())
selected_genres = st.sidebar.multiselect("Genre", genres, default=genres)

filtered = df[
    df["Year"].between(year_range[0], year_range[1])
    & df["Genre"].isin(selected_genres)
].copy()

if filtered.empty:
    st.warning("No records match the selected filters. Please change the year range or genre.")
    st.stop()

# KPI row
total_records = len(filtered)
unique_titles = filtered["Name"].nunique()
avg_rating = filtered["User Rating"].mean()
avg_reviews = filtered["Reviews"].mean()
avg_price = filtered["Price"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Bestseller records", f"{total_records:,}")
k2.metric("Unique titles", f"{unique_titles:,}")
k3.metric("Average rating", f"{avg_rating:.2f} / 5")
k4.metric("Average reviews", f"{avg_reviews:,.0f}")
k5.metric("Average price", f"{avg_price:,.2f}")

st.divider()

# Four charts maximum
left, right = st.columns(2)

with left:
    st.subheader("1. Records by genre")
    genre_counts = (
        filtered.groupby("Genre", as_index=False)
        .size()
        .rename(columns={"size": "Records"})
    )
    fig_genre = px.pie(
        genre_counts,
        names="Genre",
        values="Records",
        hole=0.45,
        title="Bestseller record share"
    )
    fig_genre.update_traces(textposition="inside", textinfo="percent+label")
    fig_genre.update_layout(margin=dict(l=10, r=10, t=55, b=10), legend_title_text="Genre")
    st.plotly_chart(fig_genre, use_container_width=True)

with right:
    st.subheader("2. Average rating by year")
    yearly_rating = (
        filtered.groupby("Year", as_index=False)["User Rating"]
        .mean()
        .sort_values("Year")
    )
    fig_rating = px.line(
        yearly_rating,
        x="Year",
        y="User Rating",
        markers=True,
        title="Average customer rating"
    )
    fig_rating.update_yaxes(range=[0, 5])
    fig_rating.update_layout(margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig_rating, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("3. Average price by genre")
    genre_price = (
        filtered.groupby("Genre", as_index=False)["Price"]
        .mean()
        .sort_values("Price", ascending=False)
    )
    fig_price = px.bar(
        genre_price,
        x="Genre",
        y="Price",
        text_auto=".2f",
        title="Mean listed price"
    )
    fig_price.update_layout(margin=dict(l=10, r=10, t=55, b=10), yaxis_title="Average price")
    st.plotly_chart(fig_price, use_container_width=True)

with right2:
    st.subheader("4. Top 10 most-reviewed titles")
    # If a title appears in multiple years, retain its highest recorded review count.
    top_books = (
        filtered.sort_values("Reviews", ascending=False)
        .drop_duplicates(subset=["Name"])
        .head(10)
        .sort_values("Reviews", ascending=True)
    )
    fig_reviews = px.bar(
        top_books,
        x="Reviews",
        y="Name",
        orientation="h",
        hover_data={"Author": True, "User Rating": ":.1f", "Year": True, "Genre": True},
        title="Highest review count per title"
    )
    fig_reviews.update_layout(
        margin=dict(l=10, r=10, t=55, b=10),
        yaxis_title="",
        xaxis_title="Number of reviews"
    )
    st.plotly_chart(fig_reviews, use_container_width=True)

with st.expander("View filtered data"):
    st.write(f"Showing {len(filtered):,} records after filtering.")
    st.dataframe(
        filtered.sort_values(["Year", "Reviews"], ascending=[True, False]),
        use_container_width=True,
        hide_index=True
    )

st.caption(
    "Notes: Each row is a bestseller-year record, not necessarily a unique book. "
    "Review counts are cumulative values in the source dataset. Price currency is not specified."
)
