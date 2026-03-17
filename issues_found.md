# Issues found

## openai.NotFoundError: Error code: 404 - 

{'code': '404', 'message': 'Authorization failed or requested resource not found.'}

We need to set up a policy to use API key in the chosen compartment

see the following doc:
[policy for API keys](https://docs.oracle.com/en-us/iaas/Content/generative-ai/add-api-permission.htm)

```
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid where ALL { request.principal.type='generativeaiapikey' }
```

## policy needed
```
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid where ALL {request.principal.type='generativeaiapikey'}
allow any-user to manage generative-ai-project in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-file in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-vector-store in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid

allow any user to manage generative-ai-file in compartment <compartment-id> where ALL { target.generativeaiproject.id='ocid1.generativeaiproject.oc1.......'}
```
