# statuspage
You can monitor any sesam-node instance (up or down) on statuspage.io using this microservice.

You can create a docker image and just plug it as system in your node.

Here , an example of system config for this inside a node.

"SESAM_API_URL", "JWT", "PAGE_ID", "COMPONENT_ID", "API_KEY" : These are required environment variables. 


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
    "image": "your ms docker-image location ",
    "port": 5000
  },
  "verify_ssl": true
}

'''
