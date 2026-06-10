from unittest.mock import patch, MagicMock
import importlib.util, pathlib

_path = pathlib.Path(__file__).resolve().parents[1] / "ptm_client.py"
_spec = importlib.util.spec_from_file_location("ptm_client", _path)
ptm_client = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ptm_client)
PTMClient = ptm_client.PTMClient


def _token_response(token="tok-1", expires_in=3600):
    m = MagicMock()
    m.status_code = 200
    m.json.return_value = {"access_token": token, "expires_in": expires_in, "scope": "tournament.read"}
    m.raise_for_status.return_value = None
    return m


def test_token_is_fetched_once_and_cached():
    c = PTMClient("http://ptm", "cid", "secret", "tournament.read")
    with patch.object(ptm_client.httpx, "post", return_value=_token_response()) as post:
        assert c._bearer() == "tok-1"
        assert c._bearer() == "tok-1"
    assert post.call_count == 1


def test_request_refetches_token_on_401():
    c = PTMClient("http://ptm", "cid", "secret", "tournament.read")
    resp401 = MagicMock(status_code=401)
    resp200 = MagicMock(status_code=200)
    with patch.object(ptm_client.httpx, "post", return_value=_token_response("tok-2")) as post, \
         patch.object(ptm_client.httpx, "request", side_effect=[resp401, resp200]) as req:
        out = c.request("GET", "/api/oauth/whoami/")
    assert out.status_code == 200
    assert req.call_count == 2
    assert post.call_count == 2
