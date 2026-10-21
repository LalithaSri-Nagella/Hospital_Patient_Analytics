"""Tests for Visit Management CRUD, filters, dropdowns, and validation operations."""

def test_visits_list_view(client):
    """Test accessing visits list and verifying table rows."""
    response = client.get("/visits")
    assert response.status_code == 200
    assert b"Patient Visits Log" in response.data
    assert b"#V-0001" in response.data
    assert b"Cardiology" in response.data

def test_visit_create_success(client):
    """Test recording a valid new visit."""
    response = client.post("/visits/new", data={
        "patient_id": "3",
        "department_id": "2",
        "visit_date": "2026-03-05",
        "visit_type": "Emergency"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Visit recorded successfully!" in response.data

def test_visit_create_invalid_patient(client):
    """Test validation when patient ID does not exist in database."""
    response = client.post("/visits/new", data={
        "patient_id": "9999",
        "department_id": "1",
        "visit_date": "2026-03-05",
        "visit_type": "Outpatient"
    })
    assert response.status_code == 200
    assert b"does not exist in the database" in response.data

def test_visit_create_invalid_department(client):
    """Test validation when department ID does not exist in database."""
    response = client.post("/visits/new", data={
        "patient_id": "1",
        "department_id": "9999",
        "visit_date": "2026-03-05",
        "visit_type": "Outpatient"
    })
    assert response.status_code == 200
    assert b"Selected department does not exist" in response.data

def test_visit_create_invalid_date(client):
    """Test validation when visit date is malformed."""
    response = client.post("/visits/new", data={
        "patient_id": "1",
        "department_id": "1",
        "visit_date": "not-a-date",
        "visit_type": "Outpatient"
    })
    assert response.status_code == 200
    assert b"Invalid date format" in response.data

def test_visit_create_invalid_visit_type(client):
    """Test validation when visit type is not in allowed list."""
    response = client.post("/visits/new", data={
        "patient_id": "1",
        "department_id": "1",
        "visit_date": "2026-03-05",
        "visit_type": "Vacation"
    })
    assert response.status_code == 200
    assert b"Please select a valid visit type" in response.data

def test_visit_edit_success(client):
    """Test updating an existing visit."""
    response = client.post("/visits/1/edit", data={
        "patient_id": "1",
        "department_id": "2",
        "visit_date": "2026-03-10",
        "visit_type": "Routine Checkup"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Visit #1 updated successfully!" in response.data
    assert b"Routine Checkup" in response.data

def test_visit_delete_success(client):
    """Test deleting a visit record."""
    response = client.post("/visits/2/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Visit #2 deleted successfully." in response.data
    
    # Confirm it is removed
    list_res = client.get("/visits")
    assert b"#V-0002" not in list_res.data

def test_visit_filters(client):
    """Test filtering visits by department and visit type."""
    # Filter by department_id=1 (Cardiology)
    res = client.get("/visits?department_id=1")
    assert res.status_code == 200
    assert b"#V-0001" in res.data
    assert b"#V-0002" not in res.data
