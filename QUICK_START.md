# NST Prep - Quick Start Guide

## 🚀 Quick Setup (3 Steps)

### 1. Start XAMPP
```bash
# Open XAMPP Control Panel and start:
- MySQL ✓
```

### 2. Create Database & Tables
```bash
cd /Users/tushar/Desktop/NSTPrep
python3 create_db.py
python3 init_db.py
```

### 3. Run Application
```bash
python3 run.py
```

Visit: `http://127.0.0.1:5000`

## 🔑 Login Credentials

**Admin**
- Username: `admin`
- Password: `admin123`

**Student**
- Username: `rahul_sharma`
- Password: `password123`

## 📊 Database Info

- **Database**: `nst_prep_db`
- **Tables**: 11 tables
- **Connection**: `mysql+pymysql://root@localhost/nst_prep_db`

## 🗂️ Tables Created

1. ✅ users - User accounts
2. ✅ students - Student profiles
3. ✅ batches - Course batches
4. ✅ enrollments - Student enrollments
5. ✅ interviews - Interview scheduling
6. ✅ mock_tests - Mock tests
7. ✅ questions - Test questions
8. ✅ test_attempts - Test attempts
9. ✅ announcements - Announcements
10. ✅ resources - Study resources
11. ✅ payments - Payment records

## 📁 Important Files

| File | Purpose |
|------|---------|
| `config.py` | Database configuration |
| `run.py` | Application entry point |
| `create_db.py` | Create database |
| `init_db.py` | Initialize tables & data |
| `app/models/*.py` | Database models |
| `DATABASE_SETUP.md` | Full setup guide |
| `DATABASE_SCHEMA.md` | Schema documentation |

## 🔧 Common Commands

### Reset Database
```bash
python3 init_db.py  # Drops and recreates all tables
```

### Access MySQL
```bash
# Via phpMyAdmin
http://localhost/phpmyadmin

# Via command line
mysql -u root -p
USE nst_prep_db;
SHOW TABLES;
```

### Check Tables
```sql
-- View all tables
SHOW TABLES;

-- View table structure
DESCRIBE users;

-- Count records
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM batches;
SELECT COUNT(*) FROM students;
```

## 🎯 Sample Data Included

- **3 Users**: 1 admin + 2 students
- **3 Batches**: Foundation, Advanced, Crash Course
- **2 Enrollments**: Students enrolled in batches
- **1 Mock Test**: Mathematics test with 2 questions
- **1 Interview**: Scheduled interview
- **2 Announcements**: Welcome + New test announcement
- **2 Resources**: Math notes + English videos
- **1 Payment**: Completed payment record

## 🔍 Verify Setup

```bash
# Test database connection
python3 -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); print('✅ Database connected!')"

# Check table count
python3 -c "from app import create_app; from app.extensions import db; from app.models import User, Student, Batch; app = create_app(); app.app_context().push(); print(f'Users: {User.query.count()}'); print(f'Students: {Student.query.count()}'); print(f'Batches: {Batch.query.count()}')"
```

## ⚠️ Troubleshooting

**MySQL not connecting?**
- Check XAMPP MySQL is running
- Verify port 3306 is not blocked
- Check credentials in `config.py`

**Tables not created?**
- Run `python3 create_db.py` first
- Then run `python3 init_db.py`
- Check for error messages

**Import errors?**
```bash
pip3 install -r requirements.txt
```

## 📚 Next Steps

1. ✅ Database setup complete
2. 🔄 Create API routes for CRUD operations
3. 🔄 Build admin dashboard functionality
4. 🔄 Implement authentication flow
5. 🔄 Connect frontend templates to backend

## 📖 Documentation

- **Setup Guide**: [DATABASE_SETUP.md](file:///Users/tushar/Desktop/NSTPrep/DATABASE_SETUP.md)
- **Schema Docs**: [DATABASE_SCHEMA.md](file:///Users/tushar/Desktop/NSTPrep/DATABASE_SCHEMA.md)
- **Walkthrough**: See artifacts folder

---

**Need Help?** Check the full documentation in `DATABASE_SETUP.md`
