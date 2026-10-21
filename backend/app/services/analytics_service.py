"""Analytics Service Module.
Performs data analysis, aggregations, metrics computation, and CSV generation
using Pandas and NumPy directly on MySQL records.
"""

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from datetime import datetime
import io
import pandas as pd
import numpy as np
from app.db import execute_query

def get_dashboard_data():
    """
    Fetch and compute all metrics, chart datasets, and recent records
    required for the main dashboard.
    """
    # 1. Total counts
    p_count_res = execute_query("SELECT COUNT(*) AS total FROM patients", fetch="one")
    v_count_res = execute_query("SELECT COUNT(*) AS total FROM visits", fetch="one")
    d_count_res = execute_query("SELECT COUNT(*) AS total FROM departments", fetch="one")
    
    total_patients = p_count_res["total"] if p_count_res else 0
    total_visits = v_count_res["total"] if v_count_res else 0
    total_departments = d_count_res["total"] if d_count_res else 0
    
    # 2. Visits this month
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    v_month_res = execute_query(
        """
        SELECT COUNT(*) AS total 
        FROM visits 
        WHERE YEAR(visit_date) = %s AND MONTH(visit_date) = %s
        """,
        (current_year, current_month),
        fetch="one"
    )
    visits_this_month = v_month_res["total"] if v_month_res else 0
    
    # 3. Monthly visit trend (Computed via Pandas)
    monthly_rows = execute_query(
        "SELECT visit_date FROM visits ORDER BY visit_date ASC",
        fetch="all"
    )
    
    if monthly_rows:
        df_monthly = pd.DataFrame(monthly_rows)
        df_monthly["visit_date"] = pd.to_datetime(df_monthly["visit_date"])
        df_monthly["period"] = df_monthly["visit_date"].dt.to_period("M")
        df_monthly["month_label"] = df_monthly["visit_date"].dt.strftime("%b %Y")
        
        monthly_summary = (
            df_monthly.groupby(["period", "month_label"], observed=False)
            .size()
            .reset_index(name="visit_count")
            .sort_values("period")
        )
        monthly_labels = monthly_summary["month_label"].tolist()
        monthly_counts = [int(c) for c in monthly_summary["visit_count"].tolist()]
    else:
        monthly_labels = []
        monthly_counts = []
        
    # 4. Department-wise visit distribution
    dept_query = """
        SELECT d.department_name, COUNT(v.visit_id) AS visit_count
        FROM departments d
        LEFT JOIN visits v ON d.department_id = v.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY visit_count DESC, d.department_name ASC
    """
    dept_rows = execute_query(dept_query, fetch="all")
    if dept_rows:
        df_dept = pd.DataFrame(dept_rows)
        dept_labels = df_dept["department_name"].tolist()
        dept_counts = [int(c) for c in df_dept["visit_count"].tolist()]
    else:
        dept_labels = []
        dept_counts = []
        
    # 5. Visit types distribution
    type_query = """
        SELECT visit_type, COUNT(*) AS count
        FROM visits
        GROUP BY visit_type
        ORDER BY count DESC
    """
    type_rows = execute_query(type_query, fetch="all")
    if type_rows:
        df_type = pd.DataFrame(type_rows)
        type_labels = df_type["visit_type"].tolist()
        type_counts = [int(c) for c in df_type["count"].tolist()]
    else:
        type_labels = []
        type_counts = []
        
    # 6. Recent visits (latest 8)
    recent_query = """
        SELECT 
            v.visit_id,
            v.patient_id,
            d.department_name,
            v.visit_date,
            v.visit_type
        FROM visits v
        JOIN departments d ON v.department_id = d.department_id
        ORDER BY v.visit_date DESC, v.visit_id DESC
        LIMIT 8
    """
    recent_visits = execute_query(recent_query, fetch="all")
    
    return {
        "stats": {
            "total_patients": total_patients,
            "total_visits": total_visits,
            "total_departments": total_departments,
            "visits_this_month": visits_this_month,
        },
        "charts": {
            "monthly_labels": monthly_labels,
            "monthly_counts": monthly_counts,
            "dept_labels": dept_labels,
            "dept_counts": dept_counts,
            "type_labels": type_labels,
            "type_counts": type_counts,
        },
        "recent_visits": recent_visits
    }

def get_analytics_report(start_date=None, end_date=None):
    """
    Generate in-depth statistical summaries and chart series using Pandas and NumPy.
    Supports filtering by custom date ranges.
    """
    conditions = []
    params = []
    
    if start_date:
        conditions.append("v.visit_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("v.visit_date <= %s")
        params.append(end_date)
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    raw_query = f"""
        SELECT 
            v.visit_id,
            v.patient_id,
            p.age_group,
            COALESCE(p.gender, 'Not Specified') AS gender,
            d.department_id,
            d.department_name,
            v.visit_date,
            v.visit_type
        FROM visits v
        JOIN departments d ON v.department_id = d.department_id
        JOIN patients p ON v.patient_id = p.patient_id
        {where_clause}
        ORDER BY v.visit_date ASC, v.visit_id ASC
    """
    
    records = execute_query(raw_query, tuple(params), fetch="all")
    
    if not records:
        return {
            "has_data": False,
            "total_visits": 0,
            "unique_patients": 0,
            "avg_visits_per_day": 0.0,
            "peak_day": {"date": "N/A", "count": 0},
            "busiest_dept": {"name": "N/A", "count": 0},
            "top_visit_type": {"name": "N/A", "count": 0},
            "date_range_str": f"{start_date or 'Beginning'} to {end_date or 'Present'}",
            "charts": {
                "monthly_labels": [],
                "monthly_counts": [],
                "dept_labels": [],
                "dept_counts": [],
                "type_labels": [],
                "type_counts": [],
                "age_labels": [],
                "age_counts": [],
            },
            "dept_breakdown": [],
            "daily_trend": []
        }
    
    df = pd.DataFrame(records)
    df["visit_date"] = pd.to_datetime(df["visit_date"])
    df["month_period"] = df["visit_date"].dt.to_period("M")
    df["month_label"] = df["visit_date"].dt.strftime("%b %Y")
    df["date_str"] = df["visit_date"].dt.strftime("%Y-%m-%d")
    
    total_visits = int(len(df))
    unique_patients = int(df["patient_id"].nunique())
    
    min_date = df["visit_date"].min()
    max_date = df["visit_date"].max()
    active_days = max(1, (max_date - min_date).days + 1)
    
    daily_counts_df = df.groupby("date_str").size().reset_index(name="visits")
    daily_counts_array = daily_counts_df["visits"].to_numpy()
    
    avg_visits_per_day = round(float(np.mean(daily_counts_array)), 2)
    max_visits_in_a_day = int(np.max(daily_counts_array))
    peak_date_row = daily_counts_df.loc[daily_counts_df["visits"].idxmax()]
    peak_day = {
        "date": peak_date_row["date_str"],
        "count": int(peak_date_row["visits"])
    }
    
    dept_counts = df["department_name"].value_counts()
    busiest_dept_name = dept_counts.index[0]
    busiest_dept_count = int(dept_counts.iloc[0])
    
    type_counts = df["visit_type"].value_counts()
    top_type_name = type_counts.index[0]
    top_type_count = int(type_counts.iloc[0])
    
    # 1. Monthly visit trend
    monthly_group = df.groupby(["month_period", "month_label"], observed=False).size().reset_index(name="count")
    monthly_group = monthly_group.sort_values("month_period")
    monthly_labels = monthly_group["month_label"].tolist()
    monthly_counts = [int(x) for x in monthly_group["count"].tolist()]
    
    # 2. Department-wise counts
    dept_labels = dept_counts.index.tolist()
    dept_series = [int(x) for x in dept_counts.values.tolist()]
    
    # 3. Visit-type distribution
    type_labels = type_counts.index.tolist()
    type_series = [int(x) for x in type_counts.values.tolist()]
    
    # 4. Age-group distribution
    age_order = ["0-17", "18-35", "36-50", "51-65", "65+"]
    age_counts = df["age_group"].value_counts()
    age_labels = []
    age_series = []
    for grp in age_order:
        age_labels.append(grp)
        age_series.append(int(age_counts.get(grp, 0)))
    for grp in age_counts.index:
        if grp not in age_labels:
            age_labels.append(grp)
            age_series.append(int(age_counts[grp]))
            
    # 5. Department breakdown table
    dept_table_data = []
    for dept_name, group in df.groupby("department_name"):
        v_count = len(group)
        u_patients = group["patient_id"].nunique()
        pct = round((v_count / total_visits) * 100, 1)
        mode_type = group["visit_type"].mode()
        common_type = mode_type.iloc[0] if not mode_type.empty else "N/A"
        dept_table_data.append({
            "department_name": dept_name,
            "total_visits": v_count,
            "unique_patients": u_patients,
            "percent_of_total": pct,
            "common_type": common_type
        })
    dept_table_data.sort(key=lambda x: x["total_visits"], reverse=True)
    
    # 6. Daily trend
    daily_trend = daily_counts_df.tail(14).to_dict(orient="records")
    
    return {
        "has_data": True,
        "total_visits": total_visits,
        "unique_patients": unique_patients,
        "avg_visits_per_day": avg_visits_per_day,
        "peak_day": peak_day,
        "busiest_dept": {"name": busiest_dept_name, "count": busiest_dept_count},
        "top_visit_type": {"name": top_type_name, "count": top_type_count},
        "date_range_str": f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}",
        "charts": {
            "monthly_labels": monthly_labels,
            "monthly_counts": monthly_counts,
            "dept_labels": dept_labels,
            "dept_counts": dept_series,
            "type_labels": type_labels,
            "type_counts": type_series,
            "age_labels": age_labels,
            "age_counts": age_series,
        },
        "dept_breakdown": dept_table_data,
        "daily_trend": daily_trend
    }

def export_visits_csv(start_date=None, end_date=None, department_id=None, visit_type=None):
    """
    Export filtered visit records to a CSV string using Pandas.
    """
    conditions = []
    params = []
    
    if start_date:
        conditions.append("v.visit_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("v.visit_date <= %s")
        params.append(end_date)
    if department_id:
        conditions.append("v.department_id = %s")
        params.append(department_id)
    if visit_type:
        conditions.append("v.visit_type = %s")
        params.append(visit_type)
        
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    query = f"""
        SELECT 
            v.visit_id AS `Visit ID`,
            v.patient_id AS `Patient ID`,
            p.age_group AS `Age Group`,
            COALESCE(p.gender, 'Not Specified') AS `Gender`,
            d.department_name AS `Department`,
            v.visit_date AS `Visit Date`,
            v.visit_type AS `Visit Type`
        FROM visits v
        JOIN departments d ON v.department_id = d.department_id
        JOIN patients p ON v.patient_id = p.patient_id
        {where_clause}
        ORDER BY v.visit_date DESC, v.visit_id DESC
    """
    rows = execute_query(query, tuple(params), fetch="all")
    
    if not rows:
        df = pd.DataFrame(columns=[
            "Visit ID", "Patient ID", "Age Group", "Gender", 
            "Department", "Visit Date", "Visit Type"
        ])
    else:
        df = pd.DataFrame(rows)
        if "Visit Date" in df.columns:
            df["Visit Date"] = pd.to_datetime(df["Visit Date"]).dt.strftime("%Y-%m-%d")
            
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()

def export_analytics_summary_csv(start_date=None, end_date=None):
    """
    Export aggregate analytics summary to CSV using Pandas.
    """
    report = get_analytics_report(start_date, end_date)
    
    summary_data = [
        {"Metric": "Date Range", "Value": report["date_range_str"]},
        {"Metric": "Total Visits", "Value": report["total_visits"]},
        {"Metric": "Unique Patients", "Value": report["unique_patients"]},
        {"Metric": "Average Visits Per Day", "Value": report["avg_visits_per_day"]},
        {"Metric": "Peak Visit Date", "Value": f"{report['peak_day']['date']} ({report['peak_day']['count']} visits)"},
        {"Metric": "Busiest Department", "Value": f"{report['busiest_dept']['name']} ({report['busiest_dept']['count']} visits)"},
        {"Metric": "Most Common Visit Type", "Value": f"{report['top_visit_type']['name']} ({report['top_visit_type']['count']} visits)"},
    ]
    df_summary = pd.DataFrame(summary_data)
    
    if report["dept_breakdown"]:
        df_dept = pd.DataFrame(report["dept_breakdown"])
        df_dept.rename(columns={
            "department_name": "Department",
            "total_visits": "Total Visits",
            "unique_patients": "Unique Patients",
            "percent_of_total": "% of Total",
            "common_type": "Most Frequent Type"
        }, inplace=True)
    else:
        df_dept = pd.DataFrame(columns=[
            "Department", "Total Visits", "Unique Patients", "% of Total", "Most Frequent Type"
        ])
        
    buffer = io.StringIO()
    buffer.write("=== HOSPITAL PATIENT DATA ANALYSIS - EXECUTIVE SUMMARY ===\n")
    df_summary.to_csv(buffer, index=False)
    buffer.write("\n=== DEPARTMENT-WISE PERFORMANCE SUMMARY ===\n")
    df_dept.to_csv(buffer, index=False)
    
    return buffer.getvalue()
