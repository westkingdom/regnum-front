"""Tests for pages/1_Groups.py, run through Streamlit's AppTest harness."""
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

PAGE = "pages/1_Groups.py"

MOCK_GROUPS_RESPONSE = (
    ["Group Alpha", "Group Beta"],
    {"Group Alpha": "id_alpha", "Group Beta": "id_beta"},
)

MOCK_MEMBERS_ALPHA_RESPONSE = {
    "members": [
        {"email": "a@westkingdom.org", "role": "member", "status": "active", "type": "user"},
        {"email": "b@westkingdom.org", "role": "owner", "status": "active", "type": "user"},
    ]
}


@pytest.fixture
def api():
    """Patch the API helpers the page imports from utils.queries."""
    with patch("utils.queries.get_all_groups") as get_all, \
         patch("utils.queries.get_group_members") as get_members, \
         patch("utils.queries.add_member_to_group") as add, \
         patch("utils.queries.remove_member_from_group") as remove:
        get_all.return_value = MOCK_GROUPS_RESPONSE
        get_members.return_value = MOCK_MEMBERS_ALPHA_RESPONSE
        add.return_value = True
        remove.return_value = True
        yield {"get_all": get_all, "get_members": get_members, "add": add, "remove": remove}


def _app(authenticated=True):
    at = AppTest.from_file(PAGE, default_timeout=10)
    if authenticated:
        at.session_state["is_authenticated"] = True
        at.session_state["user_email"] = "officer@westkingdom.org"
        at.session_state["user_name"] = "Officer"
    return at.run()


def _messages(elements):
    return [e.value for e in elements]


def test_unauthenticated_user_is_blocked(api):
    at = _app(authenticated=False)

    assert not at.exception
    assert "Authentication required." in _messages(at.error)
    api["get_all"].assert_not_called()
    api["get_members"].assert_not_called()


def test_view_groups_initial_load(api):
    at = _app()

    assert not at.exception
    api["get_all"].assert_called_once()
    assert at.selectbox(key="select_view_group").options == MOCK_GROUPS_RESPONSE[0]
    api["get_members"].assert_not_called()
    assert "Please select a group to view its members." in _messages(at.info)


def test_view_groups_load_error(api):
    api["get_all"].return_value = ([], {})

    at = _app()

    assert not at.exception
    assert "No groups found or failed to load groups. Cannot proceed with group management." in _messages(at.warning)
    assert len(at.tabs) == 0


def test_view_groups_select_group_with_members(api):
    at = _app()
    at.selectbox(key="select_view_group").set_value("Group Alpha").run()

    assert not at.exception
    api["get_members"].assert_called_once_with("id_alpha")
    assert len(at.dataframe) == 1
    df = at.dataframe[0].value
    assert list(df.columns) == ["email", "role", "status", "type"]
    assert len(df) == 2


def test_view_groups_select_group_no_members(api):
    api["get_members"].return_value = {"members": []}

    at = _app()
    at.selectbox(key="select_view_group").set_value("Group Beta").run()

    api["get_members"].assert_called_once_with("id_beta")
    assert len(at.dataframe) == 0
    assert "This group has no members (API returned an empty 'members' list or missing key)." in _messages(at.info)


def test_view_groups_member_fetch_api_error(api):
    api["get_members"].return_value = None

    at = _app()
    at.selectbox(key="select_view_group").set_value("Group Alpha").run()

    api["get_members"].assert_called_once_with("id_alpha")
    assert len(at.dataframe) == 0
    assert (
        "Could not fetch members for Group Alpha. The API might be down or the group ID is invalid (API returned None)."
        in _messages(at.warning)
    )


def _manage(at, group="Group Alpha"):
    return at.selectbox(key="select_manage_group").set_value(group).run()


def _member_email_input(at):
    return next(t for t in at.text_input if t.label == "Member Email")


def _add_member_button(at):
    return next(b for b in at.button if b.label == "Add Member")


def test_manage_members_add_valid_email(api):
    at = _manage(_app())
    _member_email_input(at).set_value("new@westkingdom.org")
    _add_member_button(at).click().run()

    assert not at.exception
    api["add"].assert_called_once_with("id_alpha", "new@westkingdom.org")


def test_manage_members_add_invalid_email(api):
    at = _manage(_app())
    _member_email_input(at).set_value("someone@example.com")
    _add_member_button(at).click().run()

    api["add"].assert_not_called()
    assert "Invalid email address. Must end with @westkingdom.org." in _messages(at.error)


def test_manage_members_remove_member(api):
    at = _manage(_app())
    at.selectbox(key="remove_member_select").set_value("b@westkingdom.org")
    at.button(key="remove_button").click().run()

    assert not at.exception
    api["remove"].assert_called_once_with("id_alpha", "b@westkingdom.org")
