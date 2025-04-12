import pytest
from httpx import AsyncClient
from pydantic import HttpUrl, parse_obj_as
from app.main import app  # Import your FastAPI app

@pytest.mark.asyncio
async def test_login_for_access_token():
    form_data = {
        "username": "admin",
        "password": "secret",
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/token", data=form_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_create_qr_code_unauthorized():
    # Attempt to create a QR code without authentication
    qr_request = {
        "url": "https://example.com",
        "fill_color": "red",
        "back_color": "white",
        "size": 10,
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/qr-codes/", json=qr_request)
    assert response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_create_and_delete_qr_code():
    form_data = {
        "username": "admin",
        "password": "secret",
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login and get the access token
        token_response = await ac.post("/token", data=form_data)
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create a QR code
        qr_request = {
            "url": "https://example.com",
            "fill_color": "red",
            "back_color": "white",
            "size": 10,
        }
        create_response = await ac.post("/qr-codes/", json=qr_request, headers=headers)
        assert create_response.status_code in [201, 409]

        if create_response.status_code == 201:
            response_data = create_response.json()

            # Validate message
            assert response_data["message"] == "QR code created successfully."

            # Validate qr_code_url is a proper URL
            qr_code_url = response_data["qr_code_url"]
            parse_obj_as(HttpUrl, qr_code_url)  # Raises if invalid

            # Validate links structure
            links = response_data["links"]
            assert isinstance(links, list)
            assert all(
                isinstance(link, dict) and
                "rel" in link and
                "href" in link and
                "action" in link and
                "type" in link
                for link in links
            )

            # Delete the QR code
            qr_filename = qr_code_url.split('/')[-1]
            delete_response = await ac.delete(f"/qr-codes/{qr_filename}", headers=headers)
            assert delete_response.status_code == 204
