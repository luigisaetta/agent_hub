# Issues found

## openai.NotFoundError: Error code: 404 - 

{'code': '404', 'message': 'Authorization failed or requested resource not found.'}

We need to set up a policy to use API key in the chosen compartment

see the following doc:
[policy for API keys](https://docs.oracle.com/en-us/iaas/Content/generative-ai/add-api-permission.htm)

```
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid where ALL { request.principal.type='generativeaiapikey' }
```

## preview of OCI SDK
To use Agent Hub features in pre-production environment (ppe) we need to install a preview version of OCI Python SDK.
```
pip install --trusted-host=artifactory.oci.oraclecorp.com -i https://artifactory.oci.oraclecorp.com/api/pypi/global-dev-pypi/simple -U oci==2.168.1+preview.1.347
```

## policy needed
```
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid where ALL {request.principal.type='generativeaiapikey'}
allow any-user to manage generative-ai-project in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-file in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-vector-store in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid

allow any user to manage generative-ai-file in compartment id ocid1.compartment.oc1..your_ocid where ALL { target.generativeaiproject.id='ocid1.generativeaiproject.oc1.......'}

allow any-user to read object-family in compartment id ocid1.compartment.oc1..your_ocid where ALL{request.principal.type='generativeaivectorconnector'}
```

## Test matrix (examples + utility)

Symbols to copy/paste: `✅` `❌`

| file | preprod | prod |
|---|---|---|
| example01.py | ✅ | ✅ |
| example02.py | ✅ | ✅ |
| example03.py | ✅ | ✅ |
| example04.py | ❌ | ✅ |
| example05.py | ✅ | ✅ |
| example06.py | ✅ | ✅ |
| example07.py | ✅ | ✅ |
| example11.py | ✅ | ❌ |
| example12.py | ✅ | ✅ |
| example13.py | ✅ | ⬜ |
| example14.py | ✅ | ⬜ |
| example15.py | ⬜ | ⬜ |
| example16.py | ❌ | ⬜ |
| example21.py | ❌ | ❌ |
| list_all_files.py | ✅ | ⬜ |
| delete_all_files.py | ⬜ | ⬜ |
| list_all_vector_stores.py | ✅ | ⬜ |
| delete_all_vs.py | ⬜ | ⬜ |
