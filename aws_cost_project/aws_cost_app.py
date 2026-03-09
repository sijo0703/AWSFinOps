import streamlit as st
import pandas as pd
import boto3
from datetime import datetime, timedelta

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
    - service (optional)

    You can adapt the field names to your export.
    """
    df = pd.read_csv(path, parse_dates=["usage_start"])
    df["BusinessUnit"] = df.get("resource_tags.businessunit", "").fillna("unknown")
    df["Service"] = df.get("service", "Unknown")
    return df

@st.cache_data(ttl=3600)
def fetch_cost_explorer(start: str, end: str, aws_access_key: str, aws_secret_key: str, region: str, session_token: str = None) -> pd.DataFrame:
    """Query AWS Cost Explorer for daily costs (all data, no filters).

    Parameters
    ----------
    start : ISO date string (YYYY-MM-DD)
    end   : ISO date string (YYYY-MM-DD)
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
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    # Process the initial response
    for g in response["ResultsByTime"]:
        date = g["TimePeriod"]["Start"]
        for group in g.get("Groups", []):
            amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
            service = group["Keys"][0] if group["Keys"] else "Unknown"
            rows.append({
                "usage_start": pd.to_datetime(date),
                "unblended_cost": amt,
                "Service": service,
                "BusinessUnit": "Total Costs",
            })
    # Handle pagination using NextPageToken
    while "NextPageToken" in response:
        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            NextPageToken=response["NextPageToken"],
        )
        for g in response["ResultsByTime"]:
            date = g["TimePeriod"]["Start"]
            for group in g.get("Groups", []):
                amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                service = group["Keys"][0] if group["Keys"] else "Unknown"
                rows.append({
                    "usage_start": pd.to_datetime(date),
                    "unblended_cost": amt,
                    "Service": service,
                    "BusinessUnit": "Total Costs",
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
    days = st.slider("Days back", 1, 365, 90)
    if st.button("Load"):
        if not aws_access_key or not aws_secret_key:
            st.error("Please provide AWS Access Key ID and Secret Access Key.")
        else:
            end = datetime.utcnow().date().isoformat()
            start = (datetime.utcnow().date() - timedelta(days=days)).isoformat()
            df = fetch_cost_explorer(start, end, aws_access_key, aws_secret_key, region, session_token if session_token else None)

if "df" in locals():
    if df.empty:
        st.warning("No data returned.")
    else:
        filtered = df
        st.write(f"Showing {len(filtered)} records for **Total AWS Costs**")

        agg = aggregate_monthly(filtered)
        st.line_chart(agg)

        st.subheader("Top 10 Services by Cost")
        service_costs = df.groupby("Service")["unblended_cost"].sum().sort_values(ascending=False).head(10)
        st.bar_chart(service_costs)
