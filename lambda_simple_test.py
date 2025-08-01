#!/usr/bin/env python3
"""
Simple test Lambda function to isolate the issue
"""

import json
from datetime import datetime

def lambda_handler(event, context):
    """Simple Lambda handler for debugging"""
    try:
        # Parse the request
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        print(f"[HOT] VantagePoint {method} {path}")
        
        # CORS headers for all responses
        response_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Content-Type': 'application/json'
        }
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({"message": "CORS OK"})
            }
        
        # Health check
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'VantagePoint CRM API',
                    'version': '2.0.0',
                    'timestamp': datetime.utcnow().isoformat(),
                    'test': 'simple'
                })
            }
        
        # Default response
        return {
            'statusCode': 404,
            'headers': response_headers,
            'body': json.dumps({"detail": "Endpoint not found"})
        }
        
    except Exception as e:
        print(f"[ERROR] Lambda error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        }