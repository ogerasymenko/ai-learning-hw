# Terraform state

- Use a remote backend (S3 + DynamoDB lock) so two people never apply at once.
- Never edit the state file by hand; use `terraform state mv` / `rm`.
- State can contain secrets in plain text: restrict access to the bucket.
- `terraform plan -out=plan.out` then apply that exact file.
