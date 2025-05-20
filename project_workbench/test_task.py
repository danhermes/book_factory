#!/usr/bin/env python
from crewai import Task
from pydantic import BaseModel

class TestOutput(BaseModel):
    result: str

def test_task_creation():
    print("Testing Task creation with proper context format...")
    try:
        # Create a task with the correct context format
        task = Task(
            description="Test task",
            expected_output="Test output",
            context=[
                {
                    "key": "test_key", 
                    "value": "test_value",
                    "description": "Test key description",
                    "expected_output": "A test value string"
                }
            ]
        )
        print("Task created successfully!")
        return True
    except Exception as e:
        print(f"Error creating task: {e}")
        return False

if __name__ == "__main__":
    test_task_creation()