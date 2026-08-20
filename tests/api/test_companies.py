def test_company_profile(client):
    response = client.get("/companies/TCS")

    assert response.status_code == 200

    data = response.json()

    assert data["company"]["id"] == "TCS"


def test_company_profit_loss(client):
    response = client.get(
        "/companies/TCS/profit-loss"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert len(data["records"]) > 0


def test_company_balance_sheet(client):
    response = client.get(
        "/companies/TCS/balance-sheet"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert len(data["records"]) > 0


def test_company_cash_flow(client):
    response = client.get(
        "/companies/TCS/cash-flow"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert len(data["records"]) > 0


def test_company_ratios(client):
    response = client.get(
        "/companies/TCS/ratios"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["company_id"] == "TCS"
    assert len(data["records"]) > 0


def test_company_not_found(client):
    response = client.get(
        "/companies/DOESNOTEXIST"
    )

    assert response.status_code == 404
