[![Build Status](https://travis-ci.org/statuspage/statuspage.svg?branch=master)](https://travis-ci.org/sesam-community/statuspage)
# statuspage

You can monitor any sesam-node instance (up or down) on statuspage.io using this microservice.

Here , an example of system config for this inside a node.

"SESAM_API_URL", "JWT", "PAGE_ID", "COMPONENT_ID", "API_KEY" : These are required environment variables. 

This script works with both self-service multinodes and single (normal) nodes.

```json
{
  "_id": "monitoring-node",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "API_KEY": "<your status page api-key>",
      "COMPONENT_ID": "<your status page component id>",
      "JWT": "<your node jwt key to access that node>",
      "LOG_LEVEL": "INFO",
      "PAGE_ID": "<your status page page-id>",
      "SESAM_API_URL": "<your node instance url like: https://yournode.sesam.cloud/api >"
    },
    "image": "sesamcommunity/statuspage:1.1.0",
    "port": 5000
  },
  "verify_ssl": true
}
```

You can also specify some optional environment variables to automatically send emails based off of which subnodes are down or if a signle node is down.

```
    "SMTP_HOST": "smtp.office365.com:587",
    "SMTP_PASSWORD": "$SECRET(smpt_password)",
    "SMTP_SENDER": "SesamMailSender@<customer.org>",
    "SMTP_USERNAME": "SesamMailSender@<customer.org>"
```