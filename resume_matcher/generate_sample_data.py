#!/usr/bin/env python3
"""
generate_sample_data.py
-------------------------
Creates a sample job description PDF and ~15 resume PDFs under
data/jd/ and data/resumes/ so you can run the pipeline end-to-end
without needing your own files first.

Uses reportlab to render plain text to simple PDFs.
"""

from __future__ import annotations
import os
import textwrap

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JD_DIR = os.path.join(BASE_DIR, "data", "jd")
RESUME_DIR = os.path.join(BASE_DIR, "data", "resumes")


def write_text_pdf(path: str, text: str) -> None:
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    x_margin, y = 50, height - 50
    c.setFont("Helvetica", 10)
    for raw_line in text.split("\n"):
        wrapped = textwrap.wrap(raw_line, width=100) or [""]
        for line in wrapped:
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 50
            c.drawString(x_margin, y, line)
            y -= 13
    c.save()


JD_TEXT = """Senior Backend Engineer

About the role:
We are hiring a Senior Backend Engineer to help scale our data platform.

Requirements:
- 5+ years of professional experience in backend software engineering
- Strong proficiency in Python
- Hands-on experience with AWS
- Experience with SQL and relational databases (PostgreSQL preferred)
- Experience building REST APIs
- Must have experience with Docker and Kubernetes
- Solid understanding of microservices architecture

Preferred qualifications:
- Experience with Kafka or similar streaming systems
- Familiarity with Terraform
- Experience with CI/CD pipelines
- Exposure to machine learning pipelines
- Experience mentoring junior engineers

Responsibilities:
- Design and build scalable backend services
- Collaborate with data science team on ML pipeline integration
- Own on-call rotation and production reliability
"""

# (name, years_stmt, skills_line, extra_bullets)
CANDIDATES = [
    ("Aditi Rao", "7 years of professional experience", "Python, AWS, PostgreSQL, Docker, Kubernetes, REST API, microservices, Terraform, CI/CD",
     ["- Led migration of monolith to microservices on AWS using Docker and Kubernetes",
      "- Built REST APIs serving 2M+ daily requests",
      "- Mentored 3 junior engineers"]),
    ("Ben Carter", "3 years of professional experience", "Python, JavaScript, React, MySQL, Git",
     ["- Built internal dashboards using React and Node.js",
      "- Wrote unit tests and participated in agile sprints"]),
    ("Chen Wei", "6 years of professional experience", "Python, AWS, Docker, Kubernetes, SQL, REST API, Kafka, CI/CD",
     ["- Designed event-driven microservices using Kafka and Kubernetes on AWS",
      "- Implemented CI/CD pipelines reducing deploy time by 40%"]),
    ("Diana Okafor", "9 years of professional experience", "Java, Spring, AWS, PostgreSQL, Docker, microservices, leadership",
     ["- Led backend team of 6 building microservices in Java and Spring",
      "- Oversaw AWS infrastructure and PostgreSQL data layer"]),
    ("Ethan Kim", "2 years of professional experience", "Python, Flask, SQL, Git, testing",
     ["- Built Flask REST APIs for internal tools",
      "- Wrote unit and integration tests"]),
    ("Fatima Al-Sayed", "8 years of professional experience", "Python, AWS, Docker, Kubernetes, PostgreSQL, REST API, Terraform, machine learning, CI/CD",
     ["- Built ML pipeline serving fraud-detection models in production on AWS",
      "- Used Terraform to manage all infrastructure as code",
      "- Mentored junior engineers on Kubernetes best practices"]),
    ("Grace Liu", "4 years of professional experience", "Python, Django, MySQL, Git, agile",
     ["- Developed Django backend for e-commerce platform",
      "- Participated in scrum ceremonies and sprint planning"]),
    ("Hassan Malik", "10 years of professional experience", "Python, AWS, Docker, Kubernetes, SQL, PostgreSQL, REST API, microservices, Kafka, Terraform, CI/CD, leadership",
     ["- Architected company-wide migration to Kubernetes on AWS",
      "- Built streaming data pipelines with Kafka",
      "- Led team of 8 backend engineers"]),
    ("Isabella Moretti", "1 years of professional experience", "JavaScript, React, HTML, CSS, Git",
     ["- Built responsive frontend components in React",
      "- Fixed CSS layout bugs across browsers"]),
    ("Jamal Thompson", "5 years of professional experience", "Python, AWS, Docker, SQL, REST API, CI/CD",
     ["- Built and deployed REST APIs on AWS using Docker containers",
      "- Set up CI/CD pipeline with automated testing"]),
    ("Karina Volkov", "6 years of professional experience", "Python, GCP, PostgreSQL, REST API, microservices, testing",
     ["- Built microservices on GCP with PostgreSQL backend",
      "- Established test automation framework"]),
    ("Liam O'Brien", "4 years of professional experience", "C#, .NET, Azure, SQL, agile",
     ["- Built enterprise applications in C# and .NET on Azure",
      "- Worked in agile team of 5"]),
    ("Mei Tanaka", "7 years of professional experience", "Python, AWS, Docker, Kubernetes, SQL, PostgreSQL, REST API, microservices, CI/CD, machine learning",
     ["- Built and scaled backend microservices for ML feature store on AWS",
      "- Owned Kubernetes cluster reliability and on-call rotation"]),
    ("Noah Peterson", "2 years of professional experience", "Python, Flask, SQL, Git",
     ["- Built internal Flask microservice for reporting",
      "- Wrote SQL queries for analytics dashboards"]),
    ("Olivia Nguyen", "5 years of professional experience", "Python, AWS, Docker, Kubernetes, PostgreSQL, REST API, Terraform, CI/CD, microservices",
     ["- Migrated legacy services to Kubernetes on AWS",
      "- Automated infrastructure provisioning with Terraform",
      "- Built REST APIs for partner integrations"]),
]


def build_resume_text(name: str, years_stmt: str, skills_line: str, bullets: list[str]) -> str:
    return f"""{name}
{name.lower().replace(' ', '.')}@email.com

Summary:
Backend software engineer with {years_stmt}.

Skills:
{skills_line}

Experience:
{chr(10).join(bullets)}

Education:
B.S. Computer Science
"""


def main():
    os.makedirs(JD_DIR, exist_ok=True)
    os.makedirs(RESUME_DIR, exist_ok=True)

    jd_path = os.path.join(JD_DIR, "sample_jd.pdf")
    write_text_pdf(jd_path, JD_TEXT)
    print(f"Wrote {jd_path}")

    for name, years_stmt, skills_line, bullets in CANDIDATES:
        fname = name.lower().replace(" ", "_").replace("'", "") + ".pdf"
        path = os.path.join(RESUME_DIR, fname)
        text = build_resume_text(name, years_stmt, skills_line, bullets)
        write_text_pdf(path, text)
        print(f"Wrote {path}")

    print(f"\nGenerated 1 JD and {len(CANDIDATES)} resumes.")
    print("Run: python run_pipeline.py --jd data/jd/sample_jd.pdf --resumes data/resumes --out output")


if __name__ == "__main__":
    main()
