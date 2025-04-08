"""
Simple verification script to check if the refactoring was successful
without requiring all dependencies.
"""

import ast
import sys

def verify_refactoring():
    """Check if the required methods exist in playback.py"""
    try:
        with open('playback.py', 'r') as f:
            source = f.read()
        
        # Parse the Python code
        tree = ast.parse(source)
        
        # Look for our methods
        methods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ['_build_midi_selection_dialog', 
                                            '_run_midi_selection_loop', 
                                            '_load_midi_file']:
                methods.add(node.name)

        
        # Check if all required methods exist
        required = {'_build_midi_selection_dialog', 
                   '_run_midi_selection_loop', 
                   '_load_midi_file'}
        
        if required.issubset(methods):
            print("Verification successful! All required methods found.")
            return True
        else:
            missing = required - methods
            print(f"Verification failed. Missing methods: {missing}")
            return False
    
    except Exception as e:
        print(f"Verification failed with error: {e}")
        return False

if __name__ == "__main__":
    success = verify_refactoring()
    sys.exit(0 if success else 1)
