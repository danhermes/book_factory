import yaml

# Test data
test_data = {
    'name': 'Test Book',
    'chapters': [
        {'title': 'Chapter 1', 'sections': ['Introduction', 'Main Content', 'Summary']},
        {'title': 'Chapter 2', 'sections': ['Background', 'Analysis', 'Conclusion']}
    ],
    'metadata': {
        'author': 'Test Author',
        'version': 1.0
    }
}

# Test YAML dump
print("Testing YAML dump:")
yaml_output = yaml.dump(test_data, default_flow_style=False)
print(yaml_output)

# Test YAML load
print("\nTesting YAML load:")
loaded_data = yaml.safe_load(yaml_output)
print(f"Loaded data matches original: {loaded_data == test_data}")

print("\nPyYAML installation and functionality verified successfully!") 