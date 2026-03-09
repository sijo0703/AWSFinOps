# AWS Cost & Usage Analyzer

A Streamlit-based application for analyzing AWS cost and usage data with an AWS console-inspired dark theme.

## Features

- **Data Sources**: Load from CSV exports or query AWS Cost Explorer directly using boto3
- **Cost Visualization**: Monthly aggregated cost trends with interactive line charts
- **Service Breakdown**: Top 10 AWS services by total cost with bar charts
- **AWS Theme**: Dark UI matching the AWS Management Console colors
- **Secure**: Supports AWS credentials input for demo purposes (use IAM roles in production)

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/sijo0703/AWSFinOps.git
   cd AWSFinOps/aws_cost_project
   ```

2. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure AWS credentials:
   - For Cost Explorer access, ensure your AWS credentials have `ce:GetCostAndUsage` permissions
   - Cost Explorer data is available in the `us-east-1` region
   - For production, use IAM roles or AWS SSO instead of entering credentials in the UI

4. Run the application:
   ```bash
   streamlit run aws_cost_app.py
   ```

## Usage

### Data Sources

- **CSV**: Upload a cost/usage CSV export from AWS Cost Explorer
- **Cost Explorer**: Query AWS directly by providing:
  - AWS Access Key ID and Secret Access Key
  - Optional Session Token (for temporary credentials)
  - AWS Region (defaults to us-east-1)
  - Number of days to look back (up to 365)

### Visualizations

After loading data, the app displays:

1. **Monthly Cost Trend**: Line chart showing total AWS costs over time
2. **Top 10 Services**: Bar chart of the highest-cost AWS services

## Project Structure

```
aws_cost_project/
├── aws_cost_app.py          # Main Streamlit application
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── .streamlit/
    └── config.toml          # Streamlit theme configuration
```

## Security Notes

- The credential input fields are for demonstration purposes
- In production environments, use:
  - IAM roles for EC2 instances
  - AWS SSO for user authentication
  - Environment variables or AWS config files
  - Never hardcode credentials in code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational and demonstration purposes.
