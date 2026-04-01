# Issues Found

## 1) Authorization Error (`404`)

Error seen:

```text
openai.NotFoundError: Error code: 404
{'code': '404', 'message': 'Authorization failed or requested resource not found.'}
```

Likely cause:
- Missing IAM policy for API key usage in the target compartment.

Reference:
- [OCI policy for API keys](https://docs.oracle.com/en-us/iaas/Content/generative-ai/add-api-permission.htm)

Minimum example policy:

```text
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid where ALL { request.principal.type='generativeaiapikey' }
```

## 2) Vector Store Header Requirement (LA)

As of March 19, 2026 (LA), all Vector Store-related calls must include the project header:

```text
OpenAI-Project: <PROJECT_ID>
```

Without this header, Vector Store operations may fail even when authentication is valid.

## 3) Additional IAM Policies Often Needed

```text
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid where ALL {request.principal.type='generativeaiapikey'}
allow any-user to manage generative-ai-project in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-file in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-vector-store in compartment id ocid1.compartment.oc1..your_ocid
allow any-user to manage generative-ai-family in compartment id ocid1.compartment.oc1..your_ocid

allow any-user to manage generative-ai-file in compartment id ocid1.compartment.oc1..your_ocid where ALL { target.generativeaiproject.id='ocid1.generativeaiproject.oc1.......' }

allow any-user to read object-family in compartment id ocid1.compartment.oc1..your_ocid where ALL { request.principal.type='generativeaivectorconnector' }
```

## 4) Test Matrix (Examples + Utilities)

Legend:
- `✅` working
- `❌` not working
- `⬜` not verified yet

| File | Status |
|---|---|
| [example01.py](examples/example01.py) | ✅ |
| [example02.py](examples/example02.py) | ✅ |
| [example03.py](examples/example03.py) | ✅ |
| [example04.py](examples/example04.py) | ✅ |
| [example05.py](examples/example05.py) | ✅ |
| [example06.py](examples/example06.py) | ✅ |
| [example07.py](examples/example07.py) | ✅ |
| [example11.py](examples/example11.py) | ✅ |
| [example12.py](examples/example12.py) | ✅ |
| [example13.py](examples/example13.py) | ✅ |
| [example14.py](examples/example14.py) | ✅ |
| [example15.py](examples/example15.py) | ⬜ |
| [example16.py](examples/example16.py) | ✅ |
| [example17.py](examples/example17.py) | ✅ |
| [example18.py](examples/example18.py) | ✅ |
| [example21.py](examples/example21.py) | ✅ |
| [list_all_files.py](examples/list_all_files.py) | ✅ |
| [delete_all_files.py](examples/delete_all_files.py) | ⬜ |
| [list_all_vector_stores.py](examples/list_all_vector_stores.py) | ✅ |
| [delete_all_vs.py](examples/delete_all_vs.py) | ⬜ |
