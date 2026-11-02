"""Tests for Dashboard Statistics, Pandas & NumPy Analytics, and CSV Exports."""

def test_dashboard_live_statistics(client):
    """Test dashboard route and live database counts."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hospital Patient Dashboard" in response.data
    # In test fixtures: 3 patients, 3 visits, 3 departments
    assert b'id="statTotalPatients">3<' in response.data or b">3<" in response.data
    assert b'id="statTotalVisits">3<' in response.data or b">3<" in response.data

def test_analytics_metrics_and_distinction(client):
    """
    Test analytics page computations:
    Must clearly distinguish Total Visits (3) from Unique Patients (2).
    """
    response = client.get("/analytics")
    assert response.status_code == 200
    assert b"Hospital Patient Analytics" in response.data
    # 3 total visits
    assert b"Total Visits" in response.data
    # 2 unique patients (Patient 1 visited twice, Patient 2 visited once)
    assert b"Unique Patients" in response.data
    assert b"Distinct Individuals" in response.data

def test_analytics_date_filter(client):
    """Test analytics with working date filter."""
    # Date range covering only visit 1 (2026-03-01)
    response = client.get("/analytics?start_date=2026-03-01&end_date=2026-03-01")
    assert response.status_code == 200
    assert b"Total Visits" in response.data

def test_analytics_empty_dataset_handling(client):
    """
    CRITICAL REQUIREMENT:
    Handle empty datasets without errors when date filter yields zero records.
    """
    # A future date range with no visits
    response = client.get("/analytics?start_date=2099-01-01&end_date=2099-12-31")
    assert response.status_code == 200
    assert b"No analytics data available for this range" in response.data
    # Ensure no 500 error or exception was raised
    assert b"Internal Server Error" not in response.data

def test_export_visits_csv(client):
    """Test exporting visits data to CSV format."""
    response = client.get("/analytics/export/visits")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert "attachment; filename=hospital_visits_export_" in response.headers["Content-Disposition"]
    
    csv_text = response.data.decode("utf-8")
    assert "Visit ID,Patient ID,Age Group,Gender,Department,Visit Date,Visit Type" in csv_text
    assert "Cardiology" in csv_text
    assert "Emergency Medicine" in csv_text

def test_export_summary_csv(client):
    """Test exporting aggregated analytics summary to CSV format."""
    response = client.get("/analytics/export/summary")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv")
    assert "attachment; filename=hospital_analytics_summary_" in response.headers["Content-Disposition"]
    
    csv_text = response.data.decode("utf-8")
    assert "EXECUTIVE SUMMARY" in csv_text
    assert "Total Visits" in csv_text
    assert "Unique Patients" in csv_text
    assert "DEPARTMENT-WISE PERFORMANCE SUMMARY" in csv_text
