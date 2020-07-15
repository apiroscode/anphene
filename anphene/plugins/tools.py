def get_updated_configuration(configuration, fields):
    updated_configuration = []
    for field in fields:
        data = next((item for item in configuration if item["name"] == field), None)
        if data and data.get("value", "false") == "true":
            updated_configuration.append({"name": field, "value": "false"})
    return updated_configuration
