import os
from extractor.pdf_reader import extract_pdf_text
from extractor.cleaner import clean_text
from extractor.parser import parse_resume

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_resumes")

BENCHMARKS = [
    {
        "file": "sample_1_standard.pdf",
        "description": "Standard One-Page Resume",
        "expected": {
            "name": "Alex Morgan",
            "email": "alex.morgan@techcorp.io",
            "phone": "+1 (555) 987-6543",
            "skills": ["Python", "Flask", "Docker", "AWS", "SQL", "JavaScript", "React"],
            "has_education": True,
            "has_experience": True,
            "has_projects": True,
            "has_certifications": True,
        }
    },
    {
        "file": "sample_2_twocolumn.pdf",
        "description": "Two-Column Layout Resume",
        "expected": {
            "name": "Priya Sharma",
            "email": "priya.sharma@example.com",
            "phone": "+91 9876543210",
            "skills": ["Python", "SQL", "Machine Learning", "TensorFlow", "Pandas", "NumPy"],
            "has_education": True,
            "has_experience": True,
            "has_projects": True,
            "has_certifications": False,
        }
    },
    {
        "file": "sample_3_missing_sections.pdf",
        "description": "Resume with Missing Sections (No Education)",
        "expected": {
            "name": "Marcus Vance",
            "email": "marcus.vance@workmail.com",
            "phone": "415-555-0199",
            "skills": ["AWS", "Docker", "Kubernetes", "Linux", "Terraform", "Python"],
            "has_education": False,
            "has_experience": True,
            "has_projects": False,
            "has_certifications": False,
        }
    },
    {
        "file": "sample_4_unusual_headings.pdf",
        "description": "Unusual Headings (Academic Background, Competencies)",
        "expected": {
            "name": "Elena Rostova",
            "email": "elena.rostova@academix.org",
            "phone": "+44 20 7946 0912",
            "skills": ["Go", "Python", "SQL", "PostgreSQL", "Docker", "AWS"],
            "has_education": True,
            "has_experience": True,
            "has_projects": False,
            "has_certifications": True,
        }
    },
]


def run_evaluation():
    total_checks = 0
    passed_checks = 0
    field_stats = {}

    def record_check(field, is_correct):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if is_correct:
            passed_checks += 1
        if field not in field_stats:
            field_stats[field] = {"total": 0, "correct": 0}
        field_stats[field]["total"] += 1
        if is_correct:
            field_stats[field]["correct"] += 1

    print("=================================================================")
    print("      RESUME INFORMATION EXTRACTOR - ACCURACY BENCHMARK         ")
    print("=================================================================\n")

    for benchmark in BENCHMARKS:
        path = os.path.join(SAMPLE_DIR, benchmark["file"])
        print(f"Testing: {benchmark['description']} ({benchmark['file']})")

        raw = extract_pdf_text(path)
        cleaned = clean_text(raw)
        result = parse_resume(cleaned)
        exp = benchmark["expected"]

        # Check Name
        name_ok = (result.get("name") == exp["name"])
        record_check("name", name_ok)

        # Check Email
        email_ok = (result.get("contact", {}).get("email") == exp["email"])
        record_check("email", email_ok)

        # Check Phone
        res_phone = result.get("contact", {}).get("phone") or ""
        phone_digits = "".join(filter(str.isdigit, res_phone))
        exp_phone_digits = "".join(filter(str.isdigit, exp["phone"]))
        phone_ok = (exp_phone_digits in phone_digits or phone_digits in exp_phone_digits)
        record_check("phone", phone_ok)

        # Check Skills (Recall on expected core skills)
        matched_skills = set(result.get("skills", []))
        expected_skills = set(exp["skills"])
        skills_ok = expected_skills.issubset(matched_skills)
        record_check("skills", skills_ok)

        # Check Education presence
        has_edu = len(result.get("education", [])) > 0
        edu_ok = (has_edu == exp["has_education"])
        record_check("education_detection", edu_ok)

        # Check Experience presence
        has_exp = len(result.get("experience", [])) > 0
        exp_ok = (has_exp == exp["has_experience"])
        record_check("experience_detection", exp_ok)

        print(f"  Name: {'PASS' if name_ok else 'FAIL'} (Extracted: '{result.get('name')}')")
        print(f"  Email: {'PASS' if email_ok else 'FAIL'} (Extracted: '{result.get('contact', {}).get('email')}')")
        print(f"  Phone: {'PASS' if phone_ok else 'FAIL'} (Extracted: '{res_phone}')")
        print(f"  Skills: {'PASS' if skills_ok else 'PARTIAL'} (Found {len(matched_skills)}: {sorted(list(matched_skills))[:5]}...)")
        print(f"  Education: {'PASS' if edu_ok else 'FAIL'}")
        print(f"  Experience: {'PASS' if exp_ok else 'FAIL'}")
        print(f"  Warnings: {result.get('warnings')}")
        print("-" * 65)

    print("\n=================================================================")
    print("                   FIELD-LEVEL ACCURACY REPORT                   ")
    print("=================================================================")
    for field, data in field_stats.items():
        pct = (data["correct"] / data["total"]) * 100
        print(f"{field:<25}: {data['correct']}/{data['total']} ({pct:5.1f}%)")

    overall_pct = (passed_checks / total_checks) * 100
    print("-" * 65)
    print(f"OVERALL ACCURACY SCORE   : {passed_checks}/{total_checks} ({overall_pct:5.1f}%)\n")


if __name__ == "__main__":
    run_evaluation()

