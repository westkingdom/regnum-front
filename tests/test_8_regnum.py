"""Tests for pages/2_Regnum.py, run through Streamlit's AppTest harness."""
import importlib.util
import json
import os
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

PAGE = "pages/2_Regnum.py"
GROUP_NAME = "12th-night"
GROUP_ID = "03jtnz0s27bz16g"
VALID_EMAIL = "test@westkingdom.org"
INVALID_EMAIL = "test@otherdomain.com"


def _load_page_module():
    spec = importlib.util.spec_from_file_location(
        "pages._2_Regnum",
        os.path.join(os.path.dirname(__file__), "..", "pages", "2_Regnum.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # main() only runs under __main__
    return module


regnum_page = _load_page_module()


@pytest.fixture
def deps():
    with patch("utils.queries.get_group_members") as get_members, \
         patch("utils.queries.add_member_to_group") as add, \
         patch("utils.email.send_registration_email") as send_email:
        get_members.return_value = {"members": [{"email": "one@westkingdom.org", "role": "member"}]}
        add.return_value = True
        send_email.return_value = True
        yield {"get_members": get_members, "add": add, "send_email": send_email}


def _app(authenticated=True):
    at = AppTest.from_file(PAGE, default_timeout=10)
    if authenticated:
        at.session_state["is_authenticated"] = True
        at.session_state["user_email"] = "officer@westkingdom.org"
        at.session_state["user_name"] = "Officer"
    return at.run()


def _select_group(at):
    at.selectbox[0].set_value(GROUP_NAME).run()
    return at


def _text_input(at, label):
    return next(t for t in at.text_input if t.label == label)


def _submit(at, sca_name="Test SCA Name", email=VALID_EMAIL):
    _text_input(at, "SCA Name*").set_value(sca_name)
    _text_input(at, "Westkingdom Email Address*").set_value(email)
    next(b for b in at.button if b.label == "Add Member").click().run()
    return at


def _messages(elements):
    return [e.value for e in elements]


# --- Data loading ---

def test_data_loading_success(tmp_path):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps([{"name": "Group A", "id": "id_a"}, {"name": "Group B", "id": "id_b"}]))

    options, name_to_id = regnum_page.load_group_data(str(path))

    assert options == ["Group A", "Group B"]
    assert name_to_id == {"Group A": "id_a", "Group B": "id_b"}


def test_data_loading_file_not_found(tmp_path):
    options, name_to_id = regnum_page.load_group_data(str(tmp_path / "missing.json"))

    assert options == []
    assert name_to_id == {}


def test_data_loading_missing_columns(tmp_path):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps([{"name": "Group A"}]))

    assert regnum_page.load_group_data(str(path)) == ([], {})


# --- Page behaviour ---

def test_unauthenticated_user_is_blocked(deps):
    at = _app(authenticated=False)

    assert not at.exception
    assert "Authentication required." in _messages(at.error)
    deps["get_members"].assert_not_called()


def test_display_members_success(deps):
    at = _select_group(_app())

    assert not at.exception
    deps["get_members"].assert_called_once_with(GROUP_ID)
    assert len(at.dataframe) == 1
    assert list(at.dataframe[0].value.columns) == ["email", "role"]


def test_display_members_no_members(deps):
    deps["get_members"].return_value = {"members": []}

    at = _select_group(_app())

    assert len(at.dataframe) == 0
    assert f"The group '{GROUP_NAME}' currently has no members." in _messages(at.info)


def test_display_members_api_fail(deps):
    deps["get_members"].return_value = None

    at = _select_group(_app())

    assert len(at.dataframe) == 0
    assert (
        f"Failed to fetch members for group '{GROUP_NAME}'. The API might be down or the group ID is invalid."
        in _messages(at.error)
    )
    # The add-member form is not offered when members can't be loaded
    assert not any(t.label == "SCA Name*" for t in at.text_input)


# --- Form submission ---

def test_form_submit_success(deps):
    at = _submit(_select_group(_app()))

    assert not at.exception
    deps["send_email"].assert_called_once()
    form_data, group_name = deps["send_email"].call_args[0]
    assert group_name == GROUP_NAME
    assert form_data["sca_name"] == "Test SCA Name"
    assert form_data["westkingdom_email"] == VALID_EMAIL
    deps["add"].assert_called_once_with(GROUP_ID, VALID_EMAIL)


def test_form_submit_email_fail(deps):
    deps["send_email"].return_value = False

    at = _submit(_select_group(_app()))

    deps["send_email"].assert_called_once()
    deps["add"].assert_not_called()
    assert (
        "Failed to send registration notification email. Member was NOT added to the group. Please contact the administrator."
        in _messages(at.error)
    )


def test_form_submit_validation_missing_email(deps):
    at = _submit(_select_group(_app()), email="")

    assert "Westkingdom email address is required." in _messages(at.error)
    deps["send_email"].assert_not_called()
    deps["add"].assert_not_called()


def test_form_submit_validation_invalid_email(deps):
    at = _submit(_select_group(_app()), email=INVALID_EMAIL)

    assert "Please provide a valid email address ending with @westkingdom.org." in _messages(at.error)
    deps["send_email"].assert_not_called()
    deps["add"].assert_not_called()


def test_form_submit_validation_missing_sca_name(deps):
    at = _submit(_select_group(_app()), sca_name="")

    assert "SCA Name is required." in _messages(at.error)
    deps["send_email"].assert_not_called()
    deps["add"].assert_not_called()
