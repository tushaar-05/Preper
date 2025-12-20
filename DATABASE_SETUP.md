# NST Prep - Database Setup Guide

## Overview

This Flask application uses MySQL database for the NST (Navy Service Test) Preparation platform. The database includes comprehensive tables for managing students, batches, enrollments, interviews, mock tests, announcements, resources, and payments.

## Database Schema

### Tables Created

1. **users** - User accounts (admin and students) with authentication
2. **students** - Student profiles with personal and academic information
3. **batches** - Course batches with pricing and capacity management
4. **enrollments** - Student enrollment in batches with payment tracking
5. **interviews** - Interview scheduling and feedback
6. **mock_tests** - Mock test configuration
7. **questions** - Test questions with options and answers
8. **test_attempts** - Student test attempts and results
9. **announcements** - System announcements with targeting
10. **resources** - Study materials and resources
11. **payments** - Payment transactions and records

## Prerequisites

1. **XAMPP** - Make sure XAMPP is installed and running
2. **Python 3.8+** - Python environment
3. **MySQL** - Running via XAMPP

## Setup Instructions

### Step 1: Start XAMPP

1. Open XAMPP Control Panel
2. Start **Apache** (for web server)
3. Start **MySQL** (for database)
4. Verify MySQL is running on port 3306

### Step 2: Install Python Dependencies

```bash
cd /Users/tushar/Desktop/NSTPrep
pip3 install -r requirements.txt
```

### Step 3: Create Database

Run the database creation script:

```bash
python3 create_db.py
```

This will:
- Connect to your XAMPP MySQL server
- Create the `nst_prep_db` database
- Verify the database was created successfully

### Step 4: Initialize Database Tables

Run the initialization script to create all tables and seed sample data:

```bash
python3 init_db.py
```

This will:
- Create all database tables
- Seed sample data including:
  - Admin user
  - Sample students
  - Sample batches
  - Sample enrollments
  - Sample mock tests
  - Sample announcements
  - Sample resources

### Step 5: Run the Application

```bash
python3 run.py
```

The application will start on `http://127.0.0.1:5000`

## Default Credentials

### Admin Account
- **Username:** admin
- **Email:** admin@nstprep.com
- **Password:** admin123

### Sample Student Account
- **Username:** rahul_sharma
- **Email:** rahul@example.com
- **Password:** password123

## Database Configuration

The database configuration is in `config.py`:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root@localhost/nst_prep_db'
```

**XAMPP Default Settings:**
- Host: `localhost`
- User: `root`
- Password: `` (empty)
- Database: `nst_prep_db`

If you have a different MySQL configuration, update the connection string in `config.py`.

## Database Models

### User Model
- Authentication with password hashing
- Role-based access (admin/student)
- Email verification support

### Student Model
- Personal information (name, phone, address)
- Academic details
- Enrollment status tracking

### Batch Model
- Batch name and description
- Pricing with discounts
- Capacity management
- Features stored as JSON
- Status tracking (upcoming, active, completed)

### Enrollment Model
- Links students to batches
- Payment status tracking
- Progress monitoring

### Interview Model
- Interview scheduling
- Interviewer details
- Feedback and ratings
- Meeting platform integration

### MockTest Model
- Test configuration (duration, marks)
- Difficulty levels
- Category-based organization

### Question Model
- Multiple choice questions
- Options stored as JSON
- Marks and negative marking

### TestAttempt Model
- Student test attempts
- Score calculation
- Answer tracking
- Performance analytics

### Announcement Model
- Priority levels
- Target audience selection
- Pinned announcements
- Expiry dates

### Resource Model
- File uploads and URLs
- Access control (free/paid/batch-specific)
- Download and view tracking

### Payment Model
- Transaction tracking
- Multiple payment methods
- Gateway integration support
- Refund management

## Troubleshooting

### MySQL Connection Error

If you get a connection error:

1. **Check XAMPP MySQL is running:**
   - Open XAMPP Control Panel
   - Ensure MySQL shows "Running" status

2. **Verify MySQL port:**
   - Default port is 3306
   - Check if another service is using this port

3. **Check MySQL credentials:**
   - XAMPP default: username=`root`, password=`` (empty)
   - Update `config.py` if you have different credentials

### Database Already Exists

If the database already exists and you want to recreate it:

```bash
# This will drop all tables and recreate them
python3 init_db.py
```

### Import Errors

If you get import errors:

```bash
# Reinstall dependencies
pip3 install -r requirements.txt --force-reinstall
```

## Database Migrations

To create new migrations after modifying models:

```bash
# Initialize migrations (only once)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade
```

## Accessing MySQL Database

### Via phpMyAdmin (Recommended)

1. Start XAMPP Apache and MySQL
2. Open browser: `http://localhost/phpmyadmin`
3. Select `nst_prep_db` database
4. View and manage tables

### Via MySQL Command Line

```bash
# Connect to MySQL
mysql -u root -p

# Use the database
USE nst_prep_db;

# Show all tables
SHOW TABLES;

# View table structure
DESCRIBE users;

# Query data
SELECT * FROM users;
```

## Sample Data

The initialization script creates:
- 3 users (1 admin, 2 students)
- 2 student profiles
- 3 batches (active, upcoming, crash course)
- 2 enrollments
- 1 mock test with 2 questions
- 1 scheduled interview
- 2 announcements
- 2 resources
- 1 completed payment

## Next Steps

1. ✅ Database and tables created
2. ✅ Sample data seeded
3. 🔄 Create routes for CRUD operations
4. 🔄 Build admin dashboard functionality
5. 🔄 Implement student dashboard
6. 🔄 Add authentication and authorization
7. 🔄 Integrate payment gateway

## Support

For issues or questions:
- Check XAMPP logs: `xampp/mysql/data/mysql_error.log`
- Check Flask logs in terminal
- Verify database connection in phpMyAdmin

---

**Note:** This is a development setup. For production, use proper environment variables, secure passwords, and a production-grade database server.
