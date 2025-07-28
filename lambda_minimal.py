import json
from datetime import datetime

# Global storage
LEADS = {}
NEXT_LEAD_ID = 1

def lambda_handler(event, context):
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    body = event.get('body', '{}')
    
    # Parse body
    try:
        body_data = json.loads(body) if body else {}
    except:
        body_data = {}
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Health check
    if path == '/health':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'healthy',
                'version': 'v6.0.0 - Minimal Working CRM',
                'total_leads': len(LEADS),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    # Login (simplified)
    if path == '/api/v1/auth/login' and method == 'POST':
        username = body_data.get('username', '')
        password = body_data.get('password', '')
        
        # Simple auth
        if username == 'agent1' and password == 'admin123':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'access_token': 'valid_token_for_agent1',
                    'token_type': 'bearer'
                })
            }
        
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps({'detail': 'Invalid credentials'})
        }
    
    # Get leads
    if path == '/api/v1/leads' and method == 'GET':
        leads_list = list(LEADS.values())
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(leads_list)
        }
    
    # Create lead
    if path == '/api/v1/leads' and method == 'POST':
        global NEXT_LEAD_ID
        
        lead = {
            'id': NEXT_LEAD_ID,
            'practice_name': body_data.get('practice_name', ''),
            'owner_name': body_data.get('owner_name', ''),
            'city': body_data.get('city', ''),
            'state': body_data.get('state', ''),
            'priority': body_data.get('priority', 'C'),
            'status': 'NEW',
            'created_at': datetime.utcnow().isoformat()
        }
        
        LEADS[NEXT_LEAD_ID] = lead
        NEXT_LEAD_ID += 1
        
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps(lead)
        }
    
    # Default response
    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'detail': 'Not found'})
    } 