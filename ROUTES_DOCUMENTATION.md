# NST Prep - Routes Documentation

## Overview

All HTML templates are now connected to the Flask backend with MySQL database integration. The application uses Flask blueprints for organized routing and Flask-Login for authentication.

## Blueprints

| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| `main` | `/` | Public pages |
| `auth` | `/` | Authentication |
| `admin` | `/admin` | Admin dashboard |
| `user` | `/` | Student dashboard |
| `payments` | `/payment` | Payment processing |

## Public Routes (main)

### GET /
- **Template**: `index.html`
- **Purpose**: Landing page
- **Auth**: Not required

## Authentication Routes (auth)

### GET/POST /login
- **Template**: `login.html`
- **Purpose**: Student login
- **Database**: Queries `User` table
- **Features**:
  - Email/password authentication
  - Password hashing verification
  - Remember me functionality
  - Last login tracking
  - Redirects to student dashboard on success

### GET/POST /register
- **Template**: `register.html`
- **Purpose**: New student registration
- **Database**: Creates `User` and `Student` records
- **Features**:
  - Form validation
  - Duplicate email/username check
  - Password hashing
  - Automatic student profile creation

### GET/POST /admin/login
- **Template**: `admin_login.html`
- **Purpose**: Admin login
- **Database**: Queries `User` table (role='admin')
- **Features**:
  - Admin-only access
  - Redirects to admin dashboard on success

### GET /logout
- **Purpose**: Logout current user
- **Features**:
  - Clears session
  - Redirects to landing page

## Admin Routes (admin)

All admin routes require `@admin_required` decorator.

### GET /admin/dashboard
- **Template**: `dashboard/admin/admin.html`
- **Database Queries**:
  - Total students count
  - Active batches count
  - Total enrollments
  - Total revenue (sum of completed payments)
  - Recent enrollments (last 5)
  - Upcoming interviews (next 5)
- **Features**: Dashboard with statistics and recent activity

### GET /admin/students
- **Template**: `dashboard/admin/students.html`
- **Database Queries**:
  - All students with user info
  - Student enrollments and batches
- **Features**: List all students with enrollment status

### GET /admin/batches
- **Template**: `dashboard/admin/batches.html`
- **Database Queries**:
  - All batches with enrollment counts
- **Features**:
  - Batch details (name, pricing, capacity)
  - Enrollment progress
  - Status indicators

### GET /admin/interviews
- **Template**: `dashboard/admin/interviews.html`
- **Database Queries**:
  - All interviews with student info
- **Features**:
  - Interview schedule
  - Student names
  - Status tracking

### GET /admin/mocks
- **Template**: `dashboard/admin/mocks.html`
- **Database Queries**:
  - All mock tests
  - Attempt statistics
  - Average scores
- **Features**:
  - Test management
  - Performance analytics

### GET /admin/announcements
- **Template**: `dashboard/admin/announcements.html`
- **Database Queries**:
  - All announcements
- **Features**:
  - Announcement list
  - Priority levels
  - Target audience

### GET /admin/resources
- **Template**: `dashboard/admin/resources.html`
- **Database Queries**:
  - All resources
- **Features**:
  - Resource management
  - Download tracking
  - Category organization

### GET /admin/settings
- **Template**: `dashboard/admin/settings.html`
- **Features**: Platform settings (placeholder)

## Student Routes (user)

All student routes require `@student_required` decorator.

### GET /me or /dashboard
- **Template**: `dashboard/user/user.html`
- **Database Queries**:
  - Student enrollments with batch info
  - Upcoming interviews (next 3)
  - Recent announcements (last 5, filtered by batch)
  - Available mock tests (next 3)
- **Features**: Student dashboard with personalized content

### GET/POST /profile
- **Template**: `dashboard/user/profile.html`
- **Database Queries**:
  - Current student profile
- **Features**:
  - View profile
  - Update profile information
  - Update email

### GET /announcement
- **Template**: `dashboard/user/announcement.html`
- **Database Queries**:
  - Announcements filtered by:
    - Target audience (all/students)
    - Student's enrolled batches
  - Ordered by pinned status and date
- **Features**:
  - View all relevant announcements
  - Pinned announcements at top

### GET /interview
- **Template**: `dashboard/user/interview.html`
- **Database Queries**:
  - Upcoming interviews (future dates)
  - Past interviews (completed/past dates)
- **Features**:
  - Interview schedule
  - Meeting links
  - Past interview history

### GET /mock
- **Template**: `dashboard/user/mock.html`
- **Database Queries**:
  - All active mock tests
  - Student's test attempts
- **Features**:
  - Available tests
  - Test status (upcoming/live/ended)
  - Attempt history with scores

### GET /prepkit
- **Template**: `dashboard/user/prepkit.html`
- **Database Queries**:
  - Resources filtered by:
    - Access level (free or student's batches)
    - Active status
  - Grouped by category
- **Features**:
  - Study materials
  - Download links
  - Category organization

### GET /doubts
- **Template**: `dashboard/user/doubts.html`
- **Features**: Doubt forum (placeholder with sample data)

## Payment Routes (payments)

All payment routes require `@student_required` decorator.

### GET /payment or /payment/history
- **Template**: `dashboard/user/payment.html`
- **Database Queries**:
  - Student's active enrollment
  - All payment transactions
- **Features**:
  - Subscription status
  - Payment history
  - Transaction details

### GET /payment/pending
- **Template**: `dashboard/user/payment-pending.html`
- **Database Queries**:
  - Available batches (active/upcoming, not full)
  - Student's current enrollments
- **Features**:
  - Available batches for enrollment
  - Pricing information
  - Enrollment button

### POST /payment/initiate
- **Purpose**: Start payment process
- **Database Operations**:
  - Create `Enrollment` record (status='pending')
  - Create `Payment` record (status='pending')
  - Generate transaction ID and order ID
- **Returns**: JSON with order details

### GET /payment/callback
- **Purpose**: Handle payment gateway callback
- **Database Operations**:
  - Update `Payment` status to 'completed'
  - Update `Enrollment` payment_status to 'completed'
  - Update `Batch` current_enrollment count
  - Update `Student` enrollment_status to 'active'
- **Features**: Simulated payment completion

### GET /payment/verify/<order_id>
- **Purpose**: Verify payment status
- **Returns**: JSON with payment details

## Database Integration Details

### Authentication Flow
1. User enters credentials
2. Query `User` table by email
3. Verify password hash
4. Check user role and status
5. Update last_login timestamp
6. Create session with Flask-Login
7. Redirect based on role

### Student Dashboard Data Flow
1. Get current user from session
2. Query `Student` by user_id
3. Get enrollments with JOIN to `Batch`
4. Get interviews filtered by student_id
5. Get announcements filtered by batch and audience
6. Get mock tests with attempt status
7. Render template with all data

### Admin Dashboard Data Flow
1. Verify admin role
2. Query aggregated statistics
3. Get recent records with JOINs
4. Format data for display
5. Render template

### Payment Flow
1. Student selects batch
2. Create pending enrollment
3. Create pending payment
4. Generate transaction IDs
5. (Simulate) Payment gateway
6. Update all related records
7. Increment batch enrollment
8. Redirect to dashboard

## Helper Functions

### Decorators
- `@admin_required` - Restrict to admin users
- `@student_required` - Restrict to student users
- `@enrollment_required` - Require active enrollment

### Utilities
- `get_current_student()` - Get logged-in student profile
- `format_currency(amount)` - Format currency display
- `get_user_batches(student_id)` - Get student's batches
- `get_user_batch_ids(student_id)` - Get batch IDs
- `get_*_status_color(status)` - Get Tailwind CSS classes

## Security Features

1. **Authentication**
   - Password hashing with Werkzeug
   - Session management with Flask-Login
   - Remember me functionality

2. **Authorization**
   - Role-based access control
   - Route protection with decorators
   - User can only access own data

3. **Input Validation**
   - Form validation
   - Email uniqueness check
   - Password strength requirements

4. **Database Security**
   - SQLAlchemy ORM (prevents SQL injection)
   - Parameterized queries
   - Transaction rollback on errors

## Template Variables

### Common Variables (All Templates)
- `current_user` - Logged-in user object
- Flash messages (success, danger, warning, info)

### Admin Templates
- `stats` - Dashboard statistics
- `students` - List of students
- `batches` - List of batches
- `interviews` - List of interviews
- `mocks` - List of mock tests
- `announcements` - List of announcements
- `resources` - List of resources

### Student Templates
- `student` - Current student profile
- `enrollments` - Student's enrollments
- `upcoming_interviews` - Future interviews
- `announcements` - Filtered announcements
- `tests` - Available mock tests
- `resources` - Accessible resources (grouped by category)
- `subscription` - Payment subscription info
- `transactions` - Payment history

## Next Steps

### Immediate Enhancements
1. Add CRUD operations for admin (create/edit/delete)
2. Implement mock test attempt functionality
3. Add interview booking system
4. Integrate real payment gateway (Razorpay/Stripe)

### Future Features
1. Email notifications
2. File upload for resources
3. Real-time doubt forum
4. Performance analytics
5. Certificate generation
6. Batch-wise leaderboards

## Testing

### Test Admin Access
```bash
# Login as admin
Email: admin@nstprep.com
Password: admin123

# Access admin routes
/admin/dashboard
/admin/students
/admin/batches
```

### Test Student Access
```bash
# Login as student
Email: rahul@example.com
Password: password123

# Access student routes
/me
/profile
/announcement
/interview
/mock
/prepkit
```

### Test Authentication
- Try accessing protected routes without login → Redirects to login
- Try accessing admin routes as student → 403 Forbidden
- Try accessing student routes as admin → 403 Forbidden

## Troubleshooting

### Import Errors
```bash
# Make sure all dependencies are installed
pip3 install -r requirements.txt
```

### Database Errors
```bash
# Reinitialize database if needed
python3 init_db.py
```

### Template Not Found
- Check template path matches route
- Ensure template file exists in correct directory

### 404 Errors
- Check blueprint is registered in app/__init__.py
- Verify route decorator syntax
- Check URL prefix for blueprint
