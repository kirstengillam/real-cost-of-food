# real-cost-of-food




## Project internal notes

main stack deployed on AWS, region us-east-1, account 111111111111

custom domain registered with cloudfare (supposed to be slightly cheaper?)
(just over $10/year)

## Before collecting any user data

If the site ever adds forms, accounts, or any user data collection, do the following before launching:
1. Set up a `privacy@[yourdomain].com` alias via Cloudflare Email Routing (free, forwards to your inbox)
2. Uncomment the contact section stub in `site/src/pages/privacy.astro` and fill in the alias

