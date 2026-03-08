import streamlit as st
import pandas as pd
import boto3
from datetime import datetime, timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt

# configure page metadata and layout early
st.set_page_config(
    page_title="AWS Cost & Usage Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# The overall theme is configured in .streamlit/config.toml to match the
# AWS console dark theme (orange primary color, dark blue backgrounds).
# You can also add custom CSS here if you need tweaks.

st.title("AWS Cost & Usage Analyzer")

@st.cache_data

def load_data_from_csv(path: str) -> pd.DataFrame:
    """Load a cost/usage CSV file. Expects at least the columns:
    - usage_start (datetime)
    - unblended_cost (numeric)
    - resource_tags.businessunit (string)

    You can adapt the field names to your export.
    """
    df = pd.read_csv(path, parse_dates=["usage_start"])
    df["BusinessUnit"] = df.get("resource_tags.businessunit", "").fillna("unknown")
    return df

@st.cache_data(ttl=3600)
def fetch_cost_explorer(start: str, end: str, tag_key: str, tag_value: str, aws_access_key: str, aws_secret_key: str, region: str, session_token: str = None) -> pd.DataFrame:
    """Query AWS Cost Explorer for daily costs filtered by a tag.

    Parameters
    ----------
    start : ISO date string (YYYY-MM-DD)
    end   : ISO date string (YYYY-MM-DD)
    tag_key  : AWS tag key
    tag_value: AWS tag value to match (EQUALS)
    aws_access_key: AWS access key ID
    aws_secret_key: AWS secret access key
    region: AWS region
    session_token: Optional session token for temporary credentials
    """
    client_kwargs = {
        "region_name": region,
        "aws_access_key_id": aws_access_key,
        "aws_secret_access_key": aws_secret_key,
    }
    if session_token:
        client_kwargs["aws_session_token"] = session_token
    client = boto3.client("ce", **client_kwargs)
    rows = []
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Tags": {
                "Key": tag_key,
                "Values": [tag_value],
                "MatchOptions": ["EQUALS"],
            }
        },
    )
    # Process the initial response
    for g in response["ResultsByTime"]:
        date = g["TimePeriod"]["Start"]
        amt = float(g["Total"]["UnblendedCost"]["Amount"])
        rows.append({
            "usage_start": pd.to_datetime(date),
            "unblended_cost": amt,
            "BusinessUnit": tag_value,
        })
    # Handle pagination using NextPageToken
    while "NextPageToken" in response:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            Filter={
                "Tags": {
                    "Key": tag_key,
                    "Values": [tag_value],
                    "MatchOptions": ["EQUALS"],
                }
            },
            NextPageToken=response["NextPageToken"],
        )
        for g in response["ResultsByTime"]:
            date = g["TimePeriod"]["Start"]
            amt = float(g["Total"]["UnblendedCost"]["Amount"])
            rows.append({
                "usage_start": pd.to_datetime(date),
                "unblended_cost": amt,
                "BusinessUnit": tag_value,
            })

    return pd.DataFrame(rows)


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Group daily rows into monthly costs."""
    return (
        df.set_index("usage_start")["unblended_cost"]
        .resample("M")
        .sum()
        .to_frame("cost")
    )


# UI controls
source = st.radio("Data source", ["CSV", "Cost Explorer"])

if source == "CSV":
    path = st.text_input("Path to CSV file", "data/aws_costs.csv")
    if st.button("Load"):
        df = load_data_from_csv(path)
else:
    st.subheader("AWS Credentials")
    aws_access_key = st.text_input("AWS Access Key ID", type="password")
    aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
    session_token = st.text_input("AWS Session Token (optional)", type="password")
    region = st.text_input("AWS Region", "us-east-1")
    tag_key = st.text_input("Tag key", "BusinessUnit")
    tag_val = st.text_input("Tag value", "LOB-A")
    days = st.slider("Days back", 1, 365, 90)
    if st.button("Load"):
        if not aws_access_key or not aws_secret_key:
            st.error("Please provide AWS Access Key ID and Secret Access Key.")
        else:
            end = datetime.utcnow().date().isoformat()
            start = (datetime.utcnow().date() - timedelta(days=days)).isoformat()
            df = fetch_cost_explorer(start, end, tag_key, tag_val, aws_access_key, aws_secret_key, region, session_token if session_token else None)

if "df" in locals():
    if df.empty:
        st.warning("No data returned.")
    else:
        units = df["BusinessUnit"].unique().tolist()
        choice = st.selectbox("Business unit / LOB", units)
        filtered = df[df["BusinessUnit"] == choice]
        st.write(f"Showing {len(filtered)} records for **{choice}**")

        agg = aggregate_monthly(filtered)
        st.line_chart(agg)

        if st.button("Forecast next 3 months"):
            model = SARIMAX(agg, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
            res = model.fit(disp=False)
            pred = res.get_forecast(steps=3)
            forecast = pred.predicted_mean
            conf = pred.conf_int()
            st.write("### Forecast")
            fig, ax = plt.subplots()
            agg.plot(ax=ax, label="historical")
            forecast.plot(ax=ax, label="forecast")
            ax.fill_between(
                conf.index,
                conf.iloc[:, 0],
                conf.iloc[:, 1],
                color="grey",
                alpha=0.3,
            )
            ax.legend()
            st.pyplot(fig)

        if st.checkbox("Show raw data"):
            st.dataframe(filtered)
