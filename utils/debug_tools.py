"""
Debugging tools for the WKRegnum application.

This module provides utility functions for debugging and testing 
different aspects of the application.
"""

import os
import streamlit as st
import json
import inspect
from typing import Dict, Any, Optional, List

def debug_info(show_env: bool = False) -> Dict[str, Any]:
    """
    Gather debug information about the current environment.
    
    Args:
        show_env: Whether to include environment variables in the output.
                 Defaults to False for security reasons.
    
    Returns:
        A dictionary containing debug information.
    """
    info = {
        "streamlit_version": st.__version__,
        "python_path": os.environ.get("PYTHONPATH", "Not set"),
        "working_directory": os.getcwd(),
        "debug_settings": {
            "USE_MOCK_DATA": os.environ.get("USE_MOCK_DATA"),
            "MOCK_API_ERRORS": os.environ.get("MOCK_API_ERRORS"),
            "BYPASS_GROUP_CHECK": os.environ.get("BYPASS_GROUP_CHECK"),
            "STREAMLIT_LOG_LEVEL": os.environ.get("STREAMLIT_LOG_LEVEL"),
        }
    }
    
    if show_env:
        info["environment"] = {k: v for k, v in os.environ.items()}
    
    return info

def debug_panel():
    """
    Display a debug panel in Streamlit with useful information.
    """
    with st.expander("Debug Information", expanded=False):
        st.write("### Application Debug Info")
        
        info = debug_info(show_env=False)
        
        st.json(info)
        
        if st.button("Show Environment Variables"):
            st.warning("Showing environment variables may expose sensitive information!")
            env_info = {k: v for k, v in os.environ.items()}
            st.json(env_info)
        
        st.write("### Session State")
        st.json({k: str(v) for k, v in st.session_state.items()})
        
        st.write("### Authentication Status")
        if "authenticated" in st.session_state:
            st.success(f"Authentication status: {st.session_state.authenticated}")
            if "user_email" in st.session_state:
                st.info(f"User email: {st.session_state.user_email}")
        else:
            st.error("Not authenticated")

def trace_function(func):
    """
    Decorator to trace function calls with their arguments and return values.
    
    Args:
        func: The function to trace.
        
    Returns:
        The wrapped function with tracing.
    """
    def wrapper(*args, **kwargs):
        arg_names = inspect.getfullargspec(func).args
        arg_dict = dict(zip(arg_names, args))
        arg_dict.update(kwargs)
        
        print(f"TRACE: Calling {func.__name__}()")
        print(f"TRACE: Arguments: {json.dumps(arg_dict, default=str)}")
        
        result = func(*args, **kwargs)
        
        print(f"TRACE: {func.__name__}() returned: {json.dumps(result, default=str)}")
        return result
    
    return wrapper

def mock_group_member(email: str, role: str = "MEMBER") -> Dict[str, str]:
    """
    Create a mock group member entry for testing.
    
    Args:
        email: The email address for the mock member.
        role: The role of the member. Defaults to "MEMBER".
        
    Returns:
        A dictionary representing a group member.
    """
    return {
        "email": email,
        "role": role,
        "status": "ACTIVE",
        "type": "USER"
    }

def create_mock_group_data(group_id: str, 
                          members: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Create mock group data for testing.
    
    Args:
        group_id: The ID of the group.
        members: Optional list of member dictionaries. If None, default members are used.
        
    Returns:
        A dictionary containing mock group data.
    """
    if members is None:
        members = [
            mock_group_member("admin@westkingdom.org", "OWNER"),
            mock_group_member("member1@westkingdom.org"),
            mock_group_member("member2@westkingdom.org")
        ]
    
    return {
        "id": group_id,
        "name": f"Group {group_id}",
        "members": members
    } 