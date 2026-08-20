def test_peers(client):
    response = client.get("/peers/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert len(data["records"]) > 0


def test_peers_not_found(client):
    response = client.get(
        "/peers/DOESNOTEXIST"
    )

    assert response.status_code == 404


def test_valuation_flags(client):
    response = client.get(
        "/valuation/flags"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 43
    assert len(data["records"]) == 43


def test_valuation_summary(client):
    response = client.get(
        "/valuation/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert "sheets" in data
    assert "Sheet1" in data["sheets"]
    assert len(data["sheets"]["Sheet1"]) == 92


def test_portfolio_statistics(client):
    response = client.get(
        "/portfolio/statistics"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 5


def test_portfolio_clusters(client):
    response = client.get(
        "/portfolio/clusters"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 92
    assert len(data["records"]) == 92


def test_tearsheet_document(client):
    response = client.get(
        "/documents/tearsheet/TCS"
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ].startswith("application/pdf")
    assert len(response.content) > 100000


def test_tearsheet_not_found(client):
    response = client.get(
        "/documents/tearsheet/DOESNOTEXIST"
    )

    assert response.status_code == 404
