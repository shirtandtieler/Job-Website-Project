from werkzeug.urls import url_encode


def modify_query(request, **new_values):
    args = request.args.copy()
    for key, val in new_values.items():
        args[key] = val
    return f"{request.path}?{url_encode(args)}"
