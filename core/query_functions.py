"""
Combined Query Functions Module
Contains both regular SQL query functions and Natural Language to SQL functions
"""

import os
import sys
import streamlit as st
import pandas as pd
import sqlite3
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from core.database import db_manager

# Load environment variables for API access
load_dotenv()

# =============================================================================
# REGULAR SQL QUERY FUNCTIONS
# =============================================================================

def is_read_only_query(query):
    """Check if query is read-only (SELECT only)"""
    query_clean = query.strip().upper()
    
    # Allow SELECT, WITH (for CTEs), and EXPLAIN
    allowed_starts = ['SELECT', 'WITH', 'EXPLAIN']
    
    # Check if query starts with allowed keywords
    for start in allowed_starts:
        if query_clean.startswith(start):
            return True
    
    return False

def execute_sql_query(query):
    """Execute SQL query with safety checks"""
    
    # Clean up query - remove trailing semicolons and whitespace
    query = query.strip().rstrip(';')
    
    # Check if query is read-only
    if not is_read_only_query(query):
        raise ValueError("Only SELECT queries are allowed for security reasons")
    
    # Check for multiple statements (basic protection)
    if ';' in query:
        raise ValueError("Multiple statements not allowed. Please execute one query at a time.")
    
    try:
        connection = db_manager.get_connection()
        if not connection:
            raise Exception("Cannot connect to database")
        
        cursor = connection.cursor()
        
        # Add LIMIT 50 if not already present (check case insensitively)
        query_upper = query.upper()
        if 'LIMIT' not in query_upper:
            query += " LIMIT 50"
        else:
            # If LIMIT exists, check if it's higher than 50
            limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if limit_match:
                existing_limit = int(limit_match.group(1))
                if existing_limit > 50:
                    # Replace with LIMIT 50
                    query = re.sub(r'LIMIT\s+\d+', 'LIMIT 50', query, flags=re.IGNORECASE)
        
        cursor.execute(query)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Get results
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return {
            'success': True,
            'columns': columns,
            'data': results,
            'row_count': len(results)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def add_to_query_history(query):
    """Add query to session state history"""
    if query.strip() and query not in st.session_state.query_history:
        st.session_state.query_history.insert(0, query)
        # Keep only last 10 queries
        st.session_state.query_history = st.session_state.query_history[:10]

def get_example_queries():
    """Get basic example queries"""
    return [
        {
            'title': 'Count All Plots',
            'query': 'SELECT COUNT(*) as total_plots FROM plots;'
        },
        {
            'title': 'List All Sandstones',
            'query': 'SELECT DISTINCT sandstone_name FROM sandstones;'
        },
        {
            'title': 'Show All Plots',
            'query': 'SELECT doi, figure_number, created_at FROM plots ORDER BY created_at DESC;'
        },
        {
            'title': 'Get Data to Replot Figure',
            'query': '''SELECT p.doi, p.figure_number, s.sandstone_name, 
       dp.p_mpa, dp.q_mpa
FROM plots p
JOIN sandstones s ON p.id = s.plot_id  
JOIN data_points dp ON s.id = dp.sandstone_id
WHERE p.doi = '10.1016/j.example.2023.01.001' 
  AND p.figure_number = '1';'''
        }
    ]

# =============================================================================
# NATURAL LANGUAGE TO SQL FUNCTIONS
# =============================================================================

def is_safe_sql(sql_query):
    """Check if generated SQL is read-only and safe"""
    
    if not sql_query or not sql_query.strip():
        return False, "Empty query"
    
    sql_upper = sql_query.strip().upper()
    
    # Allowed operations
    allowed_starts = ['SELECT', 'WITH', 'EXPLAIN']
    
    # Forbidden operations  
    forbidden_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'REPLACE', 'MERGE', 'CALL', 'EXEC',
        'PRAGMA', 'ATTACH', 'DETACH'
    ]
    
    # Check if starts with allowed operation
    if not any(sql_upper.startswith(start) for start in allowed_starts):
        return False, f"Only {', '.join(allowed_starts)} queries allowed"
    
    # Check for forbidden keywords anywhere in query
    for keyword in forbidden_keywords:
        if keyword in sql_upper:
            return False, f"Forbidden operation detected: {keyword}"
    
    # Check for multiple statements (basic SQL injection protection)
    sql_clean = sql_query.rstrip(';').strip()
    if ';' in sql_clean:
        return False, "Multiple statements not allowed"
    
    return True, "Query is safe"

def validate_and_suggest_sql_fixes(sql_query):
    """Validate generated SQL and suggest fixes for common issues"""
    
    issues = []
    suggestions = []
    
    if not sql_query:
        return issues, suggestions
    
    # If this is an auto-fixed query, show that info
    if "-- AUTO-FIXED VERSION:" in sql_query:
        # Extract the actual SQL part for validation
        actual_sql = sql_query.split("-- AUTO-FIXED VERSION:")[-1].strip()
        issues.append("Auto-fix was applied to correct SQL issues")
        suggestions.append("Review both original and fixed versions shown above")
        sql_query = actual_sql
    
    sql_upper = sql_query.upper()
    
    # Check for missing JOINs when referencing multiple tables
    tables_referenced = []
    if 'PLOTS.' in sql_upper:
        tables_referenced.append('plots')
    if 'SANDSTONES.' in sql_upper:
        tables_referenced.append('sandstones')  
    if 'DATA_POINTS.' in sql_upper:
        tables_referenced.append('data_points')
    
    joins_present = sql_upper.count('JOIN')
    
    # If we reference multiple tables but don't have enough JOINs
    if len(tables_referenced) > 1 and joins_present < (len(tables_referenced) - 1):
        issues.append("Missing JOIN statements for multiple table references")
        suggestions.append("Add proper JOINs: plots -> sandstones -> data_points")
    
    # Check for DOI format issues
    if 'HTTPS://DOI.ORG/' in sql_upper:
        issues.append("DOI contains URL prefix")
        suggestions.append("Remove 'https://doi.org/' from DOI - database stores just the DOI number")
    
    return issues, suggestions

def test_and_fix_sql(original_sql):
    """Test SQL and fix if it fails with known issues"""
    
    if not original_sql:
        return original_sql, False, "No SQL to test"
    
    # First, try to execute the original SQL
    try:
        # Do a quick syntax/table check without actually running
        connection = db_manager.get_connection()
        if not connection:
            return original_sql, False, "Cannot connect to database"
        
        cursor = connection.cursor()
        cursor.execute("EXPLAIN QUERY PLAN " + original_sql)
        cursor.close()
        connection.close()
        
        # If we get here, the SQL is valid
        return original_sql, False, "SQL is valid"
        
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for specific error patterns we can fix
        if "no such column: plots.doi" in error_msg or "plots.doi" in error_msg:
            # This is the missing plots table issue - apply fix
            
            # Extract DOI value from WHERE clause
            doi_value = "UNKNOWN_DOI"
            if "plots.doi = '" in original_sql:
                start = original_sql.find("plots.doi = '") + len("plots.doi = '")
                end = original_sql.find("'", start)
                if end > start:
                    doi_value = original_sql[start:end]
            
            # Clean DOI URLs
            doi_value = doi_value.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi:', '')
            
            # Create the corrected SQL
            fixed_sql = f"""SELECT s.sandstone_name, dp.p_mpa, dp.q_mpa 
FROM plots p 
JOIN sandstones s ON p.id = s.plot_id 
JOIN data_points dp ON s.id = dp.sandstone_id 
WHERE p.doi = '{doi_value}'"""
            
            return fixed_sql, True, f"Fixed missing plots table JOIN (DOI: {doi_value})"
        
        else:
            # Different error, can't auto-fix
            return original_sql, False, f"Cannot auto-fix: {str(e)}"

def clean_user_question(question):
    """Clean up user question to improve SQL generation"""
    
    if not question:
        return question
    
    # Clean DOI formats
    question = question.replace('https://doi.org/', '')
    question = question.replace('http://doi.org/', '')
    question = question.replace('doi:', '')
    
    # Add more cleanup rules as needed
    return question.strip()

def generate_sql_from_nl(question):
    """Generate SQL from natural language using Featherless AI"""
    
    if not question or not question.strip():
        return None
    
    # Clean the question
    cleaned_question = clean_user_question(question)
    
    # Check if HF_TOKEN is available
    if 'HF_TOKEN' not in os.environ:
        st.error("❌ API token not found. Please set HF_TOKEN in your environment.")
        return None
    
    client = OpenAI(
        base_url = "https://router.huggingface.co/v1",
        api_key=os.environ['HF_TOKEN'],
    )
    
    # Prompt for SQL generation
    system_prompt = """You are an expert SQL generator for a rock mechanics research database.

DATABASE SCHEMA:
- plots: id, doi, figure_number, plot_identifier, created_at
- sandstones: id, plot_id, sandstone_name, created_at
- data_points: id, sandstone_id, x_pixel, y_pixel, p_mpa, q_mpa, created_at

CRITICAL: SANDSTONE NAMING CONVENTION:
Format: "SandstoneType (Porosity%), FirstAuthor et al. (Year)"

EXAMPLES:
- "Adamswiller (22.6%), Wong et al. (1997)"
- "Bentheim (22.8%), Baud et al. (2006)"

COMPONENTS:
1. Sandstone Type: Adamswiller, Bentheim, Berea, etc.
2. Porosity: Percentage in first parentheses
3. Research Source: Scientific citation format
4. Publication Year: Year in second parentheses

QUERY INTERPRETATION PATTERNS:
- "Bentheim sandstone" → LIKE '%Bentheim%' (match rock type)
- "Baud studies" → LIKE '%Baud%' (match author)
- "2006 data" → LIKE '%2006%' (match year)
- "high porosity" → Need percentage comparison (>20% typical)
- "recent studies" → Years after 2000 typically
- "Wong's Adamswiller" → LIKE '%Adamswiller%Wong%'

RESEARCH CONTEXT:
- p_mpa = pressure in megapascals from triaxial/uniaxial tests
- q_mpa = deviatoric stress in megapascals
- Data sources are peer-reviewed publications
- Porosity significantly affects rock strength behavior
- Researchers often compare by: rock type, porosity range, study period, research group

SQL GUIDELINES:
- Use LOWER() for case-insensitive matching
- Always use LIKE patterns for sandstone_name searches
- Table aliases: plots p, sandstones s, data_points dp
- Add LIMIT 50 for large result sets
- For porosity comparisons, extract number from first parentheses
- Only SELECT queries

COLUMN SELECTION GUIDELINES:
For "show data" or "display" queries, select relevant research columns:
- Always include: s.sandstone_name, dp.p_mpa, dp.q_mpa
- Often useful: p.doi, p.figure_number
- For plotting: dp.x_pixel, dp.y_pixel  
- Avoid: Internal IDs, timestamps, foreign keys

NEVER use SELECT * with JOINs - always specify columns explicitly.

STANDARD "SHOW DATA" FORMAT:
SELECT s.sandstone_name, dp.p_mpa, dp.q_mpa, p.doi, p.figure_number
FROM plots p
JOIN sandstones s ON p.id = s.plot_id  
JOIN data_points dp ON s.id = dp.sandstone_id
WHERE [conditions]
LIMIT 50;

Generate ONLY the SQL query, no explanations."""
    
    try:
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct:groq",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate SQL for: {cleaned_question}"}
            ],
            max_tokens=150,
            temperature=0.1
        )

        # Extract response from chat completion
        generated_sql = completion.choices[0].message.content.strip()
        generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()
        # Test and potentially fix the SQL
        final_sql, was_fixed, fix_message = test_and_fix_sql(generated_sql)

        if was_fixed:
            return f"-- AUTO-FIXED VERSION: \n{final_sql}"
        else:
            return final_sql
    
    except Exception as e:
        st.error(f"❌ Error generating SQL: {e}")
        return None

def execute_nl_generated_sql(sql_query):
    """Execute NL-generated SQL with enhanced safety checks"""
    
    # If SQL contains auto-fix comments, extract just the executable part
    if "-- AUTO-FIXED VERSION:" in sql_query:
        # Extract only the part after the auto-fix comment
        parts = sql_query.split("-- AUTO-FIXED VERSION:")
        if len(parts) > 1:
            sql_query = parts[1].strip()
    
    # Security validation
    is_safe, safety_message = is_safe_sql(sql_query)
    if not is_safe:
        return {
            'success': False,
            'error': f"Security violation: {safety_message}",
            'security_violation': True
        }
    
    # Execute using existing safe SQL execution
    try:
        result = execute_sql_query(sql_query)
        
        if result['success']:
            return {
                'success': True,
                'columns': result['columns'],
                'data': result['data'],
                'row_count': result['row_count']
            }
        else:
            return {
                'success': False,
                'error': result['error'],
                'security_violation': False
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Execution error: {e}",
            'security_violation': False
        }

def get_example_nl_questions():
    """Get example natural language questions"""
    return [
        "How many plots are in the database?",
        "List all sandstone types",
        "What are the pressure and stress ranges?"
    ]