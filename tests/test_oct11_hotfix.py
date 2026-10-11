"""PULSEIQ October 11 regression tests: timezones, registration input, and marks analytics."""
from datetime import date, datetime, timezone
from test_tenants import client, signin, post, PASSWORD
from backend.campus_pages import college_local_date


def test_india_college_timezone_at_utc_midnight_boundary(client):
    signin(client, 'admin@test.edu')
    with client.app.state.engine.connect() as c:
        d, zone = college_local_date(c, client.get('/api/auth/me').json()['user']['college_id'],
                                     datetime(2026, 10, 10, 23, 40, tzinfo=timezone.utc))
    assert d == date(2026, 10, 11)
    assert zone == 'Asia/Kolkata'
    d = client.get('/api/v4/college-date')
    assert d.status_code == 200 and d.json()['timezone'] == 'Asia/Kolkata'


def test_registration_domain_input_and_code_error(client, monkeypatch):
    monkeypatch.setenv('REGISTRATION_INVITE_CODE','THIS-IS-ONLY-A-TEST-CODE')
    base = dict(name='PulseIQ College',domain='clg@pulseiq.edu.in',admin_name='Teacher Admin',
                admin_email='teacher@pulseiq.edu.in',admin_password=PASSWORD,
                registration_code='THIS-IS-ONLY-A-TEST-CODE')
    bad = client.post('/api/colleges/register',json=base)
    assert bad.status_code == 400
    assert 'valid college domain' in bad.json()['detail']
    badpw = client.post('/api/colleges/register',json={**base,'domain':'pulseiq.edu.in','admin_password':'tooshort'})
    assert badpw.status_code == 422
    wrongcode = client.post('/api/colleges/register',json={**base,'domain':'pulseiq.edu.in','registration_code':'incorrect'})
    assert wrongcode.status_code == 403


def test_class_analytics_reuses_published_legacy_marks_without_duplicates(client):
    signin(client,'admin@test.edu')
    post(client,'/api/v4/students',{'student_id':'BACK1','full_name':'Backward Compatible Student',
        'email':'back@test.edu','password':PASSWORD,'department':'CSE','semester':1,'section':'A'})
    faculty=post(client,'/api/admin/accounts',{'email':'legacy-teacher@test.edu',
        'full_name':'Legacy Teacher','password':PASSWORD,'role':'faculty','departments':['CSE']})
    assignment=post(client,'/api/admin/assignments',{'faculty_id':faculty['id'],
        'department':'CSE','semester':1,'section':'A','subject':'Algorithms'})['id']
    signin(client,'legacy-teacher@test.edu')
    post(client,'/api/entries',{'student_id':'BACK1','assignment_id':assignment,
        'kind':'marks','period_end':date.today().isoformat(),
        'marks_pct':65,'status':'published'})
    a=client.get('/api/v4/class-analytics',params={'assignment_id':assignment})
    assert a.status_code==200,a.text
    assert a.json()['exam_records_count']==1
    assert a.json()['pass_percentage']==100
    suc=client.get('/api/v4/success').json()['items']
    assert suc[0]['success_rate']==65
    post(client,'/api/v4/marks/batch',{'assignment_id':assignment,'exam_name':'Mid Semester 1',
        'exam_date':date.today().isoformat(),'maximum':30,
        'items':[{'student_id':'BACK1','marks':12}]})
    new=client.get('/api/v4/class-analytics',params={'assignment_id':assignment})
    assert new.status_code==200,new.text
    assert new.json()['exam_records_count']==1  # never double-count the older record
    assert new.json()['pass_percentage']==100
    assert client.get('/api/v4/success').json()['items'][0]['success_rate']==40
