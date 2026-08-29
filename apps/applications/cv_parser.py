from pathlib import Path
import re
import zipfile


def validate_cv_content(uploaded_file):
    uploaded_file.seek(0)
    signature = uploaded_file.read(8)
    uploaded_file.seek(0)
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".pdf" and not signature.startswith(b"%PDF-"):
        raise ValueError("Dosya geçerli bir PDF değil.")
    if suffix == ".docx":
        if not signature.startswith(b"PK") or not zipfile.is_zipfile(uploaded_file):
            raise ValueError("Dosya geçerli bir DOCX değil.")
        uploaded_file.seek(0)
        with zipfile.ZipFile(uploaded_file) as archive:
            if "word/document.xml" not in archive.namelist():
                raise ValueError("Dosya geçerli bir DOCX değil.")
        uploaded_file.seek(0)


def extract_cv_data(text):
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    urls = re.findall(r"https?://[^\s]+", text, flags=re.IGNORECASE)
    lower = text.lower()
    known_skills = [skill for skill in ("python", "django", "java", "spring", "docker", "sql", "aws", "react", "flutter", "kubernetes") if skill in lower]
    sections = {}
    for name, aliases in {
        "education": ("education", "eğitim", "university", "üniversite"),
        "experience": ("experience", "deneyim", "work history", "iş deneyimi"),
        "certifications": ("certification", "sertifika"),
        "languages": ("languages", "diller", "dil"),
    }.items():
        sections[name] = [line.strip() for line in text.splitlines() if any(alias in line.lower() for alias in aliases)]
    return {
        "email": email.group(0) if email else "",
        "phone": phone.group(0).strip() if phone else "",
        "github_url": next((url.rstrip(".,)") for url in urls if "github.com" in url.lower()), ""),
        "linkedin_url": next((url.rstrip(".,)") for url in urls if "linkedin.com" in url.lower()), ""),
        "skills": known_skills,
        **sections,
    }


def parse_cv_file(uploaded_file):
    validate_cv_content(uploaded_file)
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader

        try:
            reader = PdfReader(uploaded_file)
            if reader.is_encrypted:
                raise ValueError("Şifreli PDF dosyaları desteklenmez.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("PDF dosyası okunamadı.") from exc
        return text, "pdf", extract_cv_data(text)
    if suffix == ".docx":
        from docx import Document

        try:
            document = Document(uploaded_file)
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            raise ValueError("DOCX dosyası okunamadı.") from exc
        return text, "docx", extract_cv_data(text)
    raise ValueError("Yalnızca PDF veya DOCX dosyaları desteklenir.")