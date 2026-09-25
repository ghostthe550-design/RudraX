from app import app

client = app.test_client()

# 1. GET /
r = client.get('/')
assert r.status_code == 200, f'GET / failed: {r.status_code}'
assert b'Find Your Concessional Government Scheme' in r.data, 'Page heading missing in /'
print('[PASS] GET /: 200 OK')

# 2. GET /results (should redirect to /)
r = client.get('/results')
assert r.status_code == 302, f'GET /results redirect failed: {r.status_code}'
print('[PASS] GET /results redirects gracefully: 302')

# 3. POST /results (valid submission)
data = {
    'age': '24',
    'gender': 'Female',
    'caste_category': 'SC',
    'education_level': '4',
    'is_pwd': 'No',
    'repayment_status': 'NO_PRIOR_LOANS',
    'cibil_range': '750_PLUS'
}
r = client.post('/results', data=data)
assert r.status_code == 200, f'POST /results failed: {r.status_code}'
assert b'Your Evaluated Scheme Compatibility' in r.data, 'Results heading missing'
assert b'style="width: 100%;"' in r.data, 'Score bar width missing in results'
print('[PASS] POST /results (valid): 200 OK & progress bars formatted')

# 4. POST /results (invalid/missing submission)
r = client.post('/results', data={'age': '24'})
assert r.status_code == 302, 'POST /results missing fields did not redirect'
assert 'error=invalid_input' in r.headers['Location'], 'Did not redirect with error=invalid_input'
print('[PASS] POST /results (invalid): redirects with invalid_input')

# 5. GET /navigator
r = client.get('/navigator')
assert r.status_code == 200, f'GET /navigator failed: {r.status_code}'
assert b'Financial Navigator &amp; Partner Locator' in r.data, 'Navigator heading missing'
print('[PASS] GET /navigator: 200 OK')

# 6. GET /compare
r = client.get('/compare')
assert r.status_code == 200, f'GET /compare failed: {r.status_code}'
assert b'Multi-Channel Lender &amp; Scheme Comparison' in r.data, 'Compare heading missing'
print('[PASS] GET /compare: 200 OK')

# 7. GET /api/schemes
r = client.get('/api/schemes')
assert r.status_code == 200, f'GET /api/schemes failed: {r.status_code}'
json_data = r.get_json()
assert 'schemes' in json_data and len(json_data['schemes']) == 8, 'Schemes API count mismatch'
print(f'[PASS] GET /api/schemes: 200 OK, returned {len(json_data["schemes"])} schemes')

# 8. GET /static/style.css & /style.css
r1 = client.get('/static/style.css')
assert r1.status_code == 200, f'GET /static/style.css failed: {r1.status_code}'
r2 = client.get('/style.css')
assert r2.status_code == 200, f'GET /style.css fallback failed: {r2.status_code}'
print('[PASS] Static CSS routes: 200 OK for both /static/style.css and /style.css')

# 9. GET /static/i18n.js & /i18n.js
ri1 = client.get('/static/i18n.js')
assert ri1.status_code == 200, f'GET /static/i18n.js failed: {ri1.status_code}'
ri2 = client.get('/i18n.js')
assert ri2.status_code == 200, f'GET /i18n.js fallback failed: {ri2.status_code}'
assert b'I18N_DICTIONARY' in ri1.data, 'I18N dictionary missing in i18n.js'
print('[PASS] Static i18n JS routes: 200 OK for both /static/i18n.js and /i18n.js')

print('\n*** ALL AUTOMATED BACKEND & INTEGRATION TESTS PASSED! ***')
