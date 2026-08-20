def test_list_sectors(client):
    response = client.get("/sectors")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] > 0
    assert len(data["sectors"]) == data["count"]


def test_information_technology_sector(client):
    response = client.get(
        "/sectors/Information%20Technology"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sector"] == "Information Technology"
    assert data["company_count"] == 5
    assert len(data["companies"]) == 5


def test_unknown_sector(client):
    response = client.get(
        "/sectors/does_not_exist"
    )

    assert response.status_code == 404
