import yaml
import os
import json

def load_config_yaml(file_path='config.yaml'):
    """Load configuration from a YAML file."""
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return {}
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        print(f"Error parsing {file_path}: {e}")
        return {}

#Cleanup all jsons which have api_key exposed in parent folder
def cleanup_exposed_api_keys(parent_folder='.'):
    """Delete any JSON files in the parent folder that contain exposed API keys."""
    for file in os.listdir(parent_folder):
        if file.endswith('.json'):
            file_path = os.path.join(parent_folder, file)
            # Check if this json file has "apikey" field and delete that field
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue
            if 'apikey' in data:
                print(f"Removing exposed API key from {file_path}")
                del data['apikey']
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                    
if __name__ == "__main__":
    # Example usage
    config = load_config_yaml()
    print("Loaded configuration:", config)
    
    cleanup_exposed_api_keys()
                    