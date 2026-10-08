"""
In-memory Course Knowledge Graph
Contains: course catalog per skill, pre-populated for job applicant gap-skill remediation.

Keys are lowercase skill slugs (spaces → underscores, dots removed, e.g., 'ci/cd', 'typescript', 'aws').
"""

COURSE_KG = {
    "aws": [
        {
            "title": "AWS Cloud Practitioner Essentials",
            "platform": "Google",
            "url": "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/",
            "duration": "6 hours",
            "duration_hours": 6,
            "free": True,
            "level": "foundational",
            "description": "A foundational introduction to Amazon Web Services (AWS) services, terminology, security, and architecture."
        },
        {
            "title": "Ultimate AWS Certified Developer Associate",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/aws-certified-developer-associate-dva-c01/",
            "duration": "32 hours",
            "duration_hours": 32,
            "free": False,
            "level": "intermediate",
            "description": "Full preparation course for the AWS Developer Associate certification, covering Serverless, ECS, DynamoDB, CI/CD, and monitoring."
        },
        {
            "title": "AWS Solutions Architect Masterclass",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=Ia-UEYYR44s",
            "duration": "10 hours",
            "duration_hours": 10,
            "free": True,
            "level": "advanced",
            "description": "Detailed free course for AWS solutions design, focusing on VPC networking, high availability, database scaling, and IAM security."
        }
    ],
    "kubernetes": [
        {
            "title": "Kubernetes for the Absolute Beginner",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/learn-kubernetes/",
            "duration": "6 hours",
            "duration_hours": 6,
            "free": False,
            "level": "foundational",
            "description": "Learn Kubernetes basics including Pods, Services, ReplicaSets, Deployments, and YAML configuration with hands-on practice."
        },
        {
            "title": "Kubernetes Tutorial for Beginners [Crash Course]",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=VnvRFRk_51k",
            "duration": "4 hours",
            "duration_hours": 4,
            "free": True,
            "level": "foundational",
            "description": "An excellent visual walk-through of Kubernetes architecture, deployments, services, ingress, and configmaps."
        },
        {
            "title": "Certified Kubernetes Administrator (CKA) Full Course",
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=3gb-Zyqe63Y",
            "duration": "11 hours",
            "duration_hours": 11,
            "free": True,
            "level": "advanced",
            "description": "Deep dive into cluster setup, networking, storage provisioning, troubleshooting, and direct preparation for the official CKA exam."
        }
    ],
    "ci/cd": [
        {
            "title": "Introduction to Git, GitHub, and CI/CD Pipelines",
            "platform": "Coursera",
            "url": "https://www.coursera.org/learn/introduction-git-github",
            "duration": "12 hours",
            "duration_hours": 12,
            "free": True,
            "level": "foundational",
            "description": "Understand version control with Git, repository management on GitHub, and writing basic automated build/test actions."
        },
        {
            "title": "GitHub Actions: Continuous Integration and Deployment (CI/CD)",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/github-actions-ci-cd/",
            "duration": "8 hours",
            "duration_hours": 8,
            "free": False,
            "level": "intermediate",
            "description": "Learn to write real-world GitHub Actions workflows for testing, linting, Docker image building, and automated cloud deployments."
        },
        {
            "title": "Advanced CI/CD Pipelines with GitLab & Jenkins",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=8hLYX5yJ270",
            "duration": "5 hours",
            "duration_hours": 5,
            "free": True,
            "level": "advanced",
            "description": "Master advanced topics like parallel execution, caching, artifacts, and multi-stage container deployment pipelines."
        }
    ],
    "typescript": [
        {
            "title": "TypeScript Crash Course for Beginners",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=gp5H0Vw39k0",
            "duration": "4 hours",
            "duration_hours": 4,
            "free": True,
            "level": "foundational",
            "description": "Learn static typing, basic compiler configuration, interface definitions, and basic OOP principles using TypeScript."
        },
        {
            "title": "Understanding TypeScript - 2026 Edition",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/understanding-typescript/",
            "duration": "15 hours",
            "duration_hours": 15,
            "free": False,
            "level": "intermediate",
            "description": "Deep dive into TypeScript including generics, decorators, namespace modules, Webpack bundling, and React integration."
        },
        {
            "title": "Advanced TypeScript Workshop & Generic Masterclass",
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=3oShXsMc5QA",
            "duration": "6 hours",
            "duration_hours": 6,
            "free": True,
            "level": "advanced",
            "description": "Learn advanced type manipulation, utility types, conditional types, mapped types, and complex TS application architectures."
        }
    ],
    "graphql": [
        {
            "title": "GraphQL Crash Course with Node.js & Express",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=ed8SzALpx1Q",
            "duration": "3 hours",
            "duration_hours": 3,
            "free": True,
            "level": "foundational",
            "description": "Build a solid foundation in GraphQL schemas, queries, mutations, resolvers, and connecting to databases."
        },
        {
            "title": "GraphQL APIs with React & Node.js (Apollo Server)",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/graphql-react-node/",
            "duration": "14 hours",
            "duration_hours": 14,
            "free": False,
            "level": "intermediate",
            "description": "Build and deploy type-safe GraphQL APIs using Apollo Server, Apollo Client, React hooks, and authentication integrations."
        },
        {
            "title": "Advanced GraphQL: Caching, Batching, and DataLoader",
            "platform": "freeCodeCamp",
            "url": "https://www.youtube.com/watch?v=uK1XW1p6r5c",
            "duration": "5 hours",
            "duration_hours": 5,
            "free": True,
            "level": "advanced",
            "description": "Solve the N+1 query problem using DataLoader. Learn schema federation, query complexity analysis, and database pooling."
        }
    ],
    "security": [
        {
            "title": "Introduction to IT Security and Cybersecurity",
            "platform": "Coursera",
            "url": "https://www.coursera.org/learn/it-security",
            "duration": "15 hours",
            "duration_hours": 15,
            "free": True,
            "level": "foundational",
            "description": "Google-taught fundamentals of digital security, networks, cryptography, access controls, and threat modeling."
        },
        {
            "title": "Web Security & OWASP Top 10 Masterclass",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/web-security-owasp-top10/",
            "duration": "9 hours",
            "duration_hours": 9,
            "free": False,
            "level": "intermediate",
            "description": "Practical hands-on exploitation and remediation of the top 10 web vulnerabilities including XSS, SQLi, CSRF, and SSRF."
        },
        {
            "title": "OAuth 2.0 and OpenID Connect: The Complete Guide",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/oauth-2-and-openid-connect-in-simple-terms/",
            "duration": "6 hours",
            "duration_hours": 6,
            "free": False,
            "level": "advanced",
            "description": "Master authorization and identity standards. Learn scopes, authorization grant types, PKCE flow, and JWT token signatures."
        }
    ],
    "communication": [
        {
            "title": "Effective Communication in Technical Teams",
            "platform": "Coursera",
            "url": "https://www.coursera.org/specializations/effective-communication",
            "duration": "12 hours",
            "duration_hours": 12,
            "free": True,
            "level": "foundational",
            "description": "Learn to write clear documentation, present tech ideas to non-technical stakeholders, and collaborate effectively."
        },
        {
            "title": "Communication Skills for Software Engineers",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=F_fD-V0g1K4",
            "duration": "2 hours",
            "duration_hours": 2,
            "free": True,
            "level": "intermediate",
            "description": "Practical advice on navigating constructive feedback, sprint planning discussions, and cross-functional leadership."
        }
    ],
    "devops": [
        {
            "title": "DevOps Beginner Course: Linux, Git, & scripting",
            "platform": "YouTube",
            "url": "https://www.youtube.com/watch?v=hQcFE0Jg1AI",
            "duration": "6 hours",
            "duration_hours": 6,
            "free": True,
            "level": "foundational",
            "description": "Master basic Linux commands, bash scripting, Git branching, and basic networking concepts vital for DevOps."
        },
        {
            "title": "Docker and Kubernetes: The Practical Guide",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/docker-kubernetes-the-practical-guide/",
            "duration": "22 hours",
            "duration_hours": 22,
            "free": False,
            "level": "intermediate",
            "description": "Learn Docker images, containers, networks, volumes, and deploying single/multi-container apps to Kubernetes."
        },
        {
            "title": "Terraform Infrastructure as Code (IaC) Masterclass",
            "platform": "Udemy",
            "url": "https://www.udemy.com/course/terraform-hands-on-course/",
            "duration": "11 hours",
            "duration_hours": 11,
            "free": False,
            "level": "advanced",
            "description": "Provision complex multi-cloud resources. Master modules, workspace variables, remote state storage, and drift recovery."
        }
    ]
}
