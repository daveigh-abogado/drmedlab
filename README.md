# DRMed Laboratory Request System

A comprehensive clinic management system for DRMed Clinic and Laboratory, designed to streamline operations for managing patient records, laboratory requests, results, and test components/packages.

## Features

### Implemented Features (as of April 30, 2025)

#### Patient Management
- Patient record creation and management
- Patient search functionality
- Patient record viewing and updating
- Duplicate patient detection

#### Laboratory Request Management
- Creation of laboratory requests
- Selection of test components and packages
- Billing summary generation with PWD/Senior discounts
- Request status tracking

#### Laboratory Results
- Result input interface for technicians
- PDF generation for lab results
- Result status tracking (Not Started, In Progress, Completed)
- Result collection logging

#### Test Component Management
- Test component creation and management
- Result template creation using form builder
- Test package creation and management

#### Laboratory Technician Management
- Lab technician profile management
- Signature image upload and management
- PRC license tracking

### Planned Features (Not Yet Implemented)

- Automated daily backups to secure cloud storage
- Real-time WebSocket notifications for status updates
- Email delivery system for lab results
- Advanced audit logging system
- One-year data archival system
- Enhanced security features for result modifications

## Technology Stack

- **Backend:** Python 3.9+ with Django 4.2.19
- **Frontend:** HTML, Tailwind CSS, JavaScript
- **Database:** MySQL
- **PDF Generation:** pdfkit
- **Development Tools:** django-browser-reload

## Prerequisites

- Python 3.9 or higher
- Node.js and npm
- MySQL Server
- wkhtmltopdf (for PDF generation)
- Git
- GitHub Desktop (recommended)

## Installation

### 1. Repository Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/daveigh-abogado/drmedlab.git
   cd drmedlab
   ```

### 2. Environment Setup

1. Create and activate a virtual environment:

   **macOS/Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   **Windows:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

### 3. Install Dependencies

1. Install Python dependencies:
   ```bash
   # Core Framework
   pip install django==4.2.19
   
   # Database
   pip install mysqlclient
   
   # Frontend & UI
   pip install django-bootstrap-v5
   pip install django-browser-reload
   pip install django-tailwind
   
   # Image Processing & PDF Generation
   pip install Pillow==11.2.1
   pip install pdfkit
   
   # Utilities
   pip install python-dateutil
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

### 4. Database Setup

1. Start MySQL Server:

   **macOS (using Homebrew):**
   ```bash
   brew install mysql
   brew services start mysql
   ```

   **Windows:**
   Ensure MySQL Server is installed and running

2. Create and populate the database:
   ```bash
   # Log into MySQL
   mysql -u root -p
   
   # Create the database
   CREATE DATABASE drmedlabs;
   
   # Exit MySQL shell
   exit;
   
   # Import database structure and data
   mysql -u root -p drmedlabs < sql/create_tables.sql
   mysql -u root -p drmedlabs < sql/populate_tables.sql
   ```

### 5. Django Configuration

1. Create a local settings file:
   ```bash
   cp drmed_labreqsys/settings.py.example drmed_labreqsys/settings.py
   ```

2. Configure your database in `drmed_labreqsys/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'drmedlabs',
           'USER': 'your_mysql_user',
           'PASSWORD': 'your_mysql_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

3. Create required directories:
   ```bash
   # Create directory for lab technician signatures
   mkdir -p labreqsys/static/signatures
   ```

### 6. Tailwind Setup

1. Install Tailwind CSS dependencies:
   ```bash
   python manage.py tailwind install
   ```

2. Start Tailwind CSS compilation:
   ```bash
   python manage.py tailwind start
   ```

### 7. Final Setup

1. Run migrations:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

### 8. Verify Installation

1. Open your browser and navigate to:
   - Main application: http://localhost:8000
   - Admin interface: http://localhost:8000/admin

## Development Tips

1. Always run both servers during development:
   ```bash
   # Terminal 1: Django server
   python manage.py runserver
   
   # Terminal 2: Tailwind compiler
   python manage.py tailwind start
   ```

2. For Windows users, if you encounter npm errors, add this to settings.py:
   ```python
   NPM_BIN_PATH = "C:/Program Files/nodejs/npm.cmd"
   ```

## Installation Verification & Troubleshooting

Use these steps to verify your installation or troubleshoot issues:

### Git & Repository Setup
```bash
# Check Git installation
git version

# Check repository contents
ls

# Check current branch
git branch
```

### Virtual Environment
**macOS/Linux:**
```bash
# Check if virtual environment is active
echo $VIRTUAL_ENV

# Activate if needed
source .venv/bin/activate
```

**Windows:**
```bash
# Check if virtual environment is active
echo %VIRTUAL_ENV%

# Activate if needed
.venv\Scripts\activate
```

### Package Installation Verification
```bash
# Check Django installation
pip show django

# Check Tailwind installation
python -m pip show django-tailwind

# Check Node.js installation
node -v

# Check Browser Reload installation
pip show django_browser_reload
```

### Database Verification
```bash
# Check MySQL service (macOS)
brew services list

# Log into MySQL and check database
mysql -u root -p
SHOW DATABASES;
```

### PDF Generation Setup

1. Install wkhtmltopdf:
   - Download from [wkhtmltopdf downloads](https://wkhtmltopdf.org/downloads.html)
   
   **Windows Setup:**
   - Add to PATH: `C:\Program Files\wkhtmltopdf\bin`
   - Restart your machine
   
   **macOS Setup:**
   ```bash
   brew install homebrew/cask/wkhtmltopdf
   ```

2. Verify installation:
   ```bash
   wkhtmltopdf --version
   ```

3. Install pdfkit:
   ```bash
   pip install pdfkit
   ```

### Common Issues

1. **MySQL Connection Issues**
   - Verify MySQL service is running
   - Check database credentials in settings.py
   - Ensure database exists: `CREATE DATABASE drmedlabs;`

2. **Tailwind Not Compiling**
   - Verify Node.js installation
   - Check NPM_BIN_PATH in settings.py
   - Restart Tailwind compiler

3. **PDF Generation Fails**
   - Verify wkhtmltopdf in system PATH
   - Check wkhtmltopdf installation
   - Restart your terminal/IDE

4. **Missing Static Files**
   - Run `python manage.py collectstatic`
   - Check STATIC_ROOT in settings.py
   - Verify directory permissions

### System Health Check

Run this sequence to verify all components:

1. Check database connection:
   ```bash
   python manage.py dbshell
   ```

2. Verify migrations:
   ```bash
   python manage.py showmigrations
   ```

3. Start required services:
   ```bash
   # Terminal 1: Django server
   python manage.py runserver
   
   # Terminal 2: Tailwind compiler
   python manage.py tailwind start
   ```

4. Visit these URLs:
   - Main app: http://localhost:8000
   - Admin interface: http://localhost:8000/admin
   - Create test lab request to verify PDF generation

## Project Structure

- `labreqsys/` - Main application directory
  - `templates/` - HTML templates
  - `static/` - Static files (CSS, JS, images)
  - `models.py` - Database models
  - `views.py` - View functions
  - `urls.py` - URL routing

- `theme/` - Tailwind CSS theme configuration
  - `static_src/` - Source files for Tailwind CSS
  - `static/css/dist/` - Compiled CSS files

## User Roles

1. **Owner**
   - Manages test components and packages
   - Creates/edits result templates
   - Manages laboratory technicians
   - Full access to patient records

2. **Receptionist**
   - Manages patient records
   - Creates laboratory requests
   - Releases completed lab results
   - Views laboratory request records

3. **Laboratory Technician**
   - Inputs and edits lab results
   - Reviews and approves results
   - Views laboratory request records

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

ISC License

## Support

For support, please open an issue in the GitHub repository or contact the development team. 