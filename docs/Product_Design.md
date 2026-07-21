# Product Design Document

**Project:** SNAP Analytics Platform  
**Version:** 1.0  
**Author:** Saki Chen  
**Status:** Draft

---

# 1. Why This Project Exists

The SNAP Analytics Platform is a portfolio project designed to simulate the responsibilities of an Analytics Engineer in a real business environment.

Rather than focusing on dashboards alone, this project demonstrates the complete thought process behind designing an analytics product—from understanding a business problem to building trusted analytics that support decision-making.

---

# 2. Business Background

Public assistance programs generate large amounts of operational data across counties and reporting periods.

Although the data is publicly available, answering business questions consistently requires significant manual work because of inconsistent definitions, data quality issues, and fragmented reporting.

The platform is designed to demonstrate how these challenges can be solved using modern analytics engineering practices.

---

# 3. Business Problem

The platform aims to address questions such as:

- How many applications are received each month?
- Which counties experience the highest demand?
- Are applications processed within required timelines?
- How do application and redetermination trends change over time?
- Which operational metrics should decision makers monitor?

Current reporting often requires manual preparation and repeated business logic, making results difficult to trust and maintain.

---

# 4. Business Workflow

The analytics platform supports the following business workflow.

Citizen
→ Submit Application
→ Eligibility Review
→ Case Processing
→ Approval / Denial
→ Benefit Administration
→ Program Reporting
→ Analytics & Decision Support

Each business activity produces operational data that becomes the foundation for analytics.

The role of the analytics platform is not to replace business operations, but to transform operational data into trusted business insights.

---

# 5. Product Vision

Build a production-inspired analytics platform that transforms raw operational data into trusted business metrics through:

- Reliable data pipelines
- Data quality validation
- Standardized business metrics
- Analytics dashboards
- Monitoring
- Clear documentation

---

# 6. Product Scope

## Included

- Data ingestion
- Data transformation
- Data validation
- Business metrics
- Dashboard
- Monitoring
- Documentation

## Not Included

- Machine Learning
- Real-time streaming
- Case management
- Citizen portal
- AI prediction

---

# 7. Design Principles

This project follows six principles.

1. Start with the business problem.
2. Understand the business workflow before designing analytics.
3. Standardize business definitions before building dashboards.
4. Treat data quality as part of the product.
5. Design reusable analytics assets.
6. Build iteratively like a production team.

---

# 8. Success Criteria

The project is successful if it demonstrates:

- Business-first thinking
- End-to-end analytics workflow
- Production-inspired architecture
- Trusted business metrics
- Professional documentation
- Ability to clearly explain design decisions during interviews

---

# 9. What's Next

The next design stage focuses on the technical implementation:

- System Architecture
- Data Pipeline
- Validation Strategy
- Data Model
- Dashboard Design
- Monitoring
