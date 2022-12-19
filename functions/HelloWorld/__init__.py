# Copyright 2016-2021, Pulumi Corporation.  All rights reserved.
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    body = 'Hello, world!'
    return func.HttpResponse(
        body,
        status_code=200)