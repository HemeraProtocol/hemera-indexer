import random

from common.utils.exception_control import RetriableError, decode_response_error


# TODO: Implement fallback mechanism for provider uris instead of picking randomly
def pick_random_provider_uri(provider_uri):
    provider_uris = [uri.strip() for uri in provider_uri.split(",")]
    return random.choice(provider_uris)


def rpc_response_batch_to_results(response):
    for response_item in response:
        yield rpc_response_to_result(response_item)


def rpc_response_to_result(response):
    result = response.get("result")
    if result is None:
        error_message = "result is None in response {}.".format(response)
        if response.get("error") is None:
            error_message = error_message + " Make sure Ethereum node is synced."
            # When nodes are behind a load balancer it makes sense to retry the request in hopes it will go to other,
            # synced node
            raise RetriableError(error_message)
        elif response.get("error") is not None:
            return decode_response_error(response.get("error"))
        else:
            return result
    return result


def zip_rpc_response(requests, responses, index="request_id"):
    response_dict = {}
    for response in responses:
        response_dict[response["id"]] = response

    for request in requests:
        request_id = request.get(index) if isinstance(request, dict) else getattr(request, index)
        if request_id in response_dict:
            yield request, response_dict[request_id]
