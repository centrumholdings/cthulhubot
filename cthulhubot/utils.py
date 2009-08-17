

def dispatch_post(request, function_dict, kwargs=None):
    """
    Dispatch POST request according to function dictionary.

    function_dict format is {
        "post_value" : callable
    }

    If post value is present in request.POST, then callable is called with
    request.POST as first argument and optional **kwargs then. Result is then returned
    """
    if request.method == "POST":
        for recognized_post_value in function_dict:
            if request.POST.get(recognized_post_value, None):
                return function_dict[recognized_post_value](request.POST, **(kwargs or {}))

