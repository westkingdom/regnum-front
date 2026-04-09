# WKRegnum - West Kingdom Regnum Portal

WKRegnum is a Streamlit-based web application for managing the West Kingdom's officer roster (regnum) and Google Groups. The application serves as a comprehensive portal for officer management, group administration, and duty request processing.

## Core Features

- **Officer Management**: View and manage the current officer roster with search capabilities
- **Group Management**: Manage Google Groups and memberships
- **Email Integration**: Send duty request emails and notifications via Gmail API
- **Authentication**: JWT-based authentication system with role-based access
- **Public Access**: Duty request forms are publicly accessible without authentication
- **Responsive Design**: Works on desktop and mobile devices

## Target Users

- **Administrators**: Full access to all features including officer and group management
- **Officers**: Access to view roster and submit duty requests
- **Public Users**: Can submit duty request forms without authentication

## Architecture

- **Frontend**: Streamlit web application with multi-page structure
- **Backend**: RESTful API for data management
- **Deployment**: Google Cloud Run with Docker containers
- **Authentication**: JWT tokens with bcrypt password hashing
- **Email**: Gmail API with service account impersonation