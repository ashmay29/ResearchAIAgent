import google.generativeai as genai

genai.configure(api_key="AIzaSyB39lj_wXYamcs6J7_Sams46x9s8GvHQaY")
models = genai.list_models()
for m in models:
    print(m.name, getattr(m, "supported_generation_methods", None))
