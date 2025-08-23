#!/usr/bin/env python3
"""
Multi-provider mock server for testing the SA Query Language Shell.

This server starts 5 different providers on different ports:
- HR Database (port 5042) - 200+ employees with manager relationships
- CRM System (port 5043) - 150+ customers with assigned employees
- Inventory System (port 5044) - 100+ products with creator references
- Analytics Engine (port 5045) - 80+ datasets with owner references
- Document Store (port 5046) - 120+ documents with author/creator references

Some objects have overlapping IDs across providers to test merging capabilities.
"""

from flask import Flask, jsonify
import json
import threading
import time
import random
from datetime import datetime, timedelta

# Generate realistic data with cross-references
def generate_hr_data():
    """Generate 200+ employees with manager relationships."""
    employees = []
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "Legal", "Product"]
    skills_list = [
        "Python", "JavaScript", "React", "Node.js", "Java", "C++", "Go", "Rust",
        "SQL", "MongoDB", "AWS", "Docker", "Kubernetes", "Machine Learning",
        "SEO", "Content Marketing", "Social Media", "Analytics", "Google Ads",
        "Negotiation", "CRM", "Lead Generation", "Account Management",
        "Recruitment", "Employee Relations", "Performance Management",
        "Financial Planning", "Budgeting", "Risk Management", "Compliance"
    ]
    
    # Create CEO (no manager)
    ceo = {
        "__types__": ["person", "employee", "executive"],
        "__id__": "emp_001",
        "__source__": "hr_database",
        "name": "Sarah Johnson",
        "title": "Chief Executive Officer",
        "department": "Executive",
        "salary": 250000,
        "hire_date": "2020-01-01",
        "manager_id": None,
        "skills": ["Leadership", "Strategy", "Business Development"],
        "level": "C-Suite"
    }
    employees.append(ceo)
    
    # Create VPs (report to CEO)
    vp_titles = ["VP Engineering", "VP Marketing", "VP Sales", "VP Operations"]
    for i, title in enumerate(vp_titles):
        vp = {
            "__types__": ["person", "employee", "executive"],
            "__id__": f"emp_{i+2:03d}",
            "__source__": "hr_database",
            "name": f"VP {title.split()[1]}",
            "title": title,
            "department": title.split()[1],
            "salary": 180000,
            "hire_date": "2020-06-01",
            "manager_id": "emp_001",
            "skills": ["Leadership", "Management", title.split()[1]],
            "level": "VP"
        }
        employees.append(vp)
    
    # Create managers (report to VPs)
    manager_count = 0
    for dept in departments:
        for j in range(3):  # 3 managers per department
            manager_count += 1
            manager = {
                "__types__": ["person", "employee", "manager"],
                "__id__": f"emp_{manager_count+5:03d}",
                "__source__": "hr_database",
                "name": f"Manager {j+1} {dept}",
                "title": f"{dept} Manager",
                "department": dept,
                "salary": 120000,
                "hire_date": "2021-03-01",
                "manager_id": f"emp_{departments.index(dept)+2:03d}",
                "skills": random.sample(skills_list, 4),
                "level": "Manager"
            }
            employees.append(manager)
    
    # Create individual contributors (report to managers)
    ic_count = manager_count + 5
    for dept in departments:
        for k in range(20):  # 20 ICs per department
            ic_count += 1
            manager_id = f"emp_{departments.index(dept)+5:03d}"
            ic = {
                "__types__": ["person", "employee", "individual_contributor"],
                "__id__": f"emp_{ic_count:03d}",
                "__source__": "hr_database",
                "name": f"Employee {k+1} {dept}",
                "title": f"{dept} Specialist",
                "department": dept,
                "salary": random.randint(60000, 100000),
                "hire_date": (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime("%Y-%m-%d"),
                "manager_id": manager_id,
                "skills": random.sample(skills_list, random.randint(2, 5)),
                "level": "Individual Contributor"
            }
            employees.append(ic)
    
    return employees

def generate_crm_data():
    """Generate 150+ customers with assigned employee references."""
    customers = []
    companies = [
        "Acme Corp", "TechStart Inc", "Global Solutions", "Innovation Labs",
        "Data Dynamics", "Cloud Systems", "Digital Ventures", "Future Tech",
        "Smart Solutions", "NextGen Corp", "Elite Services", "Prime Partners",
        "Advanced Systems", "Creative Solutions", "Strategic Partners"
    ]
    statuses = ["active", "prospect", "inactive", "churned", "qualified"]
    
    # Get employee IDs from HR data for assignments
    hr_employees = [emp["__id__"] for emp in generate_hr_data() if emp["department"] in ["Sales", "Account Management"]]
    
    for i in range(150):
        customer = {
            "__types__": ["person", "customer"],
            "__id__": f"cust_{i+1:03d}",
            "__source__": "crm_system",
            "name": f"Customer {i+1}",
            "company": random.choice(companies),
            "email": f"customer{i+1}@{random.choice(companies).lower().replace(' ', '')}.com",
            "status": random.choice(statuses),
            "last_contact": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "value": random.randint(10000, 500000),
            "assigned_employee_id": random.choice(hr_employees),
            "industry": random.choice(["Technology", "Healthcare", "Finance", "Retail", "Manufacturing", "Education"]),
            "lead_source": random.choice(["Website", "Referral", "Cold Call", "Trade Show", "Social Media"])
        }
        customers.append(customer)
    
    return customers

def generate_inventory_data():
    """Generate 100+ products with creator references."""
    products = []
    categories = ["Software", "Hardware", "Service", "Consulting", "Training", "Support"]
    software_products = ["SA Framework", "Data Analyzer", "Cloud Manager", "Security Suite", "API Gateway"]
    hardware_products = ["Quantum Computer", "AI Server", "Network Switch", "Storage Array", "IoT Device"]
    
    # Get employee IDs from HR data for creators
    hr_employees = [emp["__id__"] for emp in generate_hr_data() if emp["department"] in ["Engineering", "Product"]]
    
    for i in range(100):
        if i < 30:  # Software products
            product = {
                "__types__": ["product", "software"],
                "__id__": f"prod_{i+1:03d}",
                "__source__": "inventory_system",
                "name": random.choice(software_products) + f" v{random.randint(1,5)}.{random.randint(0,9)}",
                "category": "Software",
                "version": f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}",
                "price": random.randint(50, 500),
                "stock": random.randint(100, 10000),
                "tags": random.sample(["AI", "Cloud", "Security", "Analytics", "API", "Mobile"], 3),
                "creator_employee_id": random.choice(hr_employees),
                "release_date": (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime("%Y-%m-%d"),
                "platforms": random.sample(["Windows", "Mac", "Linux", "Web", "Mobile"], random.randint(1, 3))
            }
        elif i < 60:  # Hardware products
            product = {
                "__types__": ["product", "hardware"],
                "__id__": f"prod_{i+1:03d}",
                "__source__": "inventory_system",
                "name": random.choice(hardware_products) + f" {random.choice(['Pro', 'Enterprise', 'Standard'])}",
                "category": "Hardware",
                "specs": f"{random.randint(100, 10000)} {random.choice(['qubits', 'cores', 'GB RAM', 'TB storage'])}",
                "price": random.randint(1000, 100000),
                "stock": random.randint(1, 100),
                "tags": random.sample(["High-Performance", "Enterprise", "Research", "Cloud-Native"], 2),
                "creator_employee_id": random.choice(hr_employees),
                "warranty_years": random.randint(1, 5),
                "dimensions": f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(10, 100)}cm"
            }
        else:  # Services
            service_types = ["Data Consulting", "Cloud Migration", "Security Audit", "Performance Optimization", "Training"]
            product = {
                "__types__": ["product", "service"],
                "__id__": f"prod_{i+1:03d}",
                "__source__": "inventory_system",
                "name": random.choice(service_types),
                "category": "Professional Services",
                "hourly_rate": random.randint(100, 300),
                "availability": random.choice(["immediate", "1 week", "2 weeks", "1 month"]),
                "tags": random.sample(["Consulting", "Data", "Strategy", "Implementation", "Support"], 3),
                "creator_employee_id": random.choice(hr_employees),
                "duration_hours": random.randint(8, 160),
                "certification_required": random.choice([True, False])
            }
        products.append(product)
    
    return products

def generate_analytics_data():
    """Generate 80+ datasets with owner references."""
    datasets = []
    schema_types = ["financial_transactions", "user_interactions", "sales_data", "customer_behavior", 
                   "product_performance", "employee_metrics", "system_logs", "marketing_campaigns"]
    
    # Get employee IDs from HR data for owners
    hr_employees = [emp["__id__"] for emp in generate_hr_data() if emp["department"] in ["Engineering", "Analytics", "Finance"]]
    
    for i in range(80):
        dataset = {
            "__types__": ["dataset", random.choice(["financial", "user_behavior", "operational", "marketing"])],
            "__id__": f"data_{i+1:03d}",
            "__source__": "analytics_engine",
            "name": f"{random.choice(['Q1', 'Q2', 'Q3', 'Q4'])} {random.randint(2020, 2024)} {random.choice(schema_types).replace('_', ' ').title()}",
            "size_gb": round(random.uniform(0.1, 50.0), 1),
            "records": random.randint(1000, 10000000),
            "last_updated": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "schema": random.choice(schema_types),
            "owner_employee_id": random.choice(hr_employees),
            "refresh_frequency": random.choice(["daily", "weekly", "monthly", "quarterly"]),
            "retention_days": random.randint(90, 2555),
            "access_level": random.choice(["public", "internal", "restricted", "confidential"])
        }
        datasets.append(dataset)
    
    return datasets

def generate_document_data():
    """Generate 120+ documents with author/creator references."""
    documents = []
    doc_types = ["contract", "report", "proposal", "policy", "procedure", "manual", "presentation", "memo"]
    statuses = ["draft", "review", "approved", "published", "archived"]
    
    # Get employee IDs from HR data for authors
    hr_employees = [emp["__id__"] for emp in generate_hr_data()]
    
    for i in range(120):
        doc_type = random.choice(doc_types)
        if doc_type == "contract":
            document = {
                "__types__": ["document", "contract"],
                "__id__": f"doc_{i+1:03d}",
                "__source__": "document_store",
                "title": f"{random.choice(['Service', 'Employment', 'Vendor', 'Partnership'])} Agreement",
                "type": "contract",
                "size_mb": round(random.uniform(0.5, 10.0), 1),
                "created": (datetime.now() - timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d"),
                "status": random.choice(statuses),
                "parties": [f"Company {chr(65 + random.randint(0, 25))}", f"Company {chr(65 + random.randint(0, 25))}"],
                "author_employee_id": random.choice(hr_employees),
                "contract_value": random.randint(10000, 1000000),
                "expiry_date": (datetime.now() + timedelta(days=random.randint(30, 3650))).strftime("%Y-%m-%d")
            }
        elif doc_type == "report":
            document = {
                "__types__": ["document", "report"],
                "__id__": f"doc_{i+1:03d}",
                "__source__": "document_store",
                "title": f"{random.choice(['Annual', 'Quarterly', 'Monthly', 'Weekly'])} {random.choice(['Performance', 'Financial', 'Operational', 'Marketing'])} Report",
                "type": "report",
                "size_mb": round(random.uniform(1.0, 20.0), 1),
                "created": (datetime.now() - timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d"),
                "status": random.choice(statuses),
                "pages": random.randint(5, 100),
                "author_employee_id": random.choice(hr_employees),
                "report_period": f"{random.randint(2020, 2024)}-{random.randint(1, 12):02d}",
                "executive_summary": random.choice([True, False])
            }
        else:
            document = {
                "__types__": ["document", doc_type],
                "__id__": f"doc_{i+1:03d}",
                "__source__": "document_store",
                "title": f"{doc_type.title()} - {random.choice(['Project', 'Process', 'Policy', 'Training'])} {i+1}",
                "type": doc_type,
                "size_mb": round(random.uniform(0.1, 15.0), 1),
                "created": (datetime.now() - timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d"),
                "status": random.choice(statuses),
                "author_employee_id": random.choice(hr_employees),
                "reviewer_employee_id": random.choice(hr_employees),
                "version": f"{random.randint(1, 10)}.{random.randint(0, 9)}",
                "tags": random.sample(["Important", "Confidential", "Draft", "Final", "Archived"], 2)
            }
        documents.append(document)
    
    return documents

def create_overlapping_objects():
    """Create objects that appear in multiple providers to test merging capabilities."""
    
    # Create some overlapping employee objects (HR + CRM perspectives)
    overlapping_employees = [
        {
            "__types__": ["person", "employee", "sales_representative"],
            "__id__": "emp_overlap_001",
            "__source__": "hr_database",
            "name": "Alex Chen",
            "title": "Senior Sales Representative",
            "department": "Sales",
            "salary": 85000,
            "hire_date": "2021-08-15",
            "manager_id": "emp_002",
            "skills": ["Sales", "CRM", "Negotiation", "Account Management"],
            "level": "Senior",
            "performance_rating": 4.2
        },
        {
            "__types__": ["person", "employee", "sales_representative"],
            "__id__": "emp_overlap_001",
            "__source__": "crm_system",
            "name": "Alex Chen",
            "title": "Senior Sales Representative",
            "department": "Sales",
            "hire_date": "2021-08-15",
            "manager_id": "emp_002",
            "skills": ["Sales", "CRM", "Negotiation", "Account Management"],
            "level": "Senior",
            "performance_rating": 4.2,
            "crm_access_level": "full",
            "assigned_customers": 23,
            "sales_quota": 1200000,
            "current_performance": "exceeding"
        },
        {
            "__types__": ["person", "employee", "engineer"],
            "__id__": "emp_overlap_002",
            "__source__": "hr_database",
            "name": "Maria Rodriguez",
            "title": "Software Engineer",
            "department": "Engineering",
            "salary": 95000,
            "hire_date": "2022-01-10",
            "manager_id": "emp_005",
            "skills": ["Python", "JavaScript", "React", "AWS"],
            "level": "Mid-level"
        },
        {
            "__types__": ["person", "employee", "engineer"],
            "__id__": "emp_overlap_002",
            "__source__": "inventory_system",
            "name": "Maria Rodriguez",
            "title": "Software Engineer",
            "department": "Engineering",
            "hire_date": "2022-01-10",
            "manager_id": "emp_005",
            "skills": ["Python", "JavaScript", "React", "AWS"],
            "level": "Mid-level",
            "products_created": 8,
            "technical_lead": False,
            "code_review_rating": 4.5
        },
        {
            "__types__": ["person", "employee", "analyst"],
            "__id__": "emp_overlap_003",
            "__source__": "hr_database",
            "name": "David Kim",
            "title": "Data Analyst",
            "department": "Analytics",
            "salary": 78000,
            "hire_date": "2022-03-20",
            "manager_id": "emp_008",
            "skills": ["SQL", "Python", "Tableau", "Statistics"],
            "level": "Junior"
        },
        {
            "__types__": ["person", "employee", "analyst"],
            "__id__": "emp_overlap_003",
            "__source__": "analytics_engine",
            "name": "David Kim",
            "title": "Data Analyst",
            "department": "Analytics",
            "hire_date": "2022-03-20",
            "manager_id": "emp_008",
            "skills": ["SQL", "Python", "Tableau", "Statistics"],
            "level": "Junior",
            "datasets_owned": 12,
            "data_access_level": "internal",
            "last_analysis": "2024-01-15"
        },
        {
            "__types__": ["person", "employee", "analyst"],
            "__id__": "emp_overlap_003",
            "__source__": "document_store",
            "name": "David Kim",
            "title": "Data Analyst",
            "department": "Analytics",
            "hire_date": "2022-03-20",
            "manager_id": "emp_008",
            "skills": ["SQL", "Python", "Tableau", "Statistics"],
            "level": "Junior",
            "documents_created": 15,
            "document_approval_rate": 0.95,
            "last_document": "2024-01-20"
        }
    ]
    
    # Create some overlapping product objects (Inventory + Analytics perspectives)
    overlapping_products = [
        {
            "__types__": ["product", "software"],
            "__id__": "prod_overlap_001",
            "__source__": "inventory_system",
            "name": "SA Framework v2.1",
            "category": "Software",
            "version": "2.1.0",
            "price": 299,
            "stock": 1000,
            "tags": ["AI", "Cloud", "Analytics"],
            "creator_employee_id": "emp_overlap_002",
            "release_date": "2023-11-15",
            "platforms": ["Windows", "Mac", "Linux", "Web"]
        },
        {
            "__types__": ["product", "software"],
            "__id__": "prod_overlap_001",
            "__source__": "analytics_engine",
            "name": "SA Framework v2.1",
            "category": "Software",
            "version": "2.1.0",
            "price": 299,
            "stock": 1000,
            "tags": ["AI", "Cloud", "Analytics"],
            "creator_employee_id": "emp_overlap_002",
            "release_date": "2023-11-15",
            "platforms": ["Windows", "Mac", "Linux", "Web"],
            "usage_metrics": {
                "active_users": 1250,
                "daily_usage_hours": 8.5,
                "error_rate": 0.02
            },
            "performance_data": {
                "avg_response_time": 120,
                "uptime_percentage": 99.8
            }
        }
    ]
    
    # Create some overlapping customer objects (CRM + Analytics perspectives)
    overlapping_customers = [
        {
            "__types__": ["person", "customer"],
            "__id__": "cust_overlap_001",
            "__source__": "crm_system",
            "name": "Enterprise Customer Alpha",
            "company": "Alpha Corp",
            "email": "contact@alphacorp.com",
            "status": "active",
            "last_contact": "2024-01-10",
            "value": 250000,
            "assigned_employee_id": "emp_overlap_001",
            "industry": "Technology",
            "lead_source": "Website"
        },
        {
            "__types__": ["person", "customer"],
            "__id__": "cust_overlap_001",
            "__source__": "analytics_engine",
            "name": "Enterprise Customer Alpha",
            "company": "Alpha Corp",
            "email": "contact@alphacorp.com",
            "status": "active",
            "last_contact": "2024-01-10",
            "value": 250000,
            "assigned_employee_id": "emp_overlap_001",
            "industry": "Technology",
            "lead_source": "Website",
            "usage_patterns": {
                "login_frequency": "daily",
                "feature_usage": ["analytics", "reporting", "export"],
                "session_duration": 45
            },
            "customer_satisfaction": 4.7
        }
    ]
    
    # Create some overlapping document objects (Document Store + Analytics perspectives)
    overlapping_documents = [
        {
            "__types__": ["document", "report"],
            "__id__": "doc_overlap_001",
            "__source__": "document_store",
            "title": "Q4 2023 Financial Performance Report",
            "type": "report",
            "size_mb": 8.5,
            "created": "2024-01-05",
            "status": "published",
            "pages": 45,
            "author_employee_id": "emp_overlap_003",
            "report_period": "2023-Q4",
            "executive_summary": True
        },
        {
            "__types__": ["document", "report"],
            "__id__": "doc_overlap_001",
            "__source__": "analytics_engine",
            "title": "Q4 2023 Financial Performance Report",
            "type": "report",
            "size_mb": 8.5,
            "created": "2024-01-05",
            "status": "published",
            "pages": 45,
            "author_employee_id": "emp_overlap_003",
            "report_period": "2023-Q4",
            "executive_summary": True,
            "data_sources": ["financial_system", "crm_system", "hr_database"],
            "generated_charts": 12,
            "view_count": 156,
            "download_count": 23
        }
    ]
    
    return {
        "overlapping_employees": overlapping_employees,
        "overlapping_products": overlapping_products,
        "overlapping_customers": overlapping_customers,
        "overlapping_documents": overlapping_documents
    }

def verify_unique_ids(provider_data):
    """Verify that each provider has unique IDs within itself."""
    for provider_name, objects in provider_data.items():
        ids = [obj["__id__"] for obj in objects]
        unique_ids = set(ids)
        if len(ids) != len(unique_ids):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Provider {provider_name} has duplicate IDs: {duplicates}")
        print(f"✓ {provider_name}: {len(objects)} objects, all IDs unique")

# Provider configurations with generated data and overlapping objects
def get_provider_data():
    """Get data for each provider with some overlapping objects."""
    base_data = {
        "hr_database": generate_hr_data(),
        "crm_system": generate_crm_data(),
        "inventory_system": generate_inventory_data(),
        "analytics_engine": generate_analytics_data(),
        "document_store": generate_document_data()
    }
    
    overlapping = create_overlapping_objects()
    
    # Add overlapping objects to appropriate providers (ensuring no duplicates within each provider)
    # HR Database gets its overlapping employees
    hr_overlaps = [obj for obj in overlapping["overlapping_employees"] if obj["__source__"] == "hr_database"]
    base_data["hr_database"].extend(hr_overlaps)
    
    # CRM System gets its overlapping employees and customers
    crm_overlaps = [obj for obj in overlapping["overlapping_employees"] if obj["__source__"] == "crm_system"]
    crm_overlaps.extend([obj for obj in overlapping["overlapping_customers"] if obj["__source__"] == "crm_system"])
    base_data["crm_system"].extend(crm_overlaps)
    
    # Inventory System gets its overlapping employees and products
    inventory_overlaps = [obj for obj in overlapping["overlapping_employees"] if obj["__source__"] == "inventory_system"]
    inventory_overlaps.extend([obj for obj in overlapping["overlapping_products"] if obj["__source__"] == "inventory_system"])
    base_data["inventory_system"].extend(inventory_overlaps)
    
    # Analytics Engine gets its overlapping employees, products, customers, and documents
    analytics_overlaps = [obj for obj in overlapping["overlapping_employees"] if obj["__source__"] == "analytics_engine"]
    analytics_overlaps.extend([obj for obj in overlapping["overlapping_products"] if obj["__source__"] == "analytics_engine"])
    analytics_overlaps.extend([obj for obj in overlapping["overlapping_customers"] if obj["__source__"] == "analytics_engine"])
    analytics_overlaps.extend([obj for obj in overlapping["overlapping_documents"] if obj["__source__"] == "analytics_engine"])
    base_data["analytics_engine"].extend(analytics_overlaps)
    
    # Document Store gets its overlapping employees and documents
    document_overlaps = [obj for obj in overlapping["overlapping_employees"] if obj["__source__"] == "document_store"]
    document_overlaps.extend([obj for obj in overlapping["overlapping_documents"] if obj["__source__"] == "document_store"])
    base_data["document_store"].extend(document_overlaps)
    
    # Verify uniqueness within each provider
    verify_unique_ids(base_data)
    
    return base_data

PROVIDERS = [
    {
        "name": "HR Database",
        "port": 5042,
        "mode": "ALL_AT_ONCE",
        "data": get_provider_data()["hr_database"],
        "description": "Employee and HR information with manager relationships (includes overlapping objects)"
    },
    {
        "name": "CRM System", 
        "port": 5043,
        "mode": "ALL_AT_ONCE",
        "data": get_provider_data()["crm_system"],
        "description": "Customer relationship management with employee assignments (includes overlapping objects)"
    },
    {
        "name": "Inventory System",
        "port": 5044, 
        "mode": "ALL_AT_ONCE",
        "data": get_provider_data()["inventory_system"],
        "description": "Product and service catalog with creator references (includes overlapping objects)"
    },
    {
        "name": "Analytics Engine",
        "port": 5045,
        "mode": "ALL_AT_ONCE", 
        "data": get_provider_data()["analytics_engine"],
        "description": "Data analytics and datasets with owner references (includes overlapping objects)"
    },
    {
        "name": "Document Store",
        "port": 5046,
        "mode": "ALL_AT_ONCE",
        "data": get_provider_data()["document_store"],
        "description": "Document management system with author references (includes overlapping objects)"
    }
]


def create_provider_app(provider_config):
    """Create a Flask app for a specific provider."""
    app = Flask(f"provider_{provider_config['port']}")
    
    @app.route('/hello')
    def hello():
        """Provider information endpoint."""
        return jsonify({
            "name": provider_config["name"],
            "mode": provider_config["mode"],
            "description": provider_config["description"],
            "version": "1.0.0"
        })
    
    @app.route('/all_data')
    def all_data():
        """Data endpoint that returns all SAObjects."""
        return jsonify(provider_config["data"])
    
    @app.route('/')
    def root():
        """Root endpoint with basic info."""
        return jsonify({
            "service": provider_config["name"],
            "endpoints": {
                "/hello": "Provider information",
                "/all_data": "All SAObject data"
            },
            "status": "running"
        })
    
    return app


def start_provider(provider_config):
    """Start a provider server in a separate thread."""
    app = create_provider_app(provider_config)
    port = provider_config["port"]
    
    def run_server():
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Give the server a moment to start
    time.sleep(0.5)
    print(f"  ✓ Started {provider_config['name']} on port {port} ({len(provider_config['data'])} objects)")
    
    return thread


if __name__ == '__main__':
    print("🚀 Starting Multi-Provider Mock Server...")
    print("=" * 60)
    print("This will start 5 different providers on different ports:")
    print()
    print("📋 Note: Some objects have overlapping IDs across providers to test merging capabilities.")
    print("   Each provider maintains unique IDs within itself.")
    print()
    
    # Start all providers
    threads = []
    total_objects = 0
    for provider in PROVIDERS:
        print(f"Starting {provider['name']}...")
        thread = start_provider(provider)
        threads.append(thread)
        total_objects += len(provider['data'])
    
    print()
    print("✅ All providers are now running!")
    print("=" * 60)
    print(f"📊 Total objects across all providers: {total_objects}")
    print("Provider URLs for providers.txt:")
    for provider in PROVIDERS:
        print(f"  http://localhost:{provider['port']} - {provider['name']} ({len(provider['data'])} objects)")
    print()
    print("🔄 Overlapping objects for testing:")
    print("   - emp_overlap_001: HR Database + CRM System")
    print("   - emp_overlap_002: HR Database + Inventory System") 
    print("   - emp_overlap_003: HR Database + Analytics Engine + Document Store")
    print("   - prod_overlap_001: Inventory System + Analytics Engine")
    print("   - cust_overlap_001: CRM System + Analytics Engine")
    print("   - doc_overlap_001: Document Store + Analytics Engine")
    print()
    print("Press Ctrl+C to stop all providers")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all providers...")
        print("Goodbye!") 