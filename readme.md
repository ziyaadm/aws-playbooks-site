# AWS Static Site: playbooks.ziyaadm.com

A fully serverless, secure, and globally-distributed static site hosting Support Playbooks for job-seeking and tech ops workflows. Built as a personal AWS resume project using Terraform.

## 🔧 Tech Stack

- **AWS S3** – Static file storage
- **AWS CloudFront** – CDN + HTTPS delivery
- **AWS ACM** – TLS certificate for HTTPS
- **AWS Route 53** – DNS & domain management
- **Terraform** – Infrastructure as Code
- **OAC (Origin Access Control)** – Secure CloudFront-only access to S3

## 🌍 Live Site

👉 [https://playbooks.ziyaadm.com](https://playbooks.ziyaadm.com)

## 🎯 Project Goals

- Showcase modern AWS infrastructure skills
- Follow best practices: encryption, access control, IaC
- Build a real, publicly accessible static website
- Set foundation for CI/CD, monitoring, and future search functionality

## 🧠 How It Works (Simplified)

> "This is like setting up a secure storefront. The S3 bucket is the back room, CloudFront is the public storefront, and only CloudFront is allowed to fetch stuff from the back."

- **S3 Bucket** stores website files (e.g., PDFs, HTML)
- **Public access is blocked** on S3 completely
- **ACM Certificate** (in us-east-1) handles HTTPS
- **CloudFront** serves traffic securely and globally
- **Origin Access Control** gives CloudFront special permission to fetch from S3
- **Route 53** maps the custom domain to CloudFront
- **Terraform** defines and provisions all of it

## 🛠 Setup Instructions

> Requires AWS credentials and Terraform installed

```bash
cd infra/
terraform init
terraform validate
terraform plan
terraform apply
```

After deploy, upload files manually for now:

```bash
aws s3 cp playbooks/index.html s3://aws-playbooks-ziyaadm/index.html
```

## 🧱 Terraform Resources Used

- `aws_s3_bucket`, `public_access_block`, `encryption`, `versioning`
- `aws_acm_certificate` (DNS validated)
- `aws_route53_record`, `aws_route53_zone`
- `aws_cloudfront_distribution` + OAC
- `aws_s3_bucket_policy` scoped to CloudFront only
- `data.aws_caller_identity` for dynamic account ID resolution

## 🔐 Security Best Practices

- S3 bucket is not public
- CloudFront is the only allowed reader
- Files encrypted with SSE-S3
- HTTPS only, minimum TLS v1.2
- Terraform manages infra declaratively

## ✅ To Do / Next Steps

-

## 📄 License

MIT License

---

> Built as a resume project by Ziyaad Motala to showcase AWS + DevOps capabilities

