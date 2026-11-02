"""Tests for Patient Management CRUD, search, filter, and validation operations."""

def test_patients_list_view(client):
    """Test accessing the patients directory and verifying seed data presence."""
    response = client.get("/patients")
    assert response.status_code == 200
    assert b"Patients Directory" in response.data
    assert b"#P-0001" in response.data
    assert b"18-35" in response.data

def test_patient_create_success(client):
    """Test creating a new patient with valid demographic data."""
    response = client.post("/patients/new", data={
        "age_group": "51-65",
        "gender": "Male"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Patient registered successfully!" in response.data
    assert b"51-65" in response.data

def test_patient_create_missing_age_group(client):
    """Test validation failure when required age group is missing."""
    response = client.post("/patients/new", data={
        "age_group": "",
        "gender": "Male"
    })
    assert response.status_code == 200
    assert b"Age group is required." in response.data

def test_patient_create_invalid_age_group(client):
    """Test validation failure when an invalid age group string is provided."""
    response = client.post("/patients/new", data={
        "age_group": "100-200",
        "gender": "Male"
    })
    assert response.status_code == 200
    assert b"Invalid age group" in response.data

def test_patient_create_invalid_gender(client):
    """Test validation failure when an invalid gender string is provided."""
    response = client.post("/patients/new", data={
        "age_group": "18-35",
        "gender": "Alien"
    })
    assert response.status_code == 200
    assert b"Invalid gender" in response.data

def test_patient_edit_success(client):
    """Test updating an existing patient record."""
    response = client.post("/patients/1/edit", data={
        "age_group": "36-50",
        "gender": "Female"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Patient #1 updated successfully!" in response.data
    assert b"36-50" in response.data

def test_patient_edit_not_found(client):
    """Test attempting to edit a non-existent patient ID."""
    response = client.get("/patients/9999/edit", follow_redirects=True)
    assert response.status_code == 200
    assert b"Patient with ID 9999 not found" in response.data

def test_patient_delete_success(client):
    """Test deleting a patient and verifying removal."""
    response = client.post("/patients/2/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Patient #2 and associated visits removed successfully." in response.data
    
    # Confirm it no longer shows in the list
    list_res = client.get("/patients?search=2")
    assert b"#P-0002" not in list_res.data

def test_patient_search_and_filter(client):
    """Test searching by patient ID and filtering by age group."""
    # Search by ID
    res1 = client.get("/patients?search=1")
    assert res1.status_code == 200
    assert b"#P-0001" in res1.data
    assert b"#P-0002" not in res1.data
    
    # Filter by age group
    res2 = client.get("/patients?age_group=65+")
    assert res2.status_code == 200
    assert b"#P-0003" in res2.data
    assert b"#P-0001" not in res2.data
