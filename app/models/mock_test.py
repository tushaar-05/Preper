from app.extensions import db
from datetime import datetime
import json


class MockTest(db.Model):
    __tablename__ = 'mock_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id')) # NULL means all batches
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    batch = db.relationship('Batch', backref=db.backref('mock_tests', lazy='dynamic'))
    # Test Configuration
    duration_minutes = db.Column(db.Integer, nullable=False, default=60)
    total_marks = db.Column(db.Integer, nullable=False, default=100)
    passing_marks = db.Column(db.Integer, nullable=False, default=40)
    
    # Difficulty & Category
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    category = db.Column(db.String(50))  # Mathematics, English, Reasoning, etc.
    
    # Availability
    is_active = db.Column(db.Boolean, default=True)
    is_free = db.Column(db.Boolean, default=False)
    is_anytime = db.Column(db.Boolean, default=False)
    
    # Schedule
    available_from = db.Column(db.DateTime)
    available_until = db.Column(db.DateTime)
    
    # Sections (stored as JSON array of strings)
    sections_json = db.Column(db.Text)  # e.g., ["Physics", "Chemistry", "Maths"]
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='mock_test', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('TestAttempt', backref='mock_test', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def total_questions(self):
        """Get total number of questions"""
        return self.questions.count()

    @property
    def sections(self):
        """Get sections as a Python list"""
        if self.sections_json:
            try:
                return json.loads(self.sections_json)
            except:
                return []
        return []
    
    @sections.setter
    def sections(self, sections_list):
        """Set sections from a Python list"""
        self.sections_json = json.dumps(sections_list)
    
    __table_args__ = (
        db.Index('idx_mocktest_batch_active', 'batch_id', 'is_active'),
        db.Index('idx_mocktest_free_active', 'is_free', 'is_active'),
    )

    def __repr__(self):
        return f'<MockTest {self.title}>'


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    mock_test_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id'), nullable=False)
    
    # Question Details
    section = db.Column(db.String(50))  # Physics, Chemistry, etc.
    question_text = db.Column(db.Text, nullable=False)
    question_image_url = db.Column(db.Text)
    question_type = db.Column(db.String(20), default='mcq')  # mcq, true_false, numerical
    
    # Options (stored as JSON for MCQ)
    # [{"text": "Option 1", "image": "url"}, ...]
    options_json = db.Column(db.Text)
    correct_answer = db.Column(db.String(500), nullable=False)
    
    # Marks
    marks = db.Column(db.Integer, default=1)
    negative_marks = db.Column(db.Float, default=0.0)
    
    # Explanation
    explanation = db.Column(db.Text)
    explanation_image_url = db.Column(db.Text)
    
    # Order
    question_number = db.Column(db.Integer)
    
    @property
    def options(self):
        """Get options as a Python list"""
        if self.options_json:
            try:
                return json.loads(self.options_json)
            except:
                return []
        return []
    
    @options.setter
    def options(self, options_list):
        """Set options from a Python list"""
        self.options_json = json.dumps(options_list)
    
    def to_dict(self):
        """Convert question to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'mock_test_id': self.mock_test_id,
            'section': self.section,
            'question_text': self.question_text,
            'question_image_url': self.question_image_url,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'explanation_image_url': self.explanation_image_url,
            'explanation_image_url': self.explanation_image_url,
            'question_number': self.question_number,
            'marks': self.marks
        }
    
    def __repr__(self):
        return f'<Question {self.id} - Test:{self.mock_test_id}>'


class TestAttempt(db.Model):
    __tablename__ = 'test_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    mock_test_id = db.Column(db.Integer, db.ForeignKey('mock_tests.id'), nullable=False)
    
    # Attempt Details
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    
    # Results
    score = db.Column(db.Float, default=0.0)
    total_marks = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed, abandoned
    
    # Answers (stored as JSON)
    answers_json = db.Column(db.Text)  # JSON: {question_id: answer, ...}
    
    # Analytics
    time_taken_minutes = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)
    unanswered = db.Column(db.Integer, default=0)
    
    @property
    def answers(self):
        """Get answers as a Python dict"""
        if self.answers_json:
            return json.loads(self.answers_json)
        return {}
    
    @answers.setter
    def answers(self, answers_dict):
        """Set answers from a Python dict"""
        self.answers_json = json.dumps(answers_dict)
    
    @property
    def is_passed(self):
        """Check if student passed the test"""
        if self.mock_test and self.percentage:
            passing_percentage = (self.mock_test.passing_marks / self.mock_test.total_marks) * 100
            return self.percentage >= passing_percentage
        return False
    
    __table_args__ = (
        db.Index('idx_attempt_student_test', 'student_id', 'mock_test_id', 'status'),
    )

    def __repr__(self):
        return f'<TestAttempt Student:{self.student_id} Test:{self.mock_test_id}>'
