#!/usr/bin/env python
"""
Detailed Query Analysis Script

Prints out EVERY query executed for a single API endpoint to help identify
exactly where N+1 problems are occurring.

Usage:
    djvenv/bin/python .claude/tests/phase2/test_detailed_queries.py
"""

import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from starview_app.models import Location

def main():
    # Enable query logging
    from django.conf import settings
    settings.DEBUG = True
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')

    client = Client()

    # Get or create test user
    test_user, _ = User.objects.get_or_create(
        username='query_test_user',
        defaults={'email': 'querytest@example.com'}
    )

    # Test location detail endpoint
    first_location = Location.objects.first()

    reset_queries()
    client.force_login(test_user)
    response = client.get(f'/api/locations/{first_location.id}/')

    print("="*80)
    print(f"LOCATION DETAIL API (/api/locations/{first_location.id}/)")
    print("="*80)
    print(f"\nTotal Queries: {len(connection.queries)}\n")

    for i, query in enumerate(connection.queries, 1):
        print(f"\nQuery {i}:")
        print(f"SQL: {query['sql'][:200]}...")  # First 200 chars
        print(f"Time: {query['time']}s")

    print("\n" + "="*80)
    print("ANALYSIS:")

    # Group queries by type
    select_queries = [q for q in connection.queries if q['sql'].startswith('SELECT')]
    insert_queries = [q for q in connection.queries if q['sql'].startswith('INSERT')]
    update_queries = [q for q in connection.queries if q['sql'].startswith('UPDATE')]

    print(f"SELECT queries: {len(select_queries)}")
    print(f"INSERT queries: {len(insert_queries)}")
    print(f"UPDATE queries: {len(update_queries)}")

    # Look for repeated patterns (N+1 indicators)
    sql_patterns = {}
    for query in connection.queries:
        # Remove specific IDs to find patterns
        pattern = query['sql'][:100]  # First 100 chars as pattern
        sql_patterns[pattern] = sql_patterns.get(pattern, 0) + 1

    print("\nMost common query patterns (potential N+1):")
    for pattern, count in sorted(sql_patterns.items(), key=lambda x: x[1], reverse=True)[:5]:
        if count > 1:
            print(f"  {count}x: {pattern}...")

if __name__ == '__main__':
    main()
