def test_create_profile_and_run_pipeline(client):
    resp = client.post(
        "/api/v1/profiles",
        json={
            "name": "Acme",
            "domain": "acme.com",
            "industry": "Widgets",
            "competitors": ["example.com"],
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    profile_uuid = body["data"]["profile_uuid"]

    run = client.post(f"/api/v1/profiles/{profile_uuid}/run")
    assert run.status_code == 200
    run_body = run.get_json()
    assert run_body["success"] is True
    assert run_body["data"]["pipeline_id"]

    q = client.get(f"/api/v1/profiles/{profile_uuid}/queries")
    assert q.status_code == 200
    q_body = q.get_json()
    assert q_body["success"] is True
    assert q_body["data"]["total"] >= 1

