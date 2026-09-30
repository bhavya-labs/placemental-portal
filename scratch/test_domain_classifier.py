def classify_drive_domain(role: str, required_skills: str) -> str:
    role_lower = (role or '').lower()
    skills_lower = (required_skills or '').lower()

    # 1. Role Title takes first precedence
    embedded_role_kw = ['embedded', 'firmware', 'hardware', 'iot', 'vlsi', 'verilog', 'microcontroller', 'robotics']
    data_role_kw = ['data scientist', 'data analyst', 'data engineer', 'machine learning', 'ai engineer', 'deep learning', 'nlp', 'business intelligence', 'bi analyst']
    cloud_role_kw = ['devops', 'cloud', 'sre', 'site reliability', 'infrastructure', 'platform engineer', 'systems engineer']
    qa_role_kw = ['qa', 'quality assurance', 'test engineer', 'sdet', 'automation tester', 'test automation']

    if any(kw in role_lower for kw in embedded_role_kw):
        return 'embedded'
    if any(kw in role_lower for kw in data_role_kw):
        return 'data'
    if any(kw in role_lower for kw in cloud_role_kw):
        return 'cloud'
    if any(kw in role_lower for kw in qa_role_kw):
        return 'qa'

    # 2. Skills-based classification if role is generic (e.g. "Software Development Engineer", "Developer", "Trainee")
    embedded_skills = ['rtos', 'assembly', 'microcontroller', 'vlsi', 'verilog', 'arm', 'arduino', 'stm32', 'embedded c']
    data_skills = ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'power bi', 'tableau']
    cloud_skills = ['kubernetes', 'docker', 'terraform', 'ansible', 'ci/cd', 'jenkins', 'aws', 'azure', 'gcp']
    qa_skills = ['selenium', 'cypress', 'playwright', 'jmeter', 'test automation', 'manual testing']

    embedded_count = sum(1 for kw in embedded_skills if kw in skills_lower)
    data_count = sum(1 for kw in data_skills if kw in skills_lower)
    cloud_count = sum(1 for kw in cloud_skills if kw in skills_lower)
    qa_count = sum(1 for kw in qa_skills if kw in skills_lower)

    skill_scores = [
        ('embedded', embedded_count),
        ('data', data_count),
        ('cloud', cloud_count),
        ('qa', qa_count)
    ]
    skill_scores.sort(key=lambda x: x[1], reverse=True)
    top_domain, top_count = skill_scores[0]

    # Require at least 2 distinct domain-specific skill matches to override the SWE default
    if top_count >= 2:
        return top_domain

    # 3. Default fallback: Generalist SWE
    return 'swe'

test_cases = [
    ('Embedded Engineer', 'C, C++, RTOS, Microcontrollers'),
    ('Data Analyst', 'Python, Pandas, SQL, Scikit-Learn'),
    ('Data Engineer', 'AWS, SQL, Spark, Python'),
    ('DevOps Engineer', 'AWS, Docker, Kubernetes, Linux'),
    ('QA Automation Engineer', 'Selenium, Java, SQL, PyTest'),
    ('Software Development Engineer', 'Java, Python, SQL'),
    ('Graduate Trainee Engineer', 'C++, Algorithms, Data Structures'),
    ('Cloud Systems Engineer', 'Linux, Bash, AWS'),
    ('Full Stack Developer', 'React, Node.js, Express, SQL')
]

for role, skills in test_cases:
    print(f'Role: "{role:<30}" | Skills: "{skills:<35}" -> Track: {classify_drive_domain(role, skills)}')
