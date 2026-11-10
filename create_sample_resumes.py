import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_resumes")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def create_sample_standard():
    """1. Standard one-page software developer resume."""
    filename = os.path.join(SAMPLE_DIR, "sample_1_standard.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "Alex Morgan")

    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "alex.morgan@techcorp.io | +1 (555) 987-6543 | github.com/alexmorgan | linkedin.com/in/alexmorgan")

    # Education
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 700, "Education")
    c.line(50, 695, 550, 695)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 678, "Bachelor of Science in Computer Science")
    c.setFont("Helvetica", 10)
    c.drawString(50, 664, "University of California, Berkeley (2018 - 2022)")
    c.drawString(65, 650, "• GPA: 3.9/4.0, Dean's Honors List")
    c.drawString(65, 636, "• Relevant Coursework: Data Structures, Operating Systems, Database Management")

    # Experience
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 606, "Work Experience")
    c.line(50, 601, 550, 601)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 584, "Full Stack Software Engineer | Dataview Inc.")
    c.setFont("Helvetica", 10)
    c.drawString(450, 584, "2022 - Present")
    c.drawString(65, 568, "• Developed backend microservices using Python, Flask, and PostgreSQL.")
    c.drawString(65, 554, "• Built reactive user interfaces using React, JavaScript, and Tailwind CSS.")
    c.drawString(65, 540, "• Containerized services using Docker and deployed to AWS ECS.")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 514, "Junior Developer Intern | Apex Labs")
    c.setFont("Helvetica", 10)
    c.drawString(450, 514, "2021 - 2022")
    c.drawString(65, 498, "• Automated test suites using pytest, reducing regression testing time by 40%.")
    c.drawString(65, 484, "• Collaborated with senior engineers on REST API design and documentation.")

    # Projects
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 454, "Projects")
    c.line(50, 449, 550, 449)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 432, "Distributed Task Scheduler | Python, Redis, Docker (2023 - 2024)")
    c.setFont("Helvetica", 10)
    c.drawString(65, 418, "• Implemented a lightweight distributed task queue handling 5,000 tasks/second.")
    c.drawString(65, 404, "• Integrated Redis pub/sub for real-time job execution telemetry.")

    # Skills
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 374, "Technical Skills")
    c.line(50, 369, 550, 369)

    c.setFont("Helvetica", 10)
    c.drawString(50, 352, "Languages & Web: Python, JavaScript, TypeScript, SQL, HTML, CSS")
    c.drawString(50, 338, "Frameworks & Tools: Flask, Django, React, Node.js, Docker, Git, GitHub")
    c.drawString(50, 324, "Databases & Cloud: PostgreSQL, MongoDB, Redis, AWS, Linux")

    # Certifications
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 294, "Certifications")
    c.line(50, 289, 550, 289)

    c.setFont("Helvetica", 10)
    c.drawString(65, 272, "• AWS Certified Developer - Associate (2023)")
    c.drawString(65, 258, "• Docker Certified Associate (2022)")

    c.save()
    print(f"Created: {filename}")


def create_sample_twocolumn():
    """2. Two-column layout style resume."""
    filename = os.path.join(SAMPLE_DIR, "sample_2_twocolumn.pdf")
    c = canvas.Canvas(filename, pagesize=letter)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "Priya Sharma")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "Email: priya.sharma@example.com | Phone: +91 9876543210")
    c.drawString(50, 720, "Portfolio: https://priyasharma.dev | GitHub: https://github.com/priyasharma")

    # Left Column (Skills & Education)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 680, "Technical Skills")
    c.line(50, 675, 230, 675)

    c.setFont("Helvetica", 9)
    skills = [
        "Python", "SQL", "Machine Learning", "Pandas",
        "NumPy", "TensorFlow", "Scikit-Learn", "Docker",
        "AWS", "Git", "GitHub", "Linux"
    ]
    y = 660
    for s in skills:
        c.drawString(55, y, f"• {s}")
        y -= 15

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 10, "Education")
    c.line(50, y - 15, 230, y - 15)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y - 30, "Bachelor of Technology")
    c.setFont("Helvetica", 9)
    c.drawString(50, y - 44, "Delhi Technological University")
    c.drawString(50, y - 58, "2019 - 2023")

    # Right Column (Experience & Projects)
    rx = 260
    c.setFont("Helvetica-Bold", 12)
    c.drawString(rx, 680, "Work Experience")
    c.line(rx, 675, 550, 675)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(rx, 660, "Data Scientist | Neural Analytics")
    c.setFont("Helvetica", 9)
    c.drawString(450, 660, "2023 - Present")
    c.drawString(rx + 10, 645, "• Built predictive ML models using Python, Scikit-Learn, and Pandas.")
    c.drawString(rx + 10, 630, "• Deployed computer vision pipelines using TensorFlow and Docker.")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(rx, 595, "Key Projects")
    c.line(rx, 590, 550, 590)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(rx, 570, "Medical Image Classifier (2022 - 2023)")
    c.setFont("Helvetica", 9)
    c.drawString(rx + 10, 555, "• Developed CNN architecture with 94.2% test accuracy.")
    c.drawString(rx + 10, 540, "• Packaged inference engine into a lightweight Flask REST API.")

    c.save()
    print(f"Created: {filename}")


def create_sample_missing_sections():
    """3. Resume with missing education and certifications."""
    filename = os.path.join(SAMPLE_DIR, "sample_3_missing_sections.pdf")
    c = canvas.Canvas(filename, pagesize=letter)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "Marcus Vance")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "Email: marcus.vance@workmail.com | Tel: 415-555-0199")

    # Experience
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 690, "Experience")
    c.line(50, 685, 550, 685)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 665, "DevOps Engineer | CloudScale Systems")
    c.setFont("Helvetica", 10)
    c.drawString(450, 665, "2020 - Present")
    c.drawString(65, 650, "• Managed multi-region Kubernetes clusters and AWS infrastructure.")
    c.drawString(65, 636, "• Automated CI/CD deployment pipelines using GitHub Actions and Terraform.")

    # Skills
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 595, "Core Skills")
    c.line(50, 590, 550, 590)

    c.setFont("Helvetica", 10)
    c.drawString(50, 570, "AWS, Docker, Kubernetes, Linux, Terraform, Git, GitHub, Python, CI/CD")

    c.save()
    print(f"Created: {filename}")


def create_sample_unusual_headings():
    """4. Resume with unusual section headings (Academic Background, Competencies, Career History)."""
    filename = os.path.join(SAMPLE_DIR, "sample_4_unusual_headings.pdf")
    c = canvas.Canvas(filename, pagesize=letter)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 750, "Elena Rostova")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "elena.rostova@academix.org | +44 20 7946 0912 | https://rostova.org")

    # Unusual heading: Academic Background
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 695, "Academic Background")
    c.line(50, 690, 550, 690)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 670, "Master of Science in Software Engineering")
    c.setFont("Helvetica", 10)
    c.drawString(50, 656, "Oxford Institute of Technology (2019 - 2021)")

    # Unusual heading: Career History
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 620, "Employment History")
    c.line(50, 615, 550, 615)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 595, "Lead Software Architect | FinTech Global")
    c.setFont("Helvetica", 10)
    c.drawString(450, 595, "2021 - Present")
    c.drawString(65, 580, "• Architected high-throughput transaction ledger in Go and PostgreSQL.")
    c.drawString(65, 566, "• Migrated legacy monolithic services to microservices on Docker and AWS.")

    # Unusual heading: Proficiencies
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 530, "Technical Proficiencies")
    c.line(50, 525, 550, 525)

    c.setFont("Helvetica", 10)
    c.drawString(50, 508, "Go, Python, SQL, PostgreSQL, Docker, AWS, Git, Linux, REST API")

    # Certificates
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, 470, "Certificates")
    c.line(50, 465, 550, 465)
    c.setFont("Helvetica", 10)
    c.drawString(65, 448, "• Certified Kubernetes Administrator (CKA)")

    c.save()
    print(f"Created: {filename}")


def create_sample_scanned_empty():
    """5. Scanned / image-only representation (blank text stream)."""
    filename = os.path.join(SAMPLE_DIR, "sample_5_scanned_empty.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    # Just draw a shape/rectangle without selectable text
    c.rect(50, 50, 500, 700, fill=0)
    c.save()
    print(f"Created: {filename}")


if __name__ == "__main__":
    create_sample_standard()
    create_sample_twocolumn()
    create_sample_missing_sections()
    create_sample_unusual_headings()
    create_sample_scanned_empty()
    print("All 5 test resumes generated successfully!")

