def test_screener_presets(client):
    response = client.get(
        "/screener/presets"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 6
    assert "quality_compounder" in data["presets"]


def test_quality_compounder(client):
    response = client.get(
        "/screener/preset/quality_compounder"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["preset"] == "quality_compounder"
    assert data["count"] > 0
    assert len(data["results"]) == data["count"]


def test_unknown_screener_preset(client):
    response = client.get(
        "/screener/preset/does_not_exist"
    )

    assert response.status_code == 404
