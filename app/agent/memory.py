from langgraph.store.memory import InMemoryStore

# 1.初始化长期记忆Store
memory_store = InMemoryStore()

namespaceStr = "preferences"

memoryStoreKey = "job_preferences"

# 2.保存用户求职偏好
def save_user_preferences(
    user_id: str,
    city: str | None = None,
    min_salary: int | None = None,
    avoid_night_shift: bool | None = None,
) -> None:

    namespace = (user_id, namespaceStr)

    # 先获取旧的偏好，避免更新一个字段覆盖其他字段
    old = memory_store.get(namespace, memoryStoreKey)

    data = dict(old.value) if old else {}

    if city is not None:
        data["city"] = city

    if min_salary is not None:
        data["min_salary"] = min_salary

    if avoid_night_shift is not None:
        data["avoid_night_shift"] = avoid_night_shift

    return memory_store.put(
        namespace,
        memoryStoreKey,
        data,
    )

# 3. 获取用户求职偏好
def get_user_preferences(user_id: str) -> dict:

    namespace = (user_id, namespaceStr)

    item = memory_store.get(
        namespace,
        memoryStoreKey
    )

    return dict(item.value) if item else {}


# 4. 本地测试
if __name__ == "__main__":

    save_user_preferences(
        user_id="user_001",
        city="苏州",
        min_salary=6000,
        avoid_night_shift=True,
    )

    print(get_user_preferences("user_001"))

    # 单独更新薪资，不覆盖城市和夜班
    save_user_preferences(
        user_id="user_001",
        min_salary=7000,
    )

    print(get_user_preferences("user_001"))
    print(get_user_preferences("user_002"))
