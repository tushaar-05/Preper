# NST Prep Database Schema

## Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o| STUDENTS : "has profile"
    USERS ||--o{ ANNOUNCEMENTS : "creates"
    USERS ||--o{ RESOURCES : "uploads"
    
    STUDENTS ||--o{ ENROLLMENTS : "enrolls in"
    STUDENTS ||--o{ INTERVIEWS : "schedules"
    STUDENTS ||--o{ TEST_ATTEMPTS : "attempts"
    STUDENTS ||--o{ PAYMENTS : "makes"
    
    BATCHES ||--o{ ENROLLMENTS : "has students"
    BATCHES ||--o{ ANNOUNCEMENTS : "targets"
    BATCHES ||--o{ RESOURCES : "restricts to"
    
    ENROLLMENTS ||--o{ PAYMENTS : "receives"
    
    MOCK_TESTS ||--o{ QUESTIONS : "contains"
    MOCK_TESTS ||--o{ TEST_ATTEMPTS : "taken as"
    
    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role
        boolean is_active
        boolean is_verified
        datetime created_at
        datetime last_login
    }
    
    STUDENTS {
        int id PK
        int user_id FK
        string full_name
        string phone UK
        date date_of_birth
        string gender
        text address
        string city
        string state
        string pincode
        string education_level
        string institution_name
        date target_exam_date
        string preferred_batch
        string enrollment_status
        datetime created_at
        datetime updated_at
    }
    
    BATCHES {
        int id PK
        string name UK
        text description
        float original_price
        float discounted_price
        boolean gst_included
        int max_students
        int current_enrollment
        date start_date
        date end_date
        string status
        text features_json
        string color
        datetime created_at
        datetime updated_at
    }
    
    ENROLLMENTS {
        int id PK
        int student_id FK
        int batch_id FK
        datetime enrollment_date
        string payment_status
        float amount_paid
        float total_amount
        float completion_percentage
        boolean is_active
        datetime completed_at
        datetime updated_at
    }
    
    INTERVIEWS {
        int id PK
        int student_id FK
        string interview_type
        string title
        text description
        datetime scheduled_date
        int duration_minutes
        string interviewer_name
        string interviewer_email
        string status
        text feedback
        int rating
        string meeting_link
        string meeting_platform
        datetime created_at
        datetime updated_at
        datetime completed_at
    }
    
    MOCK_TESTS {
        int id PK
        string title
        text description
        int duration_minutes
        int total_marks
        int passing_marks
        string difficulty_level
        string category
        boolean is_active
        boolean is_free
        datetime available_from
        datetime available_until
        datetime created_at
        datetime updated_at
    }
    
    QUESTIONS {
        int id PK
        int mock_test_id FK
        text question_text
        string question_type
        text options_json
        string correct_answer
        int marks
        float negative_marks
        text explanation
        int question_number
    }
    
    TEST_ATTEMPTS {
        int id PK
        int student_id FK
        int mock_test_id FK
        datetime started_at
        datetime submitted_at
        float score
        int total_marks
        float percentage
        string status
        text answers_json
        int time_taken_minutes
        int correct_answers
        int wrong_answers
        int unanswered
    }
    
    ANNOUNCEMENTS {
        int id PK
        int created_by FK
        string title
        text content
        string priority
        string target_audience
        int target_batch_id FK
        boolean is_pinned
        boolean is_published
        datetime published_at
        datetime expires_at
        datetime created_at
        datetime updated_at
    }
    
    RESOURCES {
        int id PK
        int uploaded_by FK
        string title
        text description
        string category
        string resource_type
        string file_path
        string file_url
        int file_size
        string file_type
        string access_level
        int target_batch_id FK
        string subject
        string topic
        boolean is_active
        int download_count
        int view_count
        datetime created_at
        datetime updated_at
    }
    
    PAYMENTS {
        int id PK
        int student_id FK
        int enrollment_id FK
        float amount
        string currency
        string payment_method
        string transaction_id UK
        string order_id
        string gateway
        text gateway_response
        string status
        string description
        string receipt_url
        float refund_amount
        text refund_reason
        datetime refunded_at
        datetime created_at
        datetime updated_at
        datetime completed_at
    }
```

## Table Descriptions

### Core Tables

#### users
User accounts with authentication and role-based access control.
- **Primary Key**: id
- **Unique Keys**: username, email
- **Relationships**: One-to-one with students, one-to-many with announcements and resources

#### students
Student profiles with personal and academic information.
- **Primary Key**: id
- **Foreign Keys**: user_id → users.id
- **Unique Keys**: phone
- **Relationships**: One-to-many with enrollments, interviews, test_attempts, payments

#### batches
Course batches with pricing, capacity, and scheduling.
- **Primary Key**: id
- **Unique Keys**: name
- **JSON Fields**: features_json (array of batch features)
- **Relationships**: One-to-many with enrollments, announcements, resources

#### enrollments
Links students to batches with payment and progress tracking.
- **Primary Key**: id
- **Foreign Keys**: student_id → students.id, batch_id → batches.id
- **Unique Constraint**: (student_id, batch_id)
- **Relationships**: One-to-many with payments

### Assessment Tables

#### mock_tests
Mock test configuration and metadata.
- **Primary Key**: id
- **Relationships**: One-to-many with questions and test_attempts

#### questions
Test questions with options and answers.
- **Primary Key**: id
- **Foreign Keys**: mock_test_id → mock_tests.id
- **JSON Fields**: options_json (array of answer options)

#### test_attempts
Student test attempts with scores and analytics.
- **Primary Key**: id
- **Foreign Keys**: student_id → students.id, mock_test_id → mock_tests.id
- **JSON Fields**: answers_json (dictionary of question_id: answer)

#### interviews
Interview scheduling and feedback.
- **Primary Key**: id
- **Foreign Keys**: student_id → students.id

### Content Tables

#### announcements
System announcements with targeting and scheduling.
- **Primary Key**: id
- **Foreign Keys**: created_by → users.id, target_batch_id → batches.id (optional)

#### resources
Study materials and resources with access control.
- **Primary Key**: id
- **Foreign Keys**: uploaded_by → users.id, target_batch_id → batches.id (optional)

### Financial Tables

#### payments
Payment transactions with gateway integration.
- **Primary Key**: id
- **Foreign Keys**: student_id → students.id, enrollment_id → enrollments.id
- **Unique Keys**: transaction_id

## Indexes

The following indexes are automatically created:
- Primary keys on all tables
- Unique indexes on username, email (users)
- Unique index on phone (students)
- Unique index on name (batches)
- Unique index on transaction_id (payments)
- Composite unique index on (student_id, batch_id) (enrollments)
- Foreign key indexes on all FK columns

## Data Types

- **int**: Integer (auto-incrementing for PKs)
- **string**: VARCHAR with specified length
- **text**: TEXT for long content
- **float**: FLOAT for decimal numbers
- **boolean**: BOOLEAN (TINYINT in MySQL)
- **date**: DATE
- **datetime**: DATETIME

## Cascade Rules

All foreign key relationships use `cascade='all, delete-orphan'` to ensure:
- When a parent record is deleted, all child records are automatically deleted
- Orphaned records (children without parents) are automatically cleaned up
