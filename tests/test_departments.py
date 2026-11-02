"""Tests for Department Management CRUD and Foreign Key Referential Integrity."""

def test_departments_list_view(client):
    """Test viewing department directory with visit counters."""
    response = client.get("/departments")
    assert response.status_code == 200
    assert b"Hospital Departments" in response.data
    assert b"Cardiology" in response.data
    assert b"Emergency Medicine" in response.data

def test_department_create_success(client):
    """Test creating a new department."""
    response = client.post("/departments/new", data={
        "department_name": "Neurology"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Department &#39;Neurology&#39; added successfully!" in response.data or b"Department 'Neurology' added successfully!" in response.data
    assert b"Neurology" in response.data

def test_department_create_empty_name(client):
    """Test validation on empty department name."""
    response = client.post("/departments/new", data={
        "department_name": "   "
    })
    assert response.status_code == 200
    assert b"Department name is required." in response.data

def test_department_create_duplicate_name(client):
    """Test preventing duplicate department names (case-insensitive)."""
    response = client.post("/departments/new", data={
        "department_name": "cardiology"
    })
    assert response.status_code == 200
    assert b"already exists" in response.data

def test_department_edit_success(client):
    """Test updating a department name."""
    response = client.post("/departments/3/edit", data={
        "department_name": "Pediatric Care"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Department updated to &#39;Pediatric Care&#39; successfully!" in response.data or b"Pediatric Care" in response.data

def test_department_delete_blocked_when_referenced(client):
    """
    CRITICAL REQUIREMENT:
    Department #1 (Cardiology) is linked to visits #1 and #3.
    Deletion must be strictly blocked and a clear error message returned.
    """
    response = client.post("/departments/1/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Cannot delete &#39;Cardiology&#39; because it is currently referenced" in response.data or b"Cannot delete 'Cardiology' because it is currently referenced" in response.data
    
    # Verify department still exists
    list_res = client.get("/departments")
    assert b"Cardiology" in list_res.data

def test_department_delete_success_when_unreferenced(client):
    """Test successfully deleting an unreferenced department (#3 has no visits)."""
    response = client.post("/departments/3/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"deleted successfully." in response.data
    
    # Verify department is removed
    list_res = client.get("/departments")
    assert b"#D-003" not in list_res.data
