from django.shortcuts import render

from .agent import run_agent


def home(request):

    if request.method == "POST":

        destination = request.POST.get("destination")
        days = request.POST.get("days")
        purpose = request.POST.get("purpose")
        activities = request.POST.get("activities")

        result = run_agent(
            destination,
            days,
            purpose,
            activities
        )

        return render(
            request,
            "packing/index.html",
            {
                "result": result
            }
        )

    return render(
        request,
        "packing/index.html"
    )