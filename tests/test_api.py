import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Event Booking API"}

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "password", "role": "user", "name": "Test User"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Create user first
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "login@example.com", "password": "password", "role": "user"},
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "password"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_rbac_flow(client: AsyncClient):
    # 1. Create Organizer
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "org@example.com", "password": "password", "role": "organizer"},
    )
    org_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "org@example.com", "password": "password"},
    )
    org_token = org_login.json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # 2. Create User
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "password", "role": "user"},
    )
    user_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "password"},
    )
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Organizer creates Event
    event_res = await client.post(
        "/api/v1/events/",
        json={
            "title": "Test Event",
            "date": "2025-12-25T10:00:00",
            "location": "Test Loc",
            "capacity": 100
        },
        headers=org_headers
    )
    assert event_res.status_code == 200
    event_id = event_res.json()["id"]

    # 4. User books Event
    booking_res = await client.post(
        "/api/v1/bookings/",
        json={"event_id": event_id},
        headers=user_headers
    )
    assert booking_res.status_code == 200
    booking_id = booking_res.json()["id"]

    # 5. Organizer tries to book (Should Fail)
    org_booking_res = await client.post(
        "/api/v1/bookings/",
        json={"event_id": event_id},
        headers=org_headers
    )
    assert org_booking_res.status_code == 403

    # 6. User updates Booking
    update_res = await client.put(
        f"/api/v1/bookings/{booking_id}",
        json={"status": "cancelled"},
        headers=user_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "cancelled"

    # 7. Organizer tries to delete Event (Should Succeed)
    delete_res = await client.delete(
        f"/api/v1/events/{event_id}",
        headers=org_headers
    )
    assert delete_res.status_code == 200

@pytest.mark.asyncio
async def test_admin_delete_user(client: AsyncClient):
    # 1. Create Admin
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "admin@example.com", "password": "password", "role": "admin", "name": "Admin User"},
    )
    admin_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "password"},
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Target User
    user_res = await client.post(
        "/api/v1/auth/signup",
        json={"email": "target@example.com", "password": "password", "role": "user", "name": "Target User"},
    )
    target_user_id = user_res.json()["id"]

    # 3. Create Organizer (to test unauthorized access)
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "org2@example.com", "password": "password", "role": "organizer", "name": "Org User"},
    )
    org_login = await client.post(
        "/api/v1/auth/login",
        data={"username": "org2@example.com", "password": "password"},
    )
    org_token = org_login.json()["access_token"]
    org_headers = {"Authorization": f"Bearer {org_token}"}

    # 4. Organizer tries to delete User (Should Fail)
    fail_res = await client.delete(
        f"/api/v1/users/{target_user_id}",
        headers=org_headers
    )
    assert fail_res.status_code == 403

    # 5. Admin deletes User (Should Succeed)
    success_res = await client.delete(
        f"/api/v1/users/{target_user_id}",
        headers=admin_headers
    )
    assert success_res.status_code == 200
    assert success_res.json()["email"] == "target@example.com"
