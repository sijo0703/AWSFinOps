# AWS Cost Explorer Streamlit Demo

This is a minimal sample project demonstrating how to:

* Build a simple **Streamlit** UI for analyzing AWS cost & usage data.
* Load either a CSV export or pull directly from **AWS Cost Explorer** using `boto3`.
* Filter costs by a tag representing a business unit or line of business.
* Plot historical spend and run a basic SARIMA forecast.

---

## Getting started

1. Clone or copy the project into a folder (e.g. `aws_cost_project`).
2. Create a Python virtual environment and install the requirements:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Ensure AWS credentials are configured (environment variables, shared config, or instance role). Cost Explorer lives in `us-east-1`. For the UI credential inputs, use temporary credentials or IAM users with minimal permissions.

> ⚠️ **Security note:** Entering credentials directly in the UI is for demo purposes only. In production, use secure methods like IAM roles, AWS SSO, or environment variables to avoid exposing secrets.
4. Run the app:
   ```powershell
   streamlit run aws_cost_app.py
   ```

## Usage

* Select **CSV** if you already have a cost/usage export. Supply the path to the file.
* Select **Cost Explorer** to query AWS directly; provide your AWS credentials (access key, secret key, optional session token), region, tag key/value, and lookback window.
* Choose the business unit in the dropdown, inspect the monthly line chart, and optionally forecast next months.

Feel free to expand with additional filters (service/region/account) or richer ML models.
