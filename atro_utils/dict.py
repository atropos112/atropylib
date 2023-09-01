import json
import difflib
import logging
import yaml
from copy import deepcopy
from pathlib import Path

def merge_dicts(current_dict: dict, updating_dict: dict, overwrite: bool = False, current_name: str | None = None, updating_dict_name: str | None = None) -> dict:
  """
  Updates a dictionary with another dictionary.
  If overwrite is False, then only keys that do not exist in the current dictionary will be added.
  """
  
  old = deepcopy(current_dict)
  new = {}
  
  if overwrite:
    new = deepcopy(current_dict)
    new.update(updating_dict)
  else:
    new = deepcopy(updating_dict)
    new.update(current_dict)
    
  if current_name and updating_dict_name:
    logging.info(f"Updating {current_name} with {updating_dict_name} with overwrite set to {overwrite}.")
  elif current_name:
    logging.info(f"Updating {current_name} with overwrite set to {overwrite}.")
  else:
    logging.info(f"Updating dictionary with overwrite set to {overwrite}.")
    
  if all([key is str for key in current_dict.keys()]) and all([key is str for key in updating_dict.keys()]):
    # Convert dictionaries to JSON strings
    old_json = json.dumps(old, sort_keys=True, indent=4)
    new_json = json.dumps(new, sort_keys=True, indent=4)
    
    # Perform the diff
    diff = difflib.ndiff(old_json.splitlines(), new_json.splitlines())
    only_diff = [l for l in diff if l.startswith('+ ') or l.startswith('- ')]
    
    
    if len(only_diff) > 0:
      logging.info("The following changes were made:")
      logging.info("\n".join(only_diff))  
    else:
      logging.info("No changes were made.")
    
  return new

def log_yaml_load_diff(current: dict, yaml_path: Path, overwrite: bool = False, current_name: str | None = None, yaml_name: str | None = None) -> dict:
  yaml_name = yaml_name or yaml_path.as_posix()
  
  if not yaml_path.exists():
    logging.info(f"File in {yaml_path.as_posix()} does not exist, skipping.")
    return current
  
  # Load YAML file into a dictionary
  with open(yaml_path, 'r') as f:
    yaml_dict = yaml.safe_load(f)
  
  return merge_dicts(current, yaml_dict, overwrite, current_name, yaml_name)
  