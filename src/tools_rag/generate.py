

'''
def generate_report(data):
prompt = f"""
    Analyze this business data.
    Provide:
    - Key Metrics
    - Growth Analysis
    - Risks
    - Opportunities
    - Recommendations
    Data:
    {data}
    """
    return llm(prompt)
'''

'''
import pandas as pd

def generate_report():
    data = pd.read_csv("data.csv")
    summary = data.describe()
    summary.to_csv("report.csv")

generate_report()
'''