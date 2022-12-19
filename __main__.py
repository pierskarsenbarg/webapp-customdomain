"""An Azure RM Python Pulumi program"""

from pulumi import export, Output, FileArchive
from pulumi_azure_native import resources, web, storage
import pulumi_docker as docker

# Create an Azure Resource Group
resource_group = resources.ResourceGroup("resource_group")

# app_service = web.AppServicePlan(
#     "appservice",
#     resource_group_name=resource_group.name,
#     kind="Linux",
#     sku=web.SkuDescriptionArgs(tier="Dynamic", name="Y1"),
#     reserved=True,
# )

storage_account = storage.StorageAccount(
    "sa",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
    kind=storage.Kind.STORAGE_V2,
)

blob_container = storage.BlobContainer(
    "blobcontainer",
    account_name=storage_account.name,
    public_access=storage._inputs.PublicAccess.NONE,
    resource_group_name=resource_group.name,
)

blob = storage.Blob(
    "function_zip",
    account_name=storage_account.name,
    container_name=blob_container.name,
    resource_group_name=resource_group.name,
    type=storage._inputs.BlobType.BLOCK,
    source=FileArchive("./functions"),
)

blob_sas = storage.list_storage_account_service_sas_output(
    account_name=storage_account.name,
    protocols=storage._enums.HttpProtocol.HTTPS,
    shared_access_expiry_time="2029-01-01",
    shared_access_start_time="2022-01-01",
    resource=storage._enums.SignedResource.C,
    resource_group_name=resource_group.name,
    permissions=storage._enums.Permissions.R,
    canonicalized_resource=Output.format("/blob/{0}/{1}", storage_account.name, blob_container.name),
    content_encoding="deflate",
    content_disposition="inline",
).apply(lambda sas: sas.service_sas_token)

signed_blob_url = Output.format("https://{0}.blob.core.windows.net/{1}/{2}?{3}", storage_account.name, blob_container.name, blob.name, blob_sas)

export("sas", signed_blob_url)

primary_storage_key = storage.list_storage_account_keys_output(
    storage_account.name, resource_group_name=resource_group.name
).apply(lambda account_keys: account_keys.keys[0].value)

connection_string = Output.format(
    "DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1}",
    storage_account.name,
    primary_storage_key,
)

export("connection_string", connection_string)

app = web.WebApp(
    "functionapp",
    kind="FunctionApp",
    resource_group_name=resource_group.name,
    # server_farm_id=app_service.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(name="runtime", value="python"),
            web.NameValuePairArgs(name="FUNCTIONS_WORKER_RUNTIME", value="python"),
            web.NameValuePairArgs(
                name="WEBSITE_RUN_FROM_PACKAGE", value=signed_blob_url
            ),
            web.NameValuePairArgs(name="FUNCTIONS_EXTENSION_VERSION", value="~4"),
            web.NameValuePairArgs(name="AzureWebJobsStorage", value=connection_string),
        ]
    ),
)

export("function_name", app.name)

# export("connect", connection_string)

# app = web.WebApp("functionapp",
#     kind="FunctionApp",
#     resource_group_name=resource_group.name,
#     server_farm_id=app_service.id,
#     site_config=web.SiteConfigArgs(
#     app_settings=[
#     web.NameValuePairArgs(name="runtime", value="node"),
#     web.NameValuePairArgs(name="FUNCTIONS_WORKER_RUNTIME", value="node"),
#     web.NameValuePairArgs(name="WEBSITE_NODE_DEFAULT_VERSION", value="~16"),
#     web.NameValuePairArgs(name="FUNCTIONS_EXTENSION_VERSION", value="~3"),
#     web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_URL", value=container_registry.login_server),
#     web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_USERNAME", value=admin_username),
#     web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_PASSWORD", value=admin_password),
#     ],
#     always_on=True,
#     linux_fx_version=image.image_name.apply(lambda image_name: f"DOCKER|{image_name}")
#     ),
#     https_only=True,

#     )

export("resource_group_name", resource_group.name)
export("url", app.default_host_name.apply(lambda host: f"https://{host}/api/HelloWorld"))



# from stack

# https://safcff285e.blob.windows.net/blobcontainer/function_zip?sv=2015-04-05&sr=c&spr=https&st=2022-01-01T00%3A00%3A00.0000000Z&se=2030-12-31T00%3A00%3A00.0000000Z&sp=r&sig=rzhjr%2BNZJX0Dx69FQgAYa4QFf%2BIjv351vxkW7b%2ByjPg%3D
# https://safcff285e.blob.core.windows.net/blobcontainer/function_zip?sp=r&st=2022-12-16T15:28:53Z&se=2022-12-16T23:28:53Z&spr=https&sv=2021-06-08&sr=b&sig=2O%2BGwU13DYrqAVyOAARVq0zIbSRbJICQcs5CXUcXIZU%3D

# from portal