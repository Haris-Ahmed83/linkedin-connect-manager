import json, os
from linkedin_api import Linkedin
from config import LINKEDIN_USERNAME, LINKEDIN_PASSWORD

api = Linkedin(LINKEDIN_USERNAME, LINKEDIN_PASSWORD,
               cookies_dir='E:\\Codes\\linkedin-connect-manager\\.linkedin_cookies')

me = api.get_user_profile()
first = me.get('firstName', {}).get('localized', {}).get('en_US', '')
last = me.get('lastName', {}).get('localized', {}).get('en_US', '')
urn_id = me.get('urn_id', '')
print(f'Logged in: {first} {last} (urn: {urn_id})')

invites = api.get_invitations(limit=3)
print(f'Invitations: {len(invites)}')
for inv in invites:
    inviter = inv.get('inviter', {})
    fn = inviter.get('firstName', {}).get('localized', {}).get('en_US', '')
    ln = inviter.get('lastName', {}).get('localized', {}).get('en_US', '')
    print(f'  - {fn} {ln} | entity: {inv.get("entity_urn", "")} | inviter: {inviter.get("urn_id", "")}')

# Test connections
conns = api.get_profile_connections(urn_id, limit=5)
print(f'Connections (first 5): {len(conns)}')
for c in conns[:3]:
    name = c.get('fullName') or c.get('name') or '?'
    urn = c.get('urn_id') or c.get('profile_urn') or '?'
    print(f'  - {name} | urn: {urn}')

print('API test complete!')
