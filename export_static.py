"""
Static-site exporter for the GitHub Pages version of this portfolio.

Renders the *actual* Django views (home + one page per Project row) through
Django's test client — so the output is byte-for-byte what Django would have
served, not a hand-reimplementation of the templates — then post-processes
the HTML slightly (strips the CSRF token, rewires the contact form for a
backend-less host) and copies the static assets into github-pages/.

Usage (from the project root, with the project's venv active):

    python export_static.py               # from local db.sqlite3
    python export_static.py --production   # from the live production DB

Re-run this any time content changes (new projects, edited copy, new
screenshots, etc.) so github-pages/ stays in sync. Use --production after
adding/editing content through the *deployed* Django admin (Render) — that
data lives in the production database, not local db.sqlite3, and requires
PROD_DATABASE_URL to be set in .env (the external connection string from
Render/Neon). See STATIC_LIMITATIONS.md in the output folder for what does
*not* carry over to a static host and why.
"""
import argparse
import os
import re
import shutil
import stat
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "github-pages"
CONTACT_EMAIL = "muhammadfaizanurrahman.08@gmail.com"

# Loaded here (not just inside portfolio/settings.py) so --production can
# inspect PROD_DATABASE_URL before Django settings/DATABASES are configured.
load_dotenv(BASE_DIR / ".env")

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument(
    "--production",
    action="store_true",
    help="Export from the live production database instead of local db.sqlite3.",
)
_args = _parser.parse_args()

if _args.production:
    _prod_url = os.environ.get("PROD_DATABASE_URL")
    if not _prod_url:
        raise SystemExit(
            "PROD_DATABASE_URL is not set in .env — cannot export from production."
        )
    os.environ["DATABASE_URL"] = _prod_url
    print("Using the PRODUCTION database for this export (PROD_DATABASE_URL).")
else:
    print("Using the local database for this export (db.sqlite3).")

import django  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.test import Client, override_settings  # noqa: E402

from core.models import Project  # noqa: E402

CSRF_INPUT_RE = re.compile(r'\s*<input[^>]*name="csrfmiddlewaretoken"[^>]*>\n?')

CONTACT_FORM_OLD = (
    '<form class="card contact-form fade-in" method="post" action="/#contact">'
)
CONTACT_FORM_NEW = (
    '<form class="card contact-form fade-in" method="post" '
    f'action="mailto:{CONTACT_EMAIL}" enctype="text/plain" id="contactForm">'
)

CONTACT_FORM_JS = f"""

// --- Static-site contact form handoff -------------------------------------
// This site is exported to a static host with no backend. The Django
// version POSTs to a view that saves the message to the database and emails
// it via the Resend API (see core/views.py); neither is possible here, so
// submitting hands off to the visitor's own email client instead. The
// <form> keeps a native mailto: action/enctype as a no-JS fallback. See
// STATIC_LIMITATIONS.md for details.
document.addEventListener("DOMContentLoaded", function () {{
  var form = document.getElementById("contactForm");
  if (!form) return;

  var RECIPIENT = "{CONTACT_EMAIL}";

  form.addEventListener("submit", function (e) {{
    e.preventDefault();

    var name = form.querySelector('[name="name"]').value.trim();
    var email = form.querySelector('[name="email"]').value.trim();
    var subject = form.querySelector('[name="subject"]').value.trim();
    var message = form.querySelector('[name="message"]').value.trim();

    var mailSubject = "Portfolio contact: " + (subject || "New message");
    var mailBody = "From: " + name + " <" + email + ">\\n\\n" + message;

    var mailtoUrl =
      "mailto:" + RECIPIENT +
      "?subject=" + encodeURIComponent(mailSubject) +
      "&body=" + encodeURIComponent(mailBody);

    showFormMessage(
      "success",
      "Thanks for reaching out! Your email app should now open with your message pre-filled \\u2014 hit send there to reach me."
    );
    window.location.href = mailtoUrl;
  }});

  function showFormMessage(type, text) {{
    var existing = form.parentElement.querySelector(".alert");
    if (existing) existing.remove();

    var alertEl = document.createElement("div");
    alertEl.className = "alert alert-" + type;
    alertEl.textContent = text;
    form.parentElement.insertBefore(alertEl, form);
  }}
}});
"""

# Render {% static %} as plain "/static/<path>" URLs instead of whitenoise's
# hashed manifest names, so the exported HTML matches the plain filenames we
# copy into github-pages/static/ below.
STATIC_EXPORT_STORAGES = {
    "default": settings.STORAGES["default"],
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

NOT_FOUND_CONTENT = """  <div class="container" style="padding: 120px 24px; text-align: center;">
    <h1 style="font-size: 2.5rem; margin-bottom: 16px;">404</h1>
    <p class="hero-desc" style="margin: 0 auto 32px; max-width: 480px;">
      This page doesn't exist. It may have moved, or the link may be out of date.
    </p>
    <a href="/" class="btn btn-primary">Back to Home</a>
  </div>
"""

STATIC_LIMITATIONS_TEMPLATE = """# Static Export Limitations

This folder (`github-pages/`) is a static export of the Django portfolio,
generated by [`export_static.py`](../export_static.py) for hosting on
GitHub Pages at `https://MFaizan108.github.io/`. GitHub Pages serves plain
files only — there is no Python/Django process, no database, and no way to
run server-side code. The items below describe what changed to make that
possible, and what genuinely can't be replicated on a static host.

## Contact form

**Django version:** `POST`s to `core.views.home`, which validates the data
with `ContactForm`, saves it as a `ContactMessage` row in the database, and
emails a notification via the Resend HTTP API (`_notify_contact_message`).
On success it redirects back to `/#contact` and shows a flash message via
Django's `messages` framework.

**Static version:** there is no server to receive the `POST`, save the
message, or send the email. The form now hands off to the visitor's own
email client instead:

- The `<form>` keeps a native `action="mailto:{contact_email}"` /
  `enctype="text/plain"` as a no-JS fallback.
- `static/core/js/main.js` intercepts the submit event, builds a
  `mailto:` link pre-filled with the subject and message body from the
  form fields, and navigates to it (`window.location.href = mailtoUrl`).
- A confirmation banner (reusing the existing `.alert.alert-success` style
  that Django's messages framework used) is shown immediately after
  submission.

This means:
- The message is **not stored anywhere** — there is no admin-visible
  record of a submission, and no way to know whether the visitor actually
  sent the resulting email.
- It requires the visitor to have a configured email client (or a browser
  `mailto:` handler). There is no server-side validation, spam filtering,
  or CSRF protection — none of which are meaningful without a backend to
  protect in the first place.
- If you need real form submissions with server-side storage/notification
  on a static host, that requires wiring up a third-party form backend
  (e.g. Formspree, Getform) — deliberately **not** done here since it would
  require creating an account/API key on your behalf, which this export
  does not invent.

## Django admin (`/admin/`)

Not available — there is no server to run it against. The static site is a
**snapshot** of whatever was in the database at export time. To publish new
projects, screenshots, or copy edits made via `/admin/`, re-run
`python export_static.py` and re-deploy `github-pages/`.

## Project images (thumbnails & screenshots)

These already work unmodified: this project stores media on Cloudinary
(`CLOUDINARY_URL` is configured), so `Project.thumbnail.url` and
`ProjectScreenshot.image.url` are already absolute
`https://res.cloudinary.com/...` URLs baked into the rendered HTML — they do
not depend on Django or `/media/` at all, so they keep working from GitHub
Pages exactly as they do today. If this project ever switches to local
filesystem storage for media (no `CLOUDINARY_URL` set), those URLs would
become Django-only `/media/...` paths and this exporter would need to be
extended to copy `media/` into the output and rewrite those URLs.

## Django messages framework

The one-off "Thanks for reaching out..." / "Please fix the errors below..."
flash messages Django shows after a form `POST` don't exist statically
(nothing ever posts to Django). The contact-form success banner described
above is a client-side equivalent shown after the `mailto:` handoff, styled
identically (`.alert.alert-success`) but not a real server confirmation.

## URL structure

Django's `{{% url %}}` template tag was resolved to real paths at export
time by actually rendering the Django views (via `django.test.Client`), so
internal links (`/`, `/#contact`, `/projects/<slug>/`, etc.) are already
correct hard-coded paths in the exported HTML. If routes in `core/urls.py`
ever change, re-run the exporter — don't hand-edit the generated HTML.

## Everything else

Every other piece of this page — layout, CSS, animations (scroll fade-ins,
sticky navbar, mobile hamburger menu, active-link highlighting), skills,
education, resume download, social links, GSMS case study — is rendered
directly from the live Django templates/data and copied through unchanged.
"""


def _force_remove(func, path, exc_info) -> None:
    """shutil.rmtree onexc handler: OneDrive-synced folders on Windows often
    get marked read-only, which makes rmdir/unlink fail with PermissionError.
    Clear the attribute and retry once."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clean_output_dir() -> None:
    """Wipe everything in OUTPUT_DIR except .git — the exported folder is
    often git-initialized on its own (pushed straight to a GitHub Pages
    repo), and blowing away its .git would destroy that history/remote."""
    if OUTPUT_DIR.exists():
        for entry in OUTPUT_DIR.iterdir():
            if entry.name == ".git":
                continue
            if entry.is_dir():
                shutil.rmtree(entry, onexc=_force_remove)
            else:
                entry.unlink()
    else:
        OUTPUT_DIR.mkdir(parents=True)


def render_page(client: Client, url: str) -> str:
    response = client.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"Unexpected status {response.status_code} rendering {url!r}")
    return response.content.decode("utf-8")


def write_page(relative_path: str, html: str) -> None:
    out_path = OUTPUT_DIR / relative_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path.relative_to(BASE_DIR)}")


def render_all_pages() -> tuple[str, list[str]]:
    client = Client()
    with override_settings(
        STORAGES=STATIC_EXPORT_STORAGES,
        ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "testserver"],
    ):
        print("Rendering home page (/)...")
        home_html = render_page(client, "/")
        home_html = CSRF_INPUT_RE.sub("", home_html)
        assert CONTACT_FORM_OLD in home_html, "contact form markup changed — update export_static.py"
        home_html = home_html.replace(CONTACT_FORM_OLD, CONTACT_FORM_NEW)
        write_page("index.html", home_html)

        slugs = list(Project.objects.order_by("order", "title").values_list("slug", flat=True))
        for slug in slugs:
            print(f"Rendering project detail (/projects/{slug}/)...")
            html = render_page(client, f"/projects/{slug}/")
            html = CSRF_INPUT_RE.sub("", html)
            write_page(f"projects/{slug}/index.html", html)

    return home_html, slugs


def copy_static_assets() -> None:
    src = BASE_DIR / "core" / "static" / "core"
    dst = OUTPUT_DIR / "static" / "core"
    shutil.copytree(src, dst)
    print(f"  copied {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}")

    js_path = dst / "js" / "main.js"
    js_path.write_text(js_path.read_text(encoding="utf-8") + CONTACT_FORM_JS, encoding="utf-8")
    print(f"  patched {js_path.relative_to(BASE_DIR)} with contact-form handoff")


def generate_404(home_html: str) -> None:
    match = re.search(r"<main>.*?</main>", home_html, flags=re.DOTALL)
    if not match:
        raise RuntimeError("Could not locate <main>...</main> in rendered home page")

    not_found_html = home_html.replace(
        match.group(0),
        "<main>\n" + NOT_FOUND_CONTENT + "</main>",
    )
    not_found_html = not_found_html.replace(
        "<title>Muhammad Faizan Ur Rahman — Backend Developer & AI Enthusiast</title>",
        "<title>Page Not Found — Muhammad Faizan Ur Rahman</title>",
    )
    write_page("404.html", not_found_html)


def generate_limitations_doc() -> None:
    out_path = OUTPUT_DIR / "STATIC_LIMITATIONS.md"
    out_path.write_text(
        STATIC_LIMITATIONS_TEMPLATE.format(contact_email=CONTACT_EMAIL),
        encoding="utf-8",
    )
    print(f"  wrote {out_path.relative_to(BASE_DIR)}")


def generate_nojekyll() -> None:
    """GitHub Pages runs Jekyll by default, which parses *.md files as Liquid
    templates — Liquid chokes on documentation text like `{% url %}` in
    STATIC_LIMITATIONS.md (not a Liquid tag) and fails the whole build. This
    file tells GitHub Pages to skip Jekyll entirely and serve the export as
    plain static files, which is what it actually is."""
    out_path = OUTPUT_DIR / ".nojekyll"
    out_path.write_text("", encoding="utf-8")
    print(f"  wrote {out_path.relative_to(BASE_DIR)}")


def verify_output() -> None:
    bad_patterns = ["{%", "{{", "127.0.0.1", "localhost", "manage.py"]
    problems = []
    for path in OUTPUT_DIR.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for pat in bad_patterns:
            if pat in text:
                problems.append(f"{path.relative_to(BASE_DIR)} contains {pat!r}")
    if not (OUTPUT_DIR / "index.html").exists():
        problems.append("github-pages/index.html is missing")
    if problems:
        raise RuntimeError("Verification failed:\n" + "\n".join(problems))
    print("Verification passed: no Django template syntax or localhost references found.")


def main() -> None:
    print(f"Exporting static site to {OUTPUT_DIR}...")
    clean_output_dir()
    home_html, slugs = render_all_pages()
    copy_static_assets()
    generate_404(home_html)
    generate_limitations_doc()
    generate_nojekyll()
    verify_output()
    print(f"Done. {1 + len(slugs)} page(s) exported: index.html, "
          + ", ".join(f"projects/{s}/index.html" for s in slugs))


if __name__ == "__main__":
    main()
