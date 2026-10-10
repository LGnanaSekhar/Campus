-- Run after deployment / import. No passwords or secrets are returned.
SELECT 'Source students' AS item, COUNT(*) AS total FROM public.students
UNION ALL SELECT 'Source faculty',COUNT(*) FROM public.faculty
UNION ALL SELECT 'PULSEIQ roster',COUNT(*) FROM public.pi3_roster
UNION ALL SELECT 'Student login accounts',COUNT(*) FROM public.pi3_accounts WHERE role='student'
UNION ALL SELECT 'Faculty login accounts',COUNT(*) FROM public.pi3_accounts WHERE role='faculty'
UNION ALL SELECT 'Teaching assignments',COUNT(*) FROM public.pi3_assignments
UNION ALL SELECT 'Learning tasks',COUNT(*) FROM public.pi3_learning_tasks
UNION ALL SELECT 'Resources',COUNT(*) FROM public.pi3_learning_resources;

SELECT s.email_domain AS source_domain,p.domain AS application_domain,
  CASE WHEN LOWER(s.email_domain)=LOWER(p.domain) THEN 'MATCH' ELSE 'MISMATCH' END AS status
FROM public.colleges s CROSS JOIN public.pi3_colleges p;
