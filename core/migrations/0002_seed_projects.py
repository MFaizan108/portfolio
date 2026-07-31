from django.db import migrations


def seed_projects(apps, schema_editor):
    Project = apps.get_model("core", "Project")
    ProjectFeature = apps.get_model("core", "ProjectFeature")
    ProjectChallenge = apps.get_model("core", "ProjectChallenge")

    gsms = Project.objects.create(
        title="GSMS – General Store Management System",
        slug="gsms",
        badge="Featured Project",
        short_description=(
            "A comprehensive Django-based General Store Management System designed to "
            "streamline inventory, purchasing, sales, customer and supplier ledgers, "
            "financial management, expenses, income tracking, and business reporting."
        ),
        tech_stack="Python, Django, PostgreSQL, HTML, Tailwind CSS, JavaScript",
        github_url="",
        live_demo_url="",
        is_featured=True,
        order=1,
        problem=(
            "Traditional general stores often rely on manual inventory records, "
            "paper-based ledgers, and disconnected financial tracking."
        ),
        solution=(
            "GSMS replaces manual records with a single Django-powered system that "
            "centralizes inventory, purchases, sales, and customer/supplier ledgers, "
            "giving store owners accurate, real-time visibility into their business."
        ),
        objective=(
            "Build a practical, role-based store management platform that automates "
            "day-to-day retail operations — from stock and purchasing to income, "
            "expenses, and profit reporting — while keeping the workflow simple for "
            "non-technical staff."
        ),
        architecture_text="User -> Django -> PostgreSQL",
        result=(
            "GSMS gives store owners a single dashboard to manage inventory, sales, "
            "purchases, and ledgers accurately, cutting down manual bookkeeping and "
            "reducing stock and cash-handling errors."
        ),
    )
    for i, text in enumerate([
        "Product Management",
        "Inventory Management",
        "Purchase Management",
        "Sales Management",
        "Customer Khata / Ledger",
        "Supplier Ledger",
        "Expense Management",
        "Income Management",
        "Profit Calculation",
        "Cash Management",
        "Reports",
        "Low Stock Alerts",
        "Expiry Tracking",
        "Audit Logs",
        "Role-Based Access",
    ]):
        ProjectFeature.objects.create(project=gsms, text=text, order=i)

    for i, (challenge, solution) in enumerate([
        (
            "Managing customer credit transactions",
            "Implemented a dedicated ledger system to track debit, credit, and balance adjustments.",
        ),
        (
            "Keeping inventory accurate across purchases, sales, and returns",
            "Centralized stock updates through a single inventory service triggered by every purchase/sale transaction.",
        ),
        (
            "Preventing stockouts and expired inventory",
            "Added low-stock alerts and expiry tracking that flag products needing attention before they become a problem.",
        ),
    ]):
        ProjectChallenge.objects.create(project=gsms, challenge=challenge, solution=solution, order=i)


def unseed_projects(apps, schema_editor):
    Project = apps.get_model("core", "Project")
    Project.objects.filter(slug__in=["gsms"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_projects, unseed_projects),
    ]
