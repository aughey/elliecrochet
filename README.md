# Ellie Does Crochet and Stuff

A markdown-driven static website generator that deploys to AWS S3 via GitHub Actions.

## How It Works

Edit `content/page.md` to update the site. Push to `main` and GitHub Actions automatically builds the HTML and deploys it to S3.

## Project Structure

```
content/
  page.md          # Site content (edit this)
  images/          # Site images (add/replace here)
templates/
  base.html        # HTML template (Jinja2)
scripts/
  generate_site.py # Builds the site
  deploy_s3.sh     # Deploys to S3
build/             # Generated output (gitignored)
```

## Editing Content

All content lives in `content/page.md`. The file uses YAML frontmatter for metadata and markdown for content.

### Frontmatter

```yaml
---
title: Ellie Does Crochet and Stuff
email: Eleanor@aughey.com
discord: patton_pup
---
```

### Sections

Top-level headings (`# Heading`) define page sections: Hero, About, Gallery, Contact, and Closing.

### Adding Images

Place images in `content/images/` and reference them in markdown:

```markdown
![Alt text](images/photo.jpg)
```

### Gallery Categories

Gallery categories are defined with `##` subheadings under the `# Gallery` section:

```markdown
# Gallery

A description of the gallery.

## Category Name

![Image 1](images/cat1.jpg)
![Image 2](images/cat2.jpg)

## Another Category

![Image 3](images/other1.jpg)
```

## Local Development

### Prerequisites

- Python 3.10+

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Build

```bash
python scripts/generate_site.py
open build/index.html
```

## Deploying to AWS S3

### 1. Create an S3 Bucket

1. Go to the [S3 console](https://s3.console.aws.amazon.com/) and create a bucket
2. Uncheck "Block all public access"
3. Enable **Static website hosting** under the bucket's Properties tab (set index document to `index.html`)
4. Add a bucket policy to allow public reads:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

### 2. Create an IAM User for Deployment

1. Go to the [IAM console](https://console.aws.amazon.com/iam/) and create a new user (e.g. `github-deployer`)
2. Attach a policy that grants access to your bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME",
        "arn:aws:s3:::YOUR-BUCKET-NAME/*"
      ]
    }
  ]
}
```

3. Create an access key for the user and save the credentials

### 3. Configure GitHub Secrets

In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add these secrets:

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user access key ID |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret access key |
| `AWS_REGION` | Your bucket's region (e.g. `us-east-1`) |
| `S3_BUCKET_NAME` | Your bucket name |

### 4. Push to Deploy

Once secrets are configured, every push to `main` triggers the GitHub Actions workflow which builds the site and syncs it to S3.

Your site will be available at:
```
http://YOUR-BUCKET-NAME.s3-website-REGION.amazonaws.com
```

### Manual Deploy

To deploy from your local machine:

```bash
source .venv/bin/activate
python scripts/generate_site.py
S3_BUCKET_NAME=your-bucket-name bash scripts/deploy_s3.sh
```

This requires the [AWS CLI](https://aws.amazon.com/cli/) configured with valid credentials.
