import os, json, base64
from requests.cookies import RequestsCookieJar, create_cookie
from linkedin_api import Linkedin

b64 = os.environ.get('LINKEDIN_COOKIES', '')
if not b64:
    print('NO LINKEDIN_COOKIES env var')
    exit(1)

cookies = json.loads(base64.b64decode(b64).decode())
jar = RequestsCookieJar()
for c in cookies:
    jar.set_cookie(create_cookie(name=c['name'], value=c['value'],
        domain=c.get('domain', '.linkedin.com'), path=c.get('path', '/'),
        secure=c.get('secure', True)))

api = Linkedin(os.environ['LINKEDIN_USERNAME'], os.environ['LINKEDIN_PASSWORD'],
               authenticate=True, cookies=jar,
               cookies_dir='E:\\Codes\\linkedin-connect-manager\\.linkedin_cookies')
me = api.get_user_profile()
first = me.get('firstName', {}).get('localized', {}).get('en_US', '')
last = me.get('lastName', {}).get('localized', {}).get('en_US', '')
urn = me.get('urn_id', '')
print(f'SUCCESS: {first} {last} (urn: {urn})')
