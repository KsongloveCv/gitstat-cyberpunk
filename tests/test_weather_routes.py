"""Weather router path tests."""


def test_weather_current_route_exists(client):
    r = client.get("/api/weather/current?lat=31.23&lon=121.47")
    assert r.status_code in (200, 503)


def test_weather_forecast_route_exists(client):
    r = client.get("/api/weather/forecast?lat=31.23&lon=121.47&days=3")
    assert r.status_code in (200, 503)


def test_weather_current_response_shape(client):
    r = client.get("/api/weather/current?lat=31.23&lon=121.47")
    if r.status_code == 200:
        body = r.json()
        assert body["code"] == 200
        assert "temperature" in body["data"]
