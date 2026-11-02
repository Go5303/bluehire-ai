from app.agent.tools.job_tools import search_jobs_tool

result = search_jobs_tool.invoke({
    "city": "苏州",
    "min_salary": 5000,
    "has_night_shift": False,
    "limit": 5,
})

print(result)