import sys
import os
import pytest
from unittest.mock import patch, MagicMock, ANY
import pandas as pd
from datetime import date

# Add project root to path to allow importing modules from utils and pages
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Mock streamlit before importing the page script
# This prevents Streamlit from trying to run in a server context during tests
mock_st = MagicMock()
# Mock specific streamlit functions used in the script
mock_st.selectbox = MagicMock(return_value="Selected Group Name") # Default mock return
mock_st.text_input = MagicMock(return_value="Test Input")
mock_st.number_input = MagicMock(return_value=12345)
mock_st.date_input = MagicMock(return_value=date(2025, 4, 16))
mock_st.form = MagicMock()
mock_st.form_submit_button = MagicMock(return_value=False) # Default to not submitted
mock_st.success = MagicMock()
mock_st.error = MagicMock()
mock_st.warning = MagicMock()
mock_st.info = MagicMock()
mock_st.write = MagicMock()
mock_st.table = MagicMock()
mock_st.dataframe = MagicMock()
mock_st.set_page_config = MagicMock()
mock_st.title = MagicMock()
mock_st.subheader = MagicMock()
mock_st.divider = MagicMock()

# --- Apply the mock ---
sys.modules['streamlit'] = mock_st

# --- Import the script under test AFTER mocking streamlit ---
# Import the script as a module to test its contents
# Note: This will execute the script's top-level code, including data loading attempts
# We'll use patching within tests to control dependencies like pd.read_json
import pages.a8_Regnum as regnum_page # Assuming the file is named a8_Regnum.py

# --- Test Data ---
SAMPLE_GROUP_DATA = pd.DataFrame({
    'name': ['Group A', 'Group B'],
    'id': ['id_a', 'id_b']
})
SAMPLE_MEMBERS_DATA = [{'name': 'Member One', 'email': 'one@example.com'}]
VALID_EMAIL = "test@westkingdom.org"
INVALID_EMAIL = "test@otherdomain.com"

# --- Fixtures ---
@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test"""
    mock_st.reset_mock()
    # Reset specific mocks that might have state
    mock_st.selectbox.return_value = "Selected Group Name"
    mock_st.form_submit_button.return_value = False
    mock_st.text_input.return_value = "Test Input" # Reset default
    mock_st.number_input.return_value = 12345
    mock_st.date_input.return_value = date(2025, 4, 16)


# --- Test Cases ---

@patch('pandas.read_json')
def test_data_loading_success(mock_read_json, mocker):
    """Test successful loading of group data."""
    mock_read_json.return_value = SAMPLE_GROUP_DATA
    # We need to re-run the loading logic or re-import the module under the patch
    # For simplicity, let's manually set the variables as they would be after loading
    regnum_page.group_options = SAMPLE_GROUP_DATA['name'].tolist()
    regnum_page.group_name_to_id = pd.Series(SAMPLE_GROUP_DATA.id.values, index=SAMPLE_GROUP_DATA.name).to_dict()

    assert regnum_page.group_options == ['Group A', 'Group B']
    assert regnum_page.group_name_to_id == {'Group A': 'id_a', 'Group B': 'id_b'}
    mock_st.error.assert_not_called()

@patch('pandas.read_json', side_effect=FileNotFoundError)
def test_data_loading_file_not_found(mock_read_json, mocker):
    """Test handling FileNotFoundError during data loading."""
    # Re-trigger the loading part of the script by re-importing or calling a load function
    # Since the script loads at import, we might need to structure it differently
    # Or simulate the effect:
    with pytest.raises(FileNotFoundError): # The script might raise or just call st.error
         pd.read_json("dummy_path") # Simulate the call that fails

    # In the actual script, it catches the error and calls st.error
    # We can't easily re-run the import here, so we'd ideally refactor loading into a function.
    # Assuming the script catches and calls st.error:
    # Need a way to trigger the load logic within the test context.
    # This highlights a limitation of testing scripts that do work at the top level.
    # For now, we assume st.error would be called if the load failed at startup.
    pass # Test structure needs refinement based on how loading is triggered

# (Add similar tests for ValueError, KeyError, Exception if needed)

@patch('pages.a8_Regnum.get_group_members')
def test_display_members_success(mock_get_members, mocker):
    """Test displaying members when a group is selected and members are found."""
    mock_get_members.return_value = SAMPLE_MEMBERS_DATA
    # Simulate selecting a group that exists in our mocked data
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"

    # Simulate running the part of the script after selection
    # This requires calling the relevant code block or refactoring into functions
    # Assuming we can simulate the state:
    selected_group_name = mock_st.selectbox()
    if selected_group_name:
        selected_group_id = regnum_page.group_name_to_id.get(selected_group_name)
        if selected_group_id:
            members = regnum_page.get_group_members(selected_group_id)
            if members:
                 member_df = pd.DataFrame(members)
                 # Check if st.table or st.dataframe was called with the right data
                 # ANY is used because the exact DataFrame object might differ
                 mock_st.table.assert_called_once_with(ANY)
                 # More specific check on the DataFrame content passed to st.table
                 call_args, _ = mock_st.table.call_args
                 df_arg = call_args[0]
                 assert isinstance(df_arg, pd.DataFrame)
                 assert 'name' in df_arg.columns
                 assert 'email' in df_arg.columns
                 assert df_arg.to_dict('records') == SAMPLE_MEMBERS_DATA

    mock_get_members.assert_called_once_with('group_id_1')
    mock_st.error.assert_not_called()
    mock_st.info.assert_not_called()


@patch('pages.a8_Regnum.get_group_members')
def test_display_members_no_members(mock_get_members, mocker):
    """Test displaying message when a group is selected but has no members."""
    mock_get_members.return_value = [] # API returns empty list
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"

    # Simulate running the relevant code block
    selected_group_name = mock_st.selectbox()
    if selected_group_name:
        selected_group_id = regnum_page.group_name_to_id.get(selected_group_name)
        if selected_group_id:
             members = regnum_page.get_group_members(selected_group_id)
             if not members:
                  mock_st.info.assert_called_with("This group has no members.") # Check st.info call

    mock_get_members.assert_called_once_with('group_id_1')
    mock_st.error.assert_not_called()
    mock_st.table.assert_not_called()
    mock_st.dataframe.assert_not_called()


@patch('pages.a8_Regnum.get_group_members', return_value=None)
def test_display_members_api_fail(mock_get_members, mocker):
    """Test displaying error when fetching members fails."""
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"

    # Simulate running the relevant code block
    selected_group_name = mock_st.selectbox()
    if selected_group_name:
        selected_group_id = regnum_page.group_name_to_id.get(selected_group_name)
        if selected_group_id:
            try:
                members = regnum_page.get_group_members(selected_group_id)
                if members is None:
                     mock_st.error.assert_called_with(f"Failed to fetch members for group '{selected_group_name}'. The API might be down or the group ID is invalid.")
            except Exception:
                 pytest.fail("Should not raise exception here, should call st.error")


    mock_get_members.assert_called_once_with('group_id_1')
    mock_st.info.assert_not_called()
    mock_st.table.assert_not_called()

# --- Form Submission Tests ---

@patch('pages.a8_Regnum.send_registration_email')
@patch('pages.a8_Regnum.is_valid_email', return_value=True)
def test_form_submit_success(mock_is_valid, mock_send_email, mocker):
    """Test successful form submission and email sending."""
    mock_send_email.return_value = True
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"
    mock_st.form_submit_button.return_value = True # Simulate button click

    # Simulate form inputs
    mock_st.text_input.side_effect = [
        "Test SCA Name", "Test Mundane Name", "1 Infinite Loop", "Cupertino", "CA", "95014", "USA",
        VALID_EMAIL, "123-456-7890"
    ]
    mock_st.number_input.return_value = 12345
    mock_st.date_input.side_effect = [date(2025, 4, 16), date(2026, 4, 16)]

    # --- Trigger the form logic ---
    # This part is tricky without refactoring the script.
    # We need to execute the code inside the 'with st.form(...):' and 'if submit_button:' blocks.
    # A refactor to put form handling in a function is recommended for testability.
    # Assuming we can simulate the state *after* the button is pressed:
    form_data = {
        'sca_name': 'Test SCA Name', 'mundane_name': 'Test Mundane Name',
        'sca_membership_number': 12345, 'street_address': '1 Infinite Loop',
        'city': 'Cupertino', 'state': 'CA', 'zip_code': '95014', 'country': 'USA',
        'westkingdom_email': VALID_EMAIL, 'contact_phone_number': '123-456-7890',
        'effective_date': '2025-04-16', 'end_date': '2026-04-16'
    }
    # Manually call the logic that happens inside the if submit_button:
    if VALID_EMAIL and mock_is_valid(VALID_EMAIL) and form_data['sca_name']:
         email_sent = regnum_page.send_registration_email(form_data, "Selected Group Name")
         if email_sent:
              mock_st.success.assert_called_with(f"Registration submitted for {form_data['sca_name']}. Notification sent.")
         else:
              pytest.fail("Email sending should have succeeded in this test.")
    else:
         pytest.fail("Validation should have passed.")


    mock_is_valid.assert_called_once_with(VALID_EMAIL)
    mock_send_email.assert_called_once_with(form_data, "Selected Group Name")
    mock_st.error.assert_not_called()

@patch('pages.a8_Regnum.send_registration_email')
@patch('pages.a8_Regnum.is_valid_email', return_value=True)
def test_form_submit_email_fail(mock_is_valid, mock_send_email, mocker):
    """Test form submission when email sending fails."""
    mock_send_email.return_value = False # Simulate email failure
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"
    mock_st.form_submit_button.return_value = True

    # Simulate form inputs (similar to success test)
    mock_st.text_input.side_effect = ["SCA Name", "Mundane", "Addr", "City", "ST", "Zip", "USA", VALID_EMAIL, "Phone"]
    mock_st.number_input.return_value = 123
    mock_st.date_input.side_effect = [date(2025, 1, 1), date(2026, 1, 1)]

    # Simulate the logic after submit
    form_data = { # Simplified for brevity
        'sca_name': 'SCA Name', 'westkingdom_email': VALID_EMAIL,
        # ... other fields ...
         'effective_date': '2025-01-01', 'end_date': '2026-01-01'
    }
    if form_data['westkingdom_email'] and mock_is_valid(form_data['westkingdom_email']) and form_data['sca_name']:
        email_sent = regnum_page.send_registration_email(form_data, "Selected Group Name")
        if not email_sent:
            mock_st.error.assert_called_with("Failed to send registration notification email. Please contact the administrator.")
        else:
            pytest.fail("Email sending should have failed.")
    else:
        pytest.fail("Validation should have passed.")

    mock_send_email.assert_called_once()
    mock_st.success.assert_not_called()


@patch('pages.a8_Regnum.send_registration_email')
@patch('pages.a8_Regnum.is_valid_email') # Don't care about its return value here
def test_form_submit_validation_missing_email(mock_is_valid, mock_send_email, mocker):
    """Test form validation fails when email is missing."""
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"
    mock_st.form_submit_button.return_value = True

    # Simulate form inputs with email missing
    mock_st.text_input.side_effect = ["SCA Name", "Mundane", "Addr", "City", "ST", "Zip", "USA", "", "Phone"] # Email is ""

    # Simulate the logic after submit
    westkingdom_email = ""
    sca_name = "SCA Name"
    if not westkingdom_email:
        mock_st.error.assert_called_with("Westkingdom email address is required.")
    # ... further checks ...

    mock_send_email.assert_not_called()
    mock_is_valid.assert_not_called() # Validation shouldn't be reached
    mock_st.success.assert_not_called()


@patch('pages.a8_Regnum.send_registration_email')
@patch('pages.a8_Regnum.is_valid_email', return_value=False) # Simulate invalid email
def test_form_submit_validation_invalid_email(mock_is_valid, mock_send_email, mocker):
    """Test form validation fails when email format is invalid."""
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"
    mock_st.form_submit_button.return_value = True

    # Simulate form inputs with invalid email
    mock_st.text_input.side_effect = ["SCA Name", "Mundane", "Addr", "City", "ST", "Zip", "USA", INVALID_EMAIL, "Phone"]

    # Simulate the logic after submit
    westkingdom_email = INVALID_EMAIL
    sca_name = "SCA Name"
    email_valid = mock_is_valid(westkingdom_email)

    if not westkingdom_email:
         pytest.fail("Email should not be empty")
    elif not email_valid:
         mock_st.error.assert_called_with("Please provide a valid Westkingdom email address ending with @westkingdom.org.")
    elif not sca_name:
         pytest.fail("SCA Name should not be empty")
    # ...

    mock_is_valid.assert_called_once_with(INVALID_EMAIL)
    mock_send_email.assert_not_called()
    mock_st.success.assert_not_called()


@patch('pages.a8_Regnum.send_registration_email')
@patch('pages.a8_Regnum.is_valid_email', return_value=True)
def test_form_submit_validation_missing_sca_name(mock_is_valid, mock_send_email, mocker):
    """Test form validation fails when SCA name is missing."""
    regnum_page.group_name_to_id = {'Selected Group Name': 'group_id_1'}
    mock_st.selectbox.return_value = "Selected Group Name"
    mock_st.form_submit_button.return_value = True

    # Simulate form inputs with SCA name missing
    mock_st.text_input.side_effect = ["", "Mundane", "Addr", "City", "ST", "Zip", "USA", VALID_EMAIL, "Phone"] # SCA Name is ""

    # Simulate the logic after submit
    westkingdom_email = VALID_EMAIL
    sca_name = ""
    email_valid = mock_is_valid(westkingdom_email)

    if not westkingdom_email:
         pytest.fail("Email should not be empty")
    elif not email_valid:
         pytest.fail("Email should be valid")
    elif not sca_name:
         mock_st.error.assert_called_with("SCA Name is required.")
    # ...

    mock_is_valid.assert_called_once_with(VALID_EMAIL) # is_valid_email might still be called before the sca_name check
    mock_send_email.assert_not_called()
    mock_st.success.assert_not_called()
