import sys
import os
import pymysql

try:
    conn = pymysql.connect(host='localhost', user='root', password='', database='nst_prep_db')
    cursor = conn.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DELETE FROM test_attempts")
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM mock_tests")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    from datetime import datetime, timedelta
    now = datetime.now()
    available_from = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    available_until = (now + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

    sql = """INSERT INTO mock_tests (title, category, duration_minutes, total_marks, passing_marks, is_active, is_free, available_from, available_until, sections_json, created_at, updated_at) 
             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"""
    cursor.execute(sql, ("Diagnostic Quiz 2024", "General Aptitude", 30, 10, 4, 1, 1, available_from, available_until, '["Logical Reasoning", "Quantitative Aptitude"]'))
    mock_id = cursor.lastrowid

    sql_q = """INSERT INTO questions (mock_test_id, section, question_text, correct_answer, marks, question_number, options_json, question_type) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    
    q1_opts = '[{"text": "3", "image": null}, {"text": "4", "image": null}, {"text": "5", "image": null}, {"text": "6", "image": null}]'
    cursor.execute(sql_q, (mock_id, "Logical Reasoning", "If A = 1 and B = 2, what is C?", "3", 5, 1, q1_opts, "mcq"))
    
    q2_opts = '[{"text": "10", "image": null}, {"text": "11", "image": null}, {"text": "12", "image": null}, {"text": "15", "image": null}]'
    cursor.execute(sql_q, (mock_id, "Quantitative Aptitude", "What is 5 + 5?", "10", 5, 2, q2_opts, "mcq"))

    conn.commit()
    cursor.close()
    conn.close()
    print("DONE_SUCCESS")
except Exception as e:
    print(f"DONE_ERROR: {str(e)}")
