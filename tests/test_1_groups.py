import sys
import os
from unittest.mock import patch, MagicMock, ANY
import pytest
import pandas as pd

# Add project root to the Python path to allow importing 'pages' and 'utils'
# Adjust the path depth (../..) based on your test directory structure
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Since Streamlit pages run top-to-bottom, we patch globally for imports
# We mock the actual functions from utils.queries, not where they are imported in pages.1_groups
MOCK_GET_ALL_GROUPS = 'utils.queries.get_all_groups'
MOCK_GET_GROUP_MEMBERS = 'utils.queries.get_group_members'
MOCK_ADD_MEMBER = 'utils.queries.add_member_to_group'
MOCK_REMOVE_MEMBER = 'utils.queries.remove_member_from_group'
MOCK_IS_VALID_EMAIL = 'utils.queries.is_valid_email'

# Mock streamlit functions used in the page
MOCK_ST_TITLE = 'streamlit.title'
MOCK_ST_HEADER = 'streamlit.header'
MOCK_ST_SUBHEADER = 'streamlit.subheader'
MOCK_ST_TABS = 'streamlit.tabs'
MOCK_ST_SIDEBAR = 'streamlit.sidebar' # Use context manager mock for 'with'
MOCK_ST_BUTTON = 'streamlit.button'
MOCK_ST_WARNING = 'streamlit.warning'
MOCK_ST_INFO = 'streamlit.info'
MOCK_ST_ERROR = 'streamlit.error'
MOCK_ST_SUCCESS = 'streamlit.success'
MOCK_ST_TEXT_INPUT = 'streamlit.text_input'
MOCK_ST_SELECTBOX = 'streamlit.selectbox'
MOCK_ST_DATAFRAME = 'streamlit.dataframe'
MOCK_ST_JSON = 'streamlit.json'
MOCK_ST_FORM = 'streamlit.form' # Use context manager mock for 'with'
MOCK_ST_FORM_SUBMIT_BUTTON = 'streamlit.form_submit_button'
MOCK_ST_RERUN = 'streamlit.experimental_rerun'

# Define mock data
MOCK_GROUPS_RESPONSE = (
    ["Group Alpha", "Group Beta"], # options
    {"Group Alpha": "id_alpha", "Group Beta": "id_beta"} # name_to_id
)

MOCK_EMPTY_GROUPS_RESPONSE = ([], {})

MOCK_MEMBERS_ALPHA_RESPONSE = {
    "members": [
        {"email": "a@westkingdom.org", "role": "member", "status": "active", "type": "user"},
        {"email": "b@westkingdom.org", "role": "owner", "status": "active", "type": "user"}
    ]
}
MOCK_MEMBERS_BETA_RESPONSE = {"members": []} # Group Beta has no members

# --- Helper to simulate running the Streamlit script ---
def run_script():
    """Imports and runs the Streamlit page script."""
    # Need to ensure the script is treated as __main__ if it has such checks
    # For simple pages, just importing might be enough to trigger execution
    import pages.pkg_1_groups # Use pkg_ prefix if needed by streamlit loader

# --- Test Fixtures ---
@pytest.fixture(autouse=True)
def mock_streamlit():
    """Auto-applied fixture to mock all Streamlit calls."""
    with patch(MOCK_ST_TITLE) as mt, \
         patch(MOCK_ST_HEADER) as mh, \
         patch(MOCK_ST_SUBHEADER) as ms, \
         patch(MOCK_ST_TABS) as mtabs, \
         patch(MOCK_ST_SIDEBAR, MagicMock()) as msidebar, \
         patch(MOCK_ST_BUTTON) as mb, \
         patch(MOCK_ST_WARNING) as mw, \
         patch(MOCK_ST_INFO) as mi, \
         patch(MOCK_ST_ERROR) as me, \
         patch(MOCK_ST_SUCCESS) as msucc, \
         patch(MOCK_ST_TEXT_INPUT) as mti, \
         patch(MOCK_ST_SELECTBOX) as msel, \
         patch(MOCK_ST_DATAFRAME) as mdf, \
         patch(MOCK_ST_JSON) as mjson, \
         patch(MOCK_ST_FORM, MagicMock()) as mform, \
         patch(MOCK_ST_FORM_SUBMIT_BUTTON) as mfsb, \
         patch(MOCK_ST_RERUN) as mrerun:

        # Configure mocks that return values or need specific setup
        mtabs.return_value = (MagicMock(), MagicMock(), MagicMock()) # Simulate 3 tabs
        mti.return_value = "" # Default search/input to empty
        msel.return_value = None # Default selectbox to no selection
        mb.return_value = False # Default button state
        mfsb.return_value = False # Default form submit

        yield { # Yield mocks for individual tests to use/modify
            'title': mt, 'header': mh, 'subheader': ms, 'tabs': mtabs,
            'sidebar': msidebar, 'button': mb, 'warning': mw, 'info': mi,
            'error': me, 'success': msucc, 'text_input': mti, 'selectbox': msel,
            'dataframe': mdf, 'json': mjson, 'form': mform,
            'form_submit_button': mfsb, 'rerun': mrerun
        }

# --- Test Cases ---

@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS)
def test_view_groups_initial_load(mock_get_all, mock_get_members, mock_streamlit):
    """Test initial state of 'View Groups' tab before selection."""
    mock_get_all.return_value = MOCK_GROUPS_RESPONSE
    mock_streamlit['selectbox'].return_value = None # Ensure no group is selected

    run_script()

    # Check if get_all_groups was called
    mock_get_all.assert_called_once()

    # Check if selectbox was populated with correct options
    # Note: We might have multiple selectboxes due to tabs, check call args
    view_tab_selectbox_call = None
    for call in mock_streamlit['selectbox'].call_args_list:
        if call.kwargs.get('key') == 'select_view_group':
            view_tab_selectbox_call = call
            break
    assert view_tab_selectbox_call is not None, "View Group selectbox not found"
    assert view_tab_selectbox_call.kwargs['options'] == MOCK_GROUPS_RESPONSE[0] # Check names list

    # Check that get_group_members was NOT called
    mock_get_members.assert_not_called()

    # Check that the info message for selection is shown
    # Need to find the correct call among potentially many st.info calls
    # A more robust way might involve checking calls within the specific tab context manager
    mock_streamlit['info'].assert_any_call("Please select a group to view its members.")

@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS)
def test_view_groups_select_group_with_members(mock_get_all, mock_get_members, mock_streamlit):
    """Test selecting a group and displaying its members."""
    mock_get_all.return_value = MOCK_GROUPS_RESPONSE
    mock_get_members.return_value = MOCK_MEMBERS_ALPHA_RESPONSE
    mock_streamlit['selectbox'].return_value = "Group Alpha" # Simulate selecting "Group Alpha"

    run_script()

    mock_get_all.assert_called_once()
    mock_get_members.assert_called_once_with("id_alpha") # Check correct ID used

    # Check that st.dataframe was called
    mock_streamlit['dataframe'].assert_called_once()
    # Optional: Check the DataFrame content passed to st.dataframe
    call_args, call_kwargs = mock_streamlit['dataframe'].call_args
    assert isinstance(call_args[0], pd.DataFrame)
    assert list(call_args[0].columns) == ['email', 'role', 'status', 'type']
    assert len(call_args[0]) == 2
    assert call_kwargs.get('hide_index') is True


@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS)
def test_view_groups_select_group_no_members(mock_get_all, mock_get_members, mock_streamlit):
    """Test selecting a group with no members."""
    mock_get_all.return_value = MOCK_GROUPS_RESPONSE
    mock_get_members.return_value = MOCK_MEMBERS_BETA_RESPONSE # Empty members list
    # Simulate selecting "Group Beta" (find the correct selectbox call)
    mock_streamlit['selectbox'].side_effect = lambda *args, **kwargs: \
        "Group Beta" if kwargs.get('key') == 'select_view_group' else None

    run_script()

    mock_get_all.assert_called_once()
    mock_get_members.assert_called_once_with("id_beta")
    mock_streamlit['dataframe'].assert_not_called() # No dataframe should be shown
    mock_streamlit['info'].assert_any_call("This group has no members (API returned an empty 'members' list or missing key).")


@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS)
def test_view_groups_member_fetch_api_error(mock_get_all, mock_get_members, mock_streamlit):
    """Test API error when fetching members."""
    mock_get_all.return_value = MOCK_GROUPS_RESPONSE
    mock_get_members.return_value = None # Simulate API failure
    # Simulate selecting "Group Alpha"
    mock_streamlit['selectbox'].side_effect = lambda *args, **kwargs: \
        "Group Alpha" if kwargs.get('key') == 'select_view_group' else None

    run_script()

    mock_get_all.assert_called_once()
    mock_get_members.assert_called_once_with("id_alpha")
    mock_streamlit['dataframe'].assert_not_called()
    mock_streamlit['warning'].assert_any_call("Could not fetch members for Group Alpha. The API might be down or the group ID is invalid (API returned None).")


@patch(MOCK_GET_ALL_GROUPS)
def test_view_groups_load_error(mock_get_all, mock_streamlit):
    """Test failure to load groups."""
    mock_get_all.return_value = MOCK_EMPTY_GROUPS_RESPONSE

    run_script()

    mock_get_all.assert_called_once()
    mock_streamlit['warning'].assert_any_call("No groups found or failed to load groups. Please check the data source or create a new group.")
    # Ensure selectbox wasn't even attempted with empty options
    assert not any(call.kwargs.get('key') == 'select_view_group' for call in mock_streamlit['selectbox'].call_args_list)


# --- Tests for Manage Members Tab (Tab 3) ---

# Mock data specifically for Manage Members tab which seems to expect a different structure from get_all_groups initially
MOCK_MANAGE_GROUPS_RESPONSE = {
    "groups": [
        {"id": "id_manage_1", "name": "Manage Group 1"},
        {"id": "id_manage_2", "name": "Manage Group 2"}
    ]
}
MOCK_MANAGE_MEMBERS_RESPONSE = {
    "members": [{"email": "member1@westkingdom.org"}]
}


@patch(MOCK_REMOVE_MEMBER)
@patch(MOCK_ADD_MEMBER)
@patch(MOCK_IS_VALID_EMAIL)
@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS) # This mock needs careful handling due to different return types expected
def test_manage_members_add_valid_email(mock_get_all, mock_get_members, mock_is_valid, mock_add, mock_remove, mock_streamlit):
    """Test adding a member with a valid email."""
    # get_all_groups called multiple times with different expected outputs
    # First for tab1 (options, map), then for tab3 (dict with 'groups')
    mock_get_all.side_effect = [MOCK_GROUPS_RESPONSE, MOCK_MANAGE_GROUPS_RESPONSE]
    mock_get_members.return_value = MOCK_MANAGE_MEMBERS_RESPONSE
    mock_is_valid.return_value = True
    mock_add.return_value = True # Simulate successful addition

    # Simulate selecting the group in the Manage tab
    mock_streamlit['selectbox'].side_effect = lambda *args, **kwargs: \
        "Manage Group 1" if kwargs.get('key') == 'select_manage_group' else \
        None # Default others

    # Simulate entering email and clicking submit in the Add form
    mock_streamlit['text_input'].side_effect = lambda *args, **kwargs: \
        "new@westkingdom.org" if kwargs.get('key') == 'add_member_form' else "" # Assume form key helps identify
    mock_streamlit['form_submit_button'].side_effect = lambda *args, **kwargs: \
        True if args[0] == "Add Member" else False # Check label


    run_script()

    # Verify correct group ID and email passed to add_member_to_group
    # The group ID 'id_manage_1' comes from MOCK_MANAGE_GROUPS_RESPONSE
    mock_add.assert_called_once_with("id_manage_1", "new@westkingdom.org")
    mock_is_valid.assert_called_once_with("new@westkingdom.org")
    mock_streamlit['success'].assert_any_call("Successfully added new@westkingdom.org to Manage Group 1")
    mock_streamlit['rerun'].assert_called_once() # Check for refresh


@patch(MOCK_REMOVE_MEMBER)
@patch(MOCK_ADD_MEMBER)
@patch(MOCK_IS_VALID_EMAIL)
@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS)
def test_manage_members_add_invalid_email(mock_get_all, mock_get_members, mock_is_valid, mock_add, mock_remove, mock_streamlit):
    """Test adding a member with an invalid email."""
    mock_get_all.side_effect = [MOCK_GROUPS_RESPONSE, MOCK_MANAGE_GROUPS_RESPONSE]
    mock_get_members.return_value = MOCK_MANAGE_MEMBERS_RESPONSE
    mock_is_valid.return_value = False # Simulate invalid email
    mock_add.return_value = True # Should not be called

    mock_streamlit['selectbox'].side_effect = lambda *args, **kwargs: \
        "Manage Group 1" if kwargs.get('key') == 'select_manage_group' else None
    mock_streamlit['text_input'].side_effect = lambda *args, **kwargs: \
        "invalid-email" if kwargs.get('key') == 'add_member_form' else ""
    mock_streamlit['form_submit_button'].side_effect = lambda *args, **kwargs: \
        True if args[0] == "Add Member" else False

    run_script()

    mock_is_valid.assert_called_once_with("invalid-email")
    mock_add.assert_not_called() # Add should not be attempted
    mock_streamlit['error'].assert_any_call("Invalid email format. Email must be from westkingdom.org domain")
    mock_streamlit['rerun'].assert_not_called()


@patch(MOCK_REMOVE_MEMBER)
@patch(MOCK_ADD_MEMBER)
@patch(MOCK_GET_GROUP_MEMBERS)
@patch(MOCK_GET_ALL_GROUPS)
def test_manage_members_remove_member(mock_get_all, mock_get_members, mock_add, mock_remove, mock_streamlit):
    """Test removing a member."""
    mock_get_all.side_effect = [MOCK_GROUPS_RESPONSE, MOCK_MANAGE_GROUPS_RESPONSE]
    # Simulate members being present for removal selectbox
    existing_member_email = "member1@westkingdom.org"
    mock_get_members.return_value = {"members": [{"email": existing_member_email}]}
    mock_remove.return_value = True # Simulate successful removal

    # Simulate selecting group and member, then clicking remove button
    mock_streamlit['selectbox'].side_effect = lambda *args, **kwargs: \
        "Manage Group 1" if kwargs.get('key') == 'select_manage_group' else \
        existing_member_email if kwargs.get('key') == 'remove_member_select' else \
        None
    # Simulate clicking the *Remove* button (not the form submit)
    mock_streamlit['button'].side_effect = lambda *args, **kwargs: \
        True if args[0] == "Remove Selected Member" else False
    # Simulate confirming the warning (st.warning returns True if confirmed, though testing this interaction is tricky)
    mock_streamlit['warning'].return_value = True


    run_script()

    # Verify correct group ID and email passed to remove_member_from_group
    mock_remove.assert_called_once_with("id_manage_1", existing_member_email)
    mock_streamlit['success'].assert_any_call(f"Successfully removed {existing_member_email}")
    mock_streamlit['rerun'].assert_called_once()
